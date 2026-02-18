"""Spatial hash grid for efficient proximity queries."""

from __future__ import annotations

from collections import defaultdict
from typing import Protocol, runtime_checkable


@runtime_checkable
class Positioned(Protocol):
    """Any object with x, y coordinates."""

    x: float
    y: float


class SpatialGrid:
    """Spatial hash grid for O(1) average-case neighbor lookups.

    Divides the world into cells of *cell_size*.  Entities are hashed
    into cells by their (x, y) position.  Neighbor queries check only
    the 9 surrounding cells (3x3 neighbourhood), so the cost is
    proportional to the local density rather than the total entity count.

    Typical usage::

        grid = SpatialGrid(cell_size=5.0)
        # Once per frame:
        grid.update(entities)
        # Per-entity query:
        nearby = grid.get_nearby(entity.x, entity.y)
    """

    def __init__(self, cell_size: float = 5.0) -> None:
        if cell_size <= 0:
            raise ValueError("cell_size must be positive")
        self.cell_size = cell_size
        self.cells: dict[tuple[int, int], list] = defaultdict(list)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Remove all entities from the grid."""
        self.cells.clear()

    def insert(self, entity: Positioned) -> None:
        """Insert a single entity into its grid cell."""
        key = self._key(entity.x, entity.y)
        self.cells[key].append(entity)

    def update(self, entities: list) -> None:
        """Rebuild the grid from scratch with *entities*.

        This is the recommended way to refresh the grid each frame.
        """
        self.clear()
        for entity in entities:
            self.insert(entity)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_nearby(self, x: float, y: float) -> list:
        """Return all entities in the 3x3 neighbourhood around *(x, y)*."""
        cx, cy = self._key(x, y)
        result: list = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                bucket = self.cells.get((cx + dx, cy + dy))
                if bucket:
                    result.extend(bucket)
        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _key(self, x: float, y: float) -> tuple[int, int]:
        """Hash world coordinates to a grid cell key."""
        return (int(x // self.cell_size), int(y // self.cell_size))
