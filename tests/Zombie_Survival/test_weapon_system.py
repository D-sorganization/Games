"""Tests for Zombie Survival WeaponSystem."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from games.Zombie_Survival.src.weapon_system import WeaponSystem


def _make_player(weapon: str = "pistol") -> MagicMock:
    p = MagicMock()
    p.x = 5.0
    p.y = 5.0
    p.angle = 0.0
    p.current_weapon = weapon
    p.get_current_weapon_damage.return_value = 20
    return p


def _make_game(weapon: str = "pistol", player: object = "default") -> SimpleNamespace:
    if player == "default":
        player = _make_player(weapon)
    game = SimpleNamespace(
        player=player,
        player_x=5.0,
        player_y=5.0,
        player_angle=0.0,
        player_current_weapon=weapon,
        bots=[],
        damage_texts=[],
        show_damage=True,
        damage_flash_timer=0,
        raycaster=MagicMock(),
        combat_manager=MagicMock(),
        entity_manager=MagicMock(),
        particle_system=MagicMock(),
        sound_manager=MagicMock(),
        event_bus=MagicMock(),
    )
    game.combat_manager.check_shot_hit.return_value = []
    game.combat_manager.handle_bomb_explosion.return_value = []
    game.combat_manager.explode_laser.return_value = []
    game.combat_manager.explode_generic.return_value = 2

    def sync_combat_state() -> None:
        pass

    game.sync_combat_state = sync_combat_state
    return game


# ---------------------------------------------------------------------------
# fire_weapon — DbC
# ---------------------------------------------------------------------------


def test_fire_weapon_no_player_raises() -> None:
    game = _make_game(player=None)
    ws = WeaponSystem(game)
    with pytest.raises(ValueError, match="DbC"):
        ws.fire_weapon()


# ---------------------------------------------------------------------------
# fire_weapon — hitscan (pistol/rifle)
# ---------------------------------------------------------------------------


def test_fire_weapon_pistol_calls_check_shot_hit() -> None:
    game = _make_game("pistol")
    ws = WeaponSystem(game)
    ws.fire_weapon()
    game.combat_manager.check_shot_hit.assert_called_once()


def test_fire_weapon_rifle_calls_check_shot_hit() -> None:
    game = _make_game("rifle")
    ws = WeaponSystem(game)
    ws.fire_weapon()
    game.combat_manager.check_shot_hit.assert_called_once()


# ---------------------------------------------------------------------------
# fire_weapon — spread (shotgun)
# ---------------------------------------------------------------------------


def test_fire_weapon_shotgun_fires_multiple_pellets() -> None:
    game = _make_game("shotgun")
    ws = WeaponSystem(game)
    ws.fire_weapon()
    assert game.combat_manager.check_shot_hit.call_count > 1


# ---------------------------------------------------------------------------
# fire_weapon — beam (laser)
# ---------------------------------------------------------------------------


def test_fire_weapon_laser_calls_check_shot_hit_is_laser() -> None:
    game = _make_game("laser")
    ws = WeaponSystem(game)
    ws.fire_weapon()
    call_kwargs = game.combat_manager.check_shot_hit.call_args
    req = call_kwargs.args[0]
    assert req.is_laser is True


# ---------------------------------------------------------------------------
# fire_weapon — projectile (plasma/rocket)
# ---------------------------------------------------------------------------


def test_fire_weapon_plasma_adds_projectile() -> None:
    game = _make_game("plasma")
    ws = WeaponSystem(game)
    ws.fire_weapon()
    game.entity_manager.add_projectile.assert_called_once()


def test_fire_weapon_rocket_adds_projectile() -> None:
    game = _make_game("rocket")
    ws = WeaponSystem(game)
    ws.fire_weapon()
    game.entity_manager.add_projectile.assert_called_once()


# ---------------------------------------------------------------------------
# fire_weapon — burst (minigun)
# ---------------------------------------------------------------------------


def test_fire_weapon_minigun_adds_multiple_projectiles() -> None:
    game = _make_game("minigun")
    ws = WeaponSystem(game)
    ws.fire_weapon()
    assert game.entity_manager.add_projectile.call_count > 1


# ---------------------------------------------------------------------------
# fire_weapon — secondary
# ---------------------------------------------------------------------------


def test_fire_weapon_secondary_skips_fire_mode_dispatch() -> None:
    game = _make_game("pistol")
    ws = WeaponSystem(game)
    ws.fire_weapon(is_secondary=True)
    req = game.combat_manager.check_shot_hit.call_args.args[0]
    assert req.is_secondary is True


# ---------------------------------------------------------------------------
# handle_bomb_explosion
# ---------------------------------------------------------------------------


def test_handle_bomb_explosion_no_player_raises() -> None:
    game = _make_game(player=None)
    ws = WeaponSystem(game)
    with pytest.raises(ValueError, match="DbC"):
        ws.handle_bomb_explosion()


def test_handle_bomb_explosion_delegates_to_combat_manager() -> None:
    game = _make_game("pistol")
    ws = WeaponSystem(game)
    ws.handle_bomb_explosion()
    game.combat_manager.handle_bomb_explosion.assert_called_once()


# ---------------------------------------------------------------------------
# explode_laser
# ---------------------------------------------------------------------------


def test_explode_laser_delegates_to_combat_manager() -> None:
    game = _make_game()
    ws = WeaponSystem(game)
    ws.explode_laser(3.0, 4.0)
    game.combat_manager.explode_laser.assert_called_once_with(3.0, 4.0, [])


# ---------------------------------------------------------------------------
# explode_plasma / explode_rocket
# ---------------------------------------------------------------------------


def test_explode_plasma_no_player_raises() -> None:
    from games.Zombie_Survival.src.projectile import Projectile

    game = _make_game(player=None)
    ws = WeaponSystem(game)
    proj = MagicMock(spec=Projectile)
    with pytest.raises(ValueError, match="DbC"):
        ws.explode_plasma(proj)


def test_explode_rocket_no_player_raises() -> None:
    from games.Zombie_Survival.src.projectile import Projectile

    game = _make_game(player=None)
    ws = WeaponSystem(game)
    proj = MagicMock(spec=Projectile)
    with pytest.raises(ValueError, match="DbC"):
        ws.explode_rocket(proj)


def test_explode_plasma_calls_explode_generic() -> None:
    from games.Zombie_Survival.src.projectile import Projectile

    game = _make_game()
    ws = WeaponSystem(game)
    proj = MagicMock(spec=Projectile)
    ws.explode_plasma(proj)
    game.combat_manager.explode_generic.assert_called_once()


def test_explode_rocket_calls_explode_generic() -> None:
    from games.Zombie_Survival.src.projectile import Projectile

    game = _make_game()
    ws = WeaponSystem(game)
    proj = MagicMock(spec=Projectile)
    ws.explode_rocket(proj)
    game.combat_manager.explode_generic.assert_called_once()
