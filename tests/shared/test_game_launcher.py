"""Tests for games.shared.game_launcher module.

Tests setup_game_path and setup_logging utilities.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from games.shared.game_launcher import setup_game_path, setup_logging

# ---------------------------------------------------------------------------
# setup_game_path
# ---------------------------------------------------------------------------


class TestSetupGamePath:
    """Tests for setup_game_path."""

    def test_returns_parent_of_game_file(self, tmp_path: object) -> None:
        """Should return the parent directory of the game file."""
        fake_file = str(Path(str(tmp_path)) / "my_game" / "main.py")
        Path(fake_file).parent.mkdir(parents=True, exist_ok=True)
        Path(fake_file).touch()

        result = setup_game_path(fake_file)
        assert result == Path(fake_file).resolve().parent

    def test_adds_path_to_sys_path(self, tmp_path: object) -> None:
        """Should add the game directory to sys.path."""
        fake_file = str(Path(str(tmp_path)) / "test_game" / "game.py")
        Path(fake_file).parent.mkdir(parents=True, exist_ok=True)
        Path(fake_file).touch()

        original_path = sys.path.copy()
        result = setup_game_path(fake_file)

        try:
            assert str(result) in sys.path
        finally:
            sys.path[:] = original_path

    def test_does_not_duplicate_sys_path(self, tmp_path: object) -> None:
        """Should not add duplicate entries to sys.path."""
        fake_file = str(Path(str(tmp_path)) / "dup_test" / "g.py")
        Path(fake_file).parent.mkdir(parents=True, exist_ok=True)
        Path(fake_file).touch()

        original_path = sys.path.copy()
        try:
            setup_game_path(fake_file)
            setup_game_path(fake_file)  # Call twice
            count = sys.path.count(str(Path(fake_file).resolve().parent))
            assert count == 1
        finally:
            sys.path[:] = original_path


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------


class TestSetupLogging:
    """Tests for setup_logging."""

    def test_sets_logging_level(self) -> None:
        """Should configure root logger level."""
        setup_logging(level=logging.DEBUG)
        assert logging.getLogger().level == logging.DEBUG

    def test_default_level_is_info(self) -> None:
        """Default logging level should be INFO."""
        setup_logging()
        assert logging.getLogger().level == logging.INFO
