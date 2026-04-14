"""Base class for projectiles with common physics and collision."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from games.shared.contracts import validate_non_negative, validate_positive

if TYPE_CHECKING:
    from .interfaces import Map


class ProjectileBase:
    """Base class for projectiles shot by bots or players."""

    def __init__(  # noqa: PLR0913
        self,
        x: float,
        y: float,
        angle: float,
        damage: int,
        speed: float,
        is_player: bool = False,
        color: tuple[int, int, int] = (255, 0, 0),
        size: float = 0.2,
        weapon_type: str = "normal",
        z: float = 0.5,
        vz: float = 0.0,
        gravity: float = 0.0,
    ):
        """Initialize projectile with position, damage, physics, and appearance."""
        validate_non_negative(damage, "damage")
        validate_positive(speed, "speed")
        self._init_core(x, y, angle, damage, speed, is_player, color, size, weapon_type)
        self._init_arc_physics(z, vz, gravity)

    def _init_core(
        self,
        x: float,
        y: float,
        angle: float,
        damage: int,
        speed: float,
        is_player: bool,
        color: tuple[int, int, int],
        size: float,
        weapon_type: str,
    ) -> None:
        """Set core position, combat, and appearance attributes."""
        self.x, self.y, self.angle = x, y, angle
        self.damage, self.speed = damage, speed
        self.is_player = is_player
        self.color, self.size, self.weapon_type = color, size, weapon_type
        self.alive = True
        self.hit_hidden_pos: tuple[int, int] | None = None

    def _init_arc_physics(self, z: float, vz: float, gravity: float) -> None:
        """Set 3D arc physics attributes."""
        self.z = z
        self.vz = vz
        self.gravity = gravity

    def update(self, game_map: Map) -> None:
        """Update projectile position and check collisions.

        Args:
            game_map: Game map for collision detection
        """
        if not self.alive:
            return

        # Calculate movement
        dx = math.cos(self.angle) * self.speed
        dy = math.sin(self.angle) * self.speed

        new_x = self.x + dx
        new_y = self.y + dy

        # Update height (3D physics)
        self.z += self.vz
        self.vz -= self.gravity

        # Ground collision
        if self.z <= 0:
            self.z = 0
            if self.weapon_type in ("bomb", "freezer"):
                self.alive = False
                return

        # Wall collision
        if game_map.is_wall(new_x, new_y):
            # Check for hidden walls (type 5)
            w_type = game_map.get_wall_type(new_x, new_y)
            if w_type == 5:
                self.hit_hidden_pos = (int(new_x), int(new_y))

            self.alive = False
            return

        # Update position
        self.x = new_x
        self.y = new_y
