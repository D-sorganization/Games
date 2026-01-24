"""Base class for projectiles with common physics and collision."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

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
        """Initialize projectile.

        Args:
            x: Initial x position
            y: Initial y position
            angle: Direction angle in radians
            damage: Damage dealt on hit
            speed: Movement speed
            is_player: Whether shot by player
            color: RGB color tuple
            size: Projectile size
            weapon_type: Type of weapon (normal, bomb, freezer, etc.)
            z: Initial height (for 3D games)
            vz: Initial vertical velocity
            gravity: Gravity acceleration
        """
        self.x = x
        self.y = y
        self.angle = angle
        self.damage = damage
        self.speed = speed
        self.is_player = is_player
        self.color = color
        self.size = size
        self.weapon_type = weapon_type
        self.alive = True

        # 3D Arc Physics
        self.z = z
        self.vz = vz
        self.gravity = gravity

        # Optional: Secret wall hit tracking
        self.hit_secret_pos: tuple[int, int] | None = None

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
            # Check for secret walls (type 5)
            w_type = game_map.get_wall_type(new_x, new_y)
            if w_type == 5:
                self.hit_secret_pos = (int(new_x), int(new_y))

            self.alive = False
            return

        # Update position
        self.x = new_x
        self.y = new_y
