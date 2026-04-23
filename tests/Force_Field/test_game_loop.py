"""Focused tests for the extracted Force Field game-loop subsystem."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pygame

from games.shared.constants import GameState


def _loop_game(**overrides: object) -> SimpleNamespace:
    """Build a lightweight game stub for game-loop tests."""
    base = {
        "running": True,
        "state": GameState.PLAYING,
        "paused": False,
        "damage_flash_timer": 3,
        "intro_start_time": 0,
        "intro_phase": 0,
        "intro_step": 0,
        "clock": MagicMock(),
        "ui_renderer": MagicMock(),
        "renderer": MagicMock(),
        "game_input_handler": MagicMock(),
        "handle_intro_events": MagicMock(),
        "_update_intro_logic": MagicMock(),
        "handle_menu_events": MagicMock(),
        "handle_key_config_events": MagicMock(),
        "handle_map_select_events": MagicMock(),
        "handle_level_complete_events": MagicMock(),
        "handle_game_over_events": MagicMock(),
        "update_game": MagicMock(),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_run_frame_updates_playing_state() -> None:
    """Playing frames should process input, update, render, and decay flash."""
    from games.Force_Field.src.game_loop import run_frame

    game = _loop_game(state=GameState.PLAYING, paused=False, damage_flash_timer=2)

    run_frame(game)

    game.game_input_handler.handle_game_events.assert_called_once_with()
    game.update_game.assert_called_once_with()
    game.renderer.render_game.assert_called_once_with(game)
    assert game.damage_flash_timer == 1


def test_run_frame_skips_update_when_paused() -> None:
    """Paused gameplay frames should still render without mutating logic."""
    from games.Force_Field.src.game_loop import run_frame

    game = _loop_game(state=GameState.PLAYING, paused=True, damage_flash_timer=2)

    run_frame(game)

    game.game_input_handler.handle_game_events.assert_called_once_with()
    game.update_game.assert_not_called()
    game.renderer.render_game.assert_called_once_with(game)
    assert game.damage_flash_timer == 2


def test_run_frame_intro_initializes_timer_and_renders(monkeypatch) -> None:
    """Intro frames should initialize timing and delegate rendering/logic."""
    from games.Force_Field.src.game_loop import run_frame

    game = _loop_game(state=GameState.INTRO, intro_start_time=0)
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1234)

    run_frame(game)

    game.handle_intro_events.assert_called_once_with()
    game.ui_renderer.render_intro.assert_called_once_with(0, 0, 0)
    game._update_intro_logic.assert_called_once_with(0)
    assert game.intro_start_time == 1234


def test_run_ticks_clock_until_stopped() -> None:
    """The outer loop should keep dispatching frames while running is true."""
    from games.Force_Field.src import game_loop

    game = _loop_game()

    def stop_after_first_frame(current_game) -> None:
        current_game.running = False

    game_loop.run_frame = stop_after_first_frame  # type: ignore[assignment]
    try:
        game_loop.run(game)
    finally:
        del game_loop.run_frame

    game.clock.tick.assert_called_once()
