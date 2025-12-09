from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Any, Dict, List

from . import constants as C  # noqa: N812
from .projectile import Projectile

if TYPE_CHECKING:
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

        type_data: Dict[str, Any] = self.type_data
        base_health = int(C.BASE_BOT_HEALTH * float(type_data["health_mult"]))
        # Apply difficulty to health
        self.health = int((base_health + (level - 1) * 3) * diff_stats["health_mult"])
        self.max_health = self.health

        base_damage = int(C.BASE_BOT_DAMAGE * float(type_data["damage_mult"]))
        # Apply difficulty to damage
        self.damage = int((base_damage + (level - 1) * 2) * diff_stats["damage_mult"])

        self.speed = float(C.BOT_SPEED * float(type_data["speed_mult"]))
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

    def update(self, game_map: Map, player: Player, other_bots: List[Bot]) -> Projectile | None:
        """Update bot AI"""
        if self.dead:
            self.death_timer += 1
            if self.death_timer > 60:  # Start disintegrating after 1 second
                self.disintegrate_timer += 1
                if self.disintegrate_timer > 100:
                    self.removed = True
            return None

        # Update animations
        if self.shoot_animation > 0:
            self.shoot_animation -= 0.1
            self.shoot_animation = max(self.shoot_animation, 0)

        # Update visual animations
        self.eye_rotation += 0.1
        self.eye_rotation %= 2 * math.pi
        self.drool_offset += 0.2
        self.mouth_timer += 1
        if self.mouth_timer > 30:
            self.mouth_open = not self.mouth_open
            self.mouth_timer = 0

        if self.enemy_type == "health_pack":
            return None

        # Calculate distance to player
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        # Face player
        self.angle = float(math.atan2(dy, dx))

        if self.enemy_type == "ball":
            # Rolling Momentum Logic
            # Accelerate towards player
            accel = 0.001 * self.speed
            dx = player.x - self.x
            dy = player.y - self.y
            dist = math.sqrt(dx * dx + dy * dy)

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

        if self.enemy_type == "beast":
            # Slow movement, big fireballs
            # Standard move logic below will handle slow movement

            # Custom Fireball Attack
            if distance < 15 and self.attack_timer <= 0:  # Long range
                if self.has_line_of_sight(game_map, player):
                    # Calculate parabola (fake 3D arc)
                    # We just spawn a big fireball projectile (fake 3D arc handled later)
                    # For now, just a big fireball projectile
                    projectile = Projectile(
                        self.x,
                        self.y,
                        self.angle,
                        damage=self.damage * 2,
                        speed=0.15,  # Slow heavy projectile
                        is_player=False,
                        color=(255, 100, 0),
                        size=1.0,  # Big
                    )
                    self.attack_timer = 120  # Slow fire rate
                    self.shoot_animation = 1.0
                    return projectile

        # Attack if in range
        if distance < C.BOT_ATTACK_RANGE and self.enemy_type != "beast":  # Beast handled above
            if self.attack_timer <= 0:
                # Check line of sight
                if self.has_line_of_sight(game_map, player):
                    # Shoot projectile instead of direct damage
                    projectile = Projectile(
                        self.x,
                        self.y,
                        self.angle,
                        C.BOT_PROJECTILE_DAMAGE + self.damage,
                        C.BOT_PROJECTILE_SPEED,
                        is_player=False,
                    )
                    self.attack_timer = C.BOT_ATTACK_COOLDOWN
                    self.shoot_animation = 1.0  # Start shoot animation
                    return projectile  # Return projectile to be added to list
        else:
            # Move toward player
            move_dx = math.cos(self.angle) * self.speed
            move_dy = math.sin(self.angle) * self.speed

            new_x = self.x + move_dx
            new_y = self.y + move_dy

            # Check wall collision
            can_move_x = not game_map.is_wall(new_x, self.y)
            can_move_y = not game_map.is_wall(self.x, new_y)

            # Check collision with other bots
            for other_bot in other_bots:
                if other_bot != self and not other_bot.dead:
                    other_dist = math.sqrt((new_x - other_bot.x) ** 2 + (self.y - other_bot.y) ** 2)
                    if other_dist < 0.5 + (0.5 if self.enemy_type == "beast" else 0):
                        can_move_x = False
                        # Beast pushes others?
                        if self.enemy_type == "beast":
                            push_x = other_bot.x + move_dx * 2
                            if not game_map.is_wall(push_x, other_bot.y):
                                other_bot.x = push_x

                    other_dist = math.sqrt((self.x - other_bot.x) ** 2 + (new_y - other_bot.y) ** 2)
                    if other_dist < 0.5 + (0.5 if self.enemy_type == "beast" else 0):
                        can_move_y = False
                         # Beast pushes others (Y only)
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

        # Update attack timer
        if self.attack_timer > 0:
            self.attack_timer -= 1

        return None  # No projectile shot this frame

    def has_line_of_sight(self, game_map: Map, player: Player) -> bool:
        """Check if bot has line of sight to player"""
        steps = 50
        for i in range(1, steps):
            t = i / steps
            check_x = self.x + (player.x - self.x) * t
            check_y = self.y + (player.y - self.y) * t
            if game_map.is_wall(check_x, check_y):
                return False
        return True

    def take_damage(self, damage: int, is_headshot: bool = False) -> None:
        """Take damage
        Args:
            damage: Base damage amount
            is_headshot: If True, do 3x damage instead of instant kill
        """
        if self.dead:
            return

        if is_headshot:
            self.health -= damage * 3  # Headshot does 3x damage, not instant kill
        else:
            self.health -= damage

        if self.health <= 0:
            self.health = 0
            self.dead = True
            self.alive = False  # Kept for backward compat logic usage, but we use dead/removed now
