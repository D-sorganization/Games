"""Focused tests for the extracted Duum screen-event handler."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pygame

from games.shared.constants import GROAN_TIMER_DELAY, PAUSE_HEARTBEAT_DELAY, GameState


def _screen_game(**overrides: object) -> SimpleNamespace:
    base = {
        "running": True,
        "state": GameState.INTRO,
        "intro_phase": 1,
        "intro_step": 0,
        "intro_start_time": 500,
        "laugh_played": False,
        "water_played": False,
        "paused": False,
        "heartbeat_timer": 0,
        "groan_timer": 0,
        "damage_flash_timer": 2,
        "flash_intensity": 0.75,
        "player": SimpleNamespace(health=40),
        "sound_manager": MagicMock(),
        "ui_renderer": MagicMock(),
        "renderer": MagicMock(),
        "handle_game_events": MagicMock(),
        "update_game": MagicMock(),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_handle_intro_events_space_transitions_to_menu(monkeypatch) -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(state=GameState.INTRO)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_SPACE)],
    )

    ScreenEventHandler(game).handle_intro_events()

    assert game.state == GameState.MENU


def test_update_intro_logic_releases_video_on_phase_transition() -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(state=GameState.INTRO, intro_phase=1, intro_start_time=500)

    ScreenEventHandler(game).update_intro_logic(elapsed=3100)

    assert game.intro_phase == 2
    assert game.intro_start_time == 0
    game.ui_renderer.release_intro_video.assert_called_once_with()


def test_handle_playing_state_updates_game_and_decays_flash() -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(state=GameState.PLAYING, paused=False, damage_flash_timer=2)

    ScreenEventHandler(game).handle_playing_state()

    game.handle_game_events.assert_called_once_with()
    game.update_game.assert_called_once_with()
    game.renderer.render_game.assert_called_once_with(game, 0.75)
    assert game.damage_flash_timer == 1


def test_handle_playing_state_paused_runs_pause_audio_without_update() -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(
        state=GameState.PLAYING,
        paused=True,
        heartbeat_timer=0,
        groan_timer=0,
        damage_flash_timer=2,
        player=SimpleNamespace(health=40),
    )

    ScreenEventHandler(game).handle_playing_state()

    game.update_game.assert_not_called()
    game.renderer.render_game.assert_called_once_with(game, 0.75)
    assert game.heartbeat_timer == PAUSE_HEARTBEAT_DELAY
    assert game.groan_timer == GROAN_TIMER_DELAY
    game.sound_manager.play_sound.assert_has_calls(
        [call("heartbeat"), call("breath"), call("groan")]
    )


def test_handle_intro_events_quit_sets_running_false(monkeypatch) -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(state=GameState.INTRO)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.QUIT)],
    )

    ScreenEventHandler(game).handle_intro_events()

    assert game.running is False


def test_handle_menu_events_escape_sets_running_false(monkeypatch) -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(state=GameState.MENU)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_ESCAPE)],
    )

    ScreenEventHandler(game).handle_menu_events()

    assert game.running is False


def test_handle_menu_events_quit_sets_running_false(monkeypatch) -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(state=GameState.MENU)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.QUIT)],
    )

    ScreenEventHandler(game).handle_menu_events()

    assert game.running is False


def test_handle_key_config_events_escape_goes_to_menu(monkeypatch) -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(state=GameState.PLAYING)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_ESCAPE)],
    )

    ScreenEventHandler(game).handle_key_config_events()

    assert game.state == GameState.MENU


def test_handle_key_config_events_quit_stops_game(monkeypatch) -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(state=GameState.PLAYING)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.QUIT)],
    )

    ScreenEventHandler(game).handle_key_config_events()

    assert game.running is False


def test_handle_map_select_events_escape_goes_to_menu(monkeypatch) -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(state=GameState.MAP_SELECT)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_ESCAPE)],
    )

    ScreenEventHandler(game).handle_map_select_events()

    assert game.state == GameState.MENU


def test_handle_map_select_events_quit_stops_game(monkeypatch) -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(state=GameState.MAP_SELECT)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.QUIT)],
    )

    ScreenEventHandler(game).handle_map_select_events()

    assert game.running is False


def test_handle_level_complete_events_space_goes_to_menu(monkeypatch) -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(state=GameState.LEVEL_COMPLETE)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_SPACE)],
    )

    ScreenEventHandler(game).handle_level_complete_events()

    assert game.state == GameState.MENU


def test_handle_level_complete_events_quit_stops_game(monkeypatch) -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(state=GameState.LEVEL_COMPLETE)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.QUIT)],
    )

    ScreenEventHandler(game).handle_level_complete_events()

    assert game.running is False


def test_handle_game_over_events_space_goes_to_menu(monkeypatch) -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(state=GameState.GAME_OVER)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_SPACE)],
    )

    ScreenEventHandler(game).handle_game_over_events()

    assert game.state == GameState.MENU


def test_handle_game_over_events_quit_stops_game(monkeypatch) -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(state=GameState.GAME_OVER)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [SimpleNamespace(type=pygame.QUIT)],
    )

    ScreenEventHandler(game).handle_game_over_events()

    assert game.running is False


def test_update_intro_logic_phase2_past_slides_goes_to_menu() -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(intro_phase=2, intro_step=10, intro_start_time=0)

    ScreenEventHandler(game).update_intro_logic(elapsed=100)

    assert game.state == GameState.MENU


def test_update_intro_logic_phase2_plays_laugh_on_first_slide() -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(
        intro_phase=2, intro_step=0, intro_start_time=500, laugh_played=False
    )

    ScreenEventHandler(game).update_intro_logic(elapsed=10)

    game.sound_manager.play_sound.assert_called_once_with("laugh")
    assert game.laugh_played is True


def test_update_intro_logic_phase1_plays_water_sound() -> None:
    from games.Duum.src.screen_event_handler import ScreenEventHandler

    game = _screen_game(
        intro_phase=1, intro_step=0, intro_start_time=500, water_played=False
    )

    ScreenEventHandler(game).update_intro_logic(elapsed=10)

    game.sound_manager.play_sound.assert_called_once_with("water")
    assert game.water_played is True
