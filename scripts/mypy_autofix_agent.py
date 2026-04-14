"""Mypy Autofix Agent - Intelligent mypy error resolution.

This script acts as an agent that:
1. Runs mypy and captures structured error output
2. Classifies each error by fixability
3. Applies real fixes where possible (import corrections, type narrowing)
4. Falls back to targeted # type: ignore[code] only when necessary

Usage:
    python scripts/mypy_autofix_agent.py \\
        [--max-fixes N] [--max-files N] [--dry-run] [--verbose]

Fix strategies and data types are in mypy_fixers.py.
"""

from __future__ import annotations

import argparse
import logging
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from mypy_fixers import (  # noqa: F401
    Fix,
    MypyError,
    fix_callable_as_type,
    fix_generic_suppression,
    fix_import_errors,
    fix_name_not_defined,
    fix_union_attr,
    is_safe_path,
    read_file_lines,
    write_file_lines,
)

logger = logging.getLogger(__name__)


@dataclass
class AgentReport:
    """Report of all actions taken."""

    total_errors: int = 0
    errors_fixed: int = 0
    real_fixes: int = 0
    suppressions: int = 0
    files_modified: list[str] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)
    skipped_reasons: list[str] = field(default_factory=list)


def run_mypy(config_file: str | None = None, targets: list[str] | None = None) -> str:
    """Run mypy and return raw output."""
    if config_file is not None and not isinstance(config_file, str):
        raise TypeError(
            f"config_file must be a str or None, got {type(config_file).__name__}"
        )
    if targets is not None and not isinstance(targets, list):
        raise TypeError(f"targets must be a list or None, got {type(targets).__name__}")
    if not targets:
        targets = []
        if Path("src").exists():
            targets.append("src")
        if Path("tests").exists():
            targets.append("tests")
        if not targets:
            targets = ["."]

    cmd = ["mypy"] + targets + ["--no-error-summary", "--show-error-codes"]
    if config_file:
        cmd.extend(["--config-file", config_file])
    cmd.extend(["--ignore-missing-imports", "--non-interactive"])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return result.stdout + result.stderr


def parse_mypy_output(output: str) -> list[MypyError]:
    """Parse mypy output into structured errors."""
    errors = []
    pattern = re.compile(
        r"^(.+?):(\d+):(\d+):\s+(error|note):\s+(.+?)(?:\s+\[([^\]]+)\])?\s*$"
    )
    for line in output.splitlines():
        match = pattern.match(line.strip())
        if match:
            file_path, line_no, col, severity, message, code = match.groups()
            if severity == "error" and code:
                errors.append(
                    MypyError(
                        file=file_path,
                        line=int(line_no),
                        column=int(col),
                        severity=severity,
                        message=message,
                        code=code or "unknown",
                    )
                )
    return errors


def _partition_errors(
    errors: list[MypyError], report: AgentReport
) -> dict[str, list[MypyError]]:
    """Split errors into safe-path files; record skips in report."""
    errors_by_file: dict[str, list[MypyError]] = defaultdict(list)
    for error in errors:
        if is_safe_path(error.file):
            errors_by_file[error.file].append(error)
        else:
            report.skipped_reasons.append(
                f"Skipped {error.file}:{error.line} - outside safe path"
            )
    return errors_by_file


def _record_fix(report: AgentReport, fix: Fix, verbose: bool) -> None:
    """Record a successful fix in the report and optionally log it."""
    if fix.strategy == "real-fix":
        report.real_fixes += 1
    else:
        report.suppressions += 1
    report.fixes_applied.append(
        f"  [{fix.strategy}] {fix.file}:{fix.line} - {fix.description}"
    )
    if verbose:
        logger.info(
            "  FIX: %s:%d [%s] %s", fix.file, fix.line, fix.strategy, fix.description
        )


def _apply_strategies_to_error(
    lines: list[str],
    error: MypyError,
    fix_strategies: list,
    report: AgentReport,
    verbose: bool,
) -> bool:
    """Try each strategy in order; record result in report. Return True if fixed."""
    fix = next((s(lines, error) for s in fix_strategies if s(lines, error)), None)
    if fix:
        _record_fix(report, fix, verbose)
        return True
    report.skipped_reasons.append(
        f"No fix available: {error.file}:{error.line}"
        f" [{error.code}] {error.message[:60]}"
    )
    return False


