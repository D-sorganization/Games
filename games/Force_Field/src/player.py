from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .bot import Bot
    from .custom_types import WeaponData
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

        # Dash Constants
        self.DASH_SPEED_MULT = 2.5
        self.DASH_STAMINA_COST = 20
        self.DASH_DURATION = 10
        self.DASH_COOLDOWN = 60

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
                "spin_timer": 0,
            }

        # Keep tracking total ammo (reserves) if we want,
        # but user request implies specific mechanics per gun
        # For now, we assume "ammo" in constants refers to reserves.
        self.ammo: dict[str, int] = {w: int(C.WEAPONS[w]["ammo"]) for w in C.WEAPONS}

        # Melee attack system
        self.melee_cooldown = 0
        self.melee_active = False
        self.melee_timer = 0

        # Invincibility system
        self.invincible = True  # Start invincible
        self.invincibility_timer = 300  # 5 seconds at 60 FPS
        self.respawn_delay = 0
        self.respawning = False

        self.current_weapon = "rifle"
        self.shooting = False
        self.shoot_timer = 0
        self.alive = True
        self.shield_active = False
        self.shield_timer = C.SHIELD_MAX_DURATION
        self.shield_recharge_delay = 0
        self.bomb_cooldown = 0
        self.bombs = C.BOMBS_START
        self.secondary_cooldown = 0
        self.zoomed = False
        self.god_mode = False

        # Weapon Sway / Turn tracking
        self.frame_turn = 0.0
        self.sway_amount = 0.0
        self.sway_timer = 0

        # Stamina
        self.stamina = 100.0
        self.max_stamina = 100.0
        self.stamina_recharge_delay = 0

        # Dash mechanics
        self.dash_cooldown = 0
        self.dash_active = False
        self.dash_timer = 0

        # Visual Effects
        self.damage_flash_timer = 0

    def move(
        self,
        game_map: Map,
        bots: list[Bot],
        forward: bool = True,
        speed: float = C.PLAYER_SPEED,
    ) -> None:
        """Move player forward or backward"""
        if self.zoomed:
            return  # No movement when zoomed
        if self.shield_active:
            return  # No movement when shield is active (as per README)

        current_speed = speed
        if self.dash_active:
            current_speed *= C.DASH_SPEED_MULT

        dx = math.cos(self.angle) * current_speed * (1 if forward else -1)
        dy = math.sin(self.angle) * current_speed * (1 if forward else -1)

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
            return  # No movement when zoomed

        if self.shield_active:
            return  # No movement when shield is active

        current_speed = speed
        if self.dash_active:
            current_speed *= C.DASH_SPEED_MULT

        angle = self.angle + math.pi / 2 * (1 if right else -1)
        dx = math.cos(angle) * current_speed
        dy = math.sin(angle) * current_speed

        from .utils import try_move_entity

        try_move_entity(self, dx, dy, game_map, bots, radius=0.5)

    def dash(self) -> None:
        """Attempt to perform a dash."""
        if self.dash_cooldown <= 0 and self.stamina >= C.DASH_STAMINA_COST:
            self.stamina -= C.DASH_STAMINA_COST
            self.dash_active = True
            self.dash_timer = C.DASH_DURATION
            self.dash_cooldown = C.DASH_COOLDOWN
            self.stamina_recharge_delay = C.DASH_COOLDOWN

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
        weapon_data: WeaponData = C.WEAPONS[self.current_weapon]
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

        # Minigun Spin-up logic
        # If we are here, we are attempting to shoot.
        if self.current_weapon == "minigun":
            w_state["firing_active"] = True
            spin_up = int(weapon_data.get("spin_up_time", 30))
            if w_state["spin_timer"] < spin_up:
                w_state["spin_timer"] += 2  # Charge up
                return False  # Not firing yet
            # Once spun up, continue firing normally
        else:
            # For non-minigun weapons, ensure spin is 0 (just in case)
            w_state["spin_timer"] = 0

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

        # Auto-reload if empty (Shotgun/others)
        if self.current_weapon != "plasma" and w_state["clip"] <= 0:
            self.reload()

        return True

    def reload(self) -> None:
        """Start reload process"""
        w_data: WeaponData = C.WEAPONS[self.current_weapon]
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
        return int(C.WEAPONS[self.current_weapon]["damage"])

    def get_current_weapon_range(self) -> int:
        """Get range of current weapon"""
        return int(C.WEAPONS[self.current_weapon]["range"])

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

        # Idle Sway (Breathing)
        if not self.is_moving:
            self.sway_timer += 1
            # Small figure-8 sway
            sway_pitch = math.sin(self.sway_timer * 0.03) * 2.0
            sway_angle = math.cos(self.sway_timer * 0.015) * 0.001

            self.pitch += sway_pitch * 0.05
            self.angle += sway_angle

            # Constrain pitch
            self.pitch = max(-C.PITCH_LIMIT, min(C.PITCH_LIMIT, self.pitch))

        # Dash logic
        if self.dash_active:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.dash_active = False

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # Global shoot timer
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        else:
            self.shooting = False
            # Spin down minigun
            if self.current_weapon == "minigun":
                w_state = self.weapon_state["minigun"]
                if w_state["spin_timer"] > 0:
                    w_state["spin_timer"] -= 1

        if self.bomb_cooldown > 0:
            self.bomb_cooldown -= 1

        if self.secondary_cooldown > 0:
            self.secondary_cooldown -= 1

        # Melee attack timers
        if self.melee_cooldown > 0:
            self.melee_cooldown -= 1

        if self.melee_timer > 0:
            self.melee_timer -= 1
            if self.melee_timer <= 0:
                self.melee_active = False

        # Invincibility timer
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        # Respawn delay
        if self.respawn_delay > 0:
            self.respawn_delay -= 1
            if self.respawn_delay <= 0:
                self.respawning = False
                self.alive = True
                self.health = self.max_health
                self.invincible = True
                self.invincibility_timer = 300  # 5 seconds of invincibility

        # Visual Effects
        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= 1

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
                    # Apply linear cooldown during overheat penalty phase
                    # to provide visual feedback via the heat bar.
                    oh_penalty = C.WEAPONS[w_name].get("overheat_penalty", 180)
                    penalty_time = int(oh_penalty)
                    if penalty_time > 0:
                        max_heat = float(C.WEAPONS[w_name]["max_heat"])
                        cool_amount = max_heat / penalty_time
                        w_state["heat"] = max(0.0, w_state["heat"] - cool_amount)

                    if w_state["overheat_timer"] <= 0:
                        w_state["overheated"] = False
                        w_state["heat"] = 0.0
                elif w_state["heat"] > 0:
                    w_state["heat"] -= C.WEAPONS[w_name].get("cooling_rate", 0.01)
                    w_state["heat"] = max(0.0, w_state["heat"])

            # Decay Minigun Spin
            if w_name == "minigun":
                # Only decay if we didn't try to fire this frame
                if w_state.get("firing_active", False):
                    # Reset flag for next frame
                    w_state["firing_active"] = False
                else:
                    if w_state["spin_timer"] > 0:
                        w_state["spin_timer"] = max(0, w_state["spin_timer"] - 1)

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

    def melee_attack(self) -> bool:
        """Execute melee attack"""
        if self.melee_cooldown <= 0:
            self.melee_cooldown = 30  # 0.5 seconds at 60 FPS
            self.melee_active = True
            self.melee_timer = 15  # Attack duration
            return True
        return False

    def take_damage(self, damage: int) -> bool:
        """Take damage and return True if player died"""
        if self.invincible or not self.alive or self.god_mode or self.shield_active:
            return False

        self.health -= damage
        self.damage_flash_timer = 15  # 15 frames of red flash

        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.respawning = True
            self.respawn_delay = 180  # 3 seconds delay at 60 FPS
            return True
        return False
