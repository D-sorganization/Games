"""Top-level state dispatch loop for Duum."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from games.shared.constants import GameState

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .game import Game


logger = logging.getLogger(__name__)


def run(game: Game) -> None:
    """Execute the main loop until the game stops running."""
    try:
        while game.running:
            run_frame(game)
            game.clock.tick(C.FPS)  # type: ignore
    except (RuntimeError, pygame.error, OSError, ValueError, TypeError) as exc:
        logger.critical("CRASH: %s", exc, exc_info=True)
        raise


def run_frame(game: Game) -> None:
    """Dispatch one frame based on the active top-level game state."""
    if game.state == GameState.INTRO:
        _run_intro_frame(game)
    elif game.state == GameState.MENU:
        game.handle_menu_events()
        game.ui_renderer.render_menu()
    elif game.state == GameState.KEY_CONFIG:
        game.handle_key_config_events()
        game.ui_renderer.render_key_config(game)
    elif game.state == GameState.MAP_SELECT:
        game.handle_map_select_events()
        game.ui_renderer.render_map_select(game)
    elif game.state == GameState.PLAYING:
        game.screen_event_handler.handle_playing_state()
    elif game.state == GameState.LEVEL_COMPLETE:
        game.handle_level_complete_events()
        game.ui_renderer.render_level_complete(game)
    elif game.state == GameState.GAME_OVER:
        game.handle_game_over_events()
        game.ui_renderer.render_game_over(game)


def _run_intro_frame(game: Game) -> None:
    """Run one frame of the intro state."""
    game.handle_intro_events()
    if game.intro_start_time == 0:
        game.intro_start_time = pygame.time.get_ticks()
    elapsed = pygame.time.get_ticks() - game.intro_start_time
    game.ui_renderer.render_intro(game.intro_phase, game.intro_step, elapsed)
    game._update_intro_logic(elapsed)
