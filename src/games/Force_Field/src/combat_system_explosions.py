"""Explosion methods extracted from CombatSystem.

This mixin provides bomb, laser, plasma, pulse, rocket, and freezer
AoE explosion logic.  It is mixed into CombatSystem so all public APIs
remain unchanged.
"""

from __future__ import annotations

import logging
import math
import random
from typing import TYPE_CHECKING

import pygame

from . import constants as C

if TYPE_CHECKING:
    from .bot import Bot
    from .game import Game
    from .player import Player
    from .projectile import Projectile

logger = logging.getLogger(__name__)


class _CombatSystemExplosionsMixin:
    """Mixin providing explosion/AoE handlers for CombatSystem."""

    # Provided by the owning CombatSystem instance
    game: Game

    @property
    def player(self) -> Player:  # type: ignore[empty-body]
        """Return the active player, raising ValueError if none exists."""
        ...

    def _handle_kill(self, bot: Bot) -> None:  # type: ignore[empty-body]
        """Record a kill -- implemented in CombatSystem."""
        ...

    # ------------------------------------------------------------------
    # Bomb explosion
    # ------------------------------------------------------------------

    def _add_bomb_particles(self, dist_to_player: float) -> None:
        """Spawn explosion particles if close enough to the player."""
        if dist_to_player >= 20:
            return
        if dist_to_player < 10:
            self.game.particle_system.add_particle(
                x=C.SCREEN_WIDTH // 2,
                y=C.SCREEN_HEIGHT // 2,
                dx=0,
                dy=0,
                color=C.WHITE,
                timer=20,
                size=3000,
            )
        explosion_center = (C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2)
        for _ in range(100):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5, 20)
            color = random.choice([C.ORANGE, C.RED, C.YELLOW, (50, 50, 50)])
            self.game.particle_system.add_particle(
                x=explosion_center[0],
                y=explosion_center[1],
                dx=math.cos(angle) * speed,
                dy=math.sin(angle) * speed,
                color=color,
                timer=random.randint(40, 80),
                size=random.randint(5, 15),
            )

    def _apply_bomb_damage_to_bots(
        self, projectile: Projectile, dist_to_player: float
    ) -> None:
        """Apply radius-falloff damage to every bot within the bomb blast."""
        for bot in self.game.bots:
            if not bot.alive:
                continue
            dx = bot.x - projectile.x
            dy = bot.y - projectile.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < C.BOMB_RADIUS:
                damage_factor = 1.0 - (dist / C.BOMB_RADIUS)
                damage = int(1000 * damage_factor)
                if bot.take_damage(damage):
                    self._handle_kill(bot)
                if dist < 5.0 and dist_to_player < 20:
                    self.game.particle_system.add_explosion(
                        C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2, count=3
                    )

    def explode_bomb(self, projectile: Projectile) -> None:
        """Handle bomb explosion logic"""
        dist_to_player = math.sqrt(
            (projectile.x - self.player.x) ** 2 + (projectile.y - self.player.y) ** 2
        )

        try:
            self.game.sound_manager.play_sound("bomb")
        except (pygame.error, OSError):
            logger.exception("Bomb Audio Failed")

        if dist_to_player < 30:
            self.game.screen_shake = max(0, 30 - dist_to_player)

        self._add_bomb_particles(dist_to_player)
        self._apply_bomb_damage_to_bots(projectile, dist_to_player)
        self.game.damage_texts.append(
            {
                "x": C.SCREEN_WIDTH // 2,
                "y": C.SCREEN_HEIGHT // 2 - 100,
                "text": "BOOM!",
                "color": C.ORANGE,
                "timer": 90,
                "vy": -0.5,
            }
        )

    # ------------------------------------------------------------------
    # Laser explosion
    # ------------------------------------------------------------------

    def _add_laser_particles(self) -> None:
        """Spawn laser impact particles at screen center."""
        for _ in range(10):
            self.game.particle_system.add_particle(
                x=C.SCREEN_WIDTH // 2,
                y=C.SCREEN_HEIGHT // 2,
                dx=random.uniform(-10, 10),
                dy=random.uniform(-10, 10),
                color=(
                    random.randint(200, 255),
                    0,
                    random.randint(200, 255),
                ),
                timer=40,
                size=random.randint(4, 8),
            )

    def explode_laser(self, impact_x: float, impact_y: float) -> None:
        """Trigger Massive Laser Explosion at Impact Point"""
        try:
            self.game.sound_manager.play_sound("boom_real")
        except (pygame.error, OSError):
            logger.exception("Boom sound failed")

        self.game.screen_shake = 10.0

        hits = 0
        for bot in self.game.bots:
            if not hasattr(bot, "alive"):
                continue
            if bot.alive:
                dist = math.sqrt((bot.x - impact_x) ** 2 + (bot.y - impact_y) ** 2)
                if dist < C.LASER_AOE_RADIUS:
                    killed = bot.take_damage(500)
                    hits += 1
                    if killed:
                        self._handle_kill(bot)
                    self._add_laser_particles()

        if hits > 0:
            self.game.damage_texts.append(
                {
                    "x": C.SCREEN_WIDTH // 2,
                    "y": C.SCREEN_HEIGHT // 2 - 80,
                    "text": "LASER ANNIHILATION!",
                    "color": (255, 0, 255),
                    "timer": 60,
                    "vy": -2,
                }
            )

    # ------------------------------------------------------------------
    # Generic AoE and projectile explosions
    # ------------------------------------------------------------------

    def _add_generic_explosion_particles(
        self, dist_to_player: float, weapon_type: str
    ) -> None:
        """Spawn AoE explosion particles when the player is nearby."""
        if dist_to_player >= 20:
            return
        count = 5 if weapon_type == "rocket" else 3
        self.game.particle_system.add_explosion(
            C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2, count=count
        )
        color = C.CYAN if weapon_type == "plasma" else C.ORANGE
        if weapon_type == "pulse":
            color = (100, 100, 255)
        elif weapon_type == "freezer":
            color = (200, 255, 255)
        for _ in range(20):
            self.game.particle_system.add_particle(
                x=C.SCREEN_WIDTH // 2,
                y=C.SCREEN_HEIGHT // 2,
                dx=random.uniform(-10, 10),
                dy=random.uniform(-10, 10),
                color=color,
                timer=40,
                size=random.randint(4, 8),
            )

    def _explode_generic(
        self, projectile: Projectile, radius: float, weapon_type: str
    ) -> None:
        """Generic explosion logic"""
        dist_to_player = math.sqrt(
            (projectile.x - self.player.x) ** 2 + (projectile.y - self.player.y) ** 2
        )
        if dist_to_player < 15:
            self.game.damage_flash_timer = 15
            self.game.screen_shake = 15.0 - dist_to_player

        self._add_generic_explosion_particles(dist_to_player, weapon_type)

        try:
            self.game.sound_manager.play_sound(
                "boom_real" if weapon_type == "rocket" else "shoot_plasma"
            )
        except (pygame.error, OSError):
            pass

        for bot in self.game.bots:
            if not bot.alive:
                continue
            dx = bot.x - projectile.x
            dy = bot.y - projectile.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < radius:
                damage_factor = 1.0 - (dist / radius)
                damage = int(projectile.damage * damage_factor)
                if bot.take_damage(damage):
                    self._handle_kill(bot)
                elif weapon_type == "freezer":
                    bot.freeze(180)  # Freeze for 3 seconds

    def explode_plasma(self, projectile: Projectile) -> None:
        """Trigger a plasma AoE explosion at the projectile's position."""
        self._explode_generic(projectile, C.PLASMA_AOE_RADIUS, "plasma")

    def explode_pulse(self, projectile: Projectile) -> None:
        """Trigger a pulse AoE explosion at the projectile's position."""
        self._explode_generic(projectile, C.PULSE_AOE_RADIUS, "pulse")

    def explode_rocket(self, projectile: Projectile) -> None:
        """Trigger a rocket AoE explosion using the configured blast radius."""
        radius = float(C.WEAPONS["rocket"].get("aoe_radius", 6.0))
        self._explode_generic(projectile, radius, "rocket")

    def explode_freezer(self, projectile: Projectile) -> None:
        """Trigger a freezer AoE explosion, slowing enemies within range."""
        self._explode_generic(projectile, 4.0, "freezer")  # Custom radius for freezer
