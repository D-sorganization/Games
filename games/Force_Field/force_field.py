#!/usr/bin/env python3
"""
First-Person Shooter Game - Force Field Arena Combat.

A raycasting-based first-person shooter featuring arena combat,
multiple weapons, enemy AI, and progressive difficulty.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pygame

logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point of the Force Field Arena Combat game.

    Initializes the game environment, sets up logging, and handles
    graceful shutdown on interruption or errors.
    """
    # Make sure the game directory is in path to import 'src'
    # This allows running the script from any directory
    game_dir = Path(__file__).resolve().parent
    if str(game_dir) not in sys.path:
        sys.path.insert(0, str(game_dir))

    from src.game import Game

    # Enhanced logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                game_dir / "force_field.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            ),
        ],
    )

    logger.info("Starting Force Field Arena Combat")

    try:
        pygame.init()
        logger.info("Pygame initialized successfully")

        game = Game()
        game.run()

    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
    except Exception as e:
        logger.exception("Fatal error occurred: %s", e)
        raise
    finally:
        try:
            pygame.quit()
            logger.info("Game shutdown complete")
        except Exception as e:
            logger.error("Error during shutdown: %s", e)


if __name__ == "__main__":
    main()
