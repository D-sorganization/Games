#!/usr/bin/env python3
"""
First-Person Shooter Game
Refactored into modules.
"""

from games.shared.game_launcher import run_game, setup_game_path


def main() -> None:
    """Entry point of the FPS Shooter application."""
    setup_game_path(__file__, use_frozen_path=True)
    from src.game import Game

    run_game(Game, __file__, center_window=True, use_frozen_path=True)


if __name__ == "__main__":
    main()
