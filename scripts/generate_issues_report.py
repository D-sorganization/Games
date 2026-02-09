#!/usr/bin/env python3
"""
Generate a report of issues to be created based on assessment scores.
"""

import json
from pathlib import Path


def main():
    summary_path = Path("docs/assessments/assessment_summary.json")
    output_path = Path("docs/assessments/ISSUES_TO_CREATE.md")

    if not summary_path.exists():
        print(f"Error: {summary_path} not found.")
        return

    try:
        with open(summary_path) as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    category_scores = data.get("category_scores", {})
    issues = []

    for cat_id, details in category_scores.items():
        score = details.get("score", 10)
        if score < 5:
            issues.append(
                f"- Category {cat_id} ({details.get('name')}) score {score} < 5. Label: jules:assessment,needs-attention"
            )

    with open(output_path, "w") as f:
        if issues:
            f.write("# Issues to Create\n\n")
            f.write("\n".join(issues))
            f.write("\n")
            print(
                f"Found {len(issues)} categories with score < 5. Report saved to {output_path}"
            )
        else:
            f.write("No categories scored below 5. No issues to create.\n")
            print(f"No categories scored below 5. Report saved to {output_path}")


if __name__ == "__main__":
    main()
