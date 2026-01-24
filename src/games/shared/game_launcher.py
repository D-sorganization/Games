#!/usr/bin/env python3
"""Shared game launcher utilities to eliminate code duplication."""

import logging
import sys
from pathlib import Path
from typing import Any

import pygame

logger = logging.getLogger(__name__)


def setup_game_path(game_file: str, use_frozen_path: bool = False) -> Path:
    """
    Setup the game directory path and add it to sys.path.

    Args:
        game_file: The __file__ attribute from the calling module
        use_frozen_path: Whether to support PyInstaller frozen executables

    Returns:
        The base path for the game
    """
    if use_frozen_path and getattr(sys, "frozen", False):
        # Running as compiled executable
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        # Running as script
        base_path = Path(game_file).resolve().parent

    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))

    return base_path


def setup_logging(level: int = logging.INFO) -> None:
    """
    Setup basic logging configuration.

    Args:
        level: The logging level to use
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def run_game(
    game_class: type[Any],
    game_file: str,
    center_window: bool = False,
    use_frozen_path: bool = False,
) -> None:
    """
    Standard game launcher that handles initialization and cleanup.

    Args:
        game_class: The Game class to instantiate and run
        game_file: The __file__ attribute from the calling module
        center_window: Whether to center the game window on screen
        use_frozen_path: Whether to support PyInstaller frozen executables
    """
    setup_game_path(game_file, use_frozen_path)
    setup_logging()

    if center_window:
        import os

        os.environ["SDL_VIDEO_CENTERED"] = "1"

    pygame.init()
    try:
        game = game_class()
        game.run()
    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
    finally:
        pygame.quit()
        sys.exit()
