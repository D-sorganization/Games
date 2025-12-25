#!/usr/bin/env python3
"""
First-Person Shooter Game
Refactored into modules.
"""

import logging
import os
import sys
from pathlib import Path

import pygame

logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point of the FPS Shooter application."""
    # Setup path for resource/module loading
    if getattr(sys, "frozen", False):
        # Running as compiled executable
        # sys._MEIPASS holds the temp folder where resources are decompressed
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        # Running as script
        base_path = Path(__file__).resolve().parent

    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))

    from src.game import Game

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    # Center the game window
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    pygame.init()
    try:
        game = Game()
        game.run()
    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
    finally:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
