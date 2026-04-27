"""Tests for scripts/run_assessment.py extracted helper functions.

Covers file_discovery, analyze_module, calculate_scores, and generate_report
following the repository's TDD / SRP guidelines (issue #680).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make scripts importable without a full package install
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.run_assessment import (  # noqa: E402
    ASSESSMENTS,
    analyze_module,
    calculate_scores,
    file_discovery,
    generate_report,
    run_assessment,
)

# ---------------------------------------------------------------------------
# Shared patch targets
# ---------------------------------------------------------------------------
_RUFF = "scripts.run_assessment.run_ruff_check_wrapper"
_BLACK = "scripts.run_assessment.run_black_check_wrapper"
_RUFF_PASS = {"exit_code": 0}
_BLACK_PASS = {"exit_code": 0}
_RUFF_FAIL = {"exit_code": 1}


# ---------------------------------------------------------------------------
# file_discovery
# ---------------------------------------------------------------------------


class TestFileDiscovery:
    """Tests for file_discovery()."""

    def test_returns_tuple_of_list_and_int(self) -> None:
        """file_discovery() should return (list[Path], int)."""
        with patch("scripts.assessment_modules.find_python_files", return_value=[]):
            files, count = file_discovery()
        assert isinstance(files, list)
        assert isinstance(count, int)

    def test_count_matches_list_length(self) -> None:
        """Count returned must equal len(files)."""
        fake_files = [Path("a.py"), Path("b.py"), Path("c.py")]
        with patch(
            "scripts.assessment_modules.find_python_files", return_value=fake_files
        ):
            files, count = file_discovery()
        assert count == len(files)
        assert count == 3

    def test_empty_repository_returns_zero(self) -> None:
        """An empty project produces an empty list and count 0."""
        with patch("scripts.assessment_modules.find_python_files", return_value=[]):
            files, count = file_discovery()
        assert files == []
        assert count == 0

    def test_returns_same_files_as_find_python_files(self) -> None:
        """file_discovery() must pass through all files from find_python_files."""
        expected = [Path("x.py"), Path("y.py")]
        with patch(
            "scripts.assessment_modules.find_python_files", return_value=expected
        ):
            files, count = file_discovery()
        assert files == expected


# ---------------------------------------------------------------------------
# analyze_module
# ---------------------------------------------------------------------------


class TestAnalyzeModule:
    """Tests for analyze_module()."""

    # --- common contract tests ---

    def test_returns_tuple_of_findings_and_score(self) -> None:
        """analyze_module() must return (list, int|None)."""
        with patch("scripts.assessment_modules.count_test_files", return_value=10):
            findings, score = analyze_module("A", [], 0)
        assert isinstance(findings, list)
        assert score is None or isinstance(score, int)

    def test_findings_are_non_empty_for_valid_id(self) -> None:
        """Every recognised assessment ID should produce at least one finding."""
        mock_run = MagicMock(returncode=1, stdout="", stderr="")
        for aid in ASSESSMENTS:
            with (
                patch("scripts.assessment_modules.count_test_files", return_value=5),
                patch(
                    "scripts.assessment_modules.check_documentation",
                    return_value={
                        "has_readme": True,
                        "has_docs_dir": True,
                        "has_changelog": True,
                    },
                ),
                patch("scripts.assessment_modules.grep_in_files", return_value=3),
                patch(_RUFF, return_value=_RUFF_PASS),
                patch(_BLACK, return_value=_BLACK_PASS),
                patch("scripts.assessment_modules.run_command", return_value=mock_run),
            ):
                findings, _ = analyze_module(aid, [], 0)
            assert len(findings) > 0, f"No findings for assessment {aid}"

    def test_unknown_id_returns_none_score(self) -> None:
        """An unrecognised assessment ID (e.g. 'Z') returns score=None."""
        findings, score = analyze_module("Z", [], 0)
        assert score is None
        assert any("REQUIRES REVIEW" in f for f in findings)

    # --- Assessment A ---

    def test_assessment_a_deducts_for_missing_src(self, tmp_path: Path) -> None:
        """Assessment A deducts 2 points when src/ does not exist."""
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            with patch("scripts.assessment_modules.count_test_files", return_value=5):
                findings, score = analyze_module("A", [], 0)
        finally:
            os.chdir(original_cwd)
        assert score is not None
        assert score <= 8

    def test_assessment_a_records_file_count(self) -> None:
        """Assessment A finding must include the file count."""
        with patch("scripts.assessment_modules.count_test_files", return_value=0):
            findings, _ = analyze_module("A", [], 42)
        assert any("42" in f for f in findings)

    # --- Assessment B ---

    def test_assessment_b_deducts_for_missing_readme(self) -> None:
        """Assessment B deducts 3 points when README.md does not exist."""
        docs = {
            "has_readme": False,
            "has_docs_dir": True,
            "has_changelog": False,
        }
        with patch("scripts.assessment_modules.check_documentation", return_value=docs):
            findings, score = analyze_module("B", [], 0)
        assert score is not None
        assert score <= 7

    def test_assessment_b_full_score_with_all_docs(self) -> None:
        """Assessment B keeps full score when all documentation is present."""
        docs = {
            "has_readme": True,
            "has_docs_dir": True,
            "has_changelog": True,
        }
        with patch("scripts.assessment_modules.check_documentation", return_value=docs):
            findings, score = analyze_module("B", [], 0)
        assert score == 10

    # --- Assessment C ---

    def test_assessment_c_deducts_for_no_tests(self) -> None:
        """Assessment C deducts 5 points when no test files exist."""
        mock_run = MagicMock(returncode=1, stdout="", stderr="")
        with (
            patch("scripts.assessment_modules.count_test_files", return_value=0),
            patch("scripts.assessment_modules.run_command", return_value=mock_run),
        ):
            findings, score = analyze_module("C", [], 0)
        assert any("Critical" in f for f in findings)
        assert score is not None
        assert score <= 5

    def test_assessment_c_notes_good_test_count(self) -> None:
        """Assessment C notes a good test count when >= 5 test files exist."""
        mock_run = MagicMock(returncode=1, stdout="", stderr="")
        with (
            patch("scripts.assessment_modules.count_test_files", return_value=10),
            patch("scripts.assessment_modules.run_command", return_value=mock_run),
        ):
            findings, score = analyze_module("C", [], 0)
        assert any("Good" in f for f in findings)

    # --- Assessment I ---

    def test_assessment_i_deducts_for_ruff_failure(self) -> None:
        """Assessment I deducts 3 points on ruff failure."""
        with (
            patch(_RUFF, return_value=_RUFF_FAIL),
            patch(_BLACK, return_value=_BLACK_PASS),
        ):
            findings, score = analyze_module("I", [], 0)
        assert score is not None
        assert score <= 7

    def test_assessment_i_full_score_when_clean(self) -> None:
        """Assessment I keeps full score when both ruff and black pass."""
        with (
            patch(_RUFF, return_value=_RUFF_PASS),
            patch(_BLACK, return_value=_BLACK_PASS),
        ):
            findings, score = analyze_module("I", [], 0)
        assert score == 10


# ---------------------------------------------------------------------------
# calculate_scores
# ---------------------------------------------------------------------------


class TestCalculateScores:
    """Tests for calculate_scores()."""

    def test_returns_clamped_score_and_display_string(self) -> None:
        """calculate_scores() returns a tuple of (int, str)."""
        clamped, display = calculate_scores(7)
        assert clamped == 7
        assert display == "7/10"

    def test_clamps_negative_to_zero(self) -> None:
        """Scores below 0 are clamped to 0."""
        clamped, display = calculate_scores(-5)
        assert clamped == 0
        assert display == "0/10"

    def test_clamps_above_ten_to_ten(self) -> None:
        """Scores above 10 are clamped to 10."""
        clamped, display = calculate_scores(15)
        assert clamped == 10
        assert display == "10/10"

    def test_none_score_returns_pending(self) -> None:
        """A None score produces 'PENDING REVIEW' display string."""
        clamped, display = calculate_scores(None)
        assert clamped is None
        assert display == "PENDING REVIEW"

    def test_zero_score_formats_correctly(self) -> None:
        """Score of exactly 0 should display as '0/10'."""
        clamped, display = calculate_scores(0)
        assert clamped == 0
        assert display == "0/10"

    def test_ten_score_formats_correctly(self) -> None:
        """Score of exactly 10 should display as '10/10'."""
        clamped, display = calculate_scores(10)
        assert clamped == 10
        assert display == "10/10"

    @pytest.mark.parametrize("raw,expected", [(1, 1), (5, 5), (8, 8)])
    def test_mid_range_scores_pass_through(self, raw: int, expected: int) -> None:
        """Mid-range integer scores should pass through unchanged."""
        clamped, display = calculate_scores(raw)
        assert clamped == expected
        assert display == f"{expected}/10"


# ---------------------------------------------------------------------------
# generate_report
# ---------------------------------------------------------------------------


class TestGenerateReport:
    """Tests for generate_report()."""

    def _minimal_assessment(self) -> dict:
        return {"name": "Test Name", "description": "Test description"}

    def test_creates_output_file(self, tmp_path: Path) -> None:
        """generate_report() must create the output file."""
        out = tmp_path / "report.md"
        generate_report("A", self._minimal_assessment(), "9/10", ["- finding"], out)
        assert out.exists()

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """generate_report() must create missing parent directories."""
        out = tmp_path / "nested" / "deep" / "report.md"
        generate_report("B", self._minimal_assessment(), "8/10", [], out)
        assert out.exists()

    def test_report_contains_assessment_id(self, tmp_path: Path) -> None:
        """Report markdown must include the assessment ID."""
        out = tmp_path / "r.md"
        generate_report("C", self._minimal_assessment(), "7/10", [], out)
        content = out.read_text(encoding="utf-8")
        assert "Assessment C" in content

    def test_report_contains_score_display(self, tmp_path: Path) -> None:
        """Report markdown must include the formatted score string."""
        out = tmp_path / "r.md"
        generate_report("D", self._minimal_assessment(), "PENDING REVIEW", [], out)
        content = out.read_text(encoding="utf-8")
        assert "PENDING REVIEW" in content

    def test_report_contains_findings(self, tmp_path: Path) -> None:
        """Report markdown must include all findings lines."""
        out = tmp_path / "r.md"
        findings = ["- finding one", "- finding two"]
        generate_report("E", self._minimal_assessment(), "6/10", findings, out)
        content = out.read_text(encoding="utf-8")
        assert "finding one" in content
        assert "finding two" in content

    def test_report_contains_assessment_name(self, tmp_path: Path) -> None:
        """Report must mention the assessment name from the assessment dict."""
        out = tmp_path / "r.md"
        assessment = {"name": "Code Quality", "description": "desc"}
        generate_report("F", assessment, "5/10", [], out)
        content = out.read_text(encoding="utf-8")
        assert "Code Quality" in content

    def test_report_overrides_existing_file(self, tmp_path: Path) -> None:
        """Calling generate_report() twice must overwrite the previous content."""
        out = tmp_path / "r.md"
        generate_report("G", self._minimal_assessment(), "10/10", ["- old"], out)
        generate_report("G", self._minimal_assessment(), "1/10", ["- new"], out)
        content = out.read_text(encoding="utf-8")
        assert "1/10" in content
        assert "- new" in content


# ---------------------------------------------------------------------------
# run_assessment (orchestrator integration)
# ---------------------------------------------------------------------------


class TestRunAssessment:
    """Integration-style tests for the run_assessment() orchestrator."""

    def test_returns_zero_for_valid_assessment(self, tmp_path: Path) -> None:
        """run_assessment() must return 0 on success."""
        out = tmp_path / "report.md"
        with (
            patch("scripts.assessment_modules.find_python_files", return_value=[]),
            patch("scripts.assessment_modules.count_test_files", return_value=5),
        ):
            result = run_assessment("A", out)
        assert result == 0

    def test_returns_one_for_unknown_assessment(self, tmp_path: Path) -> None:
        """run_assessment() must return 1 when the assessment ID is unrecognised."""
        out = tmp_path / "report.md"
        result = run_assessment("Z", out)
        assert result == 1

    def test_creates_report_file(self, tmp_path: Path) -> None:
        """run_assessment() must leave a report file at output_path."""
        out = tmp_path / "report.md"
        with (
            patch("scripts.assessment_modules.find_python_files", return_value=[]),
            patch("scripts.assessment_modules.count_test_files", return_value=5),
        ):
            run_assessment("A", out)
        assert out.exists()

    def test_all_valid_ids_succeed(self, tmp_path: Path) -> None:
        """run_assessment() must succeed (return 0) for every defined assessment."""
        mock_run = MagicMock(returncode=1, stdout="", stderr="")
        for aid in ASSESSMENTS:
            out = tmp_path / f"report_{aid}.md"
            with (
                patch("scripts.assessment_modules.find_python_files", return_value=[]),
                patch("scripts.assessment_modules.count_test_files", return_value=5),
                patch(
                    "scripts.assessment_modules.check_documentation",
                    return_value={
                        "has_readme": True,
                        "has_docs_dir": True,
                        "has_changelog": True,
                    },
                ),
                patch("scripts.assessment_modules.grep_in_files", return_value=3),
                patch(_RUFF, return_value=_RUFF_PASS),
                patch(_BLACK, return_value=_BLACK_PASS),
                patch("scripts.assessment_modules.run_command", return_value=mock_run),
            ):
                result = run_assessment(aid, out)
            assert result == 0, f"run_assessment returned non-zero for assessment {aid}"
