"""Mypy fix strategies and shared utilities for mypy_autofix_agent.

Provides:
  - MypyError / Fix data classes
  - KNOWN_UNTYPED_MODULES / COMMON_TYPE_IMPORTS constants
  - File I/O helpers (read_file_lines, write_file_lines)
  - Annotation helpers (has_type_ignore, add_type_ignore, get_line_indent)
  - Import insertion (_ensure_import)
  - Path safety check (is_safe_path)
  - All fix strategies (fix_callable_as_type, fix_union_attr,
    fix_name_not_defined, fix_import_errors, fix_generic_suppression)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MypyError:
    """Parsed mypy error."""

    file: str
    line: int
    column: int
    severity: str  # "error" or "note"
    message: str
    code: str  # e.g., "union-attr", "valid-type", "import-untyped"


@dataclass
class Fix:
    """A fix to apply."""

    file: str
    line: int
    description: str
    strategy: str  # "real-fix" or "suppression"
    original_code: str = ""


KNOWN_UNTYPED_MODULES = {
    "mujoco",
    "dm_control",
    "pinocchio",
    "pin",
    "drake",
    "pydrake",
    "opensim",
    "myosuite",
    "gymnasium",
    "gym",
    "meshcat",
    "trimesh",
    "pybullet",
    "cv2",
    "mediapipe",
    "onnxruntime",
    "sklearn",
    "scipy",
    "PIL",
    "yaml",
    "toml",
    "rich",
    "click",
    "uvicorn",
    "starlette",
    "websockets",
    "serial",
    "usb",
    "hid",
    "pygame",
    "OpenGL",
    "moderngl",
}

COMMON_TYPE_IMPORTS = {
    "Callable": "from collections.abc import Callable",
    "Iterator": "from collections.abc import Iterator",
    "Generator": "from collections.abc import Generator",
    "Sequence": "from collections.abc import Sequence",
    "Mapping": "from collections.abc import Mapping",
    "Iterable": "from collections.abc import Iterable",
    "Optional": "from typing import Optional",
    "Union": "from typing import Union",
    "Any": "from typing import Any",
    "ClassVar": "from typing import ClassVar",
    "TypeVar": "from typing import TypeVar",
    "Protocol": "from typing import Protocol",
    "TypeAlias": "from typing import TypeAlias",
    "Final": "from typing import Final",
    "Literal": "from typing import Literal",
    "overload": "from typing import overload",
    "cast": "from typing import cast",
    "TYPE_CHECKING": "from typing import TYPE_CHECKING",
    "Self": "from typing import Self",
    "TypedDict": "from typing import TypedDict",
    "NamedTuple": "from typing import NamedTuple",
    "Path": "from pathlib import Path",
    "datetime": "from datetime import datetime",
    "timedelta": "from datetime import timedelta",
    "Enum": "from enum import Enum",
    "dataclass": "from dataclasses import dataclass",
    "abstractmethod": "from abc import abstractmethod",
    "ABC": "from abc import ABC",
}


def read_file_lines(filepath: str) -> list[str]:
    """Read file and return lines (preserving newlines)."""
    path = Path(filepath)
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def write_file_lines(filepath: str, lines: list[str]) -> None:
    """Write lines back to file."""
    Path(filepath).write_text("".join(lines), encoding="utf-8")


def has_type_ignore(line: str, code: str | None = None) -> bool:
    """Check if a line already has a type: ignore comment."""
    if "# type: ignore" in line:
        if code and f"[{code}]" in line:
            return True
        if code is None:
            return True
        if "# type: ignore\n" in line or line.rstrip().endswith("# type: ignore"):
            return True
    return False


def add_type_ignore(line: str, code: str) -> str:
    """Add # type: ignore[code] to a line."""
    stripped = line.rstrip("\n\r")
    if "# type: ignore" in stripped:
        if re.search(r"# type: ignore\[([^\]]+)\]", stripped):
            return (
                re.sub(
                    r"# type: ignore\[([^\]]+)\]",
                    rf"# type: ignore[\1, {code}]",
                    stripped,
                )
                + "\n"
            )
        return stripped + "\n"
    return stripped + f"  # type: ignore[{code}]\n"


def get_line_indent(line: str) -> str:
    """Get the leading whitespace of a line."""
    return line[: len(line) - len(line.lstrip())]


def _ensure_import(lines: list[str], import_statement: str) -> bool:
    """Add an import statement if not already present. Returns True if added."""
    for line in lines:
        if import_statement in line:
            return False

    last_import_idx = -1
    in_docstring = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if in_docstring:
                in_docstring = False
                continue
            if stripped.count('"""') == 1 or stripped.count("'''") == 1:
                in_docstring = True
                continue
        if in_docstring:
            continue
        if stripped.startswith(("import ", "from ")):
            last_import_idx = i
        elif stripped and not stripped.startswith("#") and last_import_idx >= 0:
            break

    if last_import_idx >= 0:
        lines.insert(last_import_idx + 1, import_statement + "\n")
    else:
        insert_at = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                    insert_at = i + 1
                    break
                for j in range(i + 1, len(lines)):
                    if '"""' in lines[j] or "'''" in lines[j]:
                        insert_at = j + 1
                        break
                break
            elif stripped and not stripped.startswith("#"):
                insert_at = i
                break
        lines.insert(insert_at, import_statement + "\n")
    return True


