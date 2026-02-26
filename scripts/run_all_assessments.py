#!/usr/bin/env python3
"""
Run all assessments (A-O), generate summary, and identify issues.
"""

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Mapping of assessment ID to name
ASSESSMENTS = {
    "A": "Code_Structure",
    "B": "Documentation",
    "C": "Test_Coverage",
    "D": "Error_Handling",
    "E": "Performance",
    "F": "Security",
    "G": "Dependencies",
    "H": "CI_CD",
    "I": "Code_Style",
    "J": "API_Design",
    "K": "Data_Handling",
    "L": "Logging",
    "M": "Configuration",
    "N": "Scalability",
    "O": "Maintainability",
}


def main():
    """Run all assessments."""
    base_cmd = [sys.executable, "scripts/run_assessment.py"]
    output_dir = Path("docs/assessments")
    output_dir.mkdir(parents=True, exist_ok=True)

    failed = []

    # 1. Run individual assessments
    for assessment_id, name in ASSESSMENTS.items():
        output_file = output_dir / f"Assessment_{assessment_id}_{name}.md"
        cmd = base_cmd + ["--assessment", assessment_id, "--output", str(output_file)]

        logger.info("Running Assessment %s (%s)...", assessment_id, name)
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            logger.error("Assessment %s failed.", assessment_id)
            failed.append(assessment_id)

    if failed:
        logger.error("Failed assessments: %s", ", ".join(failed))
        # We continue even if some failed, to generate partial summary

    # 2. Generate Summary
    logger.info("Generating Comprehensive Assessment Summary...")
    summary_md = output_dir / "Comprehensive_Assessment.md"
    summary_json = output_dir / "assessment_summary.json"

    summary_cmd = [
        sys.executable,
        "scripts/generate_assessment_summary.py",
        "--input",
        str(output_dir / "Assessment_*.md"),
        "--output",
        str(summary_md),
        "--json-output",
        str(summary_json),
    ]

    try:
        subprocess.run(summary_cmd, check=True)
    except subprocess.CalledProcessError:
        logger.error("Failed to generate assessment summary.")
        sys.exit(1)

    # 3. Generate Issues Report
    logger.info("Generating Issues Report...")
    issues_cmd = [sys.executable, "scripts/generate_issues_report.py"]

    try:
        subprocess.run(issues_cmd, check=True)
    except subprocess.CalledProcessError:
        logger.error("Failed to generate issues report.")
        sys.exit(1)

    logger.info("All assessment tasks completed successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
