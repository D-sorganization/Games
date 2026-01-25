#!/usr/bin/env python3
"""Shared utilities for repository assessments and code review."""

import ast
import hashlib
import re
from pathlib import Path
from typing import Any


def find_python_files(root_path: Path) -> list[Path]:
    """Find all Python files, excluding common non-source directories."""
    excluded = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "env",
        "node_modules",
        ".tox",
        "build",
        "dist",
        ".eggs",
        "*.egg-info",
    }
    python_files = []
    for f in root_path.rglob("*.py"):
        if not any(ex in f.parts for ex in excluded):
            python_files.append(f)
    return python_files


def compute_file_hash(content: str) -> str:
    """Compute hash of normalized content for duplicate detection."""
    # Normalize: remove comments and whitespace
    lines = []
    for line in content.split("\n"):
        line = re.sub(r"#.*$", "", line).strip()
        if line:
            lines.append(line)
    normalized = "\n".join(lines)
    return hashlib.md5(normalized.encode()).hexdigest()


def extract_functions(content: str) -> list[dict[str, Any]]:
    """Extract function definitions from Python code."""
    functions = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(
                    {
                        "name": node.name,
                        "lineno": node.lineno,
                        "args": len(node.args.args),
                        "body_lines": (
                            node.end_lineno - node.lineno + 1
                            if hasattr(node, "end_lineno")
                            else 0
                        ),
                        "has_docstring": (ast.get_docstring(node) is not None),
                    }
                )
    except SyntaxError:
        pass
    return functions


def extract_score_from_report(report_path: Path) -> float:
    """Extract numerical score from assessment report."""
    try:
        content = report_path.read_text(encoding="utf-8")

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

        return 7.0
    except Exception:
        return 7.0


def extract_issues_from_report(report_path: Path) -> list[dict[str, Any]]:
    """Extract issues/findings from assessment report."""
    issues = []
    try:
        content = report_path.read_text(encoding="utf-8")

        severity_patterns = {
            "BLOCKER": r"BLOCKER:?\s*(.+)",
            "CRITICAL": r"CRITICAL:?\s*(.+)",
            "MAJOR": r"MAJOR:?\s*(.+)",
            "MINOR": r"MINOR:?\s*(.+)",
        }

        for severity, pattern in severity_patterns.items():
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                issues.append(
                    {
                        "severity": severity,
                        "description": match.group(1).strip(),
                        "source": report_path.stem,
                    }
                )
    except Exception:
        pass
    return issues
