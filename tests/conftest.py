"""Root conftest with shared fixtures for the games test suite.

All fixtures defined here are automatically available to every test
module under tests/ without explicit import.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Mock Map
# ---------------------------------------------------------------------------
class MockMap:
    """Lightweight map stub satisfying the Map protocol.

    Attributes:
        grid: 2D list where 0 = empty, >0 = wall type.
        width: Horizontal extent of the grid.
        height: Vertical extent of the grid.
        size: Max of width and height (used by some legacy code).
    """

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
        return True

    def get_wall_type(self, x: float, y: float) -> int:
        """Get the wall type at position.

        Args:
            x: X coordinate.
            y: Y coordinate.

        Returns:
            Wall type integer, or 1 for out-of-bounds.
        """
        ix, iy = int(x), int(y)
        if 0 <= ix < self.width and 0 <= iy < self.height:
            return self.grid[iy][ix]
        return 1


# ---------------------------------------------------------------------------
# Mock Entity
# ---------------------------------------------------------------------------
class MockEntity:
    """Lightweight entity stub with position and alive state."""

    def __init__(
        self,
        x: float,
        y: float,
        alive: bool = True,
    ) -> None:
        """Initialize entity.

        Args:
            x: X position.
            y: Y position.
            alive: Whether entity is alive.
        """
        self.x = x
        self.y = y
        self.alive = alive


# ---------------------------------------------------------------------------
# Pre-built map grids
# ---------------------------------------------------------------------------
_OPEN_GRID = [
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

_WALL_GRID = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]


# ---------------------------------------------------------------------------
# Fixtures: Maps
# ---------------------------------------------------------------------------
@pytest.fixture()
def open_map() -> MockMap:
    """A 10x10 map with border walls and open interior."""
    return MockMap([row[:] for row in _OPEN_GRID])


@pytest.fixture()
def wall_map() -> MockMap:
    """A 10x10 map with a wall at position (4, 5)."""
    return MockMap([row[:] for row in _WALL_GRID])


# ---------------------------------------------------------------------------
# Fixtures: Entities
# ---------------------------------------------------------------------------
@pytest.fixture()
def entity_at_center() -> MockEntity:
    """An alive entity at position (5, 5)."""
    return MockEntity(5.0, 5.0)


@pytest.fixture()
def dead_entity() -> MockEntity:
    """A dead entity at position (5.3, 5.0)."""
    return MockEntity(5.3, 5.0, alive=False)


# ---------------------------------------------------------------------------
# Fixtures: Game Constants (for PlayerBase tests)
# ---------------------------------------------------------------------------
DEFAULT_WEAPONS_CONFIG: dict[str, dict[str, Any]] = {
    "pistol": {
        "name": "Pistol",
        "damage": 25,
        "range": 15,
        "ammo": 999,
        "cooldown": 10,
        "clip_size": 12,
        "reload_time": 60,
        "key": "1",
    },
    "rifle": {
        "name": "Rifle",
        "damage": 20,
        "range": 25,
        "ammo": 999,
        "cooldown": 20,
        "clip_size": 30,
        "reload_time": 120,
        "key": "2",
    },
    "shotgun": {
        "name": "Shotgun",
        "damage": 20,
        "range": 12,
        "ammo": 999,
        "cooldown": 30,
        "clip_size": 2,
        "reload_time": 80,
        "pellets": 8,
        "spread": 0.15,
        "key": "3",
    },
}

DEFAULT_CONSTANTS_ATTRS: dict[str, Any] = {
    "WEAPONS": DEFAULT_WEAPONS_CONFIG,
    "SHIELD_MAX_DURATION": 600,
    "BOMBS_START": 1,
    "PITCH_LIMIT": 1.0,
    "SECONDARY_COOLDOWN": 60,
    "SHIELD_COOLDOWN_NORMAL": 60,
    "BOMB_COOLDOWN": 300,
    "SHIELD_COOLDOWN_DEPLETED": 300,
}


def make_constants(**overrides: Any) -> SimpleNamespace:
    """Create a mock constants module.

    Args:
        **overrides: Key-value pairs to override defaults.

    Returns:
        A SimpleNamespace acting as a constants module.
    """
    attrs = {**DEFAULT_CONSTANTS_ATTRS, **overrides}
    return SimpleNamespace(**attrs)


@pytest.fixture()
def game_constants() -> SimpleNamespace:
    """Default game constants as a SimpleNamespace."""
    return make_constants()


# ---------------------------------------------------------------------------
# Fixtures: PlayerBase
# ---------------------------------------------------------------------------
@pytest.fixture()
def player() -> Any:
    """A PlayerBase initialized at (5, 5) with default weapons.

    Returns:
        Initialized PlayerBase instance.
    """
    from games.shared.player_base import PlayerBase

    constants = make_constants()
    return PlayerBase(
        x=5.0,
        y=5.0,
        angle=0.0,
        weapons_config=constants.WEAPONS,
        constants=constants,
    )
