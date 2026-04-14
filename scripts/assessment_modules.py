"""Per-category analysis logic for the run_assessment script.

Each public function here handles one assessment category (A-O) and returns
a tuple of (findings, score) where findings is a list of markdown bullet
strings and score is an int 0-10 or None when it cannot be determined.

The entry point is analyze_module(), which dispatches to the right helper.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from scripts.shared.subprocess_utils import run_command

_EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".tox",
    "build",
    "dist",
}


def find_python_files() -> list[Path]:
    """Find all Python files in the repository."""
    python_files: list[Path] = []
    for pattern in ["**/*.py"]:
        python_files.extend(Path(".").glob(pattern))
    return [f for f in python_files if not any(p in f.parts for p in _EXCLUDED_DIRS)]


def count_test_files() -> int:
    """Count test files in the repository."""
    test_files: set[Path] = set()
    for pattern in ["**/test_*.py", "**/*_test.py", "**/tests/*.py"]:
        test_files.update(Path(".").glob(pattern))
    return len(test_files)


def check_documentation() -> dict:
    """Check documentation status."""
    return {
        "has_readme": Path("README.md").exists(),
        "has_docs_dir": Path("docs").exists(),
        "has_changelog": Path("CHANGELOG.md").exists(),
    }


def grep_in_files(pattern: str, files: list[Path]) -> int:
    """Count files containing a pattern."""
    count = 0
    for file in files:
        try:
            if re.search(pattern, file.read_text(encoding="utf-8")):
                count += 1
        except Exception:  # noqa: BLE001
            pass
    return count


def file_discovery() -> tuple[list[Path], int]:
    """Discover Python source files and return them with a count."""
    python_files = find_python_files()
    return python_files, len(python_files)


def _analyze_a(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """Code Structure (A)."""
    findings: list[str] = []
    score: int | None = 10
    has_src = Path("src").exists()
    has_tests = (
        Path("tests").exists()
        or Path("src/tests").exists()
        or (file_count > 0 and count_test_files() > 0)
    )
    findings.append(f"- Python files found: {file_count}")
    findings.append(f"- Source directory structure (src/): {'Y' if has_src else 'N'}")
    findings.append(f"- Tests directory/files: {'Y' if has_tests else 'N'}")
    if not has_src:
        score -= 2  # type: ignore[operator]
    if not has_tests:
        score -= 2  # type: ignore[operator]
    return findings, score


def _analyze_b(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """Documentation (B)."""
    findings: list[str] = []
    score: int | None = 10
    docs = check_documentation()
    findings.append(f"- README.md: {'Y' if docs['has_readme'] else 'N'}")
    findings.append(f"- docs/ directory: {'Y' if docs['has_docs_dir'] else 'N'}")
    findings.append(f"- CHANGELOG.md: {'Y' if docs['has_changelog'] else 'N'}")

    docstring_count = sum(
        1
        for p in python_files[:10]
        if '"""' in p.read_text(encoding="utf-8")
        or "'''" in p.read_text(encoding="utf-8")
    )
    checked = min(10, len(python_files))
    if checked > 0:
        pct = (docstring_count / checked) * 100
        findings.append(f"- Docstring presence (sample): {pct:.0f}%")
        if pct < 50:
            score -= 2  # type: ignore[operator]
    if not docs["has_readme"]:
        score -= 3  # type: ignore[operator]
    if not docs["has_docs_dir"]:
        score -= 1  # type: ignore[operator]
    return findings, score


