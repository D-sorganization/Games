from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from games.shared.constants import DEATH_ANIMATION_FRAMES, DISINTEGRATE_FRAMES
from games.shared.utils import has_line_of_sight

from . import constants as C  # noqa: N812
from .projectile import Projectile

if TYPE_CHECKING:
    from .custom_types import EnemyData
    from .map import Map
    from .player import Player


class Bot:
    """Enemy bot with AI"""

    # Dispatch table: enemy_type -> method name for type-specific behavior.
    # Each handler accepts (game_map, player, dist_sq, other_bots) and returns
    # Projectile | None.  Adding a new enemy type only requires a new handler
    # method and one entry here.
    _BEHAVIOR_DISPATCH: dict[str, str] = {
        "ball": "_update_behavior_ball",
        "ninja": "_update_behavior_ninja",
        "beast": "_update_behavior_beast",
        "minigunner": "_update_behavior_minigunner",
        "sniper": "_update_behavior_sniper",
    }

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
        self._init_stats(level, difficulty)
        self._init_visual_state(x, y)

    def _init_stats(self, level: int, difficulty: str) -> None:
        """Compute and store health, damage, speed from level and difficulty."""
        diff_stats = C.DIFFICULTIES.get(difficulty, C.DIFFICULTIES["NORMAL"])
        type_data: EnemyData = self.type_data
        base_health = int(C.BASE_BOT_HEALTH * float(type_data.get("health_mult", 1.0)))
        self.health = int((base_health + (level - 1) * 3) * diff_stats["health_mult"])
        self.max_health = self.health
        base_damage = int(C.BASE_BOT_DAMAGE * float(type_data.get("damage_mult", 1.0)))
        self.damage = int((base_damage + (level - 1) * 2) * diff_stats["damage_mult"])
        self.speed = float(C.BOT_SPEED * float(type_data.get("speed_mult", 1.0)))
        self.alive = True
        self.attack_timer = 0
        self.level = level

    def _init_visual_state(self, x: float, y: float) -> None:
        """Initialize animation, position tracking, and status flags."""
        self.walk_animation = 0.0
        self.last_x = x
        self.last_y = y
        self.shoot_animation = 0.0
        self.vx = 0.0
        self.vy = 0.0
        if self.enemy_type == "ball":
            self.damage = int(self.damage * 1.5)  # Impact damage
        self.mouth_open = False
        self.mouth_timer = 0
        self.eye_rotation = 0.0
        self.drool_offset = 0.0
        self.dead = False
        self.death_timer = 0
        self.disintegrate_timer = 0
        self.removed = False
        self.z = 0.5
        self.frozen = False

    def update(
        self, game_map: Map, player: Player, other_bots: list[Bot]
    ) -> Projectile | None:
        """Update bot AI"""
        if self.dead:
            self._update_death_animation()
            return None

        self._update_visual_animations()

        if self.enemy_type == "health_pack":
            return None

        # Calculate squared distance to player (avoid sqrt for comparisons)
        dx = player.x - self.x
        dy = player.y - self.y
        dist_sq = dx * dx + dy * dy

        # Face player
        self.angle = float(math.atan2(dy, dx))

        # Dispatch to type-specific behavior
        handler_name = self._BEHAVIOR_DISPATCH.get(self.enemy_type)
        if handler_name is not None:
            handler = getattr(self, handler_name)
            return handler(game_map, player, dist_sq, other_bots)

        # Default behavior for types without a dedicated handler
        return self._update_behavior_standard(game_map, player, dist_sq, other_bots)

    def _update_death_animation(self) -> None:
        """Update death and disintegration timers."""
        self.death_timer += 1
        if self.death_timer > DEATH_ANIMATION_FRAMES:
            self.disintegrate_timer += 1
            if self.disintegrate_timer > DISINTEGRATE_FRAMES:
                self.removed = True

    def _update_visual_animations(self) -> None:
        """Update shoot, eye, drool, and mouth animations."""
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

    # ------------------------------------------------------------------
    # Behavior handlers (uniform signature for dispatch table)
    #
    # Each handler accepts (game_map, player, dist_sq, other_bots) and
    # returns Projectile | None.
    # ------------------------------------------------------------------

    def _apply_ball_physics(
        self, game_map: Map, player: Player, dist_sq: float
    ) -> tuple[float, float]:
        """Accelerate toward player, cap speed, bounce off walls, return new pos."""
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dist_sq)
        accel = 0.001 * self.speed
        if dist > 0:
            self.vx += (dx / dist) * accel
            self.vy += (dy / dist) * accel
        current_speed = math.sqrt(self.vx**2 + self.vy**2)
        max_speed = self.speed * 2.0
        if current_speed > max_speed:
            scale = max_speed / current_speed
            self.vx *= scale
            self.vy *= scale
        new_x = self.x + self.vx
        new_y = self.y + self.vy
        if game_map.is_wall(new_x, self.y):
            self.vx *= -0.8
            new_x = self.x
        if game_map.is_wall(self.x, new_y):
            self.vy *= -0.8
            new_y = self.y
        return new_x, new_y

    def _check_ball_crush(self, new_x: float, new_y: float, player: Player) -> None:
        """Deal crush damage and reverse velocity if ball overlaps player."""
        dist_new = math.sqrt((new_x - player.x) ** 2 + (new_y - player.y) ** 2)
        if dist_new < 1.0:
            if not player.god_mode:
                player.take_damage(self.damage)
            self.vx *= -1.0
            self.vy *= -1.0

    def _update_behavior_ball(
        self,
        game_map: Map,
        player: Player,
        _dist_sq: float,
        _other_bots: list[Bot],
    ) -> Projectile | None:
        """Rolling momentum movement with wall bouncing and crush attack."""
        new_x, new_y = self._apply_ball_physics(game_map, player, _dist_sq)
        self.x = new_x
        self.y = new_y
        self.angle = math.atan2(self.vy, self.vx)
        self._check_ball_crush(new_x, new_y, player)
        return None

    def _update_behavior_ninja(
        self,
        game_map: Map,
        player: Player,
        dist_sq: float,
        other_bots: list[Bot],
    ) -> Projectile | None:
        """Ninja melee attack, then fall through to default movement."""
        if dist_sq < 1.44 and self.attack_timer <= 0:  # 1.2^2
            if not player.god_mode:
                player.take_damage(self.damage)
            self.attack_timer = 30
            return None

        # No melee this frame -- move toward player
        self._update_default_movement(game_map, player, other_bots)
        if self.attack_timer > 0:
            self.attack_timer -= 1
        return None

    def _update_behavior_beast(
        self,
        game_map: Map,
        player: Player,
        dist_sq: float,
        other_bots: list[Bot],
    ) -> Projectile | None:
        """Beast fireball attack -- slow movement, big fireballs."""
        # Custom Fireball Attack
        if dist_sq < 225 and self.attack_timer <= 0:  # 15^2, long range
            if self.has_line_of_sight(game_map, player):
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

        # No fireball this frame -- move toward player
        self._update_default_movement(game_map, player, other_bots)
        if self.attack_timer > 0:
            self.attack_timer -= 1
        return None

    def _update_behavior_minigunner(
        self,
        game_map: Map,
        player: Player,
        dist_sq: float,
        other_bots: list[Bot],
    ) -> Projectile | None:
        """Minigunner rapid-fire attack."""
        if dist_sq < 144 and self.attack_timer <= 0:  # 12^2
            if self.has_line_of_sight(game_map, player):
                projectile = Projectile(
                    self.x,
                    self.y,
                    self.angle,
                    damage=self.damage,
                    speed=0.2,  # Fast projectile
                    is_player=False,
                    color=(255, 255, 0),
                    size=0.1,
                )
                self.attack_timer = 10  # Rapid fire
                self.shoot_animation = 1.0
                return projectile

        # No burst this frame -- move toward player
        self._update_default_movement(game_map, player, other_bots)
        if self.attack_timer > 0:
            self.attack_timer -= 1
        return None

    def _update_behavior_sniper(
        self,
        game_map: Map,
        player: Player,
        dist_sq: float,
        other_bots: list[Bot],
    ) -> Projectile | None:
        """Sniper long-range, slow-fire attack."""
        if dist_sq < C.WEAPON_RANGE_SNIPER**2 and self.attack_timer <= 0:
            if self.has_line_of_sight(game_map, player):
                # Very Fast projectile
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
                self.attack_timer = 180  # Slow fire
                self.shoot_animation = 1.0
                return projectile

        # No shot this frame -- move toward player
        self._update_default_movement(game_map, player, other_bots)
        if self.attack_timer > 0:
            self.attack_timer -= 1
        return None

    # ------------------------------------------------------------------
    # Standard / default behavior (used by types not in dispatch table)
    # ------------------------------------------------------------------

    def _update_behavior_standard(
        self,
        game_map: Map,
        player: Player,
        dist_sq: float,
        other_bots: list[Bot],
    ) -> Projectile | None:
        """Default behavior for types not in the dispatch table:
        attempt a standard ranged attack if in range, otherwise move."""
        attack_range_sq = C.BOT_ATTACK_RANGE * C.BOT_ATTACK_RANGE
        if dist_sq < attack_range_sq:
            projectile = self._try_attack(game_map, player)
            if projectile is not None:
                return projectile
        else:
            self._update_default_movement(game_map, player, other_bots)

        if self.attack_timer > 0:
            self.attack_timer -= 1
        return None

    def _try_attack(self, game_map: Map, player: Player) -> Projectile | None:
        """Default ranged attack for standard enemy types."""
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
        return None

    def _check_bot_collisions(
        self,
        other_bots: list[Bot],
        new_x: float,
        new_y: float,
        move_dx: float,
        move_dy: float,
        game_map: Map,
        can_move_x: bool,
        can_move_y: bool,
    ) -> tuple[bool, bool]:
        """Check collisions with other bots; push if beast type.

        Returns:
            (can_move_x, can_move_y)
        """
        collision_radius = 0.5 + (0.5 if self.enemy_type == "beast" else 0)
        col_sq = collision_radius * collision_radius

        for other_bot in other_bots:
            if other_bot != self and not other_bot.dead:
                if (new_x - other_bot.x) ** 2 + (self.y - other_bot.y) ** 2 < col_sq:
                    can_move_x = False
                    if self.enemy_type == "beast":
                        push_x = other_bot.x + move_dx * 2
                        if not game_map.is_wall(push_x, other_bot.y):
                            other_bot.x = push_x
                if (self.x - other_bot.x) ** 2 + (new_y - other_bot.y) ** 2 < col_sq:
                    can_move_y = False
                    if self.enemy_type == "beast":
                        push_y = other_bot.y + move_dy * 2
                        if not game_map.is_wall(other_bot.x, push_y):
                            other_bot.y = push_y
        return can_move_x, can_move_y

    def _update_walk_animation(self) -> None:
        """Advance walk animation if the bot moved this frame."""
        moved = self.x != self.last_x or self.y != self.last_y
        if moved:
            self.walk_animation += 0.3
            if self.walk_animation > 2 * math.pi:
                self.walk_animation -= 2 * math.pi
        self.last_x = self.x
        self.last_y = self.y

    def _update_default_movement(
        self, game_map: Map, player: Player, other_bots: list[Bot]
    ) -> None:
        """Move toward player with wall and bot collision handling."""
        move_dx = math.cos(self.angle) * self.speed
        move_dy = math.sin(self.angle) * self.speed
        new_x = self.x + move_dx
        new_y = self.y + move_dy

        can_move_x = not game_map.is_wall(new_x, self.y)
        can_move_y = not game_map.is_wall(self.x, new_y)
        can_move_x, can_move_y = self._check_bot_collisions(
            other_bots, new_x, new_y, move_dx, move_dy, game_map, can_move_x, can_move_y
        )

        if can_move_x:
            self.x = new_x
        if can_move_y:
            self.y = new_y

        self._update_walk_animation()

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

        if self.health <= 0:
            self.health = 0
            self.dead = True
            self.alive = False
            return True
        return False