def _process_file(
    filepath: str,
    file_errors: list[MypyError],
    fix_strategies: list,
    report: AgentReport,
    max_fixes: int,
    dry_run: bool,
    verbose: bool,
    total_fixes: int,
) -> tuple[int, int]:
    """Apply fixes to one file; return (total_fixes, files_modified_delta)."""
    lines = read_file_lines(filepath)
    if not lines:
        return total_fixes, 0
    file_changed = False
    for error in sorted(file_errors, key=lambda e: e.line, reverse=True):
        if total_fixes >= max_fixes:
            break
        if _apply_strategies_to_error(lines, error, fix_strategies, report, verbose):
            total_fixes += 1
            file_changed = True
    if file_changed:
        if not dry_run:
            write_file_lines(filepath, lines)
        report.files_modified.append(filepath)
        return total_fixes, 1
    return total_fixes, 0


_DEFAULT_FIX_STRATEGIES = [
    fix_callable_as_type,
    fix_union_attr,
    fix_name_not_defined,
    fix_import_errors,
    fix_generic_suppression,
]


def _check_limits(
    filepath: str, files_modified: int, total_fixes: int, max_files: int, max_fixes: int
) -> str | None:
    """Return a skip reason string if a limit is reached, else None."""
    if files_modified >= max_files:
        return f"Skipped {filepath} - max files ({max_files}) reached"
    if total_fixes >= max_fixes:
        return f"Skipped {filepath} - max fixes ({max_fixes}) reached"
    return None


def _apply_fixes_across_files(
    errors_by_file: dict[str, list[MypyError]],
    report: AgentReport,
    max_fixes: int,
    max_files: int,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Iterate files in sorted order; apply fixes up to per-file/global limits."""
    files_modified = 0
    total_fixes = 0
    for filepath, file_errors in sorted(errors_by_file.items()):
        skip = _check_limits(
            filepath, files_modified, total_fixes, max_files, max_fixes
        )
        if skip:
            report.skipped_reasons.append(skip)
            continue
        total_fixes, delta = _process_file(
            filepath,
            file_errors,
            _DEFAULT_FIX_STRATEGIES,
            report,
            max_fixes,
            dry_run,
            verbose,
            total_fixes,
        )
        files_modified += delta
    report.errors_fixed = total_fixes


def run_agent(
    max_fixes: int = 20,
    max_files: int = 15,
    dry_run: bool = False,
    verbose: bool = False,
    config_file: str | None = None,
    targets: list[str] | None = None,
) -> AgentReport:
    """Main agent loop: observe, classify, fix, report."""
    report = AgentReport()
    if verbose:
        logger.info("Running mypy on targets: %s...", targets or "default")
    errors = parse_mypy_output(run_mypy(config_file, targets))
    report.total_errors = len(errors)
    if verbose:
        logger.info("Found %d mypy errors", len(errors))
    if not errors:
        logger.info("No mypy errors found.")
        return report
    _apply_fixes_across_files(
        _partition_errors(errors, report),
        report,
        max_fixes,
        max_files,
        dry_run,
        verbose,
    )
    return report


def log_report(report: AgentReport) -> None:
    """Log a human-readable report."""
    logger.info("=" * 60)
    logger.info("  MYPY AUTOFIX AGENT REPORT")
    logger.info("=" * 60)
    logger.info("  Total mypy errors found:  %d", report.total_errors)
    logger.info("  Errors fixed:             %d", report.errors_fixed)
    logger.info("    Real fixes:             %d", report.real_fixes)
    logger.info("    Suppressions:           %d", report.suppressions)
    logger.info("  Files modified:           %d", len(report.files_modified))
    if report.fixes_applied:
        logger.info("  Fixes applied:")
        for fix_desc in report.fixes_applied:
            logger.info("  %s", fix_desc)
    if report.skipped_reasons:
        logger.info("  Skipped (%d):", len(report.skipped_reasons))
        for reason in report.skipped_reasons[:10]:
            logger.info("    - %s", reason)
        if len(report.skipped_reasons) > 10:
            logger.info("    ... and %d more", len(report.skipped_reasons) - 10)
    logger.info("=" * 60)


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Mypy Autofix Agent - Intelligently fix mypy errors"
    )
    parser.add_argument("--max-fixes", type=int, default=20)
    parser.add_argument("--max-files", type=int, default=15)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--config-file", type=str, default=None)
    parser.add_argument("targets", nargs="*")
    args = parser.parse_args()

    report = run_agent(
        max_fixes=args.max_fixes,
        max_files=args.max_files,
        dry_run=args.dry_run,
        verbose=args.verbose,
        config_file=args.config_file,
        targets=args.targets,
    )
    log_report(report)

    if report.errors_fixed > 0:
        return 0
    if report.total_errors > 0:
        return 1
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sys.exit(main())
