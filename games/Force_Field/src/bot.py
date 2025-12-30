from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from . import constants as C  # noqa: N812
from .projectile import Projectile
from .utils import has_line_of_sight

if TYPE_CHECKING:
    from .custom_types import EnemyData
    from .map import Map
    from .player import Player


class Bot:
    """Enemy bot with AI"""

    def __init__(
        self,
        x: float,
        y: float,
        level: int,
        enemy_type: str | None = None,
        difficulty: str = "NORMAL",
    ):
        """Initialize bot
        Args:
            x, y: Position
            level: Current level (affects stats)
            enemy_type: Type of enemy (zombie, boss, demon, dinosaur, raider)
            difficulty: EASY, NORMAL, HARD, NIGHTMARE
        """
        self.x = x
        self.y = y
        self.angle: float = 0.0
        if enemy_type:
            self.enemy_type = enemy_type
        else:
            options = [k for k in C.ENEMY_TYPES if k != "health_pack"]
            self.enemy_type = random.choice(options)
        self.type_data = C.ENEMY_TYPES[self.enemy_type]

        diff_stats = C.DIFFICULTIES.get(difficulty, C.DIFFICULTIES["NORMAL"])

        type_data: EnemyData = self.type_data
        base_health = int(C.BASE_BOT_HEALTH * float(type_data.get("health_mult", 1.0)))
        # Apply difficulty to health
        self.health = int((base_health + (level - 1) * 3) * diff_stats["health_mult"])
        self.max_health = self.health

        base_damage = int(C.BASE_BOT_DAMAGE * float(type_data.get("damage_mult", 1.0)))
        # Apply difficulty to damage
        self.damage = int((base_damage + (level - 1) * 2) * diff_stats["damage_mult"])

        self.speed = float(C.BOT_SPEED * float(type_data.get("speed_mult", 1.0)))
        self.alive = True
        self.attack_timer = 0
        self.level = level
        self.walk_animation = 0.0  # For walk animation
        self.last_x = x
        self.last_y = y
        self.shoot_animation = 0.0  # For shoot animation

        # Momentum for Ball boss
        self.vx = 0.0
        self.vy = 0.0
        if self.enemy_type == "ball":
            self.damage = int(self.damage * 1.5)  # Impact damage

        # Visuals (Doom style)
        self.mouth_open = False
        self.mouth_timer = 0
        self.eye_rotation = 0.0
        self.drool_offset = 0.0

        # Death State
        self.dead = False
        self.death_timer = 0
        self.disintegrate_timer = 0
        self.removed = False  # When fully disintegrated

        # Pain State
        self.pain_timer = 0

    def update(
        self, game_map: Map, player: Player, other_bots: list[Bot]
    ) -> Projectile | None:
        """Update bot AI"""
        if self._check_status_effects():
            return None


        self._update_animations()

        if self.enemy_type == "health_pack":
            return None

        # Calculate distance to player
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        # Face player
        self.angle = float(math.atan2(dy, dx))

        # Behavior dispatch
        if self.enemy_type == "ball":
            return self._update_behavior_ball(game_map, player, dx, dy, distance)
        elif self.enemy_type == "ninja":
            return self._update_behavior_ninja(game_map, player, distance, other_bots)
        elif self.enemy_type == "beast":
            return self._update_behavior_beast(game_map, player, distance, other_bots)
        elif self.enemy_type == "minigunner":
            return self._update_behavior_minigunner(
                game_map, player, distance, other_bots
            )
        elif self.enemy_type == "sniper":
            return self._update_behavior_sniper(game_map, player, distance, other_bots)

        return self._update_behavior_standard(game_map, player, distance, other_bots)

    def _check_status_effects(self) -> bool:
        """Check pain and death states. Returns True if bot should skip update."""
        if self.pain_timer > 0:
            self.pain_timer -= 1
            return True

        if self.dead:
            self.death_timer += 1
            if self.death_timer > 60:
                self.disintegrate_timer += 1
                if self.disintegrate_timer > 100:
                    self.removed = True
            return True
        return False

    def _update_animations(self) -> None:
        if self.shoot_animation > 0:
            self.shoot_animation -= 0.1
            self.shoot_animation = max(self.shoot_animation, 0)

        self.eye_rotation += 0.1
        self.eye_rotation %= 2 * math.pi
        self.drool_offset += 0.2
        self.mouth_timer += 1
        if self.mouth_timer > 30:
            self.mouth_open = not self.mouth_open
            self.mouth_timer = 0

    def _update_behavior_ball(
        self, game_map: Map, player: Player, dx: float, dy: float, dist: float
    ) -> Projectile | None:
        # Accelerate towards player
        accel = 0.001 * self.speed

        # Normalize direction
        if dist > 0:
            self.vx += (dx / dist) * accel
            self.vy += (dy / dist) * accel

        # Max speed cap (high)
        current_speed = math.sqrt(self.vx**2 + self.vy**2)
        max_speed = self.speed * 2.0
        if current_speed > max_speed:
            scale = max_speed / current_speed
            self.vx *= scale
            self.vy *= scale

        # Move
        new_x = self.x + self.vx
        new_y = self.y + self.vy

        # Bounce off walls
        if game_map.is_wall(new_x, self.y):
            self.vx *= -0.8  # Bounce with some loss
            new_x = self.x
        if game_map.is_wall(self.x, new_y):
            self.vy *= -0.8
            new_y = self.y

        # Update pos
        self.x = new_x
        self.y = new_y

        # Visual rotation
        self.angle = math.atan2(self.vy, self.vx)

        # Collision with player (Crush)
        # Recalculate distance after move
        dist_new = math.sqrt((new_x - player.x) ** 2 + (new_y - player.y) ** 2)
        if dist_new < 1.0:
            if not player.god_mode:
                player.take_damage(self.damage)
            # Bounce back
            self.vx *= -1.0
            self.vy *= -1.0
        return None

    def _update_behavior_ninja(
        self, game_map: Map, player: Player, distance: float, other_bots: list[Bot]
    ) -> Projectile | None:
        if distance < 1.2 and self.attack_timer <= 0:
            if not player.god_mode:
                player.take_damage(self.damage)
            self.attack_timer = 30
            return None

        return self._move_and_collide(game_map, other_bots)

    def _update_behavior_beast(
        self, game_map: Map, player: Player, distance: float, other_bots: list[Bot]
    ) -> Projectile | None:
        if distance < 15 and self.attack_timer <= 0:
            if self.has_line_of_sight(game_map, player):
                projectile = Projectile(
                    self.x,
                    self.y,
                    self.angle,
                    damage=self.damage * 2,
                    speed=0.15,
                    is_player=False,
                    color=(255, 100, 0),
                    size=1.0,
                )
                self.attack_timer = 120
                self.shoot_animation = 1.0
                return projectile
        return self._move_and_collide(game_map, other_bots)

    def _update_behavior_minigunner(
        self, game_map: Map, player: Player, distance: float, other_bots: list[Bot]
    ) -> Projectile | None:
        if distance < 12 and self.attack_timer <= 0:
            if self.has_line_of_sight(game_map, player):
                projectile = Projectile(
                    self.x,
                    self.y,
                    self.angle,
                    damage=self.damage,
                    speed=0.2,
                    is_player=False,
                    color=(255, 255, 0),
                    size=0.1,
                )
                self.attack_timer = 10
                self.shoot_animation = 1.0
                return projectile
        return self._move_and_collide(game_map, other_bots)

    def _update_behavior_sniper(
        self, game_map: Map, player: Player, distance: float, other_bots: list[Bot]
    ) -> Projectile | None:
        if distance < C.WEAPON_RANGE_SNIPER and self.attack_timer <= 0:
            if self.has_line_of_sight(game_map, player):
                projectile = Projectile(
                    self.x,
                    self.y,
                    self.angle,
                    damage=self.damage,
                    speed=0.4,
                    is_player=False,
                    color=(255, 0, 0),
                    size=0.1,
                )
                self.attack_timer = 180
                self.shoot_animation = 1.0
                return projectile
        return self._move_and_collide(game_map, other_bots)

    def _update_behavior_standard(
        self, game_map: Map, player: Player, distance: float, other_bots: list[Bot]
    ) -> Projectile | None:
        if distance < C.BOT_ATTACK_RANGE and self.attack_timer <= 0:
            if self.has_line_of_sight(game_map, player):
                projectile = Projectile(
                    self.x,
                    self.y,
                    self.angle,
                    C.BOT_PROJECTILE_DAMAGE + self.damage,
                    C.BOT_PROJECTILE_SPEED,
                    is_player=False,
                )
                self.attack_timer = C.BOT_ATTACK_COOLDOWN
                self.shoot_animation = 1.0
                return projectile

        return self._move_and_collide(game_map, other_bots)

    def _move_and_collide(
        self, game_map: Map, other_bots: list[Bot]
    ) -> Projectile | None:
        # Move toward player (angle already set)
        move_dx = math.cos(self.angle) * self.speed
        move_dy = math.sin(self.angle) * self.speed

        new_x = self.x + move_dx
        new_y = self.y + move_dy

        # Check wall collision
        can_move_x = not game_map.is_wall(new_x, self.y)
        can_move_y = not game_map.is_wall(self.x, new_y)

        # Check collision with other bots
        collision_radius = 0.5 + (0.5 if self.enemy_type == "beast" else 0)
        col_sq = collision_radius * collision_radius

        for other_bot in other_bots:
            if other_bot != self and not other_bot.dead:
                if (
                    abs(new_x - other_bot.x) > collision_radius
                    and abs(self.x - other_bot.x) > collision_radius
                ):
                    pass

                dx_sq = (new_x - other_bot.x) ** 2
                dy_sq = (self.y - other_bot.y) ** 2
                if dx_sq + dy_sq < col_sq:
                    can_move_x = False
                    if self.enemy_type == "beast":
                        push_x = other_bot.x + move_dx * 2
                        if not game_map.is_wall(push_x, other_bot.y):
                            other_bot.x = push_x

                dx_sq = (self.x - other_bot.x) ** 2
                dy_sq = (new_y - other_bot.y) ** 2
                if dx_sq + dy_sq < col_sq:
                    can_move_y = False
                    if self.enemy_type == "beast":
                        push_y = other_bot.y + move_dy * 2
                        if not game_map.is_wall(other_bot.x, push_y):
                            other_bot.y = push_y

        if can_move_x:
            self.x = new_x
        if can_move_y:
            self.y = new_y

        # Update walk animation
        moved = self.x != self.last_x or self.y != self.last_y
        if moved:
            self.walk_animation += 0.3
            if self.walk_animation > 2 * math.pi:
                self.walk_animation -= 2 * math.pi
        self.last_x = self.x
        self.last_y = self.y

        if self.attack_timer > 0:
            self.attack_timer -= 1

        return None

    def has_line_of_sight(self, game_map: Map, player: Player) -> bool:
        """Check if bot has line of sight to player"""
        return has_line_of_sight(self.x, self.y, player.x, player.y, game_map)

    def take_damage(self, damage: int, is_headshot: bool = False) -> bool:
        """Take damage
        Args:
            damage: Base damage amount
            is_headshot: If True, do 3x damage instead of instant kill

        Returns:
            bool: True if this damage killed the bot
        """
        if self.dead:
            return False

        if is_headshot:
            self.health -= damage * 3
        else:
            self.health -= damage

        # Trigger Pain State
        if self.health > 0:
            # Chance to flinch based on damage
            if damage > 20 or random.random() < 0.3:
                self.pain_timer = 15  # Stun for 15 frames

        if self.health <= 0:
            self.health = 0
            self.dead = True
            self.alive = False
            return True
        return False
