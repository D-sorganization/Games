#!/usr/bin/env python3
"""
Run all assessments (A-O) and generate individual reports.
"""

import subprocess
import sys
from pathlib import Path

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

    for assessment_id, name in ASSESSMENTS.items():
        output_file = output_dir / f"Assessment_{assessment_id}_{name}.md"
        cmd = base_cmd + ["--assessment", assessment_id, "--output", str(output_file)]

        print(f"Running Assessment {assessment_id} ({name})...")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            print(f"ERROR: Assessment {assessment_id} failed.")
            failed.append(assessment_id)

    if failed:
        print(f"\nFailed assessments: {', '.join(failed)}")
        sys.exit(1)

    print("\nAll assessments completed successfully.")


if __name__ == "__main__":
    main()
