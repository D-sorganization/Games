#!/usr/bin/env python3
"""
Quality Review Generator

Analyzes files identified in .jules/review_data/diffs.txt for critical quality issues.
Generates a report in docs/assessments/Assessment_Quality_Review.md.
"""

import ast
import hashlib
import json
import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
REVIEW_DATA_PATH = Path(".jules/review_data/diffs.txt")
OUTPUT_MD_PATH = Path("docs/assessments/Assessment_Quality_Review.md")
OUTPUT_JSON_PATH = Path("docs/assessments/assessment_quality_review.json")


def parse_diff_files(diff_path: Path) -> list[Path]:
    """Parse diff file to find changed Python files."""
    if not diff_path.exists():
        logger.error(f"Review data not found at {diff_path}")
        return []

    files = set()
    try:
        content = diff_path.read_text(encoding="utf-8", errors="replace")
        # Look for "diff --git a/... b/..."
        # We care about the 'b' path (the new version)
        matches = re.findall(r"diff --git a/.* b/(.*)", content)
        for match in matches:
            path_str = match.strip()
            if path_str.endswith(".py"):
                file_path = Path(path_str)
                if file_path.exists():
                    files.add(file_path)
    except Exception as e:
        logger.error(f"Error parsing diffs: {e}")

    return sorted(list(files))


def compute_file_hash(content: str) -> str:
    """Compute hash of normalized content for duplicate detection."""
    lines = []
    for line in content.split("\n"):
        line = re.sub(r"#.*$", "", line).strip()
        if line:
            lines.append(line)
    normalized = "\n".join(lines)
    return hashlib.md5(normalized.encode(), usedforsecurity=False).hexdigest()


def check_dry_violations(files: list[Path]) -> list[dict[str, Any]]:
    """Check for duplicate code blocks (DRY)."""
    issues = []
    chunk_size = 10  # Larger chunk for critical detection
    code_blocks = defaultdict(list)

    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        lines = content.split("\n")
        last_hash = ""
        for i in range(len(lines) - chunk_size):
            chunk = "\n".join(lines[i : i + chunk_size])
            # Skip imports and simple assignments
            if len(chunk.strip()) < 100 or "import " in chunk:
                continue

            chunk_hash = compute_file_hash(chunk)
            if chunk_hash != last_hash:
                code_blocks[chunk_hash].append((file_path, i + 1))
                last_hash = chunk_hash

    reported_dry = 0
    for _, locations in code_blocks.items():
        count = len(locations)
        if count > 2:
            severity = "CRITICAL" if count > 5 else "MAJOR"
            if severity == "CRITICAL" and reported_dry < 10:
                files_inv = sorted({str(loc[0]) for loc in locations})
                issues.append(
                    {
                        "type": "DRY Violation",
                        "severity": severity,
                        "description": f"Code block duplicated in {count} locations",
                        "files": files_inv[:5],
                    }
                )
                reported_dry += 1
            elif severity == "MAJOR" and reported_dry < 20:
                files_inv = sorted({str(loc[0]) for loc in locations})
                issues.append(
                    {
                        "type": "DRY Violation",
                        "severity": severity,
                        "description": f"Code block duplicated in {count} locations",
                        "files": files_inv[:5],
                    }
                )
                reported_dry += 1

    return issues


def check_god_functions(files: list[Path]) -> list[dict[str, Any]]:
    """Check for oversized functions (God Functions)."""
    issues = []
    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Estimate length by node traversal or simple line diff
                    start = node.lineno
                    end = node.end_lineno if hasattr(node, "end_lineno") else start
                    length = end - start + 1

                    if length > 200:
                        issues.append(
                            {
                                "type": "Orthogonality / God Function",
                                "severity": "CRITICAL",
                                "description": f"Function `{node.name}` is too large ({length} lines)",
                                "files": [str(file_path)],
                            }
                        )
                    elif length > 100:
                        issues.append(
                            {
                                "type": "Orthogonality / God Function",
                                "severity": "MAJOR",
                                "description": f"Function `{node.name}` is large ({length} lines)",
                                "files": [str(file_path)],
                            }
                        )
        except Exception:
            pass
    return issues


