import math
from unittest.mock import MagicMock

from games.shared.fps_game_base import FPSGameBase


class MockConstants:
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    GREEN = (0, 255, 0)
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    SPAWN_SAFETY_MARGIN = 2
    DEFAULT_PLAYER_SPAWN = (5.0, 5.0, 0.0)


class MockGame(FPSGameBase):
    def __init__(self):
        self.C = MockConstants()
        self.render_scale = 1
        self.raycaster = MagicMock()
        self.damage_texts = []
        self.unlocked_weapons = {"pistol", "shotgun"}
        self.player = MagicMock()
        self.game_map = MagicMock()
        self.selected_map_size = 20
        self.portal = None
        self.last_death_pos = None
        self.entity_manager = MagicMock()


class TestFPSGameBase:
    def test_properties(self) -> None:
        """Test bots and projectiles properties."""
        game = MockGame()
        game.entity_manager.bots = ["bot1"]
        game.entity_manager.projectiles = ["proj1"]

        assert game.bots == ["bot1"]
        assert game.projectiles == ["proj1"]

    def test_cycle_render_scale(self) -> None:
        """Test cycling through render scales."""
        game = MockGame()

        # 1 -> 2
        game.cycle_render_scale()
        assert game.render_scale == 2
        game.raycaster.set_render_scale.assert_called_with(2)
        assert any("HIGH" in t["text"] for t in game.damage_texts)

        # 2 -> 4
        game.cycle_render_scale()
        assert game.render_scale == 4
        assert any("MEDIUM" in t["text"] for t in game.damage_texts)

        # 4 -> 8
        game.cycle_render_scale()
        assert game.render_scale == 8
        assert any("LOW" in t["text"] for t in game.damage_texts)

        # 8 -> 1
        game.cycle_render_scale()
        assert game.render_scale == 1
        assert any("ULTRA" in t["text"] for t in game.damage_texts)

        # Invalid -> 2
        game.render_scale = 99
        game.cycle_render_scale()
        assert game.render_scale == 2
        assert any("HIGH" in t["text"] for t in game.damage_texts)

        # Raycaster is None
        game.raycaster = None
        game.cycle_render_scale()
        assert game.render_scale == 4

    def test_add_message(self) -> None:
        """Test adding a temporary message."""
        game = MockGame()
        game.add_message("HELLO", MockConstants.RED)
        assert len(game.damage_texts) == 1
        msg = game.damage_texts[0]
        assert msg["text"] == "HELLO"
        assert msg["color"] == MockConstants.RED
        assert msg["x"] == MockConstants.SCREEN_WIDTH // 2
        assert msg["y"] == MockConstants.SCREEN_HEIGHT // 2 - 50

    def test_switch_weapon_with_message(self) -> None:
        """Test switching weapons and messaging."""
        game = MockGame()
        game.player.current_weapon = "pistol"

        # Switch to locked
        game.switch_weapon_with_message("plasma")
        assert any("LOCKED" in t["text"] for t in game.damage_texts)
        game.player.switch_weapon.assert_not_called()
        game.damage_texts.clear()

        # Switch to unlocked (already equipped)
        game.switch_weapon_with_message("pistol")
        game.player.switch_weapon.assert_not_called()
        assert not game.damage_texts

        # Switch to unlocked (new)
        game.switch_weapon_with_message("shotgun")
        game.player.switch_weapon.assert_called_with("shotgun")
        assert any("SHOTGUN" in t["text"] for t in game.damage_texts)

    def test_spawn_portal(self) -> None:
        """Test spawning a portal."""
        game = MockGame()

        # Spawn at last death
        game.last_death_pos = (10.0, 15.0)
        game.spawn_portal()
        assert game.portal == {"x": 10.0, "y": 15.0}

        # Spawn near player (first fails, then finds)
        game.last_death_pos = None
        game.game_map.is_wall.side_effect = lambda tx, ty: tx < 22 or ty < 22
        game.player.x = 20.0
        game.player.y = 20.0
        game.spawn_portal()
        # Should search and eventually find something where tx>=22 or ty>=22
        assert game.portal is not None
        assert game.portal["x"] > 0
        assert game.portal["y"] > 0

        # Spawn near player but no spots available (map closed)
        game.portal = None
        game.game_map.is_wall.side_effect = lambda tx, ty: True
        game.spawn_portal()
        assert game.portal is None

        # No map
        game.portal = None
        game.game_map = None
        game.spawn_portal()
        assert game.portal is None

    def test_find_safe_spawn(self) -> None:
        """Test finding a safe spawn point."""
        game = MockGame()

        # No map
        game.game_map = None
        x, y, a = game.find_safe_spawn(10.0, 10.0, 0.5)
        assert (x, y, a) == (10.0, 10.0, 0.5)

        # With map and safe base location
        game = MockGame()
        game.game_map.size = 20
        game.game_map.is_wall.return_value = False
        x, y, a = game.find_safe_spawn(10.0, 10.0, 0.5)
        assert (x, y, a) == (10.0, 10.0, 0.5)

        # With map and bad location (finds new spot)
        def is_wall_mock(tx: float, ty: float) -> bool:
            # Only safe near base + radius 2 angle 0
            return not (abs(tx - 12.0) < 0.1 and abs(ty - 10.0) < 0.1)

        game.game_map.is_wall.side_effect = is_wall_mock
        x, y, a = game.find_safe_spawn(10.0, 10.0, 0.5)
        # It should check attempt=1, radius=2, angle_offset=0 -> test_x=12, test_y=10
        assert math.isclose(x, 12.0)
        assert math.isclose(y, 10.0)
        assert a == 0.5

        # Completely walled off falls back to base
        game.game_map.is_wall.side_effect = lambda tx, ty: True
        x, y, a = game.find_safe_spawn(10.0, 10.0, 0.5)
        assert (x, y, a) == (10.0, 10.0, 0.5)

        # Test continue on boundaries
        def is_wall_mock_bounds(tx: float, ty: float) -> bool:
            return False

        game.game_map.is_wall.side_effect = is_wall_mock_bounds
        # Very close to boundary so the attempt needs to skip it
        x, y, a = game.find_safe_spawn(1.0, 1.0, 0.5)
        # Attempt 0 is at (1.0, 1.0) which is < 2, so it gets skipped
        # Attempt 1 has radius 2, check angles.
        assert x >= 2.0 or y >= 2.0 or (x == 1.0 and y == 1.0)

    def test_get_corner_positions(self) -> None:
        """Test getting corner positions."""
        game = MockGame()
        game.game_map.size = 20
        game.game_map.is_wall.return_value = False
        corners = game.get_corner_positions()
        assert len(corners) == 4

    def test_get_best_spawn_point(self) -> None:
        """Test finding the best spawn point."""
        game = MockGame()
        game.game_map.size = 20
        game.game_map.is_wall.return_value = False

        # Valid corner
        x, y, a = game._get_best_spawn_point()
        assert isinstance(x, float)

        # No map
        game.game_map = None
        assert game._get_best_spawn_point() == MockConstants.DEFAULT_PLAYER_SPAWN

        # Grid fallback
        game = MockGame()
        game.game_map.size = 20

        def is_wall_mock(vx: float, vy: float) -> bool:
            # Fail all corners. If floating point, we assume it's a corner coordinate.
            # Grid integer coordinates go from 0 to 19.
            # Block everything except vx == 10 and vy == 10.
            if isinstance(vx, float) or isinstance(vy, float):
                # corners are floats
                return True
            # grid is integers (from range)
            if vx == 10 and vy == 10:
                return False
            return True

        game.game_map.is_wall.side_effect = is_wall_mock
        game.game_map.height = 20
        game.game_map.width = 20
        # The first (x, y) not blocked will be evaluated using `is_wall(x, y)`
        x, y, a = game._get_best_spawn_point()
        assert x == 10.5
        assert y == 10.5

        # Complete fallback when everything blocked
        game.game_map.is_wall.side_effect = lambda vx, vy: True
        assert game._get_best_spawn_point() == MockConstants.DEFAULT_PLAYER_SPAWN

    def test_respawn_player(self) -> None:
        """Test respawning the player."""
        game = MockGame()
        game.game_map.size = 20
        game.game_map.is_wall.return_value = False

        game.respawn_player()
        assert game.player.health == 100
        assert game.player.alive is True
        assert game.player.shield_active is False
        assert any("RESPAWNED" in t["text"] for t in game.damage_texts)
