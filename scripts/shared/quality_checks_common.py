#!/usr/bin/env python3
"""Shared quality check utilities for code validation."""

import ast
import re
from pathlib import Path

# Configuration
BANNED_PATTERNS = [
    (re.compile(r"\bTODO\b"), "TODO placeholder found"),
    (re.compile(r"\bFIXME\b"), "FIXME placeholder found"),
    (re.compile(r"^\s*\.\.\.\s*$"), "Ellipsis placeholder"),
    (re.compile(r"NotImplementedError"), "NotImplementedError placeholder"),
    (
        re.compile(r"<(?:[A-Z_][A-Z0-9_]*|[a-z_]+_(?:here|value|name|description))>"),
        "Angle bracket placeholder",
    ),
    (re.compile(r"your.*here", re.IGNORECASE), "Template placeholder"),
    (re.compile(r"insert.*here", re.IGNORECASE), "Template placeholder"),
]

MAGIC_NUMBERS = [
    (re.compile(r"(?<![0-9])3\.141"), "Use math.pi instead of 3.141"),
    (re.compile(r"(?<![0-9])9\.8[0-9]?(?![0-9])"), "Define GRAVITY_M_S2 constant"),
    (re.compile(r"(?<![0-9])6\.67[0-9]?(?![0-9])"), "Define gravitational constant"),
]

QUALITY_CHECK_SCRIPTS = {
    "quality_check_script.py",
    "quality_check.py",
    "matlab_quality_check.py",
    "code_quality_check.py",
    "quality_checks_common.py",
}

EXCLUDE_DIRS = {
    "archive",
    "legacy",
    "experimental",
    ".git",
    "__pycache__",
    ".ruff_cache",
    ".mypy_cache",
    "matlab",
    "output",
    ".ipynb_checkpoints",
    ".Trash",
}


def _is_in_class_definition(lines: list[str], line_num: int) -> bool:
    """Check if pass is in a class definition context."""
    for i in range(line_num - 1, max(0, line_num - 10), -1):
        prev_line = lines[i - 1].strip()
        if prev_line.startswith("class "):
            return True
        if prev_line.startswith("def "):
            return False
        if prev_line.endswith(":") and any(
            keyword in prev_line
            for keyword in ["try:", "except", "finally:", "with ", "if __name__"]
        ):
            return True
    return False


def _is_in_try_except_block(lines: list[str], line_num: int) -> bool:
    """Check if pass is in a try/except block context."""
    for i in range(line_num - 1, max(0, line_num - 5), -1):
        prev_line = lines[i - 1].strip()
        if "try:" in prev_line or "except" in prev_line:
            return True
    return False


def _is_in_context_manager(lines: list[str], line_num: int) -> bool:
    """Check if pass is in a context manager context."""
    for i in range(line_num - 1, max(0, line_num - 3), -1):
        prev_line = lines[i - 1].strip()
        if prev_line.startswith("with "):
            return True
    return False


def is_legitimate_pass_context(lines: list[str], line_num: int) -> bool:
    """Check if a pass statement is in a legitimate context."""
    if line_num <= 0 or line_num > len(lines):
        return False

    line = lines[line_num - 1].strip()
    if line != "pass":
        return False

    return (
        _is_in_class_definition(lines, line_num)
        or _is_in_try_except_block(lines, line_num)
        or _is_in_context_manager(lines, line_num)
    )


def check_banned_patterns(
    lines: list[str],
    filepath: Path,
) -> list[tuple[int, str, str]]:
    """Check for banned patterns in lines."""
    issues: list[tuple[int, str, str]] = []

    if filepath.name in QUALITY_CHECK_SCRIPTS:
        return issues

    for line_num, line in enumerate(lines, 1):
        for pattern, message in BANNED_PATTERNS:
            if pattern.search(line):
                issues.append((line_num, message, line.strip()))

        if re.match(r"^\s*pass\s*$", line) and not is_legitimate_pass_context(
            lines,
            line_num,
        ):
            issues.append(
                (
                    line_num,
                    "Empty pass statement - consider adding logic or comment",
                    line.strip(),
                ),
            )

    return issues


def check_magic_numbers(
    lines: list[str],
    filepath: Path,
) -> list[tuple[int, str, str]]:
    """Check for magic numbers in lines."""
    issues: list[tuple[int, str, str]] = []

    if filepath.name in QUALITY_CHECK_SCRIPTS:
        return issues

    for line_num, line in enumerate(lines, 1):
        line_content = line[: line.index("#")] if "#" in line else line
        for pattern, message in MAGIC_NUMBERS:
            if pattern.search(line_content):
                issues.append((line_num, message, line.strip()))
    return issues


def check_ast_issues(
    content: str,
    filepath: Path,
    check_return_hints: bool = True,
) -> list[tuple[int, str, str]]:
    """Check AST for quality issues."""
    issues: list[tuple[int, str, str]] = []

    if filepath.name in QUALITY_CHECK_SCRIPTS:
        return issues

    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    issues.append(
                        (node.lineno, f"Function '{node.name}' missing docstring", ""),
                    )
                if check_return_hints and not node.returns and node.name != "__init__":
                    issues.append(
                        (
                            node.lineno,
                            f"Function '{node.name}' missing return type hint",
                            "",
                        ),
                    )
    except SyntaxError as e:
        issues.append((0, f"Syntax error: {e}", ""))
    return issues


def check_file(
    filepath: Path,
    check_return_hints: bool = True,
) -> list[tuple[int, str, str]]:
    """Check a Python file for quality issues."""
    try:
        content = filepath.read_text(encoding="utf-8")
        lines = content.splitlines()

        issues = []
        issues.extend(check_banned_patterns(lines, filepath))
        issues.extend(check_magic_numbers(lines, filepath))
        issues.extend(check_ast_issues(content, filepath, check_return_hints))
    except (OSError, UnicodeDecodeError) as e:
        return [(0, f"Error reading file: {e}", "")]
    else:
        return issues


def get_python_files(
    file_args: list[str] | None = None,
    exclude_dirs: set[str] | None = None,
) -> list[Path]:
    """Get list of Python files to check."""
    if exclude_dirs is None:
        exclude_dirs = EXCLUDE_DIRS

    if file_args:
        return [Path(arg) for arg in file_args]

    python_files = list(Path().rglob("*.py"))
    return [
        f for f in python_files if not any(part in exclude_dirs for part in f.parts)
    ]
