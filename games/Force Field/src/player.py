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
        self.is_moving = False  # Track movement for bobbing

        # Weapon State
        self.weapon_state: Dict[str, Dict[str, Any]] = {}
        for w_name, w_data in C.WEAPONS.items():
            self.weapon_state[w_name] = {
                "clip": w_data.get("clip_size", 999),
                "heat": 0.0,
                "reloading": False,
                "reload_timer": 0,
                "overheated": False,
                "overheat_timer": 0
            }

        # Keep tracking total ammo (reserves) if we want,
        # but user request implies specific mechanics per gun
        # For now, we assume "ammo" in constants refers to reserves.
        self.ammo: Dict[str, int] = {w: C.WEAPONS[w]["ammo"] for w in C.WEAPONS}

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
            # Shield/Zoom blocks movement? Maybe let shield allow movement but slower?
            # Doom style usually allows movement always.
            # I will unblock movement for Shield but keep it blocked/slow for Zoom.
            if self.zoomed:
                return
            if self.shield_active:
                speed *= 0.8

        # Doom straferunning enabled (simple vector addition handled by caller if both pressed)
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
        if self.zoomed:
            return

        # Slightly faster strafe for Doom feel? Standard speed is fine.
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
        weapon_data = C.WEAPONS[self.current_weapon]
        w_state = self.weapon_state[self.current_weapon]

        # 1. Check Global Cooldown
        if self.shoot_timer > 0:
            return False

        # 2. Check Reloading / Overheat
        if w_state["reloading"]:
            return False
        if w_state["overheated"]:
            return False

        # 3. Check Clip / Heat
        if self.current_weapon == "plasma":
            # Heat check
            pass # Fired below
        elif w_state["clip"] <= 0:
            self.reload()
            return False

        self.shooting = True
        self.shoot_timer = int(weapon_data["cooldown"])

        # Consumables
        if self.current_weapon == "plasma":
            w_state["heat"] += weapon_data.get("heat_per_shot", 0.0)
            if w_state["heat"] >= weapon_data.get("max_heat", 1.0):
                w_state["overheated"] = True
                w_state["overheat_timer"] = weapon_data.get("overheat_penalty", 180)
        else:
            w_state["clip"] -= 1

        return True

    def reload(self) -> None:
        """Start reload process"""
        w_data = C.WEAPONS[self.current_weapon]
        w_state = self.weapon_state[self.current_weapon]

        if w_state["reloading"] or w_state["overheated"]:
            return

        if self.current_weapon == "plasma":
            # Plasma doesn't reload manually, it cools down
            return

        if w_state["clip"] < w_data["clip_size"]:
             w_state["reloading"] = True
             w_state["reload_timer"] = w_data.get("reload_time", 60)

    def switch_weapon(self, weapon: str) -> None:
        """Switch to a different weapon"""
        if weapon in C.WEAPONS:
            self.current_weapon = weapon
            # Cancel reload on switch? Or background reload?
            # Classic Doom: instant switch usually, reloading was animation.
            # We'll cancel reload for now to avoid complexity or exploit.
            self.weapon_state[weapon]["reloading"] = False

    def get_current_weapon_damage(self) -> int:
        """Get damage of current weapon"""
        return int(C.WEAPONS[self.current_weapon]["damage"])

    def get_current_weapon_range(self) -> int:
        """Get range of current weapon"""
        return int(C.WEAPONS[self.current_weapon]["range"])

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
            return True
        return False

    def update(self) -> None:
        """Update player state (timers, etc)"""
        # Global shoot timer
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        else:
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
                self.shield_active = False
                self.shield_recharge_delay = C.SHIELD_COOLDOWN_DEPLETED
        elif self.shield_recharge_delay > 0:
            self.shield_recharge_delay -= 1
        elif self.shield_timer < C.SHIELD_MAX_DURATION:
            self.shield_timer += (
                2  # Recharge rate: +2 per frame; 0 to 600 in 300 frames (5 seconds at 60 FPS)
            )
            self.shield_timer = min(self.shield_timer, C.SHIELD_MAX_DURATION)

        # Update Weapons (Reloads, Heat)
        for w_name, w_state in self.weapon_state.items():
            # Reloading
            if w_state["reloading"]:
                w_state["reload_timer"] -= 1
                if w_state["reload_timer"] <= 0:
                    w_state["reloading"] = False
                    w_state["clip"] = C.WEAPONS[w_name]["clip_size"]

            # Plasma Heat / Overheat
            if w_name == "plasma":
                if w_state["overheated"]:
                    w_state["overheat_timer"] -= 1
                    # Cool down while overheated? Or fixed penalty?
                    # Usually fixed wait. We'll linearly cool it down too so visual bar goes down
                    penalty_time = C.WEAPONS[w_name].get("overheat_penalty", 180)
                    cool_amount = C.WEAPONS[w_name]["max_heat"] / penalty_time
                    w_state["heat"] = max(0.0, w_state["heat"] - cool_amount)

                    if w_state["overheat_timer"] <= 0:
                        w_state["overheated"] = False
                        w_state["heat"] = 0.0
                elif w_state["heat"] > 0:
                    w_state["heat"] -= C.WEAPONS[w_name].get("cooling_rate", 0.01)
                    w_state["heat"] = max(0.0, w_state["heat"])

    def can_secondary_fire(self) -> bool:
        """Check if secondary fire is ready"""
        return self.secondary_cooldown <= 0

    def fire_secondary(self) -> bool:
        """Execute secondary fire"""
        if self.can_secondary_fire():
            self.secondary_cooldown = C.SECONDARY_COOLDOWN
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
