"""Enemy behavior handlers extracted from Bot to keep file size under 500 lines.

Each handler follows the uniform signature::

    def _update_behavior_<type>(
        self, game_map: Map, player: Player, dist_sq: float, other_bots: list[Bot]
    ) -> Projectile | None:
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .projectile import Projectile

if TYPE_CHECKING:
    from .map import Map
    from .player import Player


class BotBehaviorMixin:
    """Mixin providing type-specific enemy behavior handlers."""

    # ------------------------------------------------------------------
    # Ball behavior
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
        _other_bots: list,
    ) -> Projectile | None:
        """Rolling momentum logic -- accelerate, bounce off walls, crush player."""
        new_x, new_y = self._apply_ball_physics(game_map, player, dist_sq)
        self.x = new_x
        self.y = new_y
        self.angle = math.atan2(self.vy, self.vx)
        self._check_ball_crush(new_x, new_y, player)
        return None

    # ------------------------------------------------------------------
    # Ninja behavior
    # ------------------------------------------------------------------

    def _update_behavior_ninja(
        self, game_map: Map, player: Player, dist_sq: float, other_bots: list
    ) -> Projectile | None:
        if dist_sq < 1.44 and self.attack_timer <= 0:  # 1.2^2
            if not player.god_mode:
                player.take_damage(self.damage)
            self.attack_timer = 30
            return None

        self._update_default_movement(game_map, player, other_bots)
        return None

    # ------------------------------------------------------------------
    # Beast behavior
    # ------------------------------------------------------------------

    def _update_behavior_beast(
        self, game_map: Map, player: Player, dist_sq: float, other_bots: list
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

    # ------------------------------------------------------------------
    # Minigunner behavior
    # ------------------------------------------------------------------

    def _update_behavior_minigunner(
        self, game_map: Map, player: Player, dist_sq: float, other_bots: list
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

    # ------------------------------------------------------------------
    # Sniper behavior
    # ------------------------------------------------------------------

    def _update_behavior_sniper(
        self, game_map: Map, player: Player, dist_sq: float, other_bots: list
    ) -> Projectile | None:
        from . import constants as C  # noqa: N812

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

    # ------------------------------------------------------------------
    # Standard / fallback behavior
    # ------------------------------------------------------------------

    def _update_behavior_standard(
        self, game_map: Map, player: Player, dist_sq: float, other_bots: list
    ) -> Projectile | None:
        from . import constants as C  # noqa: N812

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
