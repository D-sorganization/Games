"""Pluggable map generation strategies.

Provides a Protocol-based strategy pattern for map generation,
allowing different algorithms to be injected into MapBase.

Usage:
    from games.shared.map_generators import CellularAutomataGenerator
    from games.shared.map_base import MapBase

    # Default behavior (cellular automata):
    m = MapBase(50)

    # Custom generator:
    gen = CellularAutomataGenerator(wall_chance=0.50, iterations=7)
    m = MapBase(50, generator=gen)

    # Empty map for testing:
    from games.shared.map_generators import EmptyMapGenerator
    m = MapBase(50, generator=EmptyMapGenerator())
"""

from __future__ import annotations

import random
from typing import Protocol


class MapGenerator(Protocol):
    """Protocol for map generation strategies.

    Implementations must provide a ``generate`` method that fills a
    pre-allocated grid **in-place**.  The grid is a list-of-lists of
    ``int`` with dimensions ``size x size``, initialized to all zeros.
    """

    def generate(self, grid: list[list[int]], size: int) -> None:
        """Generate map content in-place on the grid.

        Args:
            grid: 2-D grid (size x size) to populate. Modified in place.
            size: Side length of the square grid.
        """
        ...


class CellularAutomataGenerator:
    """Cellular automata cave/room generator.

    This is the **default** generator extracted from the original
    ``MapBase.create_map()`` implementation.  It produces organic-looking
    cave structures by:

    1. Seeding random walls (controlled by *wall_chance*).
    2. Running cellular automata smoothing (controlled by *iterations*).

    Note: room overlay and connectivity enforcement remain in ``MapBase``
    so that every generator benefits from them.
    """

    def __init__(self, wall_chance: float = 0.45, iterations: int = 5) -> None:
        self.wall_chance = wall_chance
        self.iterations = iterations

    def generate(self, grid: list[list[int]], size: int) -> None:
        """Populate *grid* using cellular automata."""
        self._seed_walls(grid, size)
        self._set_borders(grid, size)
        self._smooth(grid, size)

    # -- helpers -------------------------------------------------------------

    def _seed_walls(self, grid: list[list[int]], size: int) -> None:
        """Fill every cell with a random wall/open value."""
        for i in range(size):
            for j in range(size):
                grid[i][j] = 1 if random.random() < self.wall_chance else 0

    @staticmethod
    def _set_borders(grid: list[list[int]], size: int) -> None:
        """Force all border cells to walls."""
        for i in range(size):
            grid[0][i] = 1
            grid[size - 1][i] = 1
            grid[i][0] = 1
            grid[i][size - 1] = 1

    def _smooth(self, grid: list[list[int]], size: int) -> None:
        """Run cellular automata smoothing for *self.iterations* passes."""
        for _ in range(self.iterations):
            new_grid = _smooth_pass(grid, size)
            _copy_grid(new_grid, grid, size)


# ---------------------------------------------------------------------------
# Module-level helpers (keep class methods short and low-complexity)
# ---------------------------------------------------------------------------


def _count_wall_neighbors(grid: list[list[int]], row: int, col: int) -> int:
    """Count how many of the 8 neighbours of (row, col) are walls (> 0)."""
    count = 0
    for ni in range(-1, 2):
        for nj in range(-1, 2):
            if ni == 0 and nj == 0:
                continue
            if grid[row + ni][col + nj] > 0:
                count += 1
    return count


def _smooth_pass(grid: list[list[int]], size: int) -> list[list[int]]:
    """Return a new grid after one cellular-automata smoothing pass."""
    new_grid = [row[:] for row in grid]
    for i in range(1, size - 1):
        for j in range(1, size - 1):
            neighbors = _count_wall_neighbors(grid, i, j)
            if neighbors > 4:
                new_grid[i][j] = 1
            elif neighbors < 4:
                new_grid[i][j] = 0
    return new_grid


def _copy_grid(src: list[list[int]], dst: list[list[int]], size: int) -> None:
    """Copy every cell from *src* into *dst* in-place."""
    for i in range(size):
        for j in range(size):
            dst[i][j] = src[i][j]


# ---------------------------------------------------------------------------
# EmptyMapGenerator
# ---------------------------------------------------------------------------


class EmptyMapGenerator:
    """Generates an empty map with only border walls.

    Useful for deterministic testing and custom scenarios where a
    blank canvas is desired.
    """

    def generate(self, grid: list[list[int]], size: int) -> None:
        """Fill *grid* with zeros and wall-only borders."""
        for y in range(size):
            for x in range(size):
                is_border = x == 0 or y == 0 or x == size - 1 or y == size - 1
                grid[y][x] = 1 if is_border else 0
