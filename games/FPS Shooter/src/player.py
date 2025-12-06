import math
from typing import TYPE_CHECKING, Dict, Any, List
from . import constants as C

if TYPE_CHECKING:
    from .map import Map
    from .bot import Bot

class Player:
    """Player with position, rotation, and shooting capabilities"""

    def __init__(self, x: float, y: float, angle: float):
        """Initialize player"""
        self.x = x
        self.y = y
        self.angle = angle
        self.health = 100
        self.max_health = 100
        weapon_ammo: Dict[str, Any] = {weapon: C.WEAPONS[weapon].get("ammo", 0) for weapon in C.WEAPONS}
        self.ammo: Dict[str, int] = {weapon: int(weapon_ammo[weapon]) for weapon in C.WEAPONS}
        self.current_weapon = "rifle"
        self.shooting = False
        self.shoot_timer = 0
        self.alive = True

    def move(
        self,
        game_map: "Map",
        bots: List["Bot"],
        forward: bool = True,
        speed: float = C.PLAYER_SPEED,
    ) -> None:
        """Move player forward or backward"""
        dx = math.cos(self.angle) * speed * (1 if forward else -1)
        dy = math.sin(self.angle) * speed * (1 if forward else -1)

        new_x = self.x + dx
        new_y = self.y + dy

        # Check wall collision
        if not game_map.is_wall(new_x, self.y):
            # Check bot collision
            collision = False
            for bot in bots:
                if bot.alive:
                    dist = math.sqrt((new_x - bot.x) ** 2 + (self.y - bot.y) ** 2)
                    if dist < 0.5:
                        collision = True
                        break
            if not collision:
                self.x = new_x

        if not game_map.is_wall(self.x, new_y):
            collision = False
            for bot in bots:
                if bot.alive:
                    dist = math.sqrt((self.x - bot.x) ** 2 + (new_y - bot.y) ** 2)
                    if dist < 0.5:
                        collision = True
                        break
            if not collision:
                self.y = new_y

    def strafe(
        self,
        game_map: "Map",
        bots: List["Bot"],
        right: bool = True,
        speed: float = C.PLAYER_SPEED,
    ) -> None:
        """Strafe left or right"""
        angle = self.angle + math.pi / 2 * (1 if right else -1)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed

        new_x = self.x + dx
        new_y = self.y + dy

        if not game_map.is_wall(new_x, self.y):
            collision = False
            for bot in bots:
                if bot.alive:
                    dist = math.sqrt((new_x - bot.x) ** 2 + (self.y - bot.y) ** 2)
                    if dist < 0.5:
                        collision = True
                        break
            if not collision:
                self.x = new_x

        if not game_map.is_wall(self.x, new_y):
            collision = False
            for bot in bots:
                if bot.alive:
                    dist = math.sqrt((self.x - bot.x) ** 2 + (new_y - bot.y) ** 2)
                    if dist < 0.5:
                        collision = True
                        break
            if not collision:
                self.y = new_y

    def rotate(self, delta: float) -> None:
        """Rotate player view"""
        self.angle += delta
        self.angle %= 2 * math.pi

    def shoot(self) -> bool:
        """Initiate shooting, return True if shot was fired"""
        weapon_data: Dict[str, Any] = C.WEAPONS[self.current_weapon]
        if self.ammo[self.current_weapon] > 0 and self.shoot_timer <= 0:
            self.shooting = True
            self.shoot_timer = int(weapon_data["cooldown"])
            self.ammo[self.current_weapon] -= 1
            return True
        return False

    def switch_weapon(self, weapon: str) -> None:
        """Switch to a different weapon"""
        if weapon in C.WEAPONS:
            self.current_weapon = weapon

    def get_current_weapon_damage(self) -> int:
        """Get damage of current weapon"""
        weapon_data: Dict[str, Any] = C.WEAPONS[self.current_weapon]
        return int(weapon_data["damage"])

    def get_current_weapon_range(self) -> int:
        """Get range of current weapon"""
        weapon_data: Dict[str, Any] = C.WEAPONS[self.current_weapon]
        return int(weapon_data["range"])

    def take_damage(self, damage: int) -> None:
        """Take damage"""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def update(self) -> None:
        """Update player state"""
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shooting = False
