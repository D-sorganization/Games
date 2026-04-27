"""Tests for Zombie Survival Game delegation and LOD properties.

Tests the delegation wiring (Game methods delegate to subsystem objects)
and the flattened LOD properties without requiring full game initialization.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from games.Zombie_Survival.src.game import Game
from games.Zombie_Survival.src.projectile import Projectile


def _make_bare_game() -> Game:
    """Create a Game instance without calling __init__ (no pygame required)."""
    game = Game.__new__(Game)
    game.weapon_system = MagicMock()
    game.screen_event_handler = MagicMock()
    game.atmosphere_manager = MagicMock()
    game.player = MagicMock()
    game.player.x = 1.5
    game.player.y = 2.5
    game.player.angle = 0.7
    game.player.health = 85
    game.player.alive = True
    game.player.is_moving = False
    game.player.current_weapon = "rifle"
    game.player.stamina = 0.75
    game.player.bombs = 2
    return game


# ---------------------------------------------------------------------------
# LOD properties — player present
# ---------------------------------------------------------------------------


def test_player_x_returns_player_x() -> None:
    game = _make_bare_game()
    assert game.player_x == 1.5


def test_player_y_returns_player_y() -> None:
    game = _make_bare_game()
    assert game.player_y == 2.5


def test_player_angle_returns_player_angle() -> None:
    game = _make_bare_game()
    assert game.player_angle == 0.7


def test_player_health_returns_player_health() -> None:
    game = _make_bare_game()
    assert game.player_health == 85


def test_player_health_setter_updates_player() -> None:
    game = _make_bare_game()
    game.player_health = 50
    assert game.player.health == 50


def test_player_alive_returns_player_alive() -> None:
    game = _make_bare_game()
    assert game.player_alive is True


def test_player_is_moving_returns_is_moving() -> None:
    game = _make_bare_game()
    assert game.player_is_moving is False


def test_player_is_moving_setter_updates_player() -> None:
    game = _make_bare_game()
    game.player_is_moving = True
    assert game.player.is_moving is True


def test_player_current_weapon_returns_weapon() -> None:
    game = _make_bare_game()
    assert game.player_current_weapon == "rifle"


def test_player_current_weapon_setter_updates_player() -> None:
    game = _make_bare_game()
    game.player_current_weapon = "shotgun"
    assert game.player.current_weapon == "shotgun"


def test_player_stamina_returns_stamina() -> None:
    game = _make_bare_game()
    assert game.player_stamina == 0.75


def test_player_stamina_setter_updates_player() -> None:
    game = _make_bare_game()
    game.player_stamina = 0.5
    assert game.player.stamina == 0.5


def test_player_bombs_returns_bombs() -> None:
    game = _make_bare_game()
    assert game.player_bombs == 2


def test_player_bombs_setter_updates_player() -> None:
    game = _make_bare_game()
    game.player_bombs = 5
    assert game.player.bombs == 5


# ---------------------------------------------------------------------------
# LOD properties — player absent (returns defaults)
# ---------------------------------------------------------------------------


def test_player_x_no_player_returns_zero() -> None:
    game = _make_bare_game()
    game.player = None
    assert game.player_x == 0.0


def test_player_y_no_player_returns_zero() -> None:
    game = _make_bare_game()
    game.player = None
    assert game.player_y == 0.0


def test_player_angle_no_player_returns_zero() -> None:
    game = _make_bare_game()
    game.player = None
    assert game.player_angle == 0.0


def test_player_health_no_player_returns_zero() -> None:
    game = _make_bare_game()
    game.player = None
    assert game.player_health == 0


def test_player_health_setter_no_player_is_noop() -> None:
    game = _make_bare_game()
    game.player = None
    game.player_health = 50  # should not raise


def test_player_alive_no_player_returns_false() -> None:
    game = _make_bare_game()
    game.player = None
    assert game.player_alive is False


def test_player_current_weapon_no_player_returns_pistol() -> None:
    game = _make_bare_game()
    game.player = None
    assert game.player_current_weapon == "pistol"


# ---------------------------------------------------------------------------
# Weapon delegation methods
# ---------------------------------------------------------------------------


def test_fire_weapon_delegates_to_weapon_system() -> None:
    game = _make_bare_game()
    game.fire_weapon(is_secondary=True)
    game.weapon_system.fire_weapon.assert_called_once_with(is_secondary=True)


def test_check_shot_hit_delegates_to_weapon_system() -> None:
    game = _make_bare_game()
    game.check_shot_hit(is_secondary=False, angle_offset=0.2, is_laser=True)
    game.weapon_system.check_shot_hit.assert_called_once_with(
        is_secondary=False, angle_offset=0.2, is_laser=True
    )


def test_handle_bomb_explosion_delegates_to_weapon_system() -> None:
    game = _make_bare_game()
    game.handle_bomb_explosion()
    game.weapon_system.handle_bomb_explosion.assert_called_once_with()


def test_explode_laser_delegates_to_weapon_system() -> None:
    game = _make_bare_game()
    game.explode_laser(3.0, 4.0)
    game.weapon_system.explode_laser.assert_called_once_with(3.0, 4.0)


def test_explode_plasma_delegates_to_weapon_system() -> None:
    game = _make_bare_game()
    projectile = MagicMock(spec=Projectile)
    game.explode_plasma(projectile)
    game.weapon_system.explode_plasma.assert_called_once_with(projectile)


def test_explode_rocket_delegates_to_weapon_system() -> None:
    game = _make_bare_game()
    projectile = MagicMock(spec=Projectile)
    game.explode_rocket(projectile)
    game.weapon_system.explode_rocket.assert_called_once_with(projectile)


# ---------------------------------------------------------------------------
# Screen event handler delegation
# ---------------------------------------------------------------------------


def test_handle_intro_events_delegates() -> None:
    game = _make_bare_game()
    game.handle_intro_events()
    game.screen_event_handler.handle_intro_events.assert_called_once_with()


def test_handle_menu_events_delegates() -> None:
    game = _make_bare_game()
    game.handle_menu_events()
    game.screen_event_handler.handle_menu_events.assert_called_once_with()


def test_handle_map_select_events_delegates() -> None:
    game = _make_bare_game()
    game.handle_map_select_events()
    game.screen_event_handler.handle_map_select_events.assert_called_once_with()


def test_handle_level_complete_events_delegates() -> None:
    game = _make_bare_game()
    game.handle_level_complete_events()
    game.screen_event_handler.handle_level_complete_events.assert_called_once_with()


def test_handle_game_over_events_delegates() -> None:
    game = _make_bare_game()
    game.handle_game_over_events()
    game.screen_event_handler.handle_game_over_events.assert_called_once_with()


def test_handle_key_config_events_delegates() -> None:
    game = _make_bare_game()
    game.handle_key_config_events()
    game.screen_event_handler.handle_key_config_events.assert_called_once_with()


def test_update_intro_logic_delegates() -> None:
    game = _make_bare_game()
    game._update_intro_logic(elapsed=500)
    game.screen_event_handler.update_intro_logic.assert_called_once_with(500)
