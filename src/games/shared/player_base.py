"""Base class for game players with common state management."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing import Protocol

    class Map(Protocol):
        """Map protocol for type checking."""

    class Bot(Protocol):
        """Bot protocol for type checking."""


class PlayerBase:
    """Base class for players with common initialization and state."""

    def __init__(
        self,
        x: float,
        y: float,
        angle: float,
        weapons_config: dict[str, Any],
        constants: Any,
    ):
        """Initialize player base.

        Args:
            x: Initial x position
            y: Initial y position
            angle: Initial angle in radians
            weapons_config: Dictionary of weapon configurations
            constants: Game constants module
        """
        self.C = constants

        # Position and orientation
        self.x = x
        self.y = y
        self.angle = angle
        self.pitch: float = 0.0  # Vertical look offset
        self.z = 0.5  # Camera height

        # Health
        self.health: int = 100
        self.max_health: int = 100

        # Movement
        self.is_moving = False  # Track movement for bobbing

        # Weapon State - initialize for all weapons
        self.weapon_state: dict[str, dict[str, Any]] = {}
        for w_name, w_data in weapons_config.items():
            self.weapon_state[w_name] = {
                "clip": w_data.get("clip_size", 999),
                "heat": 0.0,
                "reloading": False,
                "reload_timer": 0,
                "overheated": False,
                "overheat_timer": 0,
                "spin_timer": 0,
            }

        # Ammo reserves
        self.ammo: dict[str, int] = {
            w: int(weapons_config[w]["ammo"]) for w in weapons_config
        }

        # Current weapon and shooting state
        self.current_weapon = "rifle"
        self.shooting = False
        self.shoot_timer = 0
        self.alive: bool = True

        # Shield system
        self.shield_active = False
        self.shield_timer = getattr(constants, "SHIELD_MAX_DURATION", 600)
        self.shield_recharge_delay = 0

        # Bombs
        self.bomb_cooldown = 0
        self.bombs = getattr(constants, "BOMBS_START", 1)
        self.secondary_cooldown = 0

        # Zoom
        self.zoomed = False
        self.god_mode = False

        # Weapon Sway / Turn tracking
        self.frame_turn = 0.0
        self.sway_amount = 0.0

        # Stamina
        self.stamina = 100.0
        self.max_stamina = 100.0
        self.stamina_recharge_delay = 0

    def rotate(self, delta: float) -> None:
        """Rotate player view."""
        self.angle += delta
        self.angle %= 2 * math.pi
        self.frame_turn += delta

    def pitch_view(self, delta: float) -> None:
        """Change vertical view angle (pitch)."""
        pitch_limit = getattr(self.C, "PITCH_LIMIT", 1.0)
        self.pitch += delta
        self.pitch = max(-pitch_limit, min(pitch_limit, self.pitch))

    def switch_weapon(self, weapon: str) -> None:
        """Switch to a different weapon."""
        weapons = getattr(self.C, "WEAPONS", {})
        if weapon in weapons:
            if self.current_weapon in self.weapon_state:
                self.weapon_state[self.current_weapon]["reloading"] = False
            self.current_weapon = weapon
            self.weapon_state[weapon]["reloading"] = False

    def get_current_weapon_damage(self) -> int:
        """Get damage of current weapon."""
        weapons = getattr(self.C, "WEAPONS", {})
        return int(weapons[self.current_weapon]["damage"])

    def get_current_weapon_range(self) -> int:
        """Get range of current weapon."""
        weapons = getattr(self.C, "WEAPONS", {})
        return int(weapons[self.current_weapon]["range"])

    def reload(self) -> None:
        """Start reload process."""
        weapons = getattr(self.C, "WEAPONS", {})
        w_data = weapons[self.current_weapon]
        w_state = self.weapon_state[self.current_weapon]

        if w_state["reloading"] or w_state["overheated"]:
            return

        if self.current_weapon == "plasma":
            return

        if w_state["clip"] < w_data["clip_size"]:
            w_state["reloading"] = True
            w_state["reload_timer"] = w_data.get("reload_time", 60)

    def shoot(self) -> bool:
        """Initiate shooting, return True if shot was fired."""
        weapons = getattr(self.C, "WEAPONS", {})
        weapon_data = weapons[self.current_weapon]
        w_state = self.weapon_state[self.current_weapon]

        # Check global cooldown
        if self.shoot_timer > 0:
            return False

        # Check reloading/overheat
        if w_state["reloading"] or w_state["overheated"]:
            return False

        # Check clip/heat
        if self.current_weapon != "plasma" and w_state["clip"] <= 0:
            self.reload()
            return False

        # Minigun spin-up logic
        if self.current_weapon == "minigun":
            spin_up = int(weapon_data.get("spin_up_time", 30))
            if w_state["spin_timer"] < spin_up:
                w_state["spin_timer"] += 2
                return False
        else:
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

        # Auto-reload if empty
        if self.current_weapon != "plasma" and w_state["clip"] <= 0:
            self.reload()

        return True

    def can_secondary_fire(self) -> bool:
        """Check if secondary fire is ready."""
        return self.secondary_cooldown <= 0

    def fire_secondary(self) -> bool:
        """Execute secondary fire."""
        if self.can_secondary_fire():
            secondary_cooldown = getattr(self.C, "SECONDARY_COOLDOWN", 60)
            self.secondary_cooldown = secondary_cooldown
            return True
        return False

    def set_shield(self, active: bool) -> None:
        """Set shield state from input."""
        if self.shield_recharge_delay > 0:
            self.shield_active = False
            return

        if active and self.shield_timer > 0:
            self.shield_active = True
        else:
            if self.shield_active:
                cooldown_normal = getattr(self.C, "SHIELD_COOLDOWN_NORMAL", 60)
                self.shield_recharge_delay = cooldown_normal
            self.shield_active = False

    def activate_bomb(self) -> bool:
        """Try to drop a bomb."""
        bomb_cooldown = getattr(self.C, "BOMB_COOLDOWN", 300)
        if self.bomb_cooldown <= 0 and self.bombs > 0:
            self.bombs -= 1
            self.bomb_cooldown = bomb_cooldown
            self.shield_active = True
            return True
        return False

    def update_weapon_state(self) -> None:
        """Update weapon timers and state (reloading, heat, etc)."""
        weapons = getattr(self.C, "WEAPONS", {})

        for w_name, w_state in self.weapon_state.items():
            # Reloading
            if w_state["reloading"]:
                w_state["reload_timer"] -= 1
                if w_state["reload_timer"] <= 0:
                    w_state["reloading"] = False
                    w_state["clip"] = weapons[w_name]["clip_size"]

            # Auto-reload if current weapon is empty
            if (
                w_name == self.current_weapon
                and w_name != "plasma"
                and w_state["clip"] <= 0
                and not w_state["reloading"]
            ):
                self.reload()

            # Plasma heat/overheat
            if w_name == "plasma":
                w_data = weapons[w_name]
                if w_state["overheated"]:
                    w_state["overheat_timer"] -= 1
                    penalty_time = int(w_data.get("overheat_penalty", 180))
                    max_heat = float(w_data["max_heat"])
                    if penalty_time > 0:
                        cool_amount = max_heat / penalty_time
                        w_state["heat"] = max(0.0, w_state["heat"] - cool_amount)
                    if w_state["overheat_timer"] <= 0:
                        w_state["overheated"] = False
                        w_state["heat"] = 0.0
                elif w_state["heat"] > 0:
                    w_state["heat"] -= w_data.get("cooling_rate", 0.01)
                    w_state["heat"] = max(0.0, w_state["heat"])

    def update_timers(self) -> None:
        """Update common player timers."""
        # Sway
        self.sway_amount = self.sway_amount * 0.8 + self.frame_turn * 0.2
        self.frame_turn = 0.0

        # Shoot timer
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        else:
            self.shooting = False
            if self.current_weapon == "minigun":
                w_state = self.weapon_state.get("minigun", {})
                if w_state.get("spin_timer", 0) > 0:
                    w_state["spin_timer"] -= 1

        # Cooldowns
        if self.bomb_cooldown > 0:
            self.bomb_cooldown -= 1
        if self.secondary_cooldown > 0:
            self.secondary_cooldown -= 1

        # Stamina regen
        if self.stamina_recharge_delay > 0:
            self.stamina_recharge_delay -= 1
        elif self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + 0.5)

        # Shield logic
        shield_max = getattr(self.C, "SHIELD_MAX_DURATION", 600)
        shield_depleted = getattr(self.C, "SHIELD_COOLDOWN_DEPLETED", 300)

        if self.shield_active:
            if self.shield_timer > 0:
                self.shield_timer -= 1
            else:
                self.shield_active = False
                self.shield_recharge_delay = shield_depleted
        elif self.shield_recharge_delay > 0:
            self.shield_recharge_delay -= 1
        elif self.shield_timer < shield_max:
            self.shield_timer += 2
            self.shield_timer = min(self.shield_timer, shield_max)
