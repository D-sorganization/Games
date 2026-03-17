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

    def test_setup_game_path_frozen(self) -> None:
        """Should use sys._MEIPASS when frozen=True."""
        import sys
        from unittest.mock import patch

        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "_MEIPASS", "/fake/mei/pass", create=True),
        ):
            result = setup_game_path("dummy.py", use_frozen_path=True)
            assert str(result) == str(Path("/fake/mei/pass"))

        # Cleanup sys.path to not litter
        if "/fake/mei/pass" in sys.path:
            sys.path.remove("/fake/mei/pass")


# ---------------------------------------------------------------------------
# run_game
# ---------------------------------------------------------------------------


class TestRunGame:
    """Tests for run_game."""

    def test_run_game_success(self) -> None:
        from unittest.mock import MagicMock, patch

        from games.shared.game_launcher import run_game

        mock_game_class = MagicMock()
        mock_game_instance = MagicMock()
        mock_game_class.return_value = mock_game_instance

        with (
            patch("games.shared.game_launcher.setup_game_path") as mock_setup_path,
            patch("games.shared.game_launcher.setup_logging") as mock_setup_logging,
            patch("games.shared.game_launcher.pygame.init") as mock_pg_init,
            patch("games.shared.game_launcher.pygame.quit") as mock_pg_quit,
            patch("games.shared.game_launcher.sys.exit") as mock_sys_exit,
            patch.dict("os.environ", {}, clear=True),
        ):
            run_game(mock_game_class, "dummy_file.py", center_window=True)

            mock_setup_path.assert_called_once_with("dummy_file.py", False)
            mock_setup_logging.assert_called_once()
            mock_pg_init.assert_called_once()
            mock_game_class.assert_called_once()
            mock_game_instance.run.assert_called_once()
            mock_pg_quit.assert_called_once()
            mock_sys_exit.assert_called_once()

            import os

            assert os.environ.get("SDL_VIDEO_CENTERED") == "1"

    def test_run_game_keyboard_interrupt(self) -> None:
        from unittest.mock import MagicMock, patch

        from games.shared.game_launcher import run_game

        mock_game_class = MagicMock()
        mock_game_class.side_effect = KeyboardInterrupt()

        with (
            patch("games.shared.game_launcher.setup_game_path"),
            patch("games.shared.game_launcher.setup_logging"),
            patch("games.shared.game_launcher.pygame.init"),
            patch("games.shared.game_launcher.pygame.quit") as mock_pg_quit,
            patch("games.shared.game_launcher.sys.exit") as mock_sys_exit,
            patch("games.shared.game_launcher.logger.info") as mock_logger_info,
        ):
            run_game(mock_game_class, "dummy_file.py")

            mock_logger_info.assert_called_with("Game interrupted by user")
            mock_pg_quit.assert_called_once()
            mock_sys_exit.assert_called_once()
