"""Tests for the games.shared.interfaces module.

Verifies that Protocol types are runtime-checkable and that
concrete implementations satisfy them.
"""

from __future__ import annotations

from typing import Any

import pytest

from games.shared.interfaces import Bot, Map, Player, Projectile, WorldParticle


# ---------------------------------------------------------------------------
# Concrete stubs that should satisfy protocols
# ---------------------------------------------------------------------------
class ConcreteMap:
    """A minimal Map protocol implementation."""

    def __init__(self) -> None:
        """Initialize a tiny 3x3 map."""
        self.grid: list[list[int]] = [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
        ]
        self.size = 3

    @property
    def width(self) -> int:
        """Return width."""
        return 3

    @property
    def height(self) -> int:
        """Return height."""
        return 3

    def is_wall(self, x: float, y: float) -> bool:
        """Check wall."""
        ix, iy = int(x), int(y)
        if 0 <= ix < 3 and 0 <= iy < 3:
            return self.grid[iy][ix] > 0
        return True

    def get_wall_type(self, x: float, y: float) -> int:
        """Get wall type."""
        ix, iy = int(x), int(y)
        if 0 <= ix < 3 and 0 <= iy < 3:
            return self.grid[iy][ix]
        return 1


class ConcretePlayer:
    """A minimal Player protocol implementation."""

    def __init__(self) -> None:
        """Initialize player stub."""
        self.x = 1.5
        self.y = 1.5
        self.angle = 0.0
        self.pitch = 0.0
        self.zoomed = False
        self.is_moving = False


class ConcreteBot:
    """A minimal Bot protocol implementation."""

    def __init__(self) -> None:
        """Initialize bot stub."""
        self.x = 2.0
        self.y = 2.0
        self.z = 0.0
        self.alive = True
        self.removed = False
        self.dead = False
        self.death_timer = 0.0
        self.disintegrate_timer = 0.0
        self.enemy_type = "basic"
        self.type_data: dict[str, Any] = {
            "color": (255, 0, 0),
            "health_mult": 1.0,
        }
        self.walk_animation = 0.0
        self.shoot_animation = 0.0
        self.frozen = False
        self.mouth_open = False

    def take_damage(self, damage: int, is_headshot: bool = False) -> bool:
        """Handle damage."""
        return True


class ConcreteProjectile:
    """A minimal Projectile protocol implementation."""

    def __init__(self) -> None:
        """Initialize projectile stub."""
        self.x = 3.0
        self.y = 3.0
        self.z = 0.5
        self.alive = True
        self.size = 0.1
        self.color = (255, 255, 0)
        self.weapon_type = "pistol"
        self.damage = 25


class ConcreteWorldParticle:
    """A minimal WorldParticle protocol implementation."""

    def __init__(self) -> None:
        """Initialize particle stub."""
        self.x = 1.0
        self.y = 1.0
        self.z = 0.0
        self.alive = True
        self.size = 0.05
        self.color = (255, 0, 0)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestProtocolConformance:
    """Verify that concrete classes satisfy runtime protocols."""

    @pytest.mark.parametrize(
        "instance,protocol",
        [
            (ConcreteMap(), Map),
            (ConcretePlayer(), Player),
            (ConcreteBot(), Bot),
            (ConcreteProjectile(), Projectile),
            (ConcreteWorldParticle(), WorldParticle),
        ],
        ids=["Map", "Player", "Bot", "Projectile", "WorldParticle"],
    )
    def test_protocol_isinstance_check(self, instance: Any, protocol: type) -> None:
        """Concrete implementation should pass isinstance checks."""
        assert isinstance(instance, protocol)


class TestMapProtocol:
    """Tests for the Map protocol behavior."""

    def test_map_wall_check(self) -> None:
        """ConcreteMap should correctly identify walls."""
        m = ConcreteMap()
        assert m.is_wall(0.0, 0.0)
        assert not m.is_wall(1.5, 1.5)

    def test_map_properties(self) -> None:
        """Map width and height should be consistent."""
        m = ConcreteMap()
        assert m.width == 3
        assert m.height == 3

    def test_map_out_of_bounds_is_wall(self) -> None:
        """Out-of-bounds positions should be treated as walls."""
        m = ConcreteMap()
        assert m.is_wall(-1.0, 0.0)
        assert m.is_wall(0.0, 10.0)

    def test_map_get_wall_type(self) -> None:
        """Should return correct wall type."""
        m = ConcreteMap()
        assert m.get_wall_type(0.0, 0.0) == 1
        assert m.get_wall_type(1.0, 1.0) == 0


class TestBotProtocol:
    """Tests for the Bot protocol behavior."""

    def test_bot_take_damage(self) -> None:
        """Bot should accept damage calls."""
        bot = ConcreteBot()
        result = bot.take_damage(25)
        assert result is True

    def test_bot_take_damage_headshot(self) -> None:
        """Bot should accept headshot damage."""
        bot = ConcreteBot()
        result = bot.take_damage(50, is_headshot=True)
        assert result is True

    def test_bot_attributes(self) -> None:
        """Bot should have all required attributes."""
        bot = ConcreteBot()
        assert bot.alive is True
        assert bot.enemy_type == "basic"
        assert bot.frozen is False
