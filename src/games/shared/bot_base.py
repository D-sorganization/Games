"""Base class for game bots/enemies with common initialization."""

from __future__ import annotations

import random
from typing import Any

from games.shared.contracts import validate_not_none, validate_positive


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
        validate_not_none(enemy_types, "enemy_types")
        validate_not_none(difficulties, "difficulties")
        validate_positive(base_bot_health, "base_bot_health")
        validate_positive(base_bot_damage, "base_bot_damage")
        self._init_position(x, y)
        self._init_type(enemy_types, enemy_type)
        diff_stats = difficulties.get(difficulty, difficulties["NORMAL"])
        self._init_combat_stats(
            level, base_bot_health, base_bot_damage, bot_speed, diff_stats
        )
        self._init_state(level, x, y)
        self._init_visual_state()

    def _init_position(self, x: float, y: float) -> None:
        """Set initial spatial position and angle."""
        self.x = x
        self.y = y
        self.z = 0.0
        self.angle: float = 0.0

    def _init_type(self, enemy_types: dict[str, Any], enemy_type: str | None) -> None:
        """Resolve enemy type and cache its type_data."""
        if enemy_type:
            self.enemy_type = enemy_type
        else:
            options = [k for k in enemy_types if k != "health_pack"]
            self.enemy_type = random.choice(options)
        self.type_data = enemy_types[self.enemy_type]

    def _init_combat_stats(
        self,
        level: int,
        base_bot_health: int,
        base_bot_damage: int,
        bot_speed: float,
        diff_stats: dict[str, Any],
    ) -> None:
        """Compute scaled health, damage, and speed from level and difficulty."""
        health_mult = float(self.type_data.get("health_mult", 1.0))
        base_health = int(base_bot_health * health_mult)
        self.health = int((base_health + (level - 1) * 3) * diff_stats["health_mult"])
        self.max_health = self.health
        damage_mult = float(self.type_data.get("damage_mult", 1.0))
        base_damage = int(base_bot_damage * damage_mult)
        self.damage = int((base_damage + (level - 1) * 2) * diff_stats["damage_mult"])
        self.speed = float(bot_speed * float(self.type_data.get("speed_mult", 1.0)))

    def _init_state(self, level: int, x: float, y: float) -> None:
        """Set alive/dead flags, timers, animation, and momentum."""
        self.alive = True
        self.attack_timer = 0
        self.level = level
        self.walk_animation = 0.0
        self.shoot_animation = 0.0
        self.last_x = x
        self.last_y = y
        self.vx = 0.0
        self.vy = 0.0
        self.dead = False
        self.death_timer = 0.0
        self.disintegrate_timer = 0.0
        self.removed = False
        self.frozen = False
        self.frozen_timer = 0
        self.pain_timer = 0

    def _init_visual_state(self) -> None:
        """Set visual-effect fields (mouth, eyes, drool)."""
        self.mouth_open = False
        self.mouth_timer = 0
        self.eye_rotation = 0.0
        self.drool_offset = 0.0
