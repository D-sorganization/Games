from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, cast

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
        self.pitch = 0.0  # Vertical look offset
        self.health = 100
        self.max_health = 100
        self.is_moving = False  # Track movement for bobbing

        # Weapon State
        self.weapon_state: dict[str, dict[str, Any]] = {}
        for w_name, w_data in C.WEAPONS.items():
            self.weapon_state[w_name] = {
                "clip": w_data.get("clip_size", 999),
                "heat": 0.0,
                "reloading": False,
                "reload_timer": 0,
                "overheated": False,
                "overheat_timer": 0,
            }

        # Keep tracking total ammo (reserves) if we want,
        # but user request implies specific mechanics per gun
        # For now, we assume "ammo" in constants refers to reserves.
        self.ammo: dict[str, int] = {
            w: int(cast("int", C.WEAPONS[w]["ammo"])) for w in C.WEAPONS
        }

        self.current_weapon = "rifle"
        self.shooting = False
        self.shoot_timer = 0
        self.alive = True
        self.shield_active = False
        self.shield_timer = C.SHIELD_MAX_DURATION
        self.shield_recharge_delay = 0
        self.bomb_cooldown = 0
        self.bombs = 1  # Start with 1 bomb
        self.secondary_cooldown = 0
        self.zoomed = False
        self.god_mode = False

        # Weapon Sway / Turn tracking
        self.frame_turn = 0.0
        self.sway_amount = 0.0

        # Stamina
        self.stamina = 100.0
        self.max_stamina = 100.0
        self.stamina_recharge_delay = 0

    def move(
        self,
        game_map: Map,
        bots: list[Bot],
        forward: bool = True,
        speed: float = C.PLAYER_SPEED,
    ) -> None:
        """Move player forward or backward"""
        if self.shield_active or self.zoomed:
            if self.zoomed:
                return
            if self.shield_active:
                speed *= 0.8

        dx = math.cos(self.angle) * speed * (1 if forward else -1)
        dy = math.sin(self.angle) * speed * (1 if forward else -1)

        from .utils import try_move_entity

        try_move_entity(self, dx, dy, game_map, bots, radius=0.5)

    def strafe(
        self,
        game_map: Map,
        bots: list[Bot],
        right: bool = True,
        speed: float = C.PLAYER_SPEED,
    ) -> None:
        """Strafe left or right"""
        if self.zoomed:
            return

        if self.shield_active:
            speed *= 0.8

        angle = self.angle + math.pi / 2 * (1 if right else -1)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed

        from .utils import try_move_entity

        try_move_entity(self, dx, dy, game_map, bots, radius=0.5)

    def rotate(self, delta: float) -> None:
        """Rotate player view"""
        self.angle += delta
        self.angle %= 2 * math.pi
        self.frame_turn += delta

    def pitch_view(self, delta: float) -> None:
        """Change vertical view angle (pitch)"""
        self.pitch += delta
        self.pitch = max(-C.PITCH_LIMIT, min(C.PITCH_LIMIT, self.pitch))

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
        if self.current_weapon != "plasma" and w_state["clip"] <= 0:
            self.reload()
            return False

        self.shooting = True
        self.shoot_timer = int(cast("int", weapon_data["cooldown"]))

        # Consumables
        if self.current_weapon == "plasma":
            w_state["heat"] += weapon_data.get("heat_per_shot", 0.0)
            if w_state["heat"] >= weapon_data.get("max_heat", 1.0):
                w_state["overheated"] = True
                w_state["overheat_timer"] = weapon_data.get("overheat_penalty", 180)
        else:
            w_state["clip"] -= 1

        # Auto-reload if empty (Shotgun/others)
        if self.current_weapon != "plasma" and w_state["clip"] <= 0:
            self.reload()

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
            # Cancel reload of the PREVIOUS weapon to avoid pause/resume exploits.
            if self.current_weapon in self.weapon_state:
                self.weapon_state[self.current_weapon]["reloading"] = False

            self.current_weapon = weapon
            # Also ensure new weapon is clean (redundant but safe)
            self.weapon_state[weapon]["reloading"] = False

    def get_current_weapon_damage(self) -> int:
        """Get damage of current weapon"""
        return int(cast("int", C.WEAPONS[self.current_weapon]["damage"]))

    def get_current_weapon_range(self) -> int:
        """Get range of current weapon"""
        return int(cast("int", C.WEAPONS[self.current_weapon]["range"]))

    def take_damage(self, damage: int) -> None:
        """Take damage"""
        if self.shield_active or self.god_mode:
            return
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def activate_bomb(self) -> bool:
        """Try to drop a bomb"""
        if self.bomb_cooldown <= 0 and self.bombs > 0:
            self.bombs -= 1
            self.bomb_cooldown = C.BOMB_COOLDOWN
            self.shield_active = True  # Auto activate shield
            return True
        return False

    def update(self) -> None:
        """Update player state (timers, etc)"""
        # Update Sway
        # Smoothly interpolate sway for better feel
        self.sway_amount = self.sway_amount * 0.8 + self.frame_turn * 0.2
        self.frame_turn = 0.0  # Reset for next frame accumulation

        # Global shoot timer
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        else:
            self.shooting = False

        if self.bomb_cooldown > 0:
            self.bomb_cooldown -= 1

        if self.secondary_cooldown > 0:
            self.secondary_cooldown -= 1

        # Stamina Regen
        if self.stamina_recharge_delay > 0:
            self.stamina_recharge_delay -= 1
        elif self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + 0.5)

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
                2  # Recharge rate: +2 per frame; 0 to 600 in 300 frames
                # (5 seconds at 60 FPS)
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

            # Auto-reload if current weapon is empty and not doing anything
            if (
                w_name == self.current_weapon
                and w_name != "plasma"
                and w_state["clip"] <= 0
                and not w_state["reloading"]
            ):
                self.reload()

            # Plasma Heat / Overheat
            if w_name == "plasma":
                if w_state["overheated"]:
                    w_state["overheat_timer"] -= 1
                    # Cool down while overheated? Or fixed penalty?
                    # Usually fixed wait. We'll linearly cool it down too
                    # so visual bar goes down
                    oh_penalty = C.WEAPONS[w_name].get("overheat_penalty", 180)
                    penalty_time = int(cast("int", oh_penalty))
                    max_heat = float(cast("float", C.WEAPONS[w_name]["max_heat"]))
                    cool_amount = max_heat / penalty_time
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
