"""Tests for the pluggable map generation strategy pattern."""

from __future__ import annotations

from games.shared.map_base import MapBase
from games.shared.map_generators import (
    CellularAutomataGenerator,
    EmptyMapGenerator,
)

# ---------------------------------------------------------------------------
# CellularAutomataGenerator
# ---------------------------------------------------------------------------


class TestCellularAutomataGenerator:
    """Tests for the default cellular automata generator."""

    def test_produces_border_walls(self) -> None:
        """Generated grid must have walls on all four borders."""
        gen = CellularAutomataGenerator()
        size = 20
        grid = [[0] * size for _ in range(size)]
        gen.generate(grid, size)

        for i in range(size):
            assert grid[0][i] > 0, f"Top border at col {i} should be wall"
            assert grid[size - 1][i] > 0, f"Bottom border at col {i}"
            assert grid[i][0] > 0, f"Left border at row {i}"
            assert grid[i][size - 1] > 0, f"Right border at row {i}"

    def test_produces_open_spaces(self) -> None:
        """Interior should contain at least some open (0-valued) cells."""
        gen = CellularAutomataGenerator()
        size = 20
        grid = [[0] * size for _ in range(size)]
        gen.generate(grid, size)

        open_count = sum(
            1 for i in range(1, size - 1) for j in range(1, size - 1) if grid[i][j] == 0
        )
        assert open_count > 0

    def test_custom_wall_chance_higher(self) -> None:
        """Higher wall_chance should tend to produce more walls."""
        import random

        size = 30
        dense = CellularAutomataGenerator(wall_chance=0.80, iterations=1)
        sparse = CellularAutomataGenerator(wall_chance=0.10, iterations=1)

        grid_dense = [[0] * size for _ in range(size)]
        grid_sparse = [[0] * size for _ in range(size)]

        # Use fixed seeds so the comparison is deterministic
        random.seed(42)
        dense.generate(grid_dense, size)
        random.seed(42)
        sparse.generate(grid_sparse, size)

        walls_dense = sum(cell > 0 for row in grid_dense for cell in row)
        walls_sparse = sum(cell > 0 for row in grid_sparse for cell in row)

        assert walls_dense > walls_sparse

    def test_modifies_grid_in_place(self) -> None:
        """Generator must write into the provided grid, not replace it."""
        gen = CellularAutomataGenerator()
        size = 15
        grid = [[0] * size for _ in range(size)]
        original_id = id(grid)
        gen.generate(grid, size)
        assert id(grid) == original_id


# ---------------------------------------------------------------------------
# EmptyMapGenerator
# ---------------------------------------------------------------------------


class TestEmptyMapGenerator:
    """Tests for the border-only (empty) generator."""

    def test_borders_are_walls(self) -> None:
        """All border cells must be walls (value 1)."""
        gen = EmptyMapGenerator()
        size = 15
        grid = [[0] * size for _ in range(size)]
        gen.generate(grid, size)

        for i in range(size):
            assert grid[0][i] == 1
            assert grid[size - 1][i] == 1
            assert grid[i][0] == 1
            assert grid[i][size - 1] == 1

    def test_interior_is_empty(self) -> None:
        """All interior cells must be open (value 0)."""
        gen = EmptyMapGenerator()
        size = 15
        grid = [[9] * size for _ in range(size)]  # prefill with junk
        gen.generate(grid, size)

        for i in range(1, size - 1):
            for j in range(1, size - 1):
                assert grid[i][j] == 0, f"Interior cell ({i},{j}) should be 0"

    def test_modifies_grid_in_place(self) -> None:
        """Generator must write into the provided grid, not replace it."""
        gen = EmptyMapGenerator()
        size = 10
        grid = [[0] * size for _ in range(size)]
        original_id = id(grid)
        gen.generate(grid, size)
        assert id(grid) == original_id


# ---------------------------------------------------------------------------
# MapBase integration with generators
# ---------------------------------------------------------------------------


class TestMapBaseWithGenerator:
    """Tests that MapBase correctly delegates to a pluggable generator."""

    def test_default_generator_is_cellular_automata(self) -> None:
        """MapBase without explicit generator should use CellularAutomataGenerator."""
        m = MapBase(20, generate=False)
        assert isinstance(m.generator, CellularAutomataGenerator)

    def test_custom_generator_is_stored(self) -> None:
        """Explicit generator should be stored on the instance."""
        gen = EmptyMapGenerator()
        m = MapBase(15, generate=False, generator=gen)
        assert m.generator is gen

    def test_empty_generator_produces_valid_map(self) -> None:
        """MapBase with EmptyMapGenerator should still produce a connected map."""
        m = MapBase(20, generator=EmptyMapGenerator())

        # After rooms and connectivity, map should still have open space
        open_count = sum(1 for row in m.grid for cell in row if cell == 0)
        assert open_count > 0

    def test_empty_generator_map_has_border_walls(self) -> None:
        """Map generated with EmptyMapGenerator should retain border walls."""
        m = MapBase(20, generator=EmptyMapGenerator())
        size = m.size
        for i in range(size):
            assert m.grid[0][i] > 0
            assert m.grid[size - 1][i] > 0
            assert m.grid[i][0] > 0
            assert m.grid[i][size - 1] > 0

    def test_custom_protocol_generator(self) -> None:
        """Any object satisfying the MapGenerator protocol should work."""

        class CheckerboardGenerator:
            """Fills the grid with a checkerboard of walls and open cells."""

            def generate(self, grid: list[list[int]], size: int) -> None:
                for y in range(size):
                    for x in range(size):
                        if x == 0 or y == 0 or x == size - 1 or y == size - 1:
                            grid[y][x] = 1
                        else:
                            grid[y][x] = (x + y) % 2

        m = MapBase(20, generator=CheckerboardGenerator())
        # Should succeed without error; connectivity enforcement will
        # close off isolated cells, so we just verify it ran.
        assert m.size == 20
        assert any(cell == 0 for row in m.grid for cell in row)


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    """Ensure existing code that never passes a generator still works."""

    def test_mapbase_positional_args_unchanged(self) -> None:
        """MapBase(size) and MapBase(size, generate=False) still work."""
        m1 = MapBase(10)
        assert m1.size == 10
        m2 = MapBase(10, generate=False)
        assert all(cell == 0 for row in m2.grid for cell in row)

    def test_mapbase_generate_true_produces_map(self) -> None:
        """Default generate=True should produce a non-empty map."""
        m = MapBase(20)
        wall_count = sum(1 for row in m.grid for cell in row if cell > 0)
        assert wall_count > 0

    def test_subclass_without_generator_works(self) -> None:
        """A subclass calling super().__init__(size) should work unchanged."""

        class GameMap(MapBase):
            def __init__(self, size: int = 20) -> None:
                super().__init__(size)

        m = GameMap(20)
        assert m.size == 20
        assert isinstance(m.generator, CellularAutomataGenerator)

    def test_subclass_generate_false_works(self) -> None:
        """A subclass passing generate=False should still work."""

        class GameMap(MapBase):
            def __init__(self, size: int = 20) -> None:
                super().__init__(size, generate=False)

        m = GameMap(15)
        assert all(cell == 0 for row in m.grid for cell in row)
