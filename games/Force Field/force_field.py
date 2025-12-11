#!/usr/bin/env python3
"""
First-Person Shooter Game
Refactored into modules.
"""

# Make sure src is in path if running directly from this directory
import logging
import os
import sys

import pygame

sys.path.append(os.path.dirname(__file__))

from src.game import Game


def main() -> None:
    """Entry point of the FPS Shooter application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    pygame.init()
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