def check_secrets(files: list[Path]) -> list[dict[str, Any]]:
    """Check for hardcoded secrets."""
    issues = []
    # Simple heuristic regex for secrets
    patterns = [
        r'api_key\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']',
        r'secret\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']',
        r'password\s*=\s*["\'][^"\']{8,}["\']',
    ]

    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append(
                        {
                            "type": "Security / Secrets",
                            "severity": "CRITICAL",
                            "description": "Potential hardcoded secret found",
                            "files": [str(file_path)],
                        }
                    )
                    break
        except Exception:
            pass
    return issues


def check_error_handling(files: list[Path]) -> list[dict[str, Any]]:
    """Check for broad exception handling."""
    issues = []
    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            matches = len(re.findall(r"except\s+Exception\s*:", content))
            if matches > 0:
                severity = "MAJOR"
                if matches > 5:
                    severity = "CRITICAL"

                issues.append(
                    {
                        "type": "Error Handling",
                        "severity": severity,
                        "description": f"Found {matches} broad `except Exception` clauses",
                        "files": [str(file_path)],
                    }
                )
        except Exception:
            pass
    return issues


def check_magic_numbers(files: list[Path]) -> list[dict[str, Any]]:
    """Check for magic numbers."""
    issues = []
    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            # Primitive check for numbers that are not 0, 1, -1
            # We look for lines with just numbers or assignments
            matches = re.findall(r"(?<![a-zA-Z0-9_])\d{2,}(?![a-zA-Z0-9_])", content)
            # Filter out line numbers or common benign numbers if possible,
            # but simple count is often enough for heuristic
            count = len(matches)
            if count > 20:
                issues.append(
                    {
                        "type": "Code Quality / Magic Numbers",
                        "severity": "MAJOR",
                        "description": f"High usage of numeric literals ({count} occurrences)",
                        "files": [str(file_path)],
                    }
                )
        except Exception:
            pass
    return issues


def generate_markdown_report(issues: list[dict[str, Any]], output_path: Path):
    """Generate Markdown report."""

    # Sort by severity
    severity_order = {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2}
    issues.sort(key=lambda x: (severity_order.get(x["severity"], 3), x["type"]))

    critical_count = sum(1 for i in issues if i["severity"] == "CRITICAL")

    md = [
        "# Assessment Quality Review",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d')}",
        f"**Critical Issues**: {critical_count}",
        "",
        "## Executive Summary",
        "This report is based on the analysis of files identified in `.jules/review_data/diffs.txt`.",
        "It highlights critical quality issues requiring immediate attention.",
        "",
        "## Findings",
        ""
    ]

    if not issues:
        md.append("No critical or major issues found.")
    else:
        for issue in issues:
            icon = "🔴" if issue["severity"] == "CRITICAL" else "🟠"
            md.append(f"### {icon} [{issue['severity']}] {issue['type']}")
            md.append(f"- **Description**: {issue['description']}")
            if issue.get("files"):
                md.append(f"- **Files**: {', '.join(issue['files'][:5])}")
                if len(issue['files']) > 5:
                    md.append(f"  ...and {len(issue['files']) - 5} more")
            md.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    logger.info(f"Markdown report generated at {output_path}")


def main():
    logger.info(f"Parsing review data from {REVIEW_DATA_PATH}")
    files = parse_diff_files(REVIEW_DATA_PATH)
    logger.info(f"Found {len(files)} Python files to analyze.")

    all_issues = []

    logger.info("Checking for DRY violations...")
    all_issues.extend(check_dry_violations(files))

    logger.info("Checking for God Functions...")
    all_issues.extend(check_god_functions(files))

    logger.info("Checking for Secrets...")
    all_issues.extend(check_secrets(files))

    logger.info("Checking Error Handling...")
    all_issues.extend(check_error_handling(files))

    logger.info("Checking Magic Numbers...")
    all_issues.extend(check_magic_numbers(files))

    # Save JSON
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "issues": all_issues}, f, indent=2)

    generate_markdown_report(all_issues, OUTPUT_MD_PATH)


if __name__ == "__main__":
    main()
