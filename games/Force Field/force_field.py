#!/usr/bin/env python3
"""
First-Person Shooter Game
Refactored into modules.
"""

import logging
import sys
from pathlib import Path

import pygame

logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point of the FPS Shooter application."""
    # Make sure the game directory is in path to import 'src'
    # This allows running the script from any directory
    game_dir = Path(__file__).resolve().parent
    if str(game_dir) not in sys.path:
        sys.path.insert(0, str(game_dir))

    from src.game import Game  # noqa: PLC0415

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

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
