"""Shot visual and hit-damage helpers for CombatManagerBase.

This mixin provides secondary-hit handling, damage application, and
shot tracer/impact visual effects.  Mixed into CombatManagerBase.
"""

from __future__ import annotations

import logging
import math
import random
from typing import Any

import pygame

logger = logging.getLogger(__name__)


class _CombatVisualsMixin:
    """Mixin providing shot visuals and damage helpers for CombatManagerBase.

    Requires the concrete class to supply:
      self.C              - game constants module
      self.particle_system
      self.handle_kill(bot)
      self.explode_laser(x, y, damage_texts)
    """

    def _handle_secondary_hit(
        self,
        player: Any,
        closest_bot: Any | None,
        closest_dist: float,
        wall_dist: float,
        damage_texts: list[dict[str, Any]],
    ) -> None:
        """Handle secondary fire (laser explosion at impact)."""
        impact_dist = (
            closest_dist if (closest_bot and closest_dist < wall_dist) else wall_dist
        )
        ray_angle = player.angle
        impact_x = player.x + math.cos(ray_angle) * impact_dist
        impact_y = player.y + math.sin(ray_angle) * impact_dist

        try:
            self.explode_laser(impact_x, impact_y, damage_texts)  # type: ignore[attr-defined]
        except (ValueError, AttributeError, pygame.error):
            logger.exception("Error in explode_laser")

        laser_duration = getattr(self.C, "LASER_DURATION", 10)  # type: ignore[attr-defined]
        laser_width = getattr(self.C, "LASER_WIDTH", 5)  # type: ignore[attr-defined]
        self.particle_system.add_laser(  # type: ignore[attr-defined]
            start=(self.C.SCREEN_WIDTH - 200, self.C.SCREEN_HEIGHT - 180),  # type: ignore[attr-defined]
            end=(self.C.SCREEN_WIDTH // 2, self.C.SCREEN_HEIGHT // 2),  # type: ignore[attr-defined]
            color=(0, 255, 255),
            timer=laser_duration,
            width=laser_width,
        )

    def _apply_hit_damage(
        self,
        player: Any,
        bot: Any,
        distance: float,
        weapon_range: float,
        base_damage: int,
        is_headshot: bool,
        damage_texts: list[dict[str, Any]],
        show_damage: bool,
    ) -> None:
        """Apply damage to a bot that was hit."""
        final_damage = self._calculate_final_damage(
            player, bot, distance, weapon_range, base_damage
        )
        bot.take_damage(final_damage, is_headshot=is_headshot)

        if show_damage:
            self._append_damage_text(damage_texts, final_damage, is_headshot)

        self._spawn_hit_particles()

        if not bot.alive:
            self.handle_kill(bot)  # type: ignore[attr-defined]

    def _calculate_final_damage(
        self,
        player: Any,
        bot: Any,
        distance: float,
        weapon_range: float,
        base_damage: int,
    ) -> int:
        """Return damage after applying range and accuracy factors."""
        range_factor = max(0.3, 1.0 - (distance / weapon_range))
        dx = bot.x - player.x
        dy = bot.y - player.y
        bot_angle = math.atan2(dy, dx)
        if bot_angle < 0:
            bot_angle += 2 * math.pi
        angle_diff = abs(bot_angle - player.angle)
        if angle_diff > math.pi:
            angle_diff = 2 * math.pi - angle_diff
        accuracy_factor = max(0.5, 1.0 - (angle_diff / 0.15))
        return int(base_damage * range_factor * accuracy_factor)

    def _append_damage_text(
        self,
        damage_texts: list[dict[str, Any]],
        final_damage: int,
        is_headshot: bool,
    ) -> None:
        """Append a floating damage number to the HUD list."""
        damage_color = getattr(self.C, "DAMAGE_TEXT_COLOR", (255, 255, 255))  # type: ignore[attr-defined]
        damage_texts.append(
            {
                "x": self.C.SCREEN_WIDTH // 2 + random.randint(-20, 20),  # type: ignore[attr-defined]
                "y": self.C.SCREEN_HEIGHT // 2 - 50,  # type: ignore[attr-defined]
                "text": str(final_damage) + ("!" if is_headshot else ""),
                "color": self.C.RED if is_headshot else damage_color,  # type: ignore[attr-defined]
                "timer": 60,
                "vy": -1.0,
            }
        )

    def _spawn_hit_particles(self) -> None:
        """Spawn screen-space hit particle effects."""
        sw2 = self.C.SCREEN_WIDTH // 2  # type: ignore[attr-defined]
        sh2 = self.C.SCREEN_HEIGHT // 2  # type: ignore[attr-defined]
        self.particle_system.add_explosion(sw2, sh2, count=5)  # type: ignore[attr-defined]
        blood_color = getattr(self.C, "BLUE_BLOOD", (0, 0, 200))  # type: ignore[attr-defined]
        particle_lifetime = getattr(self.C, "PARTICLE_LIFETIME", 30)  # type: ignore[attr-defined]
        for _ in range(10):
            self.particle_system.add_particle(  # type: ignore[attr-defined]
                x=sw2,
                y=sh2,
                dx=random.uniform(-5, 5),
                dy=random.uniform(-5, 5),
                color=blood_color,
                timer=particle_lifetime,
                size=random.randint(2, 5),
            )

    def _add_shot_visuals(
        self,
        player: Any,
        aim_angle: float,
        closest_bot: Any | None,
        closest_dist: float,
        wall_dist: float,
    ) -> None:
        """Add tracer and impact visual effects."""
        fov = getattr(self.C, "FOV", 1.0)  # type: ignore[attr-defined]
        angle_diff = aim_angle - player.angle
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

        screen_hit_x = (0.5 - angle_diff / fov) * self.C.SCREEN_WIDTH  # type: ignore[attr-defined]
        screen_hit_y = self.C.SCREEN_HEIGHT // 2 + getattr(player, "pitch", 0)  # type: ignore[attr-defined]

        self.particle_system.add_trace(  # type: ignore[attr-defined]
            start=(self.C.SCREEN_WIDTH * 0.6, self.C.SCREEN_HEIGHT),  # type: ignore[attr-defined]
            end=(screen_hit_x, screen_hit_y),
            color=(255, 255, 100),
            timer=5,
            width=1,
        )

        if not closest_bot:
            hit_world_x = player.x + math.cos(aim_angle) * wall_dist
            hit_world_y = player.y + math.sin(aim_angle) * wall_dist
            self.particle_system.add_world_explosion(  # type: ignore[attr-defined]
                hit_world_x,
                hit_world_y,
                0.5,
                count=10,
                color=(255, 200, 100),
                speed=0.1,
            )
            for _ in range(5):
                self.particle_system.add_particle(  # type: ignore[attr-defined]
                    x=screen_hit_x,
                    y=screen_hit_y,
                    dx=random.uniform(-3, 3),
                    dy=random.uniform(-3, 3),
                    color=(255, 200, 100),
                    timer=20,
                    size=random.randint(1, 3),
                )
