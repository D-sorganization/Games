"""Tests for scripts/analyze_completist_data.py extracted helper functions.

Covers the private helpers introduced when ``generate_report`` was
decomposed as part of issue #743. The test file uses a temporary
``ISSUES_DIR`` / ``REPORT_DIR`` to avoid touching the working tree.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Make scripts importable without a full package install
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import analyze_completist_data as acd  # noqa: E402


def _finding(
    *,
    file: str = "src/games/shared/python/foo.py",
    line: str = "10",
    type_: str = "Stub",
    name: str = "do_thing",
) -> acd.Finding:
    return acd.Finding(file=file, line=line, name=name, type=type_)


# ---------------------------------------------------------------------------
# _collect_report_data
# ---------------------------------------------------------------------------


def test_collect_report_data_filters_tests_from_criticals() -> None:
    stub_in_test = _finding(file="tests/shared/test_foo.py")
    stub_in_src = _finding(file="src/games/shared/python/foo.py")
    with (
        patch.object(acd, "analyze_stubs", return_value=[stub_in_test, stub_in_src]),
        patch.object(acd, "analyze_not_implemented", return_value=[]),
        patch.object(acd, "analyze_todos", return_value=([], [])),
        patch.object(acd, "analyze_docs", return_value=[]),
        patch.object(acd, "analyze_abstract_methods", return_value=[]),
    ):
        data = acd._collect_report_data()

    assert len(data["criticals"]) == 1
    assert data["criticals"][0]["file"] == "src/games/shared/python/foo.py"


def test_collect_report_data_sorts_criticals_by_impact_desc() -> None:
    high = _finding(file="src/games/shared/python/high.py")
    low = _finding(file="tools/low.py")
    with (
        patch.object(acd, "analyze_stubs", return_value=[low, high]),
        patch.object(acd, "analyze_not_implemented", return_value=[]),
        patch.object(acd, "analyze_todos", return_value=([], [])),
        patch.object(acd, "analyze_docs", return_value=[]),
        patch.object(acd, "analyze_abstract_methods", return_value=[]),
    ):
        data = acd._collect_report_data()

    impacts = [acd.calculate_metrics(c)[0] for c in data["criticals"]]
    assert impacts == sorted(impacts, reverse=True)
    assert data["criticals"][0]["file"] == "src/games/shared/python/high.py"


# ---------------------------------------------------------------------------
# _build_report_body
# ---------------------------------------------------------------------------


def test_build_report_body_includes_key_sections() -> None:
    data = acd._ReportData(criticals=[], todos=[], fixmes=[], missing_docs=[])
    body = acd._build_report_body(data, "2026-04-11")

    joined = "\n".join(body)
    assert "# Completist Report: 2026-04-11" in joined
    assert "## Executive Summary" in joined
    assert "## Critical Incomplete (Top 50)" in joined
    assert "## Feature Gap Matrix" in joined
    assert "## Technical Debt Register" in joined
    assert "## Recommended Implementation Order" in joined


def test_build_report_body_lists_critical_row() -> None:
    crit = _finding(file="src/games/shared/python/core.py", line="42", type_="Stub")
    data = acd._ReportData(criticals=[crit], todos=[], fixmes=[], missing_docs=[])
    body = acd._build_report_body(data, "2026-04-11")
    joined = "\n".join(body)
    assert "`src/games/shared/python/core.py`" in joined
    assert "| 42 |" in joined
    assert "Stub" in joined


# ---------------------------------------------------------------------------
# _create_issues_section
# ---------------------------------------------------------------------------


def test_create_issues_section_header_only_when_no_high_impact(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(acd, "ISSUES_DIR", str(tmp_path))
    low_impact = _finding(file="tools/low.py")  # impact=3
    lines = acd._create_issues_section([low_impact])
    assert lines[0] == "\n## Issues Created"
    # No issue files should have been created
    assert list(tmp_path.glob("Issue_*.md")) == []


def test_create_issues_section_creates_files_for_high_impact(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(acd, "ISSUES_DIR", str(tmp_path))
    high = _finding(file="src/games/shared/python/core.py")  # impact=5
    lines = acd._create_issues_section([high])

    created = list(tmp_path.glob("Issue_*.md"))
    assert len(created) == 1
    # Reporting line references the created file
    assert any("Created" in line for line in lines[1:])


# ---------------------------------------------------------------------------
# _write_report_files
# ---------------------------------------------------------------------------


def test_write_report_files_writes_dated_and_latest(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(acd, "REPORT_DIR", str(tmp_path))
    payload = ["line 1", "line 2"]
    dated = acd._write_report_files(payload, "2026-04-11")

    assert os.path.exists(dated)
    assert os.path.exists(os.path.join(str(tmp_path), "COMPLETIST_LATEST.md"))
    with open(dated, encoding="utf-8") as f:
        text = f.read()
    assert text == "line 1\nline 2"


# ---------------------------------------------------------------------------
# generate_report orchestration
# ---------------------------------------------------------------------------


def test_generate_report_is_thin_orchestrator(tmp_path: Path, monkeypatch) -> None:
    """End-to-end smoke test: the public entry point still produces a report."""
    monkeypatch.setattr(acd, "REPORT_DIR", str(tmp_path / "report"))
    monkeypatch.setattr(acd, "ISSUES_DIR", str(tmp_path / "issues"))

    with (
        patch.object(acd, "analyze_stubs", return_value=[]),
        patch.object(acd, "analyze_not_implemented", return_value=[]),
        patch.object(acd, "analyze_todos", return_value=([], [])),
        patch.object(acd, "analyze_docs", return_value=[]),
        patch.object(acd, "analyze_abstract_methods", return_value=[]),
    ):
        acd.generate_report()

    latest = os.path.join(str(tmp_path / "report"), "COMPLETIST_LATEST.md")
    assert os.path.exists(latest)
    with open(latest, encoding="utf-8") as f:
        text = f.read()
    assert "Completist Report" in text
    assert "## Executive Summary" in text
