"""Explosion-related methods for CombatManagerBase.

This mixin provides bomb, laser, and generic AOE explosion logic.  It is
mixed into CombatManagerBase so all public APIs remain unchanged.
"""

from __future__ import annotations

import logging
import math
import random
from contextlib import suppress
from typing import Any

import pygame

logger = logging.getLogger(__name__)


class _CombatExplosionsMixin:
    """Mixin providing explosion helpers for CombatManagerBase.

    Requires the concrete class to supply:
      self.C              - game constants module
      self.particle_system
      self.sound_manager
      self.entity_manager
      self.handle_kill(bot)
    """

    def handle_bomb_explosion(
        self,
        player: Any,
        bots: list[Any],
        damage_texts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Handle bomb explosion centered on the player."""
        sw2 = self.C.SCREEN_WIDTH // 2  # type: ignore[attr-defined]
        sh2 = self.C.SCREEN_HEIGHT // 2  # type: ignore[attr-defined]

        self._spawn_bomb_particles(sw2, sh2, player)  # type: ignore[attr-defined]
        self._apply_bomb_damage(player, bots, sw2, sh2)  # type: ignore[attr-defined]

        with suppress(pygame.error, OSError):
            self.sound_manager.play_sound("bomb")  # type: ignore[attr-defined]

        damage_texts.append(
            {
                "x": sw2,
                "y": sh2 - 100,
                "text": "BOMB DROPPED!",
                "color": self.C.ORANGE,  # type: ignore[attr-defined]
                "timer": 120,
                "vy": -0.5,
            }
        )
        return damage_texts

    def _spawn_bomb_particles(self, sw2: int, sh2: int, player: Any) -> None:
        """Spawn screen-space and world-space particles for a bomb explosion."""
        self.particle_system.add_particle(  # type: ignore[attr-defined]
            x=sw2,
            y=sh2,
            dx=0,
            dy=0,
            color=self.C.WHITE,  # type: ignore[attr-defined]
            timer=40,
            size=3000,
        )
        self.particle_system.add_world_explosion(  # type: ignore[attr-defined]
            player.x,
            player.y,
            0.5,
            count=100,
            color=self.C.ORANGE,  # type: ignore[attr-defined]
            speed=0.5,
        )
        for _ in range(300):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5, 25)
            color = random.choice(
                [
                    self.C.ORANGE,  # type: ignore[attr-defined]
                    self.C.RED,  # type: ignore[attr-defined]
                    self.C.YELLOW,  # type: ignore[attr-defined]
                    getattr(self.C, "DARK_RED", (139, 0, 0)),  # type: ignore[attr-defined]
                    (50, 50, 50),
                ]
            )
            self.particle_system.add_particle(  # type: ignore[attr-defined]
                x=sw2,
                y=sh2,
                dx=math.cos(angle) * speed,
                dy=math.sin(angle) * speed,
                color=color,
                timer=random.randint(40, 100),
                size=random.randint(5, 25),
            )

    def _apply_bomb_damage(
        self, player: Any, bots: list[Any], sw2: int, sh2: int
    ) -> None:
        """Apply AOE damage to bots in bomb radius."""
        bomb_radius = getattr(self.C, "BOMB_RADIUS", 10.0)  # type: ignore[attr-defined]
        for bot in bots:
            if not bot.alive:
                continue
            dx = bot.x - player.x
            dy = bot.y - player.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < bomb_radius:
                if bot.take_damage(1000):
                    self.handle_kill(bot)  # type: ignore[attr-defined]
                if dist < 5.0:
                    self.particle_system.add_explosion(sw2, sh2, count=3)  # type: ignore[attr-defined]

    def explode_laser(
        self,
        impact_x: float,
        impact_y: float,
        damage_texts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Trigger a laser AOE explosion at an impact point."""
        with suppress(pygame.error, OSError):
            self.sound_manager.play_sound("boom_real")  # type: ignore[attr-defined]

        try:
            self.particle_system.add_world_explosion(  # type: ignore[attr-defined]
                impact_x,
                impact_y,
                0.5,
                count=80,
                color=(0, 255, 255),
                speed=0.4,
            )
            sw2 = self.C.SCREEN_WIDTH // 2  # type: ignore[attr-defined]
            sh2 = self.C.SCREEN_HEIGHT // 2  # type: ignore[attr-defined]
            laser_radius = getattr(self.C, "LASER_AOE_RADIUS", 5.0)  # type: ignore[attr-defined]
            hits = self._apply_laser_damage(impact_x, impact_y, laser_radius, sw2, sh2)  # type: ignore[attr-defined]
            if hits > 0:
                damage_texts.append(
                    {
                        "x": sw2,
                        "y": sh2 - 80,
                        "text": "LASER ANNIHILATION!",
                        "color": (255, 0, 255),
                        "timer": 60,
                        "vy": -2,
                    }
                )
        except (ValueError, AttributeError, pygame.error):
            logger.exception("Critical Laser Error")

        return damage_texts

    def _apply_laser_damage(
        self,
        impact_x: float,
        impact_y: float,
        laser_radius: float,
        sw2: int,
        sh2: int,
    ) -> int:
        """Apply AOE damage to bots within laser radius; return hit count."""
        hits = 0
        for bot in self.entity_manager.bots:  # type: ignore[attr-defined]
            if not getattr(bot, "alive", False):
                continue
            dist = math.sqrt((bot.x - impact_x) ** 2 + (bot.y - impact_y) ** 2)
            if dist < laser_radius:
                killed = bot.take_damage(500)
                hits += 1
                if killed:
                    self.handle_kill(bot)  # type: ignore[attr-defined]
                for _ in range(10):
                    self.particle_system.add_particle(  # type: ignore[attr-defined]
                        x=sw2,
                        y=sh2,
                        dx=random.uniform(-10, 10),
                        dy=random.uniform(-10, 10),
                        color=(random.randint(200, 255), 0, random.randint(200, 255)),
                        timer=40,
                        size=random.randint(4, 8),
                    )
        return hits

    def explode_generic(
        self,
        projectile: Any,
        radius: float,
        weapon_type: str,
        player: Any,
        damage_flash_timer: int,
    ) -> int:
        """Generic AOE explosion around a projectile impact."""
        dist_to_player = math.sqrt(
            (projectile.x - player.x) ** 2 + (projectile.y - player.y) ** 2
        )
        if dist_to_player < 15:
            damage_flash_timer = 15

        sw2 = self.C.SCREEN_WIDTH // 2  # type: ignore[attr-defined]
        sh2 = self.C.SCREEN_HEIGHT // 2  # type: ignore[attr-defined]
        color = self.C.CYAN if weapon_type == "plasma" else self.C.ORANGE  # type: ignore[attr-defined]

        self._spawn_generic_explosion_fx(
            projectile, dist_to_player, weapon_type, color, sw2, sh2
        )  # type: ignore[attr-defined]

        with suppress(pygame.error, OSError):
            self.sound_manager.play_sound(  # type: ignore[attr-defined]
                "boom_real" if weapon_type == "rocket" else "shoot_plasma"
            )

        self._apply_generic_aoe_damage(projectile, radius)  # type: ignore[attr-defined]
        return damage_flash_timer

    def _spawn_generic_explosion_fx(
        self,
        projectile: Any,
        dist_to_player: float,
        weapon_type: str,
        color: tuple[int, int, int],
        sw2: int,
        sh2: int,
    ) -> None:
        """Spawn world and screen particles for a generic explosion."""
        self.particle_system.add_world_explosion(  # type: ignore[attr-defined]
            projectile.x,
            projectile.y,
            getattr(projectile, "z", 0.5),
            count=50,
            color=color,
            speed=0.3,
        )
        if dist_to_player < 20:
            count = 5 if weapon_type == "rocket" else 3
            self.particle_system.add_explosion(sw2, sh2, count=count)  # type: ignore[attr-defined]
            for _ in range(20):
                self.particle_system.add_particle(  # type: ignore[attr-defined]
                    x=sw2,
                    y=sh2,
                    dx=random.uniform(-10, 10),
                    dy=random.uniform(-10, 10),
                    color=color,
                    timer=40,
                    size=random.randint(4, 8),
                )

    def _apply_generic_aoe_damage(self, projectile: Any, radius: float) -> None:
        """Apply damage to bots within AOE radius of a projectile."""
        for bot in self.entity_manager.bots:  # type: ignore[attr-defined]
            if not bot.alive:
                continue
            dx = bot.x - projectile.x
            dy = bot.y - projectile.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < radius:
                damage = int(projectile.damage * (1.0 - dist / radius))
                if bot.take_damage(damage):
                    self.handle_kill(bot)  # type: ignore[attr-defined]
