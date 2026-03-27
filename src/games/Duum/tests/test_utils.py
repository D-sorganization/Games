"""Tests for utility functions."""

import math
import unittest

from games.shared.utils import cast_ray_dda, has_line_of_sight, try_move_entity
from src.map import Map
from src.projectile import Projectile


class MockEntity:
    """Mock entity for testing movement."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.alive = True


class TestUtils(unittest.TestCase):
    """Test utility functions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.map = Map(20)
        # Clear center area for testing
        for y in range(5, 15):
            for x in range(5, 15):
                self.map.grid[y][x] = 0

    def test_cast_ray_dda_bounds_checking(self) -> None:
        """Test that cast_ray_dda properly handles out-of-bounds coordinates."""
        # Test ray going out of bounds from near boundary
        # Note: cast_ray_dda now returns 7 values:
        # (dist, wall_type, hit_x, hit_y, side, map_x, map_y)
        distance, wall_type, hit_x, hit_y, side, map_x, map_y = cast_ray_dda(
            18.5,
            10.0,
            0.0,
            self.map,
            max_dist=50.0,  # Ray going east
        )

        # Should hit a wall (either boundary or existing wall)
        self.assertGreater(distance, 0)
        self.assertGreater(wall_type, 0)  # Any wall type > 0 is valid

        # Test ray going in negative direction (out of bounds)
        distance, wall_type, hit_x, hit_y, side, map_x, map_y = cast_ray_dda(
            1.5,
            10.0,
            math.pi,
            self.map,
            max_dist=50.0,  # Ray going west
        )

        # Should hit a wall
        self.assertGreater(distance, 0)
        self.assertGreater(wall_type, 0)

    def test_has_line_of_sight_clear_path(self) -> None:
        """Test line of sight with clear path."""
        # Clear path in center area
        self.assertTrue(has_line_of_sight(8.0, 8.0, 12.0, 12.0, self.map))

    def test_has_line_of_sight_blocked_path(self) -> None:
        """Test line of sight with blocked path."""
        # Add wall in the middle
        self.map.grid[10][10] = 1

        # Should be blocked
        self.assertFalse(has_line_of_sight(8.0, 8.0, 12.0, 12.0, self.map))

    def test_try_move_entity_valid_move(self) -> None:
        """Test entity movement to valid position."""
        entity = MockEntity(10.0, 10.0)
        original_x = entity.x

        # Move east (should succeed in clear area)
        try_move_entity(entity, 1.0, 0.0, self.map, [])

        self.assertEqual(entity.x, original_x + 1.0)
        self.assertEqual(entity.y, 10.0)

    def test_try_move_entity_wall_collision(self) -> None:
        """Test entity movement blocked by wall."""
        entity = MockEntity(1.5, 1.5)  # Near boundary
        original_x = entity.x

        # Try to move west into boundary wall
        try_move_entity(entity, -1.0, 0.0, self.map, [])

        # Should not move due to wall collision
        self.assertEqual(entity.x, original_x)

    def test_try_move_entity_obstacle_collision(self) -> None:
        """Test entity movement blocked by other entity."""
        entity1 = MockEntity(10.0, 10.0)
        entity2 = MockEntity(10.5, 10.0)  # Close to entity1

        original_x = entity1.x

        # Try to move entity1 toward entity2
        try_move_entity(entity1, 0.6, 0.0, self.map, [entity2])

        # Should not move due to collision with entity2
        self.assertEqual(entity1.x, original_x)

    def test_projectile_bounds_handling(self) -> None:
        """Test that projectiles handle map boundaries correctly."""
        # Create projectile near boundary
        projectile = Projectile(
            x=18.5, y=10.0, angle=0.0, damage=10, speed=1.0, is_player=True
        )

        # Update projectile (should move toward boundary)
        projectile.update(self.map)

        # Should either be stopped by wall or marked as not alive
        # The key is that it shouldn't crash
        self.assertTrue(isinstance(projectile.alive, bool))

        # Test projectile going out of bounds in negative direction
        projectile2 = Projectile(
            x=1.5, y=10.0, angle=math.pi, damage=10, speed=1.0, is_player=True
        )

        projectile2.update(self.map)

        # Should handle boundary correctly without crashing
        self.assertTrue(isinstance(projectile2.alive, bool))


if __name__ == "__main__":
    unittest.main()
