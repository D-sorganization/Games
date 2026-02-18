"""Tests for FPSGameBase shared methods."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from games.shared.fps_game_base import FPSGameBase


def _make_constants():
    """Create a minimal constants module for testing."""
    return SimpleNamespace(
        SCREEN_WIDTH=800,
        SCREEN_HEIGHT=600,
        WHITE=(255, 255, 255),
        RED=(255, 0, 0),
        GREEN=(0, 255, 0),
        YELLOW=(255, 255, 0),
        CYAN=(0, 255, 255),
        SPAWN_SAFETY_MARGIN=5,
        DEFAULT_PLAYER_SPAWN=(5.5, 5.5, 0.0),
    )


def _make_game():
    """Create an FPSGameBase instance with minimal state for testing."""
    game = FPSGameBase()
    game.C = _make_constants()
    game.render_scale = 2
    game.raycaster = None
    game.damage_texts = []
    game.unlocked_weapons = {"pistol", "rifle"}
    game.player = None
    game.game_map = None
    game.selected_map_size = 40
    game.portal = None
    game.last_death_pos = None
    game.entity_manager = MagicMock()
    game.entity_manager.bots = []
    game.entity_manager.projectiles = []
    return game


class TestProperties:
    def test_bots_property(self):
        game = _make_game()
        game.entity_manager.bots = ["bot1", "bot2"]
        assert game.bots == ["bot1", "bot2"]

    def test_projectiles_property(self):
        game = _make_game()
        game.entity_manager.projectiles = ["proj1"]
        assert game.projectiles == ["proj1"]


class TestAddMessage:
    def test_adds_damage_text(self):
        game = _make_game()
        game.add_message("TEST", (255, 0, 0))
        assert len(game.damage_texts) == 1
        msg = game.damage_texts[0]
        assert msg["text"] == "TEST"
        assert msg["color"] == (255, 0, 0)
        assert msg["timer"] == 60

    def test_position_is_centered(self):
        game = _make_game()
        game.add_message("HI", (0, 0, 0))
        msg = game.damage_texts[0]
        assert msg["x"] == 400  # 800 // 2
        assert msg["y"] == 250  # 600 // 2 - 50


class TestCycleRenderScale:
    def test_cycles_through_scales(self):
        game = _make_game()
        game.render_scale = 2
        game.cycle_render_scale()
        assert game.render_scale == 4

    def test_wraps_around(self):
        game = _make_game()
        game.render_scale = 8
        game.cycle_render_scale()
        assert game.render_scale == 1

    def test_invalid_scale_resets_to_2(self):
        game = _make_game()
        game.render_scale = 99
        game.cycle_render_scale()
        assert game.render_scale == 2

    def test_updates_raycaster(self):
        game = _make_game()
        game.raycaster = MagicMock()
        game.render_scale = 1
        game.cycle_render_scale()
        game.raycaster.set_render_scale.assert_called_once_with(2)

    def test_adds_quality_message(self):
        game = _make_game()
        game.render_scale = 1
        game.cycle_render_scale()
        assert any("QUALITY" in t["text"] for t in game.damage_texts)


class TestSwitchWeaponWithMessage:
    def test_switch_unlocked_weapon(self):
        game = _make_game()
        game.player = MagicMock()
        game.player.current_weapon = "pistol"
        game.switch_weapon_with_message("rifle")
        game.player.switch_weapon.assert_called_once_with("rifle")

    def test_switch_locked_weapon_shows_locked(self):
        game = _make_game()
        game.player = MagicMock()
        game.switch_weapon_with_message("plasma")
        game.player.switch_weapon.assert_not_called()
        assert any("LOCKED" in t["text"] for t in game.damage_texts)

    def test_switch_same_weapon_no_op(self):
        game = _make_game()
        game.player = MagicMock()
        game.player.current_weapon = "pistol"
        game.switch_weapon_with_message("pistol")
        game.player.switch_weapon.assert_not_called()


class TestSpawnPortal:
    def test_uses_last_death_pos(self):
        game = _make_game()
        game.last_death_pos = (10.0, 20.0)
        game.spawn_portal()
        assert game.portal == {"x": 10.0, "y": 20.0}

    def test_fallback_near_player(self):
        game = _make_game()
        game.player = MagicMock()
        game.player.x = 5.0
        game.player.y = 5.0
        mock_map = MagicMock()
        mock_map.is_wall.return_value = False
        game.game_map = mock_map
        game.spawn_portal()
        assert game.portal is not None
        assert "x" in game.portal
        assert "y" in game.portal


class TestFindSafeSpawn:
    def test_returns_base_when_no_map(self):
        game = _make_game()
        result = game.find_safe_spawn(10.0, 20.0, 1.5)
        assert result == (10.0, 20.0, 1.5)

    def test_finds_non_wall_position(self):
        game = _make_game()
        mock_map = MagicMock()
        mock_map.size = 40
        mock_map.is_wall.return_value = False
        game.game_map = mock_map
        result = game.find_safe_spawn(20.0, 20.0, 0.0)
        assert result == (20.0, 20.0, 0.0)  # First attempt succeeds

    def test_expands_search_radius(self):
        game = _make_game()
        mock_map = MagicMock()
        mock_map.size = 40
        call_count = [0]

        def is_wall(x, y):
            call_count[0] += 1
            return call_count[0] < 10  # First 9 are walls

        mock_map.is_wall.side_effect = is_wall
        game.game_map = mock_map
        result = game.find_safe_spawn(20.0, 20.0, 0.0)
        assert len(result) == 3  # Returns a valid tuple


class TestGetBestSpawnPoint:
    def test_fallback_when_no_map(self):
        game = _make_game()
        result = game._get_best_spawn_point()
        assert result == (5.5, 5.5, 0.0)

    def test_uses_corner_positions(self):
        game = _make_game()
        mock_map = MagicMock()
        mock_map.size = 40
        mock_map.height = 40
        mock_map.width = 40
        mock_map.is_wall.return_value = False
        game.game_map = mock_map
        result = game._get_best_spawn_point()
        assert len(result) == 3


class TestRespawnPlayer:
    def test_resets_player_state(self):
        game = _make_game()
        mock_map = MagicMock()
        mock_map.size = 40
        mock_map.height = 40
        mock_map.width = 40
        mock_map.is_wall.return_value = False
        game.game_map = mock_map
        game.player = MagicMock()
        game.player.alive = False
        game.player.health = 0
        game.respawn_player()
        assert game.player.alive is True
        assert game.player.health == 100
        assert game.player.shield_active is False

    def test_shows_respawned_message(self):
        game = _make_game()
        mock_map = MagicMock()
        mock_map.size = 40
        mock_map.height = 40
        mock_map.width = 40
        mock_map.is_wall.return_value = False
        game.game_map = mock_map
        game.player = MagicMock()
        game.respawn_player()
        assert any("RESPAWNED" in t["text"] for t in game.damage_texts)
