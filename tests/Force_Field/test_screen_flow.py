"""Focused tests for the extracted Force Field screen-flow subsystem."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pygame

from games.shared.constants import GameState


def _screen_flow_game(**overrides: object) -> SimpleNamespace:
    """Build a lightweight game stub for screen-flow tests."""
    base = {
        "ui_renderer": MagicMock(),
        "running": True,
        "state": GameState.MAP_SELECT,
        "selected_map_size": 40,
        "selected_difficulty": "NORMAL",
        "selected_start_level": 1,
        "selected_lives": 3,
        "start_game": MagicMock(),
        "start_level": MagicMock(),
        "sound_manager": MagicMock(),
        "game_over_timer": 0,
        "binding_action": None,
        "paused": False,
        "input_manager": SimpleNamespace(
            bindings={"move_forward": pygame.K_w, "move_backward": pygame.K_s},
            bind_key=MagicMock(),
        ),
        "intro_phase": 1,
        "intro_step": 0,
        "intro_start_time": 100,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_handle_map_select_events_start_click_starts_game(monkeypatch) -> None:
    """Start-button clicks should kick off gameplay and grab the mouse."""
    from games.Force_Field.src.screen_flow import handle_map_select_events

    game = _screen_flow_game()
    game.ui_renderer.is_start_button_clicked.return_value = True
    event = SimpleNamespace(type=pygame.MOUSEBUTTONDOWN, pos=(400, 210))

    set_visible = MagicMock()
    set_grab = MagicMock()

    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (400, 300))
    monkeypatch.setattr(pygame.mouse, "set_visible", set_visible)
    monkeypatch.setattr(pygame.event, "get", lambda: [event])
    monkeypatch.setattr(pygame.event, "set_grab", set_grab)

    handle_map_select_events(game)

    game.start_game.assert_called_once_with()
    assert game.state == GameState.PLAYING
    set_visible.assert_called_once_with(False)
    set_grab.assert_called_once_with(True)


def test_handle_key_config_events_click_binds_action(monkeypatch) -> None:
    """Clicking a binding row should select that action for rebinding."""
    from games.Force_Field.src.screen_flow import handle_key_config_events

    game = _screen_flow_game(state=GameState.KEY_CONFIG)
    event = SimpleNamespace(type=pygame.MOUSEBUTTONDOWN, pos=(210, 125))

    monkeypatch.setattr(pygame.event, "get", lambda: [event])

    handle_key_config_events(game)

    assert game.binding_action == "move_backward"


def test_update_intro_logic_releases_video_on_phase_transition() -> None:
    """Crossing from phase 1 to phase 2 should release the intro video."""
    from games.Force_Field.src.screen_flow import update_intro_logic

    game = _screen_flow_game(state=GameState.INTRO, intro_phase=1, intro_start_time=500)

    update_intro_logic(game, elapsed=3100)

    assert game.intro_phase == 2
    assert game.intro_start_time == 0
    game.ui_renderer.release_intro_video.assert_called_once_with()