def _analyze_c(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """Test Coverage (C)."""
    findings: list[str] = []
    score: int | None = 10
    test_count = count_test_files()
    findings.append(f"- Test files found: {test_count}")
    if test_count == 0:
        score -= 5  # type: ignore[operator]
        findings.append("- Critical: No tests found")
    elif test_count < 5:
        score -= 2  # type: ignore[operator]
        findings.append("- Warning: Low number of test files")
    else:
        findings.append("- Good number of test files")
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        cmd = [sys.executable, "-m", "pytest", "--cov=src", "--cov-report=term-missing"]
        result = run_command(cmd, check=False, env=env)
        if result.returncode == 0:
            findings.append("- Pytest execution: passed")
            m = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", result.stdout)
            if m:
                cov = int(m.group(1))
                findings.append(f"- Coverage: {cov}%")
                if cov < 50:
                    score -= 2  # type: ignore[operator]
                elif cov < 80:
                    score -= 1  # type: ignore[operator]
        else:
            findings.append(f"- Pytest execution: failed (exit {result.returncode})")
            score -= 2  # type: ignore[operator]
    except Exception as e:  # noqa: BLE001
        findings.append(f"- Pytest execution failed to start: {e}")
    return findings, score


def _analyze_d(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """Error Handling (D)."""
    findings: list[str] = []
    score: int | None = 10
    try_count = grep_in_files(r"try:", python_files)
    _except_pat = r"except Exception as e:"  # noqa: BLE001
    except_count = grep_in_files(_except_pat, python_files)
    findings.append(f"- Files with try blocks: {try_count}")
    findings.append(f"- Files with except blocks: {except_count}")
    if try_count == 0:
        score -= 2  # type: ignore[operator]
        findings.append("- Warning: No error handling detected in sample")
    return findings, score


def _analyze_e(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """Performance (E)."""
    findings: list[str] = []
    score: int | None = 10
    perf = grep_in_files(r"import cProfile|import timeit|import pstats", python_files)
    sleep_uses = grep_in_files(r"time\.sleep", python_files)
    findings.append(f"- Files with performance tools: {perf}")
    findings.append(f"- Files using time.sleep: {sleep_uses}")
    if perf == 0:
        findings.append("- Note: No explicit performance profiling tools found in code")
        score -= 1  # type: ignore[operator]
    if sleep_uses > 2:
        findings.append("- Warning: Multiple uses of time.sleep detected")
        score -= 1  # type: ignore[operator]
    return findings, score


def _analyze_f(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """Security (F)."""
    findings: list[str] = []
    score: int | None = 10
    shell_true = grep_in_files(r"subprocess\..*shell=True", python_files)
    if shell_true > 0:
        findings.append(
            f"- Critical: subprocess with shell=True found in {shell_true} files"
        )
        score -= 3  # type: ignore[operator]
    else:
        findings.append("- subprocess with shell=True: Not found (Good)")
    secrets_found = grep_in_files(r"api_key|password|secret|token", python_files)
    if secrets_found > 0:
        findings.append(f"- Warning: Potential secrets found in {secrets_found} files")
        score -= 1  # type: ignore[operator]
    unsafe_eval = grep_in_files(r"eval\(|exec\(", python_files)
    if unsafe_eval > 0:
        findings.append(f"- Critical: Unsafe eval/exec detected in {unsafe_eval} files")
        score -= 3  # type: ignore[operator]
    return findings, score


def _analyze_g(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """Dependencies (G)."""
    findings: list[str] = []
    score: int | None = 10
    has_req = Path("requirements.txt").exists()
    has_pyproject = Path("pyproject.toml").exists()
    findings.append(f"- requirements.txt: {'Y' if has_req else 'N'}")
    findings.append(f"- pyproject.toml: {'Y' if has_pyproject else 'N'}")
    has_lock = (
        Path("poetry.lock").exists()
        or Path("package-lock.json").exists()
        or Path("requirements.lock").exists()
    )
    findings.append(f"- Lock file: {'Y' if has_lock else 'N'}")
    if not (has_req or has_pyproject):
        score -= 5  # type: ignore[operator]
        findings.append("- Critical: No dependency definition found")
    if not has_lock:
        findings.append("- Note: No lock file found (reproducibility risk)")
        score -= 1  # type: ignore[operator]
    return findings, score


def _analyze_h(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """CI/CD (H)."""
    findings: list[str] = []
    score: int | None = 10
    has_gha = Path(".github/workflows").exists()
    findings.append(f"- GitHub Workflows: {'Y' if has_gha else 'N'}")
    if not has_gha:
        score -= 3  # type: ignore[operator]
        findings.append("- Warning: No GitHub Actions workflows found")
    else:
        wf_count = len(list(Path(".github/workflows").glob("*.yml"))) + len(
            list(Path(".github/workflows").glob("*.yaml"))
        )
        findings.append(f"- Number of workflows: {wf_count}")
    return findings, score


def _analyze_i(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """Code Style (I) -- delegates to linter wrappers in run_assessment."""
    from scripts.run_assessment import run_black_check_wrapper, run_ruff_check_wrapper

    findings: list[str] = []
    score: int | None = 10
    ruff_result = run_ruff_check_wrapper()
    black_result = run_black_check_wrapper()
    findings.append(
        f"- Ruff check: {'passed' if ruff_result['exit_code'] == 0 else 'issues found'}"
    )
    black_status = "formatted" if black_result["exit_code"] == 0 else "needs formatting"
    findings.append(f"- Black formatting: {black_status}")
    if ruff_result["exit_code"] != 0:
        score -= 3  # type: ignore[operator]
    if black_result["exit_code"] != 0:
        score -= 2  # type: ignore[operator]
    return findings, score


def _analyze_j(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """API Design (J)."""
    findings: list[str] = []
    score: int | None = 10
    files_with_hints = grep_in_files(r"def\s+.*\s*->\s*.*:", python_files)
    findings.append(f"- Files with type hints: {files_with_hints}/{file_count}")
    if file_count > 0:
        ratio = files_with_hints / file_count
        findings.append(f"- Type hint coverage: {ratio:.0%}")
        if ratio < 0.2:
            score -= 3  # type: ignore[operator]
            findings.append("- Warning: Low type hint usage (< 20%)")
        elif ratio < 0.5:
            score -= 1  # type: ignore[operator]
        else:
            findings.append("- Good type hint usage")
    abc_usage = grep_in_files(
        r"from abc import |class .*\(ABC\):|class .*\(Protocol\):", python_files
    )
    findings.append(f"- Files using ABC/Protocol: {abc_usage}")
    return findings, score


def _analyze_k(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """Data Handling (K)."""
    findings: list[str] = []
    score: int | None = 10
    _data_pat = r"import json|import pickle|import sqlite3|import csv|import pandas"
    data_imports = grep_in_files(f"{_data_pat}|import dataclasses", python_files)
    findings.append(f"- Files with data handling imports: {data_imports}")
    dataclass_usage = grep_in_files(r"@dataclass", python_files)
    findings.append(f"- Files using @dataclass: {dataclass_usage}")
    if data_imports == 0 and dataclass_usage == 0 and file_count > 5:
        score -= 2  # type: ignore[operator]
        findings.append("- Note: Limited explicit data handling structures detected")
    return findings, score


def _analyze_l(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """Logging (L)."""
    findings: list[str] = []
    score: int | None = 10
    log_imports = grep_in_files(r"import logging|from logging import", python_files)
    findings.append(f"- Files importing logging: {log_imports}")
    if log_imports < 2 and file_count > 5:
        score -= 2  # type: ignore[operator]
        findings.append("- Warning: Sparse logging detected")
    return findings, score


def _analyze_m(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """Configuration (M)."""
    findings: list[str] = []
    score: int | None = 10
    config_files = (
        list(Path(".").glob("*.ini"))
        + list(Path(".").glob("*.toml"))
        + list(Path(".").glob("*.env"))
    )
    findings.append(f"- Config files found: {[f.name for f in config_files]}")
    if not config_files:
        score -= 1  # type: ignore[operator]
        findings.append("- Note: No standard config files found in root")
    return findings, score


def _analyze_n(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """Scalability (N)."""
    findings: list[str] = []
    score: int | None = 10
    concurrency = grep_in_files(
        r"import asyncio|import multiprocessing|import threading|concurrent\.futures",
        python_files,
    )
    cache_usage = grep_in_files(r"lru_cache|@cache", python_files)
    findings.append(f"- Files with concurrency imports: {concurrency}")
    findings.append(f"- Files using caching: {cache_usage}")
    if concurrency == 0 and cache_usage == 0:
        findings.append("- Note: No explicit concurrency or caching detected")
    return findings, score


def _analyze_o(
    python_files: list[Path], file_count: int
) -> tuple[list[str], int | None]:
    """Maintainability (O)."""
    findings: list[str] = []
    score: int | None = 10
    long_files = 0
    total_lines = 0
    for p in python_files:
        try:
            lc = len(p.read_text(encoding="utf-8").splitlines())
            total_lines += lc
            if lc > 1500:
                long_files += 1
        except Exception:  # noqa: BLE001
            pass
    avg_lines = total_lines / file_count if file_count > 0 else 0
    findings.append(f"- Average lines per file: {avg_lines:.0f}")
    findings.append(f"- Files > 1500 lines: {long_files}")
    if long_files > 0:
        score -= min(3, long_files)  # type: ignore[operator]
        findings.append(f"- Warning: {long_files} large files detected (> 1500 lines)")
    if avg_lines > 500:
        score -= 1  # type: ignore[operator]
        findings.append("- Warning: High average file size")
    return findings, score


_ANALYZERS = {
    "A": _analyze_a,
    "B": _analyze_b,
    "C": _analyze_c,
    "D": _analyze_d,
    "E": _analyze_e,
    "F": _analyze_f,
    "G": _analyze_g,
    "H": _analyze_h,
    "I": _analyze_i,
    "J": _analyze_j,
    "K": _analyze_k,
    "L": _analyze_l,
    "M": _analyze_m,
    "N": _analyze_n,
    "O": _analyze_o,
}


def analyze_module(
    assessment_id: str,
    python_files: list[Path],
    file_count: int,
) -> tuple[list[str], int | None]:
    """Analyse a repository for a single assessment category (A-O).

    Args:
        assessment_id: Single uppercase letter identifying the assessment.
        python_files:  List of Python source Path objects from file_discovery().
        file_count:    Number of entries in python_files.

    Returns:
        A tuple of (findings, score) where score is an int 0-10 or None.
    """
    analyzer = _ANALYZERS.get(assessment_id)
    if analyzer is not None:
        return analyzer(python_files, file_count)
    return [
        f"- Python files analyzed: {file_count}",
        "- **REQUIRES REVIEW**: No automated checks available for this category",
        "- Score must be assigned by Jules bot or manual code review",
    ], None
