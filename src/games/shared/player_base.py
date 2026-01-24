"""Base class for game players with common state management."""

from __future__ import annotations

from typing import Any


class PlayerBase:
    """Base class for players with common initialization and state."""

    def __init__(self, x: float, y: float, angle: float, weapons_config: dict[str, Any]):
        """Initialize player base.

        Args:
            x: Initial x position
            y: Initial y position
            angle: Initial angle in radians
            weapons_config: Dictionary of weapon configurations
        """
        # Position and orientation
        self.x = x
        self.y = y
        self.angle = angle
        self.pitch = 0.0  # Vertical look offset

        # Health
        self.health = 100
        self.max_health = 100

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
        self.alive = True

        # Shield system
        self.shield_active = False
        self.shield_timer = 0  # Subclasses should set from constants
        self.shield_recharge_delay = 0

        # Bombs
        self.bomb_cooldown = 0
        self.bombs = 1  # Default start with 1 bomb
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
