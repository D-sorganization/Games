"""Base class for game bots/enemies with common initialization."""

from __future__ import annotations

import random
from typing import Any


class BotBase:
    """Base class for enemy bots with common state management."""

    def __init__(
        self,
        x: float,
        y: float,
        level: int,
        enemy_types: dict[str, Any],
        base_bot_health: int,
        base_bot_damage: int,
        bot_speed: float,
        difficulties: dict[str, Any],
        enemy_type: str | None = None,
        difficulty: str = "NORMAL",
    ):
        """Initialize bot base.

        Args:
            x: Initial x position
            y: Initial y position
            level: Current level (affects stats)
            enemy_types: Dictionary of enemy type configurations
            base_bot_health: Base health value
            base_bot_damage: Base damage value
            bot_speed: Base movement speed
            difficulties: Dictionary of difficulty configurations
            enemy_type: Specific enemy type or None for random
            difficulty: Difficulty level (EASY, NORMAL, HARD, NIGHTMARE)
        """
        # Position
        self.x = x
        self.y = y
        self.z = 0.0
        self.angle: float = 0.0

        # Enemy type selection
        if enemy_type:
            self.enemy_type = enemy_type
        else:
            options = [k for k in enemy_types if k != "health_pack"]
            self.enemy_type = random.choice(options)

        self.type_data = enemy_types[self.enemy_type]
        diff_stats = difficulties.get(difficulty, difficulties["NORMAL"])

        # Health calculation
        base_health = int(base_bot_health * float(self.type_data.get("health_mult", 1.0)))
        self.health = int((base_health + (level - 1) * 3) * diff_stats["health_mult"])
        self.max_health = self.health

        # Damage calculation
        base_damage = int(base_bot_damage * float(self.type_data.get("damage_mult", 1.0)))
        self.damage = int((base_damage + (level - 1) * 2) * diff_stats["damage_mult"])

        # Speed
        self.speed = float(bot_speed * float(self.type_data.get("speed_mult", 1.0)))

        # State
        self.alive = True
        self.attack_timer = 0
        self.level = level

        # Animation
        self.walk_animation = 0.0
        self.shoot_animation = 0.0
        self.last_x = x
        self.last_y = y

        # Momentum (for special enemy types)
        self.vx = 0.0
        self.vy = 0.0

        # Visual effects
        self.mouth_open = False
        self.mouth_timer = 0
        self.eye_rotation = 0.0
        self.drool_offset = 0.0

        # Death state
        self.dead = False
        self.death_timer = 0.0
        self.disintegrate_timer = 0.0
        self.removed = False

        # Status effects
        self.frozen = False
        self.frozen_timer = 0
        self.pain_timer = 0
