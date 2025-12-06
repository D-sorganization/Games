#!/usr/bin/env python3
"""
First-Person Shooter Game
Refactored into modules.
"""

# Make sure src is in path if running directly from this directory
import os
import sys

import pygame

sys.path.append(os.path.dirname(__file__))

from src.game import Game


def main() -> None:
    """Entry point of the FPS Shooter application."""
    pygame.init()
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
