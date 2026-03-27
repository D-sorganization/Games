"""Map for Force Field game with quality validation."""

from __future__ import annotations

from games.shared.map_base import MapBase

from .constants import DEFAULT_MAP_SIZE


class Map(MapBase):
    """Game map with walls and buildings, validates map quality."""

    def __init__(self, size: int = DEFAULT_MAP_SIZE):
        """Initialize a map with walls and buildings.

        Args:
            size: Map size (default: DEFAULT_MAP_SIZE)
        """
        super().__init__(size, generate=False)
        self._create_validated_map()

    def _create_validated_map(self) -> None:
        """Create map with quality validation (retry up to 20 times)."""
        for _ in range(20):
            # Use parent's create_map logic
            super().create_map()

            # Validate map quality
            if self._is_valid_map():
                break
        # If all attempts fail, keep the last generated map

    def _is_valid_map(self) -> bool:
        """Check if map meets quality criteria (15% walkable area)."""
        size = self.size
        min_walkable = int(size * size * 0.15)

        # Count walkable tiles
        walkable_count = sum(
            1 for i in range(size) for j in range(size) if self.grid[i][j] == 0
        )

        return walkable_count >= min_walkable
