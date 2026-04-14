#!/usr/bin/env python3
"""Run a specific assessment (A-O) on the repository.

Per-category analysis logic lives in assessment_modules.py.
This file is the thin orchestrator: wrappers, scoring, report generation.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.assessment_modules import analyze_module, file_discovery  # noqa: E402
from scripts.shared.logging_config import setup_script_logging  # noqa: E402
from scripts.shared.subprocess_utils import (  # noqa: E402,F401
    run_black_check,
    run_command,
    run_ruff_check,
)

logger = setup_script_logging()

ASSESSMENTS = {
    "A": {"name": "Code Structure", "description": "Code structure and organization"},
    "B": {"name": "Documentation", "description": "README, docstrings, comments"},
    "C": {"name": "Test Coverage", "description": "Test coverage, test quality"},
    "D": {"name": "Error Handling", "description": "Exception handling, logging"},
    "E": {"name": "Performance", "description": "Efficiency, optimization"},
    "F": {"name": "Security", "description": "Vulnerabilities, best practices"},
    "G": {"name": "Dependencies", "description": "Dependency management"},
    "H": {"name": "CI/CD", "description": "Continuous Integration/Deployment"},
    "I": {"name": "Code Style", "description": "Linting, formatting, code quality"},
    "J": {"name": "API Design", "description": "Interface consistency"},
    "K": {"name": "Data Handling", "description": "Data validation, serialization"},
    "L": {"name": "Logging", "description": "Logging practices"},
    "M": {"name": "Configuration", "description": "Config management"},
    "N": {"name": "Scalability", "description": "Performance at scale"},
    "O": {"name": "Maintainability", "description": "Code maintainability"},
}


def run_ruff_check_wrapper() -> dict:
    """Run ruff and return statistics."""
    try:
        result = run_ruff_check(statistics=True, json_output=True)
        return {
            "exit_code": result.returncode,
            "output": result.stdout,
            "errors": result.stderr,
        }
    except FileNotFoundError:
        return {"exit_code": -1, "output": "", "errors": "ruff not installed"}


def run_black_check_wrapper() -> dict:
    """Run black check and return results."""
    try:
        result = run_black_check()
        return {
            "exit_code": result.returncode,
            "files_to_format": result.stdout.count("would reformat"),
        }
    except FileNotFoundError:
        return {"exit_code": -1, "files_to_format": 0, "errors": "black not installed"}


def calculate_scores(score: int | None) -> tuple[int | None, str]:
    """Clamp and format a raw score value."""
    if score is not None:
        clamped = max(0, min(10, score))
        return clamped, f"{clamped}/10"
    return None, "PENDING REVIEW"


def generate_report(
    assessment_id: str,
    assessment: dict,
    score_display: str,
    findings: list[str],
    output_path: Path,
) -> None:
    """Write the assessment markdown report to disk."""
    report_content = f"""# Assessment {assessment_id}: {assessment["name"]}

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Assessment**: {assessment_id} - {assessment["name"]}
**Description**: {assessment["description"]}
**Generated**: Automated via Jules Assessment Auto-Fix workflow

## Score: {score_display}

## Findings

{chr(10).join(findings)}

## Recommendations

- Review findings above
- Address any items marked N
- Re-run assessment after fixes

## Automation Notes

This assessment was generated automatically. For detailed analysis:
1. Run specific tools (ruff, black, pytest, etc.)
2. Review code manually for context-specific issues
3. Create GitHub issues for actionable items
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_content, encoding="utf-8")


def run_assessment(assessment_id: str, output_path: Path) -> int:
    """Run a specific assessment and generate report.

    Args:
        assessment_id: Assessment ID (A-O)
        output_path: Path to save the assessment report

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    assessment = ASSESSMENTS.get(assessment_id)
    if not assessment:
        logger.error("Unknown assessment: %s", assessment_id)
        return 1

    logger.info("Running Assessment %s: %s...", assessment_id, assessment["name"])
    python_files, file_count = file_discovery()
    findings, raw_score = analyze_module(assessment_id, python_files, file_count)
    _, score_display = calculate_scores(raw_score)
    generate_report(assessment_id, assessment, score_display, findings, output_path)
    logger.info("Assessment %s report saved to %s", assessment_id, output_path)
    logger.info("  Score: %s", score_display)
    return 0


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description="Run repository assessment")
    parser.add_argument(
        "--assessment",
        required=True,
        choices=list("ABCDEFGHIJKLMNO"),
        help="Assessment ID (A-O)",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output file path for assessment report",
    )
    args = parser.parse_args()
    sys.exit(run_assessment(args.assessment, args.output))


if __name__ == "__main__":
    main()
