"""Tests for the games.shared.utils module."""

from __future__ import annotations

import math

import pytest

from games.shared.utils import cast_ray_dda, has_line_of_sight, try_move_entity


class MockMap:
    """A simple mock map for testing raycasting and movement."""

    def __init__(self, grid: list[list[int]]) -> None:
        """Initialize with a 2D grid.

        Args:
            grid: 2D list where 0 = empty, >0 = wall type.
        """
        self.grid = grid
        self.height = len(grid)
        self.width = len(grid[0]) if grid else 0
        self.size = max(self.width, self.height)

    def is_wall(self, x: float, y: float) -> bool:
        """Check if position is a wall.

        Args:
            x: X coordinate.
            y: Y coordinate.

        Returns:
            True if the tile at (int(x), int(y)) is a wall.
        """
        ix, iy = int(x), int(y)
        if 0 <= ix < self.width and 0 <= iy < self.height:
            return self.grid[iy][ix] > 0
        return True  # Out of bounds is wall


class MockEntity:
    """A simple mock entity with x, y, alive attributes."""

    def __init__(self, x: float, y: float, alive: bool = True) -> None:
        """Initialize entity.

        Args:
            x: X position.
            y: Y position.
            alive: Whether entity is alive.
        """
        self.x = x
        self.y = y
        self.alive = alive


# ----- Simple open map for basic tests -----
OPEN_MAP = MockMap(
    [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]
)

# Map with a wall in the middle
WALL_MAP = MockMap(
    [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 1, 0, 0, 0, 0, 1],  # Wall at (4, 5)
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]
)


class TestCastRayDda:
    """Tests for the cast_ray_dda function."""

    def test_ray_hits_east_wall(self) -> None:
        """Ray cast east should hit the east wall."""
        dist, wall_type, _, _, _, _, _ = cast_ray_dda(
            5.0, 5.0, 0.0, OPEN_MAP, max_dist=20.0
        )
        # Should hit the wall at x=9 (east border)
        assert dist > 0
        assert dist < 20.0
        assert wall_type > 0

    def test_ray_hits_south_wall(self) -> None:
        """Ray cast south should hit the south wall."""
        dist, wall_type, _, _, _, _, _ = cast_ray_dda(
            5.0, 5.0, math.pi / 2, OPEN_MAP, max_dist=20.0
        )
        assert dist > 0
        assert dist < 20.0
        assert wall_type > 0

    def test_ray_hits_west_wall(self) -> None:
        """Ray cast west should hit the west wall."""
        dist, wall_type, _, _, _, _, _ = cast_ray_dda(
            5.0, 5.0, math.pi, OPEN_MAP, max_dist=20.0
        )
        assert dist > 0
        assert dist < 20.0
        assert wall_type > 0

    def test_ray_hits_north_wall(self) -> None:
        """Ray cast north should hit the north wall."""
        dist, wall_type, _, _, _, _, _ = cast_ray_dda(
            5.0, 5.0, 3 * math.pi / 2, OPEN_MAP, max_dist=20.0
        )
        assert dist > 0
        assert dist < 20.0
        assert wall_type > 0

    def test_ray_returns_max_dist_in_open_space(self) -> None:
        """Ray should return max_dist when no wall is close enough."""
        short_max = 0.5  # Very short max distance
        dist, wall_type, _, _, _, _, _ = cast_ray_dda(
            5.0, 5.0, 0.0, OPEN_MAP, max_dist=short_max
        )
        # Should not have found a wall within 0.5 units
        assert dist <= short_max + 0.1

    def test_ray_hits_middle_wall(self) -> None:
        """Ray should hit a wall placed in the middle of the map."""
        # Cast from (2.5, 5.5) east toward wall at (4, 5)
        dist, wall_type, _, _, _, map_x, _ = cast_ray_dda(
            2.5, 5.5, 0.0, WALL_MAP, max_dist=20.0
        )
        assert wall_type > 0
        assert map_x == 4

    def test_ray_returns_seven_element_tuple(self) -> None:
        """cast_ray_dda should return a 7-element tuple."""
        result = cast_ray_dda(5.0, 5.0, 0.0, OPEN_MAP)
        assert len(result) == 7


