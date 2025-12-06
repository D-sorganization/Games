import math
import random
from typing import TYPE_CHECKING, List, Optional, Any, Dict
from . import constants as C
from .projectile import Projectile

if TYPE_CHECKING:
    from .map import Map
    from .player import Player

class Bot:
    """Enemy bot with AI"""

    def __init__(self, x: float, y: float, level: int, enemy_type: str | None = None):
        """Initialize bot
        Args:
            x, y: Position
            level: Current level (affects stats)
            enemy_type: Type of enemy (zombie, boss, demon, dinosaur, raider)
        """
        self.x = x
        self.y = y
        self.angle: float = 0.0
        self.enemy_type = enemy_type if enemy_type else random.choice(list(C.ENEMY_TYPES.keys()))
        self.type_data = C.ENEMY_TYPES[self.enemy_type]

        type_data: Dict[str, Any] = self.type_data
        base_health = int(C.BASE_BOT_HEALTH * float(type_data["health_mult"]))
        self.health = base_health + (level - 1) * 3
        self.max_health = self.health

        base_damage = int(C.BASE_BOT_DAMAGE * float(type_data["damage_mult"]))
        self.damage = base_damage + (level - 1) * 2

        self.speed = float(C.BOT_SPEED * float(type_data["speed_mult"]))
        self.alive = True
        self.attack_timer = 0
        self.level = level
        self.walk_animation = 0.0  # For walk animation
        self.last_x = x
        self.last_y = y
        self.shoot_animation = 0.0  # For shoot animation

    def update(self, game_map: "Map", player: "Player", other_bots: List["Bot"]) -> Optional[Projectile]:
        """Update bot AI
        Returns:
            Projectile if bot shoots, None otherwise
        """
        if not self.alive:
            return None

        # Update animations
        if self.shoot_animation > 0:
            self.shoot_animation -= 0.1
            if self.shoot_animation < 0:
                self.shoot_animation = 0

        # Calculate distance to player
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        # Face player
        self.angle = float(math.atan2(dy, dx))

        # Attack if in range
        if distance < C.BOT_ATTACK_RANGE:
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
                if other_bot != self and other_bot.alive:
                    other_dist = math.sqrt((new_x - other_bot.x) ** 2 + (self.y - other_bot.y) ** 2)
                    if other_dist < 0.5:
                        can_move_x = False
                    other_dist = math.sqrt((self.x - other_bot.x) ** 2 + (new_y - other_bot.y) ** 2)
                    if other_dist < 0.5:
                        can_move_y = False

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

    def has_line_of_sight(self, game_map: "Map", player: "Player") -> bool:
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
        if is_headshot:
            self.health -= damage * 3  # Headshot does 3x damage, not instant kill
        else:
            self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False
