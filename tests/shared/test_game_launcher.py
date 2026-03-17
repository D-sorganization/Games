"""Tests for games.shared.game_launcher module.

Tests setup_game_path and setup_logging utilities.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from games.shared.game_launcher import run_game, setup_game_path, setup_logging

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

    def test_frozen_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: object
    ) -> None:
        """Should use sys._MEIPASS if execution is frozen."""
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        meipass_dir = Path(str(tmp_path)) / "meipass"
        meipass_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(sys, "_MEIPASS", str(meipass_dir), raising=False)
        result = setup_game_path("fake_file.py", use_frozen_path=True)
        assert result == meipass_dir


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


# ---------------------------------------------------------------------------
# run_game
# ---------------------------------------------------------------------------


class TestRunGame:
    """Tests for run_game standard launcher."""

    @patch("games.shared.game_launcher.sys.exit")
    @patch("games.shared.game_launcher.pygame")
    @patch("games.shared.game_launcher.setup_game_path")
    @patch("games.shared.game_launcher.setup_logging")
    def test_run_game_normal(
        self,
        mock_setup_log: MagicMock,
        mock_setup_path: MagicMock,
        mock_pygame: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """Should initialize appropriately and run the game, then clean up."""
        mock_game_class = MagicMock()
        mock_game_instance = MagicMock()
        mock_game_class.return_value = mock_game_instance

        import os

        if "SDL_VIDEO_CENTERED" in os.environ:
            del os.environ["SDL_VIDEO_CENTERED"]

        run_game(
            mock_game_class, "test_file.py", center_window=True, use_frozen_path=True
        )

        mock_setup_path.assert_called_with("test_file.py", True)
        mock_setup_log.assert_called()
        mock_pygame.init.assert_called()
        mock_game_instance.run.assert_called()
        mock_pygame.quit.assert_called()
        mock_sys_exit.assert_called()

        assert os.environ.get("SDL_VIDEO_CENTERED") == "1"

    @patch("games.shared.game_launcher.sys.exit")
    @patch("games.shared.game_launcher.pygame")
    @patch("games.shared.game_launcher.setup_game_path")
    @patch("games.shared.game_launcher.setup_logging")
    def test_run_game_keyboard_interrupt(
        self,
        mock_setup_log: MagicMock,
        mock_setup_path: MagicMock,
        mock_pygame: MagicMock,
        mock_sys_exit: MagicMock,
    ) -> None:
        """Should catch KeyboardInterrupt gracefully and exit cleanly."""
        mock_game_class = MagicMock()
        mock_game_instance = MagicMock()
        mock_game_instance.run.side_effect = KeyboardInterrupt()
        mock_game_class.return_value = mock_game_instance

        run_game(mock_game_class, "test_file.py")

        mock_pygame.quit.assert_called()
        mock_sys_exit.assert_called()
