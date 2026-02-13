"""Tests for the games.shared.map_base module."""

from __future__ import annotations

import pytest

from games.shared.contracts import ContractViolation
from games.shared.map_base import MapBase


class TestMapBaseInit:
    """Tests for MapBase initialization."""

    def test_init_creates_grid(self) -> None:
        """MapBase should create a grid of the specified size."""
        m = MapBase(10, generate=False)
        assert m.size == 10
        assert len(m.grid) == 10
        assert len(m.grid[0]) == 10

    def test_init_empty_grid_when_no_generate(self) -> None:
        """Grid should be all zeros when generate is False."""
        m = MapBase(5, generate=False)
        for row in m.grid:
            for cell in row:
                assert cell == 0

    def test_init_rejects_zero_size(self) -> None:
        """Should reject zero map size."""
        with pytest.raises(ContractViolation, match="map_size"):
            MapBase(0, generate=False)

    def test_init_rejects_negative_size(self) -> None:
        """Should reject negative map size."""
        with pytest.raises(ContractViolation, match="map_size"):
            MapBase(-5, generate=False)


class TestMapBaseProperties:
    """Tests for MapBase properties."""

    def test_width_property(self) -> None:
        """Width should equal size."""
        m = MapBase(15, generate=False)
        assert m.width == 15

    def test_height_property(self) -> None:
        """Height should equal size."""
        m = MapBase(15, generate=False)
        assert m.height == 15


class TestMapBaseWallChecks:
    """Tests for wall checking methods."""

    def test_is_wall_empty_grid(self) -> None:
        """Empty grid should have no walls (except borders)."""
        m = MapBase(10, generate=False)
        # Interior should be clear
        assert not m.is_wall(5.0, 5.0)

    def test_is_wall_with_wall(self) -> None:
        """Manually placed wall should be detected."""
        m = MapBase(10, generate=False)
        m.grid[3][3] = 1
        assert m.is_wall(3.0, 3.0)

    def test_is_wall_out_of_bounds(self) -> None:
        """Out-of-bounds positions should be treated as walls."""
        m = MapBase(10, generate=False)
        assert m.is_wall(-1.0, 5.0)
        assert m.is_wall(5.0, -1.0)
        assert m.is_wall(10.0, 5.0)
        assert m.is_wall(5.0, 10.0)

    def test_get_wall_type_empty(self) -> None:
        """Empty cell should return 0."""
        m = MapBase(10, generate=False)
        assert m.get_wall_type(5.0, 5.0) == 0

    def test_get_wall_type_with_wall(self) -> None:
        """Wall cell should return the correct type."""
        m = MapBase(10, generate=False)
        m.grid[4][4] = 3
        assert m.get_wall_type(4.0, 4.0) == 3

    def test_get_wall_type_out_of_bounds(self) -> None:
        """Out-of-bounds should return 1 (default wall)."""
        m = MapBase(10, generate=False)
        assert m.get_wall_type(-1.0, 5.0) == 1


class TestMapBaseGeneration:
    """Tests for procedural map generation."""

    def test_generated_map_has_border_walls(self) -> None:
        """Generated map should have walls on all borders."""
        m = MapBase(20)
        size = m.size
        for i in range(size):
            assert m.grid[0][i] > 0, f"Top border at ({i},0) should be wall"
            assert m.grid[size - 1][i] > 0, f"Bottom border at ({i},{size-1})"
            assert m.grid[i][0] > 0, f"Left border at (0,{i})"
            assert m.grid[i][size - 1] > 0, f"Right border at ({size-1},{i})"

    def test_generated_map_has_open_spaces(self) -> None:
        """Generated map should have some open spaces in the interior."""
        m = MapBase(20)
        open_count = 0
        for i in range(1, m.size - 1):
            for j in range(1, m.size - 1):
                if m.grid[i][j] == 0:
                    open_count += 1
        # Should have at least some open space
        assert open_count > 0

    def test_generated_map_is_connected(self) -> None:
        """All open cells should be reachable from each other (connectivity)."""
        m = MapBase(20)

        # Find first open cell
        start = None
        for i in range(m.size):
            for j in range(m.size):
                if m.grid[i][j] == 0:
                    start = (j, i)
                    break
            if start:
                break

        if start is None:
            return  # No open cells (unlikely but valid)

        # BFS from start
        visited: set[tuple[int, int]] = {start}
        queue = [start]
        while queue:
            x, y = queue.pop(0)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < m.size
                    and 0 <= ny < m.size
                    and m.grid[ny][nx] == 0
                    and (nx, ny) not in visited
                ):
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        # Count total open cells
        total_open = sum(
            1 for i in range(m.size) for j in range(m.size) if m.grid[i][j] == 0
        )

        assert (
            len(visited) == total_open
        ), f"Not all open cells are connected: {len(visited)}/{total_open}"
