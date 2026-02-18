"""Base class for game maps with pluggable generation strategies."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from games.shared.contracts import validate_positive
from games.shared.map_generators import CellularAutomataGenerator

if TYPE_CHECKING:
    from games.shared.map_generators import MapGenerator


class MapBase:
    """Base class for game maps with walls and buildings.

    The generation algorithm is pluggable via the *generator* parameter.
    Any object satisfying the :class:`~games.shared.map_generators.MapGenerator`
    protocol can be passed in.  When *generator* is ``None`` (the default),
    a :class:`~games.shared.map_generators.CellularAutomataGenerator` is used,
    preserving full backward compatibility.
    """

    def __init__(
        self,
        size: int,
        generate: bool = True,
        generator: MapGenerator | None = None,
    ):
        """Initialize a map with walls and buildings.

        Args:
            size: Map size (grid dimensions).
            generate: Whether to generate the map immediately (default: True).
            generator: Optional map-generation strategy.  Defaults to
                :class:`CellularAutomataGenerator` when ``None``.
        """
        validate_positive(size, "map_size")
        self.size = size
        self.generator: MapGenerator = (
            generator if generator is not None else CellularAutomataGenerator()
        )
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        if generate:
            self.create_map()

    @property
    def width(self) -> int:
        """Get map width."""
        return self.size

    @property
    def height(self) -> int:
        """Get map height."""
        return self.size

    def create_map(self) -> None:
        """Create the map layout by delegating to the pluggable generator.

        After the generator fills the base terrain the method adds
        rectangular room overlays and ensures full connectivity, just
        as the original implementation did.
        """
        # 1 + 2. Delegate base terrain generation to the strategy
        self.generator.generate(self.grid, self.size)

        # 3. Add Buildings / Rooms overlay (Rectangular structures for variety)
        self._add_rooms()

        # 4. Ensure connectivity (Flood fill)
        self._ensure_connectivity()

    def _add_rooms(self) -> None:
        """Add rectangular rooms to the map."""
        size = self.size
        num_rooms = random.randint(3, 5)

        for _ in range(num_rooms):
            w = random.randint(5, 10)
            h = random.randint(5, 10)

            # Ensure within bounds
            if size - w - 2 < 2 or size - h - 2 < 2:
                continue

            x = random.randint(2, size - w - 2)
            y = random.randint(2, size - h - 2)

            # Carve room (set to 0)
            for i in range(y, y + h):
                for j in range(x, x + w):
                    if 0 <= i < size and 0 <= j < size:
                        self.grid[i][j] = 0

            # Add walls around room (type 2, 3, 4)
            wall_type = random.choice([2, 3, 4])
            for i in range(y, y + h):
                if 0 <= i < size:
                    if 0 <= x < size:
                        self.grid[i][x] = wall_type
                    if 0 <= x + w - 1 < size:
                        self.grid[i][x + w - 1] = wall_type
            for j in range(x, x + w):
                if 0 <= j < size:
                    if 0 <= y < size:
                        self.grid[y][j] = wall_type
                    if 0 <= y + h - 1 < size:
                        self.grid[y + h - 1][j] = wall_type

    def _ensure_connectivity(self) -> None:
        """Ensure map connectivity using flood fill."""
        size = self.size
        cx, cy = size // 2, size // 2
        start_x, start_y = -1, -1

        # Find valid start point near center
        for r in range(size // 2):
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                tx = int(cx + math.cos(rad) * r)
                ty = int(cy + math.sin(rad) * r)
                if 0 < tx < size and 0 < ty < size and self.grid[ty][tx] == 0:
                    start_x, start_y = tx, ty
                    break
            if start_x != -1:
                break

        if start_x == -1:
            start_x, start_y = cx, cy
            self.grid[cy][cx] = 0

        # Identify connected region
        queue = [(start_x, start_y)]
        visited = {(start_x, start_y)}

        while queue:
            x, y = queue.pop(0)

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < size
                    and 0 <= ny < size
                    and self.grid[ny][nx] == 0
                    and (nx, ny) not in visited
                ):
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        # Close off unconnected areas
        for i in range(size):
            for j in range(size):
                if self.grid[i][j] == 0 and (j, i) not in visited:
                    self.grid[i][j] = 1

    def is_wall(self, x: float, y: float) -> bool:
        """Check if position contains a wall."""
        map_x = int(x)
        map_y = int(y)
        if 0 <= map_x < self.size and 0 <= map_y < self.size:
            return self.grid[map_y][map_x] != 0
        return True

    def get_wall_type(self, x: float, y: float) -> int:
        """Get the wall type at position."""
        map_x = int(x)
        map_y = int(y)
        if 0 <= map_x < self.size and 0 <= map_y < self.size:
            return self.grid[map_y][map_x]
        return 1
