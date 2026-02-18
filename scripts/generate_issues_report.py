#!/usr/bin/env python3
"""
Generate a report of issues to be created based on assessment scores.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def main():
    summary_path = Path("docs/assessments/assessment_summary.json")
    output_path = Path("docs/assessments/ISSUES_TO_CREATE.md")

    if not summary_path.exists():
        logger.error("%s not found.", summary_path)
        return

    try:
        with open(summary_path) as f:
            data = json.load(f)
    except Exception as e:
        logger.error("Error loading JSON: %s", e)
        return

    category_scores = data.get("category_scores", {})
    issues = []

    for cat_id, details in category_scores.items():
        score = details.get("score", 10)
        if score < 5:
            issues.append(
                f"- Category {cat_id} ({details.get('name')}) "
                f"score {score} < 5. Label: jules:assessment,needs-attention"
            )

    with open(output_path, "w") as f:
        if issues:
            f.write("# Issues to Create\n\n")
            f.write("\n".join(issues))
            f.write("\n")
            logger.info(
                "Found %d categories with score < 5. Report saved to %s",
                len(issues),
                output_path,
            )
        else:
            f.write("No categories scored below 5. No issues to create.\n")
            logger.info("No categories scored below 5. Report saved to %s", output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
