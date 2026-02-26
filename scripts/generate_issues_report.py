#!/usr/bin/env python3
"""
Generate a report of issues to be created based on assessment scores.
"""

import json
from datetime import datetime
from pathlib import Path

from scripts.shared.logging_config import setup_script_logging

logger = setup_script_logging()


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
                f"- **Category {cat_id} ({details.get('name')})**\n"
                f"  - Score: {score}/10\n"
                f"  - Action: Create GitHub Issue\n"
                f"  - Label: `jules:assessment,needs-attention`"
            )

    # Prepare report content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"# Issues to Create Report\n\n**Date**: {timestamp}\n\n"

    if issues:
        content += "## Found Categories with Score < 5\n\n"
        content += "\n".join(issues)
        content += (
            "\n\n## Instructions\n\nRun the following command to create issues:\n"
        )
        # Potential future command integration
        content += (
            "```bash\n# Example command (requires gh cli)\n# gh issue create ...\n```\n"
        )
        logger.info(
            "Found %d categories with score < 5. Report saved to %s",
            len(issues),
            output_path,
        )
    else:
        content += (
            "## Status: All Good\n\n"
            "No categories scored below 5. No issues to create.\n"
        )
        logger.info("No categories scored below 5. Report saved to %s", output_path)

    with open(output_path, "w") as f:
        f.write(content)


if __name__ == "__main__":
    main()
