from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Dict, List

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .bot import Bot
    from .map import Map


class Player:
    """Player with position, rotation, and shooting capabilities"""

    def __init__(self, x: float, y: float, angle: float):
        """Initialize player"""
        self.x = x
        self.y = y
        self.angle = angle
        self.health = 100
        self.max_health = 100
        self.lives = C.DEFAULT_LIVES
        weapon_ammo: Dict[str, Any] = {
            weapon: C.WEAPONS[weapon].get("ammo", 0) for weapon in C.WEAPONS
        }
        self.ammo: Dict[str, int] = {weapon: int(weapon_ammo[weapon]) for weapon in C.WEAPONS}
        self.current_weapon = "rifle"
        self.shooting = False
        self.shoot_timer = 0
        self.alive = True
        self.shield_active = False
        self.shield_timer = C.SHIELD_MAX_DURATION
        self.shield_recharge_delay = 0
        self.bomb_cooldown = 0
        self.secondary_cooldown = 0
        self.zoomed = False

    def move(
        self,
        game_map: Map,
        bots: List[Bot],
        forward: bool = True,
        speed: float = C.PLAYER_SPEED,
    ) -> None:
        """Move player forward or backward"""
        if self.shield_active or self.zoomed:
            # Shield/Zoom blocks movement
            return

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
        game_map: Map,
        bots: List[Bot],
        right: bool = True,
        speed: float = C.PLAYER_SPEED,
    ) -> None:
        """Strafe left or right"""
        if self.shield_active or self.zoomed:
            return

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
        if self.shield_active:
            return
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def activate_bomb(self) -> bool:
        """Try to drop a bomb"""
        if self.bomb_cooldown <= 0:
            self.bomb_cooldown = C.BOMB_COOLDOWN
            self.shield_active = True  # Auto activate shield
            # Don't deplete shield for this auto-activation or sets logic elsewhere?
            # User said: "activate the shield and a bomb drops"
            return True
        return False

    def update(self) -> None:
        """Update player state"""
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shooting = False

        if self.bomb_cooldown > 0:
            self.bomb_cooldown -= 1

        if self.secondary_cooldown > 0:
            self.secondary_cooldown -= 1

        # Shield Logic
        if self.shield_active:
            if self.shield_timer > 0:
                self.shield_timer -= 1
            else:
                # Run out
                self.shield_active = False
                self.shield_recharge_delay = C.SHIELD_COOLDOWN_DEPLETED
        # Recharge logic
        elif self.shield_recharge_delay > 0:
            self.shield_recharge_delay -= 1
        elif self.shield_timer < C.SHIELD_MAX_DURATION:
            self.shield_timer += 2  # Recharge rate: +2 per frame; 0 to 600 in 300 frames (5 seconds at 60 FPS)
            self.shield_timer = min(self.shield_timer, C.SHIELD_MAX_DURATION)

    def can_secondary_fire(self) -> bool:
        """Check if secondary fire is ready"""
        return self.secondary_cooldown <= 0 and self.ammo[self.current_weapon] > 0

    def fire_secondary(self) -> bool:
        """Execute secondary fire"""
        if self.can_secondary_fire():
            self.secondary_cooldown = C.SECONDARY_COOLDOWN
            if self.ammo[self.current_weapon] >= 1:
                self.ammo[self.current_weapon] -= 1
            return True
        return False

    def set_shield(self, active: bool) -> None:
        """Set shield state from input"""
        if self.shield_recharge_delay > 0:
            self.shield_active = False
            return

        if active and self.shield_timer > 0:
            self.shield_active = True
        else:
            if self.shield_active:
                # Was active, now stopping
                self.shield_recharge_delay = C.SHIELD_COOLDOWN_NORMAL
            self.shield_active = False
