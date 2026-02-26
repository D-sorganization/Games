#!/usr/bin/env python3
"""
Generate comprehensive assessment summary from individual assessment reports.

This script aggregates all A-O assessment results and creates:
1. A comprehensive markdown summary
2. A JSON file with structured metrics
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from scripts.shared.logging_config import setup_script_logging

logger = setup_script_logging()


def extract_score_from_report(report_path: Path) -> float:
    """Extract numerical score from assessment report."""
    try:
        with open(report_path) as f:
            content = f.read()

        # Look for score patterns like "Overall: 8.5" or "Score: 8.5/10"
        patterns = [
            r"Overall.*?(\d+\.?\d*)",
            r"Score.*?(\d+\.?\d*)",
            r"\*\*(\d+\.?\d*)\*\*.*?/10",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1))

        # Default score if not found
        return 7.0

    except Exception as e:
        logger.warning(f"Could not extract score from {report_path}: {e}")
        return 7.0


def extract_issues_from_report(report_path: Path) -> list[dict[str, Any]]:
    """Extract issues/findings from assessment report."""
    issues = []

    try:
        with open(report_path) as f:
            content = f.read()

        # Look for severity markers or warnings/criticals
        # We also look for standard bullet points that indicate issues
        severity_patterns = {
            "BLOCKER": r"BLOCKER:?\s*(.+)",
            "CRITICAL": r"CRITICAL:?\s*(.+)",
            "MAJOR": r"MAJOR:?\s*(.+)",
            "MINOR": r"MINOR:?\s*(.+)",
            "WARNING": r"Warning:?\s*(.+)",
        }

        for severity, pattern in severity_patterns.items():
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                issues.append(
                    {
                        "severity": severity.upper(),
                        "description": match.group(1).strip(),
                        "source": report_path.stem,
                    }
                )

    except Exception as e:
        logger.warning(f"Could not extract issues from {report_path}: {e}")

    return issues


def generate_summary(
    input_reports: list[Path],
    output_md: Path,
    output_json: Path,
) -> int:
    """
    Generate comprehensive summary from assessment reports.

    Args:
        input_reports: List of assessment report files
        output_md: Path to save markdown summary
        output_json: Path to save JSON metrics

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    logger.info(f"Generating assessment summary from {len(input_reports)} reports...")

    # Category mapping with weights based on prompt
    # Code 25%, Testing 15%, Docs 10%, Security 15%, Perf 15%, Ops 10%, Design 10%
    categories = {
        "A": {"name": "Code Structure", "weight": 8.33, "group": "Code"},
        "B": {"name": "Documentation", "weight": 10.0, "group": "Docs"},
        "C": {"name": "Test Coverage", "weight": 15.0, "group": "Testing"},
        "D": {"name": "Error Handling", "weight": 2.5, "group": "Design"},
        "E": {"name": "Performance", "weight": 15.0, "group": "Perf"},
        "F": {"name": "Security", "weight": 15.0, "group": "Security"},
        "G": {"name": "Dependencies", "weight": 2.5, "group": "Ops"},
        "H": {"name": "CI/CD", "weight": 2.5, "group": "Ops"},
        "I": {"name": "Code Style", "weight": 8.33, "group": "Code"},
        "J": {"name": "API Design", "weight": 2.5, "group": "Design"},
        "K": {"name": "Data Handling", "weight": 2.5, "group": "Design"},
        "L": {"name": "Logging", "weight": 2.5, "group": "Ops"},
        "M": {"name": "Configuration", "weight": 2.5, "group": "Ops"},
        "N": {"name": "Scalability", "weight": 2.5, "group": "Design"},
        "O": {"name": "Maintainability", "weight": 8.34, "group": "Code"},
    }

    # Collect scores and issues
    scores = {}
    all_issues = []

    for report in input_reports:
        # Extract assessment ID from filename (e.g., Assessment_A_Code_Structure.md)
        match = re.search(r"Assessment_([A-O])_.*", report.name)
        if match:
            assessment_id = match.group(1)
            scores[assessment_id] = extract_score_from_report(report)
            all_issues.extend(extract_issues_from_report(report))

    # Calculate weighted average
    total_weighted_score = 0.0
    total_weight = 0.0

    # Calculate group scores
    group_scores = {
        "Code": {"total": 0.0, "weight": 0.0, "target": 25},
        "Testing": {"total": 0.0, "weight": 0.0, "target": 15},
        "Docs": {"total": 0.0, "weight": 0.0, "target": 10},
        "Security": {"total": 0.0, "weight": 0.0, "target": 15},
        "Perf": {"total": 0.0, "weight": 0.0, "target": 15},
        "Ops": {"total": 0.0, "weight": 0.0, "target": 10},
        "Design": {"total": 0.0, "weight": 0.0, "target": 10},
    }

    for assessment_id, score in scores.items():
        if assessment_id in categories:
            cat = categories[assessment_id]
            weight = float(cast(Any, cat["weight"]))
            total_weighted_score += score * weight
            total_weight += weight

            group = cat["group"]
            if group in group_scores:
                group_scores[group]["total"] += score * weight
                group_scores[group]["weight"] += weight

    overall_score = total_weighted_score / total_weight if total_weight > 0 else 7.0

    # Prioritize issues for Top 5 Recommendations
    # Priority: BLOCKER > CRITICAL > MAJOR > WARNING
    severity_order = {"BLOCKER": 0, "CRITICAL": 1, "MAJOR": 2, "WARNING": 3}

    sorted_issues = sorted(
        all_issues, key=lambda x: severity_order.get(x["severity"], 4)
    )

    top_5_recommendations = sorted_issues[:5]

    # Generate markdown summary
    md_content = f"""# Comprehensive Assessment Summary

**Date**: {datetime.now().strftime("%Y-%m-%d")}
**Generated**: Automated via Jules Assessment Auto-Fix workflow
**Overall Score**: {overall_score:.1f}/10

## Executive Summary

Repository assessment completed across all {len(scores)} categories.

### Overall Health: {overall_score:.1f}/10

### Weighted Average Breakdown
| Group | Target Weight | Effective Score (Contribution) |
|-------|---------------|--------------------------------|
"""
    for group, data in group_scores.items():
        # Contribution is weighted score for this group relative to total weight (100)
        # But we want to show how well this group performed.
        # Actually, "Code 25%" means Code categories contribute 25% to total score.
        # So we can just show the average score for the group.
        group_avg = data["total"] / data["weight"] if data["weight"] > 0 else 0
        md_content += f"| {group} | {data['target']}% | {group_avg:.1f}/10 |\n"

    md_content += """
### Category Scores

| Category | Name | Score | Weight |
|----------|------|-------|--------|
"""

    for aid in sorted(scores.keys()):
        if aid in categories:
            cat_info = categories[aid]
            score = scores[aid]
            name = cat_info["name"]
            weight = float(cast(Any, cat_info["weight"]))
            md_content += f"| **{aid}** | {name} | {score:.1f} | {weight}% |\n"

    md_content += """
## Top 5 Recommendations

"""

    if top_5_recommendations:
        for i, issue in enumerate(top_5_recommendations, 1):
            sev = issue["severity"]
            desc = issue["description"]
            src = issue["source"]
            md_content += f"{i}. **[{sev}]** {desc} (Source: {src})\n"
    else:
        md_content += "No major issues found. Maintain current practices.\n"

    md_content += """
## Detailed Recommendations

- Address all items in the Top 5 Recommendations list above.
- Review individual assessment reports for detailed findings.
- Focus on categories with scores below 5/10.

## Next Assessment

Recommended: 30 days from today

---

*Generated by Jules Assessment Auto-Fix*
"""

    # Save markdown
    output_md.parent.mkdir(parents=True, exist_ok=True)
    with open(output_md, "w") as f:
        f.write(md_content)

    logger.info(f"✓ Markdown summary saved to {output_md}")

    # Generate JSON metrics
    category_scores: dict[str, dict[str, Any]] = {}
    for k, v in scores.items():
        if k in categories:
            cat = categories[k]
            category_scores[k] = {
                "score": v,
                "name": cat["name"],
                "weight": cat["weight"],
            }

    json_data = {
        "timestamp": datetime.now().isoformat(),
        "overall_score": round(overall_score, 2),
        "category_scores": category_scores,
        "top_recommendations": top_5_recommendations,
        "total_issues": len(all_issues),
        "reports_analyzed": len(input_reports),
    }

    # Save JSON
    with open(output_json, "w") as f:
        json.dump(json_data, f, indent=2)

    logger.info(f"✓ JSON metrics saved to {output_json}")

    return 0


def main():
    """Parse CLI arguments and generate assessment summary."""
    parser = argparse.ArgumentParser(description="Generate assessment summary")
    parser.add_argument(
        "--input",
        nargs="+",
        type=Path,
        required=True,
        help="Input assessment report files (can use wildcards)",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output markdown summary file",
    )
    parser.add_argument(
        "--json-output",
        required=True,
        type=Path,
        help="Output JSON metrics file",
    )

    args = parser.parse_args()

    # Expand wildcards if needed
    input_reports = []
    for pattern in args.input:
        if "*" in str(pattern):
            # Expand glob pattern
            input_reports.extend(Path(".").glob(str(pattern)))
        else:
            input_reports.append(pattern)

    # Filter to existing files
    input_reports = [p for p in input_reports if p.exists() and p.is_file()]

    if not input_reports:
        logger.error("No valid input reports found")
        return 1

    exit_code = generate_summary(input_reports, args.output, args.json_output)
    return exit_code


if __name__ == "__main__":
    sys.exit(main() or 0)
