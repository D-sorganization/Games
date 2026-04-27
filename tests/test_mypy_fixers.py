"""Tests for scripts/mypy_fixers.py extracted helper functions.

Covers the private helpers introduced when the public fix functions were
decomposed as part of issue #746.
"""

from __future__ import annotations

import os
import sys

# Make scripts importable without a full package install
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from scripts.mypy_fixers import (
    MypyError,
    _extract_union_attr_parts,
    _find_last_import_index,
    _find_post_docstring_index,
    _insert_isinstance_narrowing,
    _replace_callable_annotation,
    _resolve_union_narrowing,
)

# ---------------------------------------------------------------------------
# _find_last_import_index  (extracted in issue #746)
# ---------------------------------------------------------------------------


def test_find_last_import_index_returns_minus1_for_empty() -> None:
    assert _find_last_import_index([]) == -1


def test_find_last_import_index_returns_minus1_for_no_imports() -> None:
    lines = ["x = 1\n", "y = 2\n"]
    assert _find_last_import_index(lines) == -1


def test_find_last_import_index_simple_import() -> None:
    lines = ["import os\n", "import sys\n", "x = 1\n"]
    assert _find_last_import_index(lines) == 1


def test_find_last_import_index_from_import() -> None:
    lines = ["from pathlib import Path\n", "x = 1\n"]
    assert _find_last_import_index(lines) == 0


def test_find_last_import_index_ignores_docstring_content() -> None:
    lines = [
        '"""Module docstring.\n',
        "import os inside docstring\n",
        '"""\n',
        "import sys\n",
        "x = 1\n",
    ]
    # Only the real 'import sys' at index 3 should be found
    assert _find_last_import_index(lines) == 3


def test_find_last_import_index_comment_lines_ignored() -> None:
    lines = ["import os\n", "# a comment\n", "import sys\n", "x = 1\n"]
    assert _find_last_import_index(lines) == 2


# ---------------------------------------------------------------------------
# _find_post_docstring_index  (extracted in issue #746)
# ---------------------------------------------------------------------------


def test_find_post_docstring_index_empty_returns_0() -> None:
    assert _find_post_docstring_index([]) == 0


def test_find_post_docstring_index_no_docstring() -> None:
    lines = ["x = 1\n"]
    assert _find_post_docstring_index(lines) == 0


def test_find_post_docstring_index_single_line_docstring() -> None:
    lines = ['"""Single line."""\n', "import os\n"]
    # Should return 1, right after the docstring
    assert _find_post_docstring_index(lines) == 1


def test_find_post_docstring_index_multi_line_docstring() -> None:
    lines = [
        '"""Multi\n',
        "line docstring.\n",
        '"""\n',
        "import os\n",
    ]
    assert _find_post_docstring_index(lines) == 3


# ---------------------------------------------------------------------------
# _replace_callable_annotation  (extracted in issue #746)
# ---------------------------------------------------------------------------


def test_replace_callable_annotation_replaces_callable() -> None:
    lines = ["def foo(fn: callable) -> None:\n", "    pass\n"]
    original = _replace_callable_annotation(lines, 0)
    assert original is not None
    # After replacement, the function line (now at index 0 since no imports
    # existed before it) contains Callable[..., Any]
    combined = "".join(lines)
    assert "Callable[..., Any]" in combined


def test_replace_callable_annotation_returns_none_when_no_match() -> None:
    lines = ["def foo(x: int) -> None:\n"]
    assert _replace_callable_annotation(lines, 0) is None


def test_replace_callable_annotation_adds_imports() -> None:
    lines = ["def foo(fn: callable) -> None:\n", "    pass\n"]
    _replace_callable_annotation(lines, 0)
    combined = "".join(lines)
    assert "from collections.abc import Callable" in combined
    assert "from typing import Any" in combined


# ---------------------------------------------------------------------------
# _extract_union_attr_parts  (extracted in issue #746)
# ---------------------------------------------------------------------------


def _make_error(message: str, code: str = "union-attr") -> MypyError:
    return MypyError(
        file="src/games/foo.py",
        line=5,
        column=1,
        severity="error",
        message=message,
        code=code,
    )


def test_extract_union_attr_parts_parses_message() -> None:
    msg = 'Item "None" of "str | None" has no attribute "upper"'
    result = _extract_union_attr_parts(_make_error(msg))
    assert result is not None
    bad_type, attr, good_type = result
    assert bad_type == "None"
    assert attr == "upper"
    assert good_type == "str"


def test_extract_union_attr_parts_returns_none_on_no_match() -> None:
    assert _extract_union_attr_parts(_make_error("unrelated message")) is None


def test_extract_union_attr_parts_returns_none_when_no_good_types() -> None:
    msg = 'Item "None" of "None" has no attribute "upper"'
    assert _extract_union_attr_parts(_make_error(msg)) is None


# ---------------------------------------------------------------------------
# _insert_isinstance_narrowing  (extracted in issue #746)
# ---------------------------------------------------------------------------


def test_insert_isinstance_narrowing_inserts_before_target() -> None:
    lines = ["    result = obj.upper()\n"]
    original = _insert_isinstance_narrowing(lines, 0, "obj", "str")
    assert "assert isinstance(obj, str)" in lines[0]
    assert lines[1] == original


def test_insert_isinstance_narrowing_preserves_indentation() -> None:
    lines = ["        result = obj.upper()\n"]
    _insert_isinstance_narrowing(lines, 0, "obj", "str")
    assert lines[0].startswith("        assert")


# ---------------------------------------------------------------------------
# _resolve_union_narrowing  (extracted in issue #746)
# ---------------------------------------------------------------------------


def test_resolve_union_narrowing_returns_tuple() -> None:
    lines = ["    result = obj.upper()\n"]
    msg = 'Item "None" of "str | None" has no attribute "upper"'
    error = MypyError(
        file="src/games/foo.py",
        line=1,
        column=1,
        severity="error",
        message=msg,
        code="union-attr",
    )
    result = _resolve_union_narrowing(lines, error)
    assert result is not None
    var_name, target_type, _orig, idx = result
    assert var_name == "obj"
    assert target_type == "str"
    assert idx == 0


def test_resolve_union_narrowing_returns_none_for_bad_message() -> None:
    lines = ["    result = obj.upper()\n"]
    error = MypyError(
        file="src/games/foo.py",
        line=1,
        column=1,
        severity="error",
        message="unrelated",
        code="union-attr",
    )
    assert _resolve_union_narrowing(lines, error) is None


def test_resolve_union_narrowing_skips_if_isinstance_already_nearby() -> None:
    lines = [
        "    assert isinstance(obj, str)\n",
        "    assert isinstance(obj, str)\n",
        "    assert isinstance(obj, str)\n",
        "    result = obj.upper()\n",
    ]
    msg = 'Item "None" of "str | None" has no attribute "upper"'
    error = MypyError(
        file="src/games/foo.py",
        line=4,
        column=1,
        severity="error",
        message=msg,
        code="union-attr",
    )
    assert _resolve_union_narrowing(lines, error) is None