class TestHasLineOfSight:
    """Tests for the has_line_of_sight function."""

    def test_line_of_sight_in_open_map(self) -> None:
        """Points in open space should have line of sight."""
        assert has_line_of_sight(2.5, 2.5, 7.5, 2.5, OPEN_MAP)

    def test_no_line_of_sight_through_wall(self) -> None:
        """Points separated by a wall should not have line of sight."""
        # Wall at (4, 5) should block sight from (2.5, 5.5) to (6.5, 5.5)
        assert not has_line_of_sight(2.5, 5.5, 6.5, 5.5, WALL_MAP)

    def test_same_point_has_line_of_sight(self) -> None:
        """Same point should have line of sight to itself."""
        assert has_line_of_sight(5.0, 5.0, 5.0, 5.0, OPEN_MAP)

    def test_very_close_points_have_sight(self) -> None:
        """Very close points should have line of sight."""
        assert has_line_of_sight(5.0, 5.0, 5.001, 5.001, OPEN_MAP)


class TestTryMoveEntity:
    """Tests for the try_move_entity function."""

    def test_move_in_open_space(self) -> None:
        """Entity should move freely in open space."""
        entity = MockEntity(5.0, 5.0)
        try_move_entity(entity, 1.0, 0.0, OPEN_MAP, [])
        assert entity.x == pytest.approx(6.0)
        assert entity.y == pytest.approx(5.0)

    def test_move_blocked_by_wall_x(self) -> None:
        """Entity should not move into a wall (X direction)."""
        entity = MockEntity(1.5, 5.0)
        try_move_entity(entity, -1.0, 0.0, OPEN_MAP, [])
        # Should be blocked by wall at x=0
        assert entity.x == pytest.approx(1.5)

    def test_move_blocked_by_wall_y(self) -> None:
        """Entity should not move into a wall (Y direction)."""
        entity = MockEntity(5.0, 1.5)
        try_move_entity(entity, 0.0, -1.0, OPEN_MAP, [])
        # Should be blocked by wall at y=0
        assert entity.y == pytest.approx(1.5)

    def test_move_blocked_by_obstacle(self) -> None:
        """Entity should not move into another entity."""
        entity = MockEntity(5.0, 5.0)
        obstacle = MockEntity(5.3, 5.0)
        try_move_entity(entity, 0.5, 0.0, OPEN_MAP, [obstacle], radius=0.5)
        # Should be blocked by the obstacle
        assert entity.x == pytest.approx(5.0)

    def test_move_ignores_dead_obstacle(self) -> None:
        """Entity should move through dead obstacles."""
        entity = MockEntity(5.0, 5.0)
        dead_obstacle = MockEntity(5.3, 5.0, alive=False)
        try_move_entity(entity, 0.5, 0.0, OPEN_MAP, [dead_obstacle], radius=0.5)
        # Should pass through dead obstacle
        assert entity.x == pytest.approx(5.5)

    def test_move_ignores_self(self) -> None:
        """Entity should not collide with itself."""
        entity = MockEntity(5.0, 5.0)
        try_move_entity(entity, 0.5, 0.0, OPEN_MAP, [entity], radius=0.5)
        assert entity.x == pytest.approx(5.5)

    def test_y_movement_independent(self) -> None:
        """Y movement should work independently of X."""
        entity = MockEntity(5.0, 5.0)
        try_move_entity(entity, 0.0, 1.0, OPEN_MAP, [])
        assert entity.x == pytest.approx(5.0)
        assert entity.y == pytest.approx(6.0)

    def test_diagonal_move_partial_block(self) -> None:
        """If X is blocked but Y is free, only Y should move."""
        entity = MockEntity(1.5, 5.0)
        try_move_entity(entity, -1.0, 1.0, OPEN_MAP, [])
        assert entity.x == pytest.approx(1.5)  # Blocked by wall
        assert entity.y == pytest.approx(6.0)  # Free to move
