"""Focused tests for the extracted Duum gameplay updater."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pygame


class _PressedKeys:
    """Tiny indexable key-state stub for pygame-style lookups."""

    def __init__(self, pressed: set[int] | None = None) -> None:
        self._pressed = pressed or set()

    def __getitem__(self, key: int) -> bool:
        return key in self._pressed


def test_update_damage_texts_ticks_and_filters_expired() -> None:
    """Damage text updates should move entries and prune expired rows."""
    from games.Duum.src import gameplay_updater

    game = SimpleNamespace(
        damage_texts=[
            {"y": 20, "vy": -1, "timer": 2},
            {"y": 10, "vy": 1, "timer": 1},
        ]
    )

    gameplay_updater.update_damage_texts(game)

    assert game.damage_texts == [{"y": 19, "vy": -1, "timer": 1}]


def test_handle_keyboard_movement_applies_forward_motion_and_turn() -> None:
    """Keyboard movement should drive the player and set movement state."""
    from games.Duum.src import gameplay_updater

    player = SimpleNamespace(
        stamina=10,
        stamina_recharge_delay=0,
        is_moving=False,
        move=MagicMock(),
        strafe=MagicMock(),
        rotate=MagicMock(),
        pitch_view=MagicMock(),
    )
    actions = {"move_forward", "turn_left"}
    game = SimpleNamespace(
        player=player,
        game_map=object(),
        bots=[],
        input_manager=SimpleNamespace(
            is_action_pressed=lambda action: action in actions
        ),
    )

    gameplay_updater.handle_keyboard_movement(game, _PressedKeys())

    player.move.assert_called_once()
    player.rotate.assert_called_once_with(-0.05)
    assert player.is_moving is True


def test_check_item_pickups_unlocks_weapon_and_announces() -> None:
    """Weapon pickups should unlock the weapon and append a screen message."""
    from games.Duum.src import gameplay_updater

    player = SimpleNamespace(
        x=5.0,
        y=5.0,
        health=100,
        bombs=0,
        ammo={"pistol": 5},
        switch_weapon=MagicMock(),
    )
    bot = SimpleNamespace(
        x=5.0,
        y=5.0,
        enemy_type="pickup_shotgun",
        alive=True,
        removed=False,
    )
    game = SimpleNamespace(
        player=player,
        bots=[bot],
        unlocked_weapons={"pistol"},
        damage_texts=[],
    )

    gameplay_updater.check_item_pickups(game)

    player.switch_weapon.assert_called_once_with("shotgun")
    assert "shotgun" in game.unlocked_weapons
    assert bot.alive is False
    assert bot.removed is True
    assert game.damage_texts[0]["text"] == "SHOTGUN ACQUIRED!"


def test_update_game_delegates_live_frame_components(monkeypatch) -> None:
    """Gameplay updates should run the extracted subsystems in order."""
    from games.Duum.src import gameplay_updater

    keys = _PressedKeys()
    update_damage_texts = MagicMock()
    handle_keyboard_movement = MagicMock()
    check_item_pickups = MagicMock()
    monkeypatch.setattr(gameplay_updater, "update_damage_texts", update_damage_texts)
    monkeypatch.setattr(
        gameplay_updater,
        "handle_keyboard_movement",
        handle_keyboard_movement,
    )
    monkeypatch.setattr(gameplay_updater, "check_item_pickups", check_item_pickups)
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: keys)

    player = SimpleNamespace(alive=True, set_shield=MagicMock(), update=MagicMock())
    particle_system = SimpleNamespace(update=MagicMock())
    entity_manager = SimpleNamespace(
        update_bots=MagicMock(),
        update_projectiles=MagicMock(),
    )
    atmosphere_manager = SimpleNamespace(
        update_fog_reveal=MagicMock(),
        update_atmosphere=MagicMock(),
        check_kill_combo=MagicMock(),
    )
    game = SimpleNamespace(
        paused=False,
        player=player,
        game_map=object(),
        input_manager=SimpleNamespace(
            is_action_pressed=lambda action: action == "shield"
        ),
        joystick=None,
        particle_system=particle_system,
        entity_manager=entity_manager,
        atmosphere_manager=atmosphere_manager,
        flash_intensity=0.3,
        _check_game_over=MagicMock(return_value=False),
        _check_portal_completion=MagicMock(return_value=False),
        bots=[],
    )

    gameplay_updater.update_game(game)

    player.set_shield.assert_called_once_with(True)
    particle_system.update.assert_called_once_with()
    update_damage_texts.assert_called_once_with(game)
    handle_keyboard_movement.assert_called_once_with(game, keys)
    player.update.assert_called_once_with()
    entity_manager.update_bots.assert_called_once_with(game.game_map, player, game)
    check_item_pickups.assert_called_once_with(game)
    entity_manager.update_projectiles.assert_called_once_with(
        game.game_map,
        player,
        game,
    )
    atmosphere_manager.update_fog_reveal.assert_called_once_with()
    atmosphere_manager.update_atmosphere.assert_called_once_with()
    atmosphere_manager.check_kill_combo.assert_called_once_with()
    assert game.flash_intensity == 0.19999999999999998
