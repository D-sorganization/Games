from __future__ import annotations

import math
from typing import Protocol


class MapProtocol(Protocol):
    """Protocol for maps used in projectile updates."""

    def is_wall(self, x: float, y: float) -> bool:
        """Return True if the coordinate is a wall."""
        return False

    def get_wall_type(self, x: float, y: float) -> int:
        """Return the wall type at the coordinate."""
        return 0


class Projectile:
    """Projectile shot by bots or player."""

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
    ) -> None:
        """Initialize projectile."""
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
        self.hit_secret_pos: tuple[int, int] | None = None

    def update(self, game_map: MapProtocol) -> None:
        """Update projectile position."""
        if not self.alive:
            return

        dx = math.cos(self.angle) * self.speed
        dy = math.sin(self.angle) * self.speed

        new_x = self.x + dx
        new_y = self.y + dy

        # Update height
        self.z += self.vz
        self.vz -= self.gravity

        # Bounds check / Ground Hit
        if self.z <= 0:
            self.z = 0
            if self.weapon_type in {"bomb", "freezer"}:
                self.alive = False
                return

        # Check wall collision
        if game_map.is_wall(new_x, new_y):
            wall_type = game_map.get_wall_type(new_x, new_y)
            if wall_type == 5:
                self.hit_secret_pos = (int(new_x), int(new_y))
            self.alive = False
            return

        self.x = new_x
        self.y = new_y
