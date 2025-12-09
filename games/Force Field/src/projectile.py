import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .map import Map


class Projectile:
    """Projectile shot by bots or player"""

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
    ):
        """Initialize projectile"""
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

    def update(self, game_map: "Map") -> None:
        """Update projectile position"""
        if not self.alive:
            return

        dx = math.cos(self.angle) * self.speed
        dy = math.sin(self.angle) * self.speed

        new_x = self.x + dx
        new_y = self.y + dy

        # Check wall collision
        if game_map.is_wall(new_x, new_y):
            self.alive = False
            return

        self.x = new_x
        self.y = new_y
