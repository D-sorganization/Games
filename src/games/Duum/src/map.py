"""Map for Duum game."""

from __future__ import annotations

from games.shared.map_base import MapBase

from .constants import DEFAULT_MAP_SIZE


class Map(MapBase):
    """Game map with walls and buildings."""

    def __init__(self, size: int = DEFAULT_MAP_SIZE):
        """Initialize a map with walls and buildings.

        Args:
            size: Map size (default: DEFAULT_MAP_SIZE)
        """
        super().__init__(size)
