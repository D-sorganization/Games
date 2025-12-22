from __future__ import annotations

import logging
import math
import random
from typing import TYPE_CHECKING, Any, cast

import pygame

from . import constants as C  # noqa: N812
from .weapon_renderer import WeaponRenderer

if TYPE_CHECKING:
    from .game import Game
    from .player import Player

logger = logging.getLogger(__name__)


class GameRenderer:
    """Handles 3D world rendering and game view composition"""

    def __init__(self, screen: pygame.Surface) -> None:
        """Initialize the game renderer with a screen surface."""
        self.screen = screen
        self.weapon_renderer = WeaponRenderer(screen)

        # Optimization: Shared surface for alpha effects
        size = (C.SCREEN_WIDTH, C.SCREEN_HEIGHT)
        self.effects_surface = pygame.Surface(size, pygame.SRCALPHA)

    def render_game(self, game: Game) -> None:
        """Render gameplay"""
        assert game.raycaster is not None
        assert game.player is not None

        # Calculate Head Bob
        bob_offset = 0.0
        if game.player.is_moving:
            bob_offset = math.sin(pygame.time.get_ticks() * 0.015) * 15.0

        # 1. 3D World (Raycaster)
        game.raycaster.render_floor_ceiling(
            self.screen, game.player, game.level, view_offset_y=bob_offset
        )
        game.raycaster.render_3d(
            self.screen, game.player, game.bots, game.level, view_offset_y=bob_offset
        )
        game.raycaster.render_projectiles(
            self.screen, game.player, game.projectiles, view_offset_y=bob_offset
        )

        # 2. Effects
        self.effects_surface.fill((0, 0, 0, 0))
        self._render_particles(game.particle_system.particles)
        self.screen.blit(self.effects_surface, (0, 0))

        # 3. Portal
        self._render_portal(game.portal, game.player)

        # 4. Weapon Model
        weapon_pos = self.weapon_renderer.render_weapon(game.player)
        if game.player.shooting:
            self.weapon_renderer.render_muzzle_flash(game.player.current_weapon, weapon_pos)

        # 5. UI / HUD
        game.ui_renderer.render_hud(game)

        pygame.display.flip()

    def _render_particles(self, particles: list[Any]) -> None:
        """Render particle effects including lasers and explosion particles.

        Args:
            particles: List of Particle objects.
        """
        for p in particles:
            # Handle Particle Object
            if p.ptype == "laser":
                alpha = int(255 * (p.timer / C.LASER_DURATION))
                start = p.start_pos
                end = p.end_pos
                color = (*p.color, alpha)
                pygame.draw.line(self.effects_surface, color, start, end, p.width)
                # Spread
                for i in range(5):
                    offset = (i - 2) * 20
                    target_end = (end[0] + offset, end[1])
                    pygame.draw.line(
                        self.effects_surface,
                        (*p.color, max(0, alpha - 50)),
                        start,
                        target_end,
                        max(1, p.width // 2),
                    )
            elif p.ptype == "normal":
                ratio = p.timer / C.PARTICLE_LIFETIME
                alpha = int(255 * ratio)
                alpha = max(0, min(255, alpha))
                color = p.color
                rgba = (*color, alpha) if len(color) == 3 else (*color[:3], alpha)
                pygame.draw.circle(
                    self.effects_surface,
                    rgba,
                    (int(p.x), int(p.y)),
                    int(p.size),
                )

    def _render_portal(self, portal: dict[str, Any] | None, player: Player) -> None:
        """Render portal visual effects if active.

        Args:
            portal: Portal dictionary with position and state, or None if inactive.
            player: The player object for relative positioning.
        """
        if portal:
            sx = portal["x"] - player.x
            sy = portal["y"] - player.y

            cs = math.cos(player.angle)
            sn = math.sin(player.angle)
            a = sy * cs - sx * sn
            b = sx * cs + sy * sn

            if b > 0.1:
                screen_x = int((0.5 * C.SCREEN_WIDTH) * (1 + a / b * 2.0))
                screen_y = C.SCREEN_HEIGHT // 2
                size = int(800 / b)

                if -size < screen_x < C.SCREEN_WIDTH + size:
                    color = (0, 255, 255)
                    # Draw rings
                    center = (screen_x, screen_y)
                    pygame.draw.circle(self.screen, color, center, size // 2, 2)
                    pygame.draw.circle(self.screen, C.WHITE, center, size // 4, 1)