def is_safe_path(filepath: str) -> bool:
    """Check if a file is safe to modify."""
    path = Path(filepath)
    parts = path.parts
    if not any(p in ("src", "tests") for p in parts):
        return False
    if any(p.startswith(".") or p == "__pycache__" or p == "vendor" for p in parts):
        return False
    if path.suffix != ".py":
        return False
    return True


def fix_callable_as_type(lines: list[str], error: MypyError) -> Fix | None:
    """Fix 'callable is not valid as a type' by replacing with Callable."""
    if not isinstance(lines, list):
        raise TypeError(f"lines must be a list, got {type(lines).__name__}")
    if not isinstance(error, MypyError):
        raise TypeError(f"error must be a MypyError, got {type(error).__name__}")
    if error.code != "valid-type":
        return None
    if '"callable" is not valid as a type' not in error.message.lower():
        return None

    idx = error.line - 1
    if idx >= len(lines):
        return None

    line = lines[idx]
    if ": callable" in line.lower():
        original = line
        line = re.sub(
            r":\s*callable\b", ": Callable[..., Any]", line, flags=re.IGNORECASE
        )
        lines[idx] = line
        _ensure_import(lines, "from collections.abc import Callable")
        _ensure_import(lines, "from typing import Any")
        return Fix(
            file=error.file,
            line=error.line,
            description="Replace 'callable' with 'Callable[..., Any]'",
            strategy="real-fix",
            original_code=original.strip(),
        )
    return None


def fix_union_attr(lines: list[str], error: MypyError) -> Fix | None:
    """Fix union-attr by adding isinstance narrowing."""
    if not isinstance(lines, list):
        raise TypeError(f"lines must be a list, got {type(lines).__name__}")
    if not isinstance(error, MypyError):
        raise TypeError(f"error must be a MypyError, got {type(error).__name__}")
    if error.code != "union-attr":
        return None

    match = re.search(
        r'Item "(\w+)" of "([^"]+)" has no attribute "(\w+)"', error.message
    )
    if not match:
        return None

    bad_type, union_type, attr = match.groups()
    types_in_union = [t.strip() for t in union_type.split("|")]
    good_types = [t for t in types_in_union if t != bad_type and t != "None"]
    if not good_types:
        return None

    idx = error.line - 1
    if idx >= len(lines):
        return None

    line = lines[idx]
    indent = get_line_indent(line)
    var_match = re.search(rf"(\w+)\.{re.escape(attr)}", line)
    if not var_match:
        return None

    var_name = var_match.group(1)
    target_type = good_types[0]

    for check_idx in range(max(0, idx - 3), idx):
        if f"isinstance({var_name}" in lines[check_idx]:
            return None

    assert_line = f"{indent}assert isinstance({var_name}, {target_type})\n"
    lines.insert(idx, assert_line)
    narrowing_desc = (
        f"Add isinstance({var_name}, {target_type}) narrowing for union-attr"
    )
    return Fix(
        file=error.file,
        line=error.line,
        description=narrowing_desc,
        strategy="real-fix",
        original_code=line.strip(),
    )


def fix_name_not_defined(lines: list[str], error: MypyError) -> Fix | None:
    """Fix name-defined errors by adding missing imports."""
    if error.code != "name-defined":
        return None
    match = re.search(r'Name "(\w+)" is not defined', error.message)
    if not match:
        return None
    name = match.group(1)
    if name in COMMON_TYPE_IMPORTS:
        import_line = COMMON_TYPE_IMPORTS[name]
        if _ensure_import(lines, import_line):
            return Fix(
                file=error.file,
                line=error.line,
                description=f"Add missing import: {import_line}",
                strategy="real-fix",
            )
    return None


def fix_import_errors(lines: list[str], error: MypyError) -> Fix | None:
    """Fix import-untyped and import-not-found with targeted suppression."""
    if error.code not in ("import-untyped", "import-not-found"):
        return None
    idx = error.line - 1
    if idx >= len(lines):
        return None
    line = lines[idx]
    if has_type_ignore(line, error.code):
        return None
    lines[idx] = add_type_ignore(line, error.code)
    return Fix(
        file=error.file,
        line=error.line,
        description=f"Suppress {error.code} for third-party import",
        strategy="suppression",
        original_code=line.strip(),
    )


def fix_generic_suppression(lines: list[str], error: MypyError) -> Fix | None:
    """Last resort: add targeted # type: ignore[code] suppression."""
    suppressible_codes = {
        "assignment",
        "arg-type",
        "return-value",
        "attr-defined",
        "override",
        "misc",
        "call-overload",
        "type-arg",
        "index",
        "operator",
        "no-untyped-call",
        "redundant-cast",
        "var-annotated",
    }
    if error.code not in suppressible_codes:
        return None
    idx = error.line - 1
    if idx >= len(lines):
        return None
    line = lines[idx]
    if has_type_ignore(line, error.code):
        return None
    lines[idx] = add_type_ignore(line, error.code)
    return Fix(
        file=error.file,
        line=error.line,
        description=f"Suppress mypy [{error.code}]: {error.message[:80]}",
        strategy="suppression",
        original_code=line.strip(),
    )
