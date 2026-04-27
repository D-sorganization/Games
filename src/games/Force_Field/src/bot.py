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

    x: float
    y: float
    z: float
    angle: float
    enemy_type: str
    type_data: EnemyData
    health: int
    max_health: int
    speed: float
    alive: bool
    attack_timer: int
    level: int
    walk_animation: float
    shoot_animation: float
    last_x: float
    last_y: float
    vx: float
    vy: float
    mouth_open: bool
    mouth_timer: int
    eye_rotation: float
    drool_offset: float
    dead: bool
    death_timer: float
    disintegrate_timer: float
    removed: bool
    pain_timer: int
    frozen: bool
    frozen_timer: int

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
        "ice_zombie": "_update_behavior_standard",
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
        self.z = 0.0
        self.angle: float = 0.0
        if enemy_type:
            self.enemy_type = enemy_type
        else:
            options = [k for k in C.ENEMY_TYPES if k != "health_pack"]
            self.enemy_type = random.choice(options)
        self.type_data = C.ENEMY_TYPES[self.enemy_type]
        self._init_stats(level, difficulty)
        self._init_visual_state(x, y)
        self._init_combat_state()

    def _init_stats(self, level: int, difficulty: str) -> None:
        """Compute and store health, damage, and speed from level and difficulty."""
        diff_stats = C.DIFFICULTIES.get(difficulty, C.DIFFICULTIES["NORMAL"])  # type: ignore
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
        """Initialize animation and position-tracking state."""
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

    def _init_combat_state(self) -> None:
        """Initialize death, pain, and frozen state flags."""
        self.dead = False
        self.death_timer = 0
        self.disintegrate_timer = 0
        self.removed = False
        self.pain_timer = 0
        self.frozen = False
        self.frozen_timer = 0

    def update(
        self, game_map: Map, player: Player, other_bots: list[Bot]
    ) -> Projectile | None:
        """Update bot AI"""
        if self._check_status_effects():
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

    def _check_status_effects(self) -> bool:
        """Check pain, frozen, and death states.

        Returns:
            bool: True if bot should skip update.
        """
        if self.frozen:
            self.frozen_timer -= 1
            if self.frozen_timer <= 0:
                self.frozen = False
            return True

        if self.pain_timer > 0:
            self.pain_timer -= 1
            return True

        if self.dead:
            self._update_death_animation()
            return True
        return False

    def _update_death_animation(self) -> None:
        """Advance the death / disintegration timers."""
        self.death_timer += 1
        if self.death_timer > DEATH_ANIMATION_FRAMES:
            self.disintegrate_timer += 1
            if self.disintegrate_timer > DISINTEGRATE_FRAMES:
                self.removed = True

    def _update_visual_animations(self) -> None:
        """Update shoot animation decay, eye rotation, drool, and mouth toggle."""
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

    def _try_attack(
        self,
        game_map: Map,
        player: Player,
        dist_sq: float,
        *,
        attack_range_sq: float,
        damage: int,
        speed: float,
        cooldown: int,
        color: tuple[int, int, int] = (255, 0, 0),
        size: float = 0.2,
    ) -> Projectile | None:
        """Attempt a ranged attack if in range, off cooldown, and has LOS.

        Returns:
            A new Projectile on success, otherwise None.
        """
        if dist_sq >= attack_range_sq or self.attack_timer > 0:
            return None
        if not self.has_line_of_sight(game_map, player):
            return None

        projectile = Projectile(
            self.x,
            self.y,
            self.angle,
            damage,
            speed,
            is_player=False,
            color=color,
            size=size,
        )
        self.attack_timer = cooldown
        self.shoot_animation = 1.0
        return projectile

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
        dist_sq: float,
        _other_bots: list[Bot],
    ) -> Projectile | None:
        """Rolling momentum logic -- accelerate, bounce off walls, crush player."""
        new_x, new_y = self._apply_ball_physics(game_map, player, dist_sq)
        self.x = new_x
        self.y = new_y
        self.angle = math.atan2(self.vy, self.vx)
        self._check_ball_crush(new_x, new_y, player)
        return None

    def _update_behavior_ninja(
        self, game_map: Map, player: Player, dist_sq: float, other_bots: list[Bot]
    ) -> Projectile | None:
        if dist_sq < 1.44 and self.attack_timer <= 0:  # 1.2^2
            if not player.god_mode:
                player.take_damage(self.damage)
            self.attack_timer = 30
            return None

        self._update_default_movement(game_map, player, other_bots)
        return None

    def _update_behavior_beast(
        self, game_map: Map, player: Player, dist_sq: float, other_bots: list[Bot]
    ) -> Projectile | None:
        projectile = self._try_attack(
            game_map,
            player,
            dist_sq,
            attack_range_sq=225,  # 15^2
            damage=self.damage * 2,
            speed=0.15,
            cooldown=120,
            color=(255, 100, 0),
            size=1.0,
        )
        if projectile is not None:
            return projectile
        self._update_default_movement(game_map, player, other_bots)
        return None

    def _update_behavior_minigunner(
        self, game_map: Map, player: Player, dist_sq: float, other_bots: list[Bot]
    ) -> Projectile | None:
        projectile = self._try_attack(
            game_map,
            player,
            dist_sq,
            attack_range_sq=144,  # 12^2
            damage=self.damage,
            speed=0.2,
            cooldown=10,
            color=(255, 255, 0),
            size=0.1,
        )
        if projectile is not None:
            return projectile
        self._update_default_movement(game_map, player, other_bots)
        return None

    def _update_behavior_sniper(
        self, game_map: Map, player: Player, dist_sq: float, other_bots: list[Bot]
    ) -> Projectile | None:
        projectile = self._try_attack(
            game_map,
            player,
            dist_sq,
            attack_range_sq=C.WEAPON_RANGE_SNIPER**2,
            damage=self.damage,
            speed=0.4,
            cooldown=180,
            color=(255, 0, 0),
            size=0.1,
        )
        if projectile is not None:
            return projectile
        self._update_default_movement(game_map, player, other_bots)
        return None

    def _update_behavior_standard(
        self, game_map: Map, player: Player, dist_sq: float, other_bots: list[Bot]
    ) -> Projectile | None:
        projectile = self._try_attack(
            game_map,
            player,
            dist_sq,
            attack_range_sq=C.BOT_ATTACK_RANGE**2,
            damage=C.BOT_PROJECTILE_DAMAGE + self.damage,
            speed=C.BOT_PROJECTILE_SPEED,
            cooldown=C.BOT_ATTACK_COOLDOWN,
        )
        if projectile is not None:
            return projectile

        self._update_default_movement(game_map, player, other_bots)
        return None

    def _check_bot_collisions(
        self,
        other_bots: list[Bot],
        new_x: float,
        new_y: float,
        move_dx: float,
        move_dy: float,
        game_map: Map,
    ) -> tuple[bool, bool]:
        """Check collisions against other bots and optionally push them (beast)."""
        collision_radius = 0.5 + (0.5 if self.enemy_type == "beast" else 0)
        col_sq = collision_radius * collision_radius
        can_move_x = not game_map.is_wall(new_x, self.y)
        can_move_y = not game_map.is_wall(self.x, new_y)

        for other_bot in other_bots:
            if other_bot is self or other_bot.dead:
                continue
            if (
                abs(self.x - other_bot.x) > C.MAX_COLLISION_DIST
                or abs(self.y - other_bot.y) > C.MAX_COLLISION_DIST
            ):
                continue
            can_move_x, can_move_y = self._test_bot_collision(
                other_bot,
                new_x,
                new_y,
                move_dx,
                move_dy,
                col_sq,
                can_move_x,
                can_move_y,
                game_map,
            )
            if not can_move_x and not can_move_y:
                break
        return can_move_x, can_move_y

    def _test_bot_collision(
        self,
        other_bot: Bot,
        new_x: float,
        new_y: float,
        move_dx: float,
        move_dy: float,
        col_sq: float,
        can_move_x: bool,
        can_move_y: bool,
        game_map: Map,
    ) -> tuple[bool, bool]:
        """Test one bot pair for x/y collision and apply beast push if needed."""
        if can_move_x:
            if (new_x - other_bot.x) ** 2 + (self.y - other_bot.y) ** 2 < col_sq:
                can_move_x = False
                if self.enemy_type == "beast":
                    push_x = other_bot.x + move_dx * 2
                    if not game_map.is_wall(push_x, other_bot.y):
                        other_bot.x = push_x
        if can_move_y:
            if (self.x - other_bot.x) ** 2 + (new_y - other_bot.y) ** 2 < col_sq:
                can_move_y = False
                if self.enemy_type == "beast":
                    push_y = other_bot.y + move_dy * 2
                    if not game_map.is_wall(other_bot.x, push_y):
                        other_bot.y = push_y
        return can_move_x, can_move_y

    def _update_walk_animation(self) -> None:
        """Advance walk animation if the bot moved this frame."""
        if abs(self.x - self.last_x) > 0.001 or abs(self.y - self.last_y) > 0.001:
            self.walk_animation += 0.3
            if self.walk_animation > 2 * math.pi:
                self.walk_animation -= 2 * math.pi
        self.last_x = self.x
        self.last_y = self.y

    def _update_default_movement(
        self, game_map: Map, player: Player, other_bots: list[Bot]
    ) -> None:
        # Move toward player (angle already set)
        move_dx = math.cos(self.angle) * self.speed
        move_dy = math.sin(self.angle) * self.speed
        new_x = self.x + move_dx
        new_y = self.y + move_dy

        can_move_x, can_move_y = self._check_bot_collisions(
            other_bots, new_x, new_y, move_dx, move_dy, game_map
        )

        if can_move_x:
            self.x = new_x
        if can_move_y:
            self.y = new_y

        self._update_walk_animation()

        if self.attack_timer > 0:
            self.attack_timer -= 1

    def has_line_of_sight(self, game_map: Map, player: Player) -> bool:
        """Check if bot has line of sight to player"""
        return has_line_of_sight(self.x, self.y, player.x, player.y, game_map)

    def freeze(self, duration: int) -> None:
        """Freeze the bot for a duration."""
        if not self.dead:
            self.frozen = True
            self.frozen_timer = duration

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
