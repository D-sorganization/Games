#!/usr/bin/env python3
"""
Run a specific assessment (A-O) on the repository.

This script executes an individual assessment and generates a detailed report
based on actual code analysis.
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from scripts.shared.logging_config import setup_script_logging
from scripts.shared.subprocess_utils import run_black_check, run_ruff_check

logger = setup_script_logging()

# Assessment definitions
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


def find_python_files() -> list[Path]:
    """Find all Python files in the repository."""
    python_files = []
    for pattern in ["**/*.py"]:
        python_files.extend(Path(".").glob(pattern))
    # Exclude common non-source directories
    excluded = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        ".tox",
        "build",
        "dist",
    }
    return [f for f in python_files if not any(p in f.parts for p in excluded)]


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


def count_test_files() -> int:
    """Count test files in the repository."""
    test_patterns = ["**/test_*.py", "**/*_test.py", "**/tests/*.py"]
    test_files = set()
    for pattern in test_patterns:
        test_files.update(Path(".").glob(pattern))
    return len(test_files)


def check_documentation() -> dict:
    """Check documentation status."""
    has_readme = Path("README.md").exists()
    has_docs = Path("docs").exists()
    has_changelog = Path("CHANGELOG.md").exists()
    return {
        "has_readme": has_readme,
        "has_docs_dir": has_docs,
        "has_changelog": has_changelog,
    }


def grep_in_files(pattern: str, files: list[Path]) -> int:
    """Count files containing a pattern."""
    count = 0
    for file in files:
        try:
            content = file.read_text(encoding="utf-8")
            if re.search(pattern, content):
                count += 1
        except Exception:
            pass
    return count


def run_assessment(assessment_id: str, output_path: Path) -> int:
    """
    Run a specific assessment and generate report.

    Args:
        assessment_id: Assessment ID (A-O)
        output_path: Path to save the assessment report

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    assessment = ASSESSMENTS.get(assessment_id)
    if not assessment:
        logger.error(f"Unknown assessment: {assessment_id}")
        return 1

    logger.info(f"Running Assessment {assessment_id}: {assessment['name']}...")

    # Gather metrics based on assessment type
    findings = []
    score = 10  # Start with perfect score

    python_files = find_python_files()
    file_count = len(python_files)

    if assessment_id == "A":  # Code Structure
        has_src = Path("src").exists()
        has_tests = (
            Path("tests").exists()
            or Path("src/tests").exists()
            or (file_count > 0 and count_test_files() > 0)
        )
        findings.append(f"- Python files found: {file_count}")
        findings.append(
            f"- Source directory structure (src/): {'✓' if has_src else '✗'}"
        )
        findings.append(f"- Tests directory/files: {'✓' if has_tests else '✗'}")
        if not has_src:
            score -= 2
        if not has_tests:
            score -= 2

    elif assessment_id == "B":  # Documentation
        docs = check_documentation()
        findings.append(f"- README.md: {'✓' if docs['has_readme'] else '✗'}")
        findings.append(f"- docs/ directory: {'✓' if docs['has_docs_dir'] else '✗'}")
        findings.append(f"- CHANGELOG.md: {'✓' if docs['has_changelog'] else '✗'}")

        # Check for docstrings in top 10 files
        docstring_count = 0
        checked_files = 0
        for p in python_files[:10]:
            content = p.read_text(encoding="utf-8")
            if '"""' in content or "'''" in content:
                docstring_count += 1
            checked_files += 1

        if checked_files > 0:
            docstring_percent = (docstring_count / checked_files) * 100
            findings.append(f"- Docstring presence (sample): {docstring_percent:.0f}%")
            if docstring_percent < 50:
                score -= 2

        if not docs["has_readme"]:
            score -= 3
        if not docs["has_docs_dir"]:
            score -= 1

    elif assessment_id == "C":  # Test Coverage
        test_count = count_test_files()
        findings.append(f"- Test files found: {test_count}")
        if test_count == 0:
            score -= 5
            findings.append("- Critical: No tests found")
        elif test_count < 5:
            score -= 2
            findings.append("- Warning: Low number of test files")
        else:
            findings.append("- Good number of test files")

    elif assessment_id == "D":  # Error Handling
        try_count = grep_in_files(r"try:", python_files)
        except_count = grep_in_files(r"except:", python_files)
        findings.append(f"- Files with try blocks: {try_count}")
        findings.append(f"- Files with except blocks: {except_count}")
        if try_count == 0:
            score -= 2
            findings.append("- Warning: No error handling detected in sample")

    elif assessment_id == "E":  # Performance
        # Check for profilers or common optimization patterns
        perf_imports = grep_in_files(
            r"import cProfile|import timeit|import pstats", python_files
        )
        findings.append(f"- Files with performance tools: {perf_imports}")
        if perf_imports == 0:
            findings.append(
                "- Note: No explicit performance profiling tools found in code"
            )
            # Deduct slightly or neutral depending on philosophy.
            # Let's keep it neutral but report it.
            score -= 1

    elif assessment_id == "F":  # Security
        # Basic check for subprocess without shell=True or hardcoded secrets
        subprocess_shell = grep_in_files(r"subprocess\..*shell=True", python_files)
        if subprocess_shell > 0:
            findings.append(
                f"- Critical: subprocess with shell=True found in "
                f"{subprocess_shell} files"
            )
            score -= 3
        else:
            findings.append("- subprocess with shell=True: Not found (Good)")

    elif assessment_id == "G":  # Dependencies
        has_req = Path("requirements.txt").exists()
        has_pyproject = Path("pyproject.toml").exists()
        findings.append(f"- requirements.txt: {'✓' if has_req else '✗'}")
        findings.append(f"- pyproject.toml: {'✓' if has_pyproject else '✗'}")
        if not (has_req or has_pyproject):
            score -= 5
            findings.append("- Critical: No dependency definition found")

    elif assessment_id == "H":  # CI/CD
        has_github_workflows = Path(".github/workflows").exists()
        findings.append(f"- GitHub Workflows: {'✓' if has_github_workflows else '✗'}")
        if not has_github_workflows:
            score -= 3
            findings.append("- Warning: No GitHub Actions workflows found")

    elif assessment_id == "I":  # Code Style
        ruff_result = run_ruff_check_wrapper()
        black_result = run_black_check_wrapper()
        ruff_status = "✓ passed" if ruff_result["exit_code"] == 0 else "✗ issues found"
        findings.append(f"- Ruff check: {ruff_status}")
        black_status = (
            "✓ formatted" if black_result["exit_code"] == 0 else "✗ needs formatting"
        )
        findings.append(f"- Black formatting: {black_status}")
        if ruff_result["exit_code"] != 0:
            score -= 3
        if black_result["exit_code"] != 0:
            score -= 2

    elif assessment_id == "L":  # Logging
        logging_imports = grep_in_files(
            r"import logging|from logging import", python_files
        )
        findings.append(f"- Files importing logging: {logging_imports}")
        if logging_imports < 2 and file_count > 5:
            score -= 2
            findings.append("- Warning: Sparse logging detected")

    elif assessment_id == "M":  # Configuration
        config_files = (
            list(Path(".").glob("*.ini"))
            + list(Path(".").glob("*.toml"))
            + list(Path(".").glob("*.env"))
        )
        findings.append(f"- Config files found: {[f.name for f in config_files]}")
        if not config_files:
            score -= 1
            findings.append("- Note: No standard config files found in root")

    else:
        # Generic assessment for J, K, N, O
        findings.append(f"- Python files analyzed: {file_count}")
        findings.append("- Manual review recommended for detailed assessment")
        # Default neutral score for subjective categories unless we have
        # specific heuristics
        score = 7

    # Ensure score is within bounds
    score = max(0, min(10, score))

    # Generate report
    report_content = f"""# Assessment {assessment_id}: {assessment["name"]}

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Assessment**: {assessment_id} - {assessment["name"]}
**Description**: {assessment["description"]}
**Generated**: Automated via Jules Assessment Auto-Fix workflow

## Score: {score}/10

## Findings

{chr(10).join(findings)}

## Recommendations

- Review findings above
- Address any ✗ items
- Re-run assessment after fixes

## Automation Notes

This assessment was generated automatically. For detailed analysis:
1. Run specific tools (ruff, black, pytest, etc.)
2. Review code manually for context-specific issues
3. Create GitHub issues for actionable items
"""

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write report
    with open(output_path, "w") as f:
        f.write(report_content)

    logger.info(f"✓ Assessment {assessment_id} report saved to {output_path}")
    logger.info(f"  Score: {score}/10")
    return 0


def main():
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

    exit_code = run_assessment(args.assessment, args.output)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
