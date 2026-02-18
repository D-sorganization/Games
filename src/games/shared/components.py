"""Composable component mixins for game entities.

Provides lightweight mixins that can be composed via multiple inheritance
to build game entities with specific capabilities. Uses cooperative
__init__ with **kwargs for clean MRO chaining.

Usage:
    from games.shared.components import Positioned, HasHealth, Collidable

    class Pickup(Positioned, Collidable, Animated):
        def __init__(self, x, y):
            super().__init__(x=x, y=y, radius=0.5)
"""

from __future__ import annotations

import math
from typing import Any

from games.shared.contracts import (
    validate_non_negative,
    validate_positive,
    validate_range,
)


class Positioned:
    """Mixin: entity has a 2D position."""

    def __init__(self, x: float = 0.0, y: float = 0.0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.x = x
        self.y = y

    def distance_to(self, other: Positioned) -> float:
        """Euclidean distance to another positioned entity."""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def move_toward(self, target_x: float, target_y: float, speed: float) -> None:
        """Move toward a target point, capped by speed."""
        validate_non_negative(speed, "speed")
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 1e-6:
            step = min(speed, dist)
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step


class HasHealth:
    """Mixin: entity has health that can be damaged and healed."""

    def __init__(self, max_health: float = 100.0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        validate_positive(max_health, "max_health")
        self.health = max_health
        self.max_health = max_health
        self.alive = True

    def take_damage(self, amount: float) -> bool:
        """Apply damage. Returns True if this killed the entity."""
        validate_non_negative(amount, "damage")
        if not self.alive:
            return False
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False
            return True
        return False

    def heal(self, amount: float) -> None:
        """Restore health, capped at max_health."""
        validate_non_negative(amount, "heal_amount")
        if self.alive:
            self.health = min(self.max_health, self.health + amount)

    @property
    def health_fraction(self) -> float:
        """Health as a 0.0-1.0 fraction."""
        return self.health / self.max_health if self.max_health > 0 else 0.0


class Collidable:
    """Mixin: entity has a collision radius for overlap checks."""

    def __init__(self, radius: float = 0.5, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        validate_positive(radius, "radius")
        self.collision_radius = radius

    def overlaps(self, other: Collidable) -> bool:
        """Check if this entity overlaps another (requires Positioned)."""
        if not isinstance(self, Positioned) or not isinstance(other, Positioned):
            return False
        dist = self.distance_to(other)
        return dist < (self.collision_radius + other.collision_radius)


class Animated:
    """Mixin: entity has animation state."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.animation_timer: float = 0.0
        self.animation_speed: float = 1.0
        self.current_animation: str = "idle"

    def advance_animation(self, dt: float = 1.0) -> None:
        """Advance animation timer by dt * speed."""
        validate_non_negative(dt, "dt")
        self.animation_timer += dt * self.animation_speed

    def set_animation(self, name: str) -> None:
        """Switch to a new animation, resetting the timer."""
        if name != self.current_animation:
            self.current_animation = name
            self.animation_timer = 0.0


class HasVelocity:
    """Mixin: entity has velocity for physics updates."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.vx: float = 0.0
        self.vy: float = 0.0

    def apply_velocity(self) -> None:
        """Move position by velocity (requires Positioned)."""
        if isinstance(self, Positioned):
            self.x += self.vx
            self.y += self.vy

    def apply_friction(self, factor: float = 0.9) -> None:
        """Reduce velocity by a friction factor."""
        validate_range(factor, 0.0, 1.0, "friction_factor")
        self.vx *= factor
        self.vy *= factor
