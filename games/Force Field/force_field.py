#!/usr/bin/env python3
"""
First-Person Shooter Game
Refactored into modules.
"""

import logging
import os
import sys

import pygame

# Make sure the game directory is in path to import 'src'
# This allows running the script from any directory
GAME_DIR = os.path.dirname(os.path.abspath(__file__))
if GAME_DIR not in sys.path:
    sys.path.insert(0, GAME_DIR)

from src.game import Game


def main() -> None:
    """Entry point of the FPS Shooter application."""
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
        logging.info("Game interrupted by user")
    finally:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
