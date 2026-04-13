"""Focused tests for games.Force_Field.src.game_input."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pygame

from games.Force_Field.src import constants as C
from games.Force_Field.src.game_input import GameInputHandler


def _make_game() -> SimpleNamespace:
    player = MagicMock()
    player.ammo = {"pistol": 12, "rifle": 24}
    player.rotate = MagicMock()
    player.pitch_view = MagicMock()
    player.reload = MagicMock()
    player.dash = MagicMock()
    player.shoot.return_value = False
    player.fire_secondary.return_value = False
    player.melee_attack.return_value = False
    player.activate_bomb.return_value = False
    player.zoomed = False

    input_manager = MagicMock()
    input_manager.is_action_just_pressed.side_effect = lambda event, action: (
        action
        in {
            "pause",
            "reload",
        }
    )

    game = SimpleNamespace(
        running=True,
        player=player,
        paused=False,
        cheat_mode_active=False,
        current_cheat_input="",
        unlocked_weapons={"pistol"},
        god_mode=False,
        dragging_speed_slider=False,
        pause_start_time=0,
        total_paused_time=0,
        movement_speed_multiplier=1.0,
        show_minimap=True,
        state="game",
        binding_action="move_forward",
        add_message=MagicMock(),
        switch_weapon_with_message=MagicMock(),
        execute_melee_attack=MagicMock(),
        save_game=MagicMock(),
        cycle_render_scale=MagicMock(),
        combat_system=SimpleNamespace(fire_weapon=MagicMock()),
        entity_manager=SimpleNamespace(add_projectile=MagicMock()),
        input_manager=input_manager,
        sound_manager=SimpleNamespace(
            pause_all=MagicMock(),
            unpause_all=MagicMock(),
            start_music=MagicMock(),
        ),
        ui_renderer=SimpleNamespace(
            render_subtitle_text=MagicMock(
                side_effect=lambda item, *_args, **_kwargs: MagicMock(
                    get_width=lambda: len(item) * 10
                )
            )
        ),
    )
    return game


def _event(**kwargs):
    return SimpleNamespace(**kwargs)


def test_handle_game_events_toggles_pause_and_resume(monkeypatch) -> None:
    """Pause input should lock, then restore, the game state."""
    game = _make_game()
    handler = GameInputHandler(game)
    event = _event(type=pygame.KEYDOWN, key=pygame.K_p, unicode="p")
    batches = [[event], [event]]
    ticks = iter([1000, 1500])
    monkeypatch.setattr(pygame.event, "get", lambda: batches.pop(0))
    monkeypatch.setattr(
        pygame.time,
        "get_ticks",
        lambda: next(ticks),
    )
    mouse_visible = MagicMock()
    event_grab = MagicMock()
    monkeypatch.setattr(pygame.mouse, "set_visible", mouse_visible)
    monkeypatch.setattr(pygame.event, "set_grab", event_grab)

    handler.handle_game_events()
    assert game.paused is True
    game.sound_manager.pause_all.assert_called_once_with()
    mouse_visible.assert_called_once_with(True)
    event_grab.assert_called_once_with(False)
    assert game.pause_start_time == 1000

    handler.handle_game_events()
    assert game.paused is False
    game.sound_manager.unpause_all.assert_called_once_with()
    assert game.total_paused_time == 500
    assert game.pause_start_time == 0
    assert event_grab.call_args_list[-1].args == (True,)


def test_handle_game_events_applies_cheat_code_unlock(monkeypatch) -> None:
    """Cheat input should unlock all weapons and refill ammo."""
    game = _make_game()
    game.cheat_mode_active = True
    handler = GameInputHandler(game)
    events = [
        _event(type=pygame.KEYDOWN, key=pygame.K_i, unicode="I"),
        _event(type=pygame.KEYDOWN, key=pygame.K_d, unicode="D"),
        _event(type=pygame.KEYDOWN, key=pygame.K_f, unicode="F"),
        _event(type=pygame.KEYDOWN, key=pygame.K_a, unicode="A"),
    ]
    monkeypatch.setattr(pygame.event, "get", lambda: events)

    handler.handle_game_events()

    assert game.unlocked_weapons == set(C.WEAPONS.keys())
    assert game.player.ammo == {"pistol": 999, "rifle": 999}
    assert game.current_cheat_input == ""
    assert game.cheat_mode_active is False
    game.add_message.assert_any_call("ALL WEAPONS UNLOCKED", C.YELLOW)
