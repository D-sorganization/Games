"""Tests for the games.shared.utils module.

Uses shared fixtures from conftest.py for MockMap and MockEntity.
Parametrizes ray direction tests for comprehensive coverage.
"""

from __future__ import annotations

import math

import pytest

from games.shared.utils import cast_ray_dda, has_line_of_sight, try_move_entity

# Import from conftest (available via pytest)
from tests.conftest import MockEntity, MockMap


class TestCastRayDda:
    """Tests for the cast_ray_dda function."""

    @pytest.mark.parametrize(
        "angle,direction",
        [
            (0.0, "east"),
            (math.pi / 2, "south"),
            (math.pi, "west"),
            (3 * math.pi / 2, "north"),
            (math.pi / 4, "southeast"),
            (3 * math.pi / 4, "southwest"),
            (5 * math.pi / 4, "northwest"),
            (7 * math.pi / 4, "northeast"),
        ],
        ids=[
            "east",
            "south",
            "west",
            "north",
            "southeast",
            "southwest",
            "northwest",
            "northeast",
        ],
    )
    def test_ray_hits_wall_in_direction(
        self,
        open_map: MockMap,
        angle: float,
        direction: str,
    ) -> None:
        """Ray should hit a wall when cast in any cardinal/diagonal direction."""
        dist, wall_type, _, _, _, _, _ = cast_ray_dda(
            5.0, 5.0, angle, open_map, max_dist=20.0
        )
        assert dist > 0, f"Distance should be positive ({direction})"
        assert dist < 20.0, f"Should hit wall before max ({direction})"
        assert wall_type > 0, f"Should return wall type ({direction})"

    def test_ray_returns_max_dist_in_open_space(self, open_map: MockMap) -> None:
        """Ray should return max_dist when no wall is close enough."""
        short_max = 0.5
        dist, _, _, _, _, _, _ = cast_ray_dda(
            5.0, 5.0, 0.0, open_map, max_dist=short_max
        )
        assert dist <= short_max + 0.1

    def test_ray_hits_middle_wall(self, wall_map: MockMap) -> None:
        """Ray should detect a wall placed in the middle of the map."""
        dist, wall_type, _, _, _, map_x, _ = cast_ray_dda(
            2.5, 5.5, 0.0, wall_map, max_dist=20.0
        )
        assert wall_type > 0
        assert map_x == 4

    def test_ray_returns_seven_element_tuple(self, open_map: MockMap) -> None:
        """cast_ray_dda should return a 7-element tuple."""
        result = cast_ray_dda(5.0, 5.0, 0.0, open_map)
        assert len(result) == 7


class TestHasLineOfSight:
    """Tests for the has_line_of_sight function."""

    @pytest.mark.parametrize(
        "x1,y1,x2,y2,expected",
        [
            (2.5, 2.5, 7.5, 2.5, True),
            (2.5, 2.5, 2.5, 7.5, True),
            (2.5, 2.5, 7.5, 7.5, True),
            (5.0, 5.0, 5.0, 5.0, True),
            (5.0, 5.0, 5.001, 5.001, True),
        ],
        ids=[
            "horizontal",
            "vertical",
            "diagonal",
            "same_point",
            "very_close",
        ],
    )
    def test_open_map_line_of_sight(
        self,
        open_map: MockMap,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        expected: bool,
    ) -> None:
        """Points in open space should have line of sight."""
        assert has_line_of_sight(x1, y1, x2, y2, open_map) == expected

    def test_no_line_of_sight_through_wall(self, wall_map: MockMap) -> None:
        """Wall at (4,5) should block horizontal sight."""
        assert not has_line_of_sight(2.5, 5.5, 6.5, 5.5, wall_map)


class TestTryMoveEntity:
    """Tests for the try_move_entity function."""

    def test_move_in_open_space(self, open_map: MockMap) -> None:
        """Entity should move freely in open space."""
        entity = MockEntity(5.0, 5.0)
        try_move_entity(entity, 1.0, 0.0, open_map, [])
        assert entity.x == pytest.approx(6.0)
        assert entity.y == pytest.approx(5.0)

    @pytest.mark.parametrize(
        "start_x,start_y,dx,dy,exp_x,exp_y",
        [
            (1.5, 5.0, -1.0, 0.0, 1.5, 5.0),
            (5.0, 1.5, 0.0, -1.0, 5.0, 1.5),
            (8.5, 5.0, 1.0, 0.0, 8.5, 5.0),
            (5.0, 8.5, 0.0, 1.0, 5.0, 8.5),
        ],
        ids=["wall_west", "wall_north", "wall_east", "wall_south"],
    )
    def test_move_blocked_by_wall(
        self,
        open_map: MockMap,
        start_x: float,
        start_y: float,
        dx: float,
        dy: float,
        exp_x: float,
        exp_y: float,
    ) -> None:
        """Entity should not move into border walls."""
        entity = MockEntity(start_x, start_y)
        try_move_entity(entity, dx, dy, open_map, [])
        assert entity.x == pytest.approx(exp_x)
        assert entity.y == pytest.approx(exp_y)

    def test_move_blocked_by_obstacle(self, open_map: MockMap) -> None:
        """Entity should not move into another alive entity."""
        entity = MockEntity(5.0, 5.0)
        obstacle = MockEntity(5.3, 5.0)
        try_move_entity(entity, 0.5, 0.0, open_map, [obstacle], radius=0.5)
        assert entity.x == pytest.approx(5.0)

    def test_move_ignores_dead_obstacle(self, open_map: MockMap) -> None:
        """Entity should pass through dead obstacles."""
        entity = MockEntity(5.0, 5.0)
        dead = MockEntity(5.3, 5.0, alive=False)
        try_move_entity(entity, 0.5, 0.0, open_map, [dead], radius=0.5)
        assert entity.x == pytest.approx(5.5)

    def test_move_ignores_self(self, open_map: MockMap) -> None:
        """Entity should not collide with itself."""
        entity = MockEntity(5.0, 5.0)
        try_move_entity(entity, 0.5, 0.0, open_map, [entity], radius=0.5)
        assert entity.x == pytest.approx(5.5)

    def test_y_movement_independent(self, open_map: MockMap) -> None:
        """Y movement should work independently of X."""
        entity = MockEntity(5.0, 5.0)
        try_move_entity(entity, 0.0, 1.0, open_map, [])
        assert entity.x == pytest.approx(5.0)
        assert entity.y == pytest.approx(6.0)

    def test_diagonal_move_partial_block(self, open_map: MockMap) -> None:
        """If X is blocked but Y is free, only Y should move."""
        entity = MockEntity(1.5, 5.0)
        try_move_entity(entity, -1.0, 1.0, open_map, [])
        assert entity.x == pytest.approx(1.5)
        assert entity.y == pytest.approx(6.0)
