"""Tests for the shared SpatialGrid module."""

from __future__ import annotations

import pytest

from games.shared.spatial_grid import Positioned, SpatialGrid

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _Point:
    """Minimal positioned entity for testing."""

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"_Point({self.x}, {self.y})"


# ---------------------------------------------------------------------------
# Construction / protocol
# ---------------------------------------------------------------------------


class TestPositionedProtocol:
    def test_point_satisfies_protocol(self) -> None:
        p = _Point(1.0, 2.0)
        assert isinstance(p, Positioned)

    def test_object_without_xy_does_not_satisfy(self) -> None:
        class NoXY:
            pass

        assert not isinstance(NoXY(), Positioned)


class TestConstruction:
    def test_default_cell_size(self) -> None:
        grid = SpatialGrid()
        assert grid.cell_size == 5.0

    def test_custom_cell_size(self) -> None:
        grid = SpatialGrid(cell_size=10.0)
        assert grid.cell_size == 10.0

    def test_invalid_cell_size_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            SpatialGrid(cell_size=0)
        with pytest.raises(ValueError, match="positive"):
            SpatialGrid(cell_size=-1.0)

    def test_empty_grid_has_no_cells(self) -> None:
        grid = SpatialGrid()
        assert len(grid.cells) == 0


# ---------------------------------------------------------------------------
# insert / clear
# ---------------------------------------------------------------------------


class TestInsertAndClear:
    def test_insert_single(self) -> None:
        grid = SpatialGrid(cell_size=5.0)
        p = _Point(2.5, 3.5)
        grid.insert(p)
        assert len(grid.cells) == 1
        assert p in list(grid.cells.values())[0]

    def test_insert_multiple_same_cell(self) -> None:
        grid = SpatialGrid(cell_size=5.0)
        a = _Point(1.0, 1.0)
        b = _Point(2.0, 2.0)
        grid.insert(a)
        grid.insert(b)
        assert len(grid.cells) == 1
        bucket = list(grid.cells.values())[0]
        assert a in bucket
        assert b in bucket

    def test_insert_different_cells(self) -> None:
        grid = SpatialGrid(cell_size=5.0)
        a = _Point(1.0, 1.0)  # cell (0, 0)
        b = _Point(6.0, 6.0)  # cell (1, 1)
        grid.insert(a)
        grid.insert(b)
        assert len(grid.cells) == 2

    def test_clear(self) -> None:
        grid = SpatialGrid(cell_size=5.0)
        grid.insert(_Point(1.0, 1.0))
        grid.insert(_Point(6.0, 6.0))
        assert len(grid.cells) == 2
        grid.clear()
        assert len(grid.cells) == 0


# ---------------------------------------------------------------------------
# update (bulk rebuild)
# ---------------------------------------------------------------------------


class TestUpdate:
    def test_update_rebuilds(self) -> None:
        grid = SpatialGrid(cell_size=5.0)
        a = _Point(1.0, 1.0)
        b = _Point(6.0, 6.0)
        grid.update([a, b])
        assert len(grid.cells) == 2

    def test_update_clears_previous(self) -> None:
        grid = SpatialGrid(cell_size=5.0)
        grid.insert(_Point(100.0, 100.0))
        grid.update([_Point(1.0, 1.0)])
        assert len(grid.cells) == 1
        # The old point at (100, 100) should be gone
        assert grid.cells.get((20, 20)) is None

    def test_update_empty_list(self) -> None:
        grid = SpatialGrid(cell_size=5.0)
        grid.insert(_Point(1.0, 1.0))
        grid.update([])
        assert len(grid.cells) == 0


# ---------------------------------------------------------------------------
# get_nearby
# ---------------------------------------------------------------------------


class TestGetNearby:
    def test_empty_grid_returns_empty(self) -> None:
        grid = SpatialGrid(cell_size=5.0)
        assert grid.get_nearby(0.0, 0.0) == []

    def test_returns_entity_in_same_cell(self) -> None:
        grid = SpatialGrid(cell_size=5.0)
        p = _Point(2.5, 2.5)
        grid.insert(p)
        result = grid.get_nearby(2.5, 2.5)
        assert p in result

    def test_returns_entity_in_adjacent_cell(self) -> None:
        grid = SpatialGrid(cell_size=5.0)
        # Place entity in cell (1, 1)
        p = _Point(7.0, 7.0)
        grid.insert(p)
        # Query from cell (0, 0) -- adjacent diagonally
        result = grid.get_nearby(4.9, 4.9)
        assert p in result

    def test_does_not_return_distant_entity(self) -> None:
        grid = SpatialGrid(cell_size=5.0)
        # Place entity far away: cell (10, 10)
        far = _Point(52.0, 52.0)
        grid.insert(far)
        result = grid.get_nearby(0.0, 0.0)
        assert far not in result

    def test_returns_all_nearby_entities(self) -> None:
        grid = SpatialGrid(cell_size=5.0)
        # All within 3x3 neighbourhood of cell (1,1)
        points = [
            _Point(5.5, 5.5),  # cell (1, 1) - same
            _Point(0.5, 5.5),  # cell (0, 1) - adjacent
            _Point(5.5, 0.5),  # cell (1, 0) - adjacent
            _Point(10.5, 10.5),  # cell (2, 2) - adjacent to (1,1)
        ]
        far = _Point(50.0, 50.0)  # cell (10, 10) - NOT adjacent
        grid.update(points + [far])

        result = grid.get_nearby(7.0, 7.0)  # query cell (1, 1)
        for p in points:
            assert p in result
        assert far not in result

    def test_self_included_in_nearby(self) -> None:
        """An entity at the query position appears in its own nearby list."""
        grid = SpatialGrid(cell_size=5.0)
        p = _Point(3.0, 3.0)
        grid.insert(p)
        result = grid.get_nearby(p.x, p.y)
        assert p in result


# ---------------------------------------------------------------------------
# Negative coordinates
# ---------------------------------------------------------------------------


class TestNegativeCoordinates:
    def test_insert_negative(self) -> None:
        grid = SpatialGrid(cell_size=5.0)
        p = _Point(-3.0, -7.0)
        grid.insert(p)
        result = grid.get_nearby(-3.0, -7.0)
        assert p in result

    def test_nearby_across_origin(self) -> None:
        grid = SpatialGrid(cell_size=5.0)
        # Cell (-1, -1) and cell (0, 0) are adjacent
        a = _Point(-1.0, -1.0)  # cell (-1, -1)
        b = _Point(1.0, 1.0)  # cell (0, 0)
        grid.update([a, b])
        result_a = grid.get_nearby(-1.0, -1.0)
        result_b = grid.get_nearby(1.0, 1.0)
        # Both should see each other (adjacent cells)
        assert b in result_a
        assert a in result_b


# ---------------------------------------------------------------------------
# Cell size edge cases
# ---------------------------------------------------------------------------


class TestCellSizeVariation:
    def test_small_cell_size(self) -> None:
        grid = SpatialGrid(cell_size=1.0)
        a = _Point(0.5, 0.5)  # cell (0, 0)
        b = _Point(1.5, 1.5)  # cell (1, 1)
        c = _Point(5.0, 5.0)  # cell (5, 5) -- too far
        grid.update([a, b, c])
        result = grid.get_nearby(0.5, 0.5)
        assert a in result
        assert b in result
        assert c not in result

    def test_large_cell_size(self) -> None:
        grid = SpatialGrid(cell_size=100.0)
        # Everything lands in cell (0, 0) with large cell size
        points = [_Point(i, i) for i in range(50)]
        grid.update(points)
        result = grid.get_nearby(25.0, 25.0)
        assert len(result) == len(points)
