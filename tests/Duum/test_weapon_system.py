"""Focused tests for the extracted Duum weapon system."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from games.Duum.src.game import Game
from games.Duum.src.projectile import Projectile
from games.Duum.src.weapon_system import WeaponSystem
from games.shared.constants import MINIGUN_BULLETS_PER_SHOT


def _make_game(weapon_name: str = "pistol") -> MagicMock:
    """Build a lightweight Duum game stub for weapon-system tests."""
    game = MagicMock()
    player = MagicMock()
    player.x = 5.0
    player.y = 7.0
    player.angle = 0.25
    player.current_weapon = weapon_name
    player.get_current_weapon_damage.return_value = 25

    game.player = player
    game.bots = []
    game.damage_texts = []
    game.damage_flash_timer = 0
    game.show_damage = False
    game.flash_intensity = 0.0
    game.raycaster = MagicMock()
    game.entity_manager = MagicMock()
    game.particle_system = MagicMock()
    game.combat_manager = MagicMock()
    game.sound_manager = MagicMock()
    game.sync_combat_state = MagicMock()
    return game


def test_fire_weapon_secondary_delegates_to_hitscan() -> None:
    game = _make_game("pistol")
    weapon_system = WeaponSystem(game)

    with patch.object(weapon_system, "check_shot_hit") as check_shot_hit:
        weapon_system.fire_weapon(is_secondary=True)

    game.sound_manager.play_sound.assert_called_once_with("shoot_pistol")
    check_shot_hit.assert_called_once_with(is_secondary=True)
    assert game.flash_intensity == 0.8


def test_fire_weapon_projectile_adds_projectile() -> None:
    game = _make_game("plasma")
    weapon_system = WeaponSystem(game)

    weapon_system.fire_weapon()

    game.entity_manager.add_projectile.assert_called_once()
    projectile = game.entity_manager.add_projectile.call_args.args[0]
    assert isinstance(projectile, Projectile)
    assert projectile.weapon_type == "plasma"


def test_fire_spread_calls_hitscan_for_each_pellet() -> None:
    from games.Duum.src import constants as C  # noqa: N812

    game = _make_game("shotgun")
    weapon_system = WeaponSystem(game)

    with patch.object(weapon_system, "check_shot_hit") as check_shot_hit:
        weapon_system._fire_spread(C.WEAPONS["shotgun"], "shotgun")

    assert check_shot_hit.call_count == int(C.WEAPONS["shotgun"].get("pellets", 8))


def test_fire_burst_adds_projectiles_and_muzzle_explosion() -> None:
    game = _make_game("minigun")
    weapon_system = WeaponSystem(game)

    weapon_system.fire_weapon()

    assert game.entity_manager.add_projectile.call_count == MINIGUN_BULLETS_PER_SHOT
    game.particle_system.add_explosion.assert_called_once()


def test_check_shot_hit_updates_damage_texts_and_syncs_state() -> None:
    game = _make_game("rifle")
    weapon_system = WeaponSystem(game)
    expected_texts = [{"text": "hit"}]
    game.combat_manager.check_shot_hit.return_value = expected_texts

    weapon_system.check_shot_hit(is_laser=True, angle_offset=0.1)

    request = game.combat_manager.check_shot_hit.call_args.args[0]
    assert request.player is game.player
    assert request.raycaster is game.raycaster
    assert request.is_laser is True
    assert request.angle_offset == 0.1
    assert game.damage_texts == expected_texts
    game.sync_combat_state.assert_called_once_with()


def test_handle_bomb_explosion_updates_damage_texts_and_syncs_state() -> None:
    game = _make_game()
    weapon_system = WeaponSystem(game)
    game.combat_manager.handle_bomb_explosion.return_value = [{"text": "boom"}]

    weapon_system.handle_bomb_explosion()

    assert game.damage_texts == [{"text": "boom"}]
    game.sync_combat_state.assert_called_once_with()


def test_explode_rocket_updates_flash_timer_and_syncs_state() -> None:
    game = _make_game("rocket")
    weapon_system = WeaponSystem(game)
    projectile = MagicMock(spec=Projectile)
    game.combat_manager.explode_generic.return_value = 9

    weapon_system.explode_rocket(projectile)

    assert game.damage_flash_timer == 9
    game.sync_combat_state.assert_called_once_with()


@pytest.mark.parametrize(
    ("method_name", "args", "kwargs"),
    [
        ("fire_weapon", (), {"is_secondary": True}),
        (
            "check_shot_hit",
            (),
            {"is_secondary": True, "angle_offset": 0.2, "is_laser": True},
        ),
        ("handle_bomb_explosion", (), {}),
        ("explode_laser", (1.0, 2.0), {}),
        ("explode_plasma", (MagicMock(spec=Projectile),), {}),
        ("explode_rocket", (MagicMock(spec=Projectile),), {}),
    ],
)
def test_game_weapon_methods_delegate_to_weapon_system(
    method_name: str,
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> None:
    game = Game.__new__(Game)
    game.weapon_system = MagicMock()

    getattr(Game, method_name)(game, *args, **kwargs)

    getattr(game.weapon_system, method_name).assert_called_once_with(*args, **kwargs)
