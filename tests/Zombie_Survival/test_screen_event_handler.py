"""Tests for Zombie Survival ScreenEventHandler."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pygame

from games.shared.constants import GROAN_TIMER_DELAY, PAUSE_HEARTBEAT_DELAY, GameState


def _make_game(**overrides: object) -> SimpleNamespace:
    base = {
        "running": True,
        "state": GameState.INTRO,
        "intro_phase": 1,
        "intro_step": 0,
        "intro_start_time": 500,
        "paused": False,
        "heartbeat_timer": 0,
        "groan_timer": 0,
        "damage_flash_timer": 2,
        "game_over_timer": 0,
        "binding_action": None,
        "player": MagicMock(),
        "player_health": 100,
        "sound_manager": MagicMock(),
        "ui_renderer": MagicMock(),
        "renderer": MagicMock(),
        "input_manager": MagicMock(),
        "handle_game_events": MagicMock(),
        "update_game": MagicMock(),
        "start_game": MagicMock(),
        "start_level": MagicMock(),
        "selected_map_size": 40,
        "selected_difficulty": "NORMAL",
        "selected_start_level": 1,
        "selected_lives": 3,
        "level": 1,
    }
    base["ui_renderer"].intro_video = None
    base.update(overrides)
    return SimpleNamespace(**base)


# ---------------------------------------------------------------------------
# handle_intro_events
# ---------------------------------------------------------------------------


def test_handle_intro_events_space_goes_to_menu(monkeypatch) -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(state=GameState.INTRO)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_SPACE)],
    )
    ScreenEventHandler(game).handle_intro_events()
    assert game.state == GameState.MENU


def test_handle_intro_events_quit_sets_running_false(monkeypatch) -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(state=GameState.INTRO)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.QUIT)],
    )
    ScreenEventHandler(game).handle_intro_events()
    assert game.running is False


# ---------------------------------------------------------------------------
# handle_menu_events
# ---------------------------------------------------------------------------


def test_handle_menu_events_escape_sets_running_false(monkeypatch) -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(state=GameState.MENU)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_ESCAPE)],
    )
    ScreenEventHandler(game).handle_menu_events()
    assert game.running is False


def test_handle_menu_events_quit_sets_running_false(monkeypatch) -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(state=GameState.MENU)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.QUIT)],
    )
    ScreenEventHandler(game).handle_menu_events()
    assert game.running is False


def test_handle_menu_events_space_goes_to_map_select(monkeypatch) -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(state=GameState.MENU)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_SPACE)],
    )
    ScreenEventHandler(game).handle_menu_events()
    assert game.state == GameState.MAP_SELECT


# ---------------------------------------------------------------------------
# handle_level_complete_events
# ---------------------------------------------------------------------------


def test_handle_level_complete_events_space_starts_next_level(monkeypatch) -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(state=GameState.LEVEL_COMPLETE, level=2)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_SPACE)],
    )
    ScreenEventHandler(game).handle_level_complete_events()
    assert game.state == GameState.PLAYING
    assert game.level == 3


def test_handle_level_complete_events_escape_goes_to_menu(monkeypatch) -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(state=GameState.LEVEL_COMPLETE)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_ESCAPE)],
    )
    ScreenEventHandler(game).handle_level_complete_events()
    assert game.state == GameState.MENU


def test_handle_level_complete_events_quit_stops_game(monkeypatch) -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(state=GameState.LEVEL_COMPLETE)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.QUIT)],
    )
    ScreenEventHandler(game).handle_level_complete_events()
    assert game.running is False


# ---------------------------------------------------------------------------
# handle_game_over_events
# ---------------------------------------------------------------------------


def test_handle_game_over_events_space_restarts_game(monkeypatch) -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(state=GameState.GAME_OVER, game_over_timer=0)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_SPACE)],
    )
    ScreenEventHandler(game).handle_game_over_events()
    assert game.state == GameState.PLAYING
    game.start_game.assert_called_once()


def test_handle_game_over_events_quit_stops_game(monkeypatch) -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(state=GameState.GAME_OVER, game_over_timer=0)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.QUIT)],
    )
    ScreenEventHandler(game).handle_game_over_events()
    assert game.running is False


def test_handle_game_over_events_increments_timer(monkeypatch) -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(state=GameState.GAME_OVER, game_over_timer=0)
    monkeypatch.setattr(pygame.event, "get", lambda: [])
    ScreenEventHandler(game).handle_game_over_events()
    assert game.game_over_timer == 1


def test_handle_game_over_events_timer_120_plays_sound(monkeypatch) -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(state=GameState.GAME_OVER, game_over_timer=119)
    monkeypatch.setattr(pygame.event, "get", lambda: [])
    ScreenEventHandler(game).handle_game_over_events()
    game.sound_manager.play_sound.assert_called_once_with("game_over2")


# ---------------------------------------------------------------------------
# handle_key_config_events
# ---------------------------------------------------------------------------


def test_handle_key_config_events_escape_goes_to_menu(monkeypatch) -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(state=GameState.MENU, binding_action=None, paused=False)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_ESCAPE)],
    )
    ScreenEventHandler(game).handle_key_config_events()
    assert game.state == GameState.MENU


def test_handle_key_config_events_quit_stops_game(monkeypatch) -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(binding_action=None)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.QUIT)],
    )
    ScreenEventHandler(game).handle_key_config_events()
    assert game.running is False


# ---------------------------------------------------------------------------
# handle_playing_state
# ---------------------------------------------------------------------------


def test_handle_playing_state_not_paused_calls_update_and_render() -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(paused=False, damage_flash_timer=2)
    ScreenEventHandler(game).handle_playing_state()

    game.handle_game_events.assert_called_once()
    game.update_game.assert_called_once()
    game.renderer.render_game.assert_called_once_with(game)
    assert game.damage_flash_timer == 1


def test_handle_playing_state_paused_skips_update() -> None:
    from games.Zombie_Survival.src.screen_event_handler import ScreenEventHandler

    game = _make_game(
        paused=True,
        heartbeat_timer=0,
        groan_timer=0,
        player_health=40,
        damage_flash_timer=2,
    )
    ScreenEventHandler(game).handle_playing_state()

    game.update_game.assert_not_called()
    assert game.heartbeat_timer == PAUSE_HEARTBEAT_DELAY
    assert game.groan_timer == GROAN_TIMER_DELAY
    game.sound_manager.play_sound.assert_any_call("heartbeat")
    game.sound_manager.play_sound.assert_any_call("groan")
