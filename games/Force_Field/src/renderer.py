from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Any

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

        # Pre-calculated colors or surfaces can be added here if needed
        self._portal_glow_surface_cache: dict[int, pygame.Surface] = {}

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
            self.screen,
            game.player,
            game.bots,
            game.projectiles,
            game.level,
            view_offset_y=bob_offset,
        )

        # 2. Effects
        self.effects_surface.fill((0, 0, 0, 0))
        self._render_particles(game.particle_system.particles)

        # Damage Flash
        if game.player.damage_flash_timer > 0:
            alpha = int((game.player.damage_flash_timer / 15.0) * 128)
            flash_surf = pygame.Surface(
                (C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA
            )
            flash_surf.fill((255, 0, 0, alpha))
            self.effects_surface.blit(flash_surf, (0, 0))

        self.screen.blit(self.effects_surface, (0, 0))

        # 3. Portal
        self._render_portal(game.portal, game.player)

        # 4. Weapon Model
        weapon_pos = self.weapon_renderer.render_weapon(game.player)
        if game.player.shooting:
            self.weapon_renderer.render_muzzle_flash(
                game.player.current_weapon, weapon_pos
            )

        # 5. UI / HUD
        if game.show_minimap:
            game.raycaster.render_minimap(
                self.screen,
                game.player,
                game.bots,
                game.visited_cells,
                game.portal,
            )
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
        if not portal:
            return

        sx = portal["x"] - player.x
        sy = portal["y"] - player.y

        cs = math.cos(player.angle)
        sn = math.sin(player.angle)
        a = sy * cs - sx * sn
        b = sx * cs + sy * sn

        if b <= 0.1:
            return

        screen_x = int((0.5 * C.SCREEN_WIDTH) * (1 + a / b * 2.0))
        screen_y = C.SCREEN_HEIGHT // 2
        base_size = int(800 / b)

        if not (-base_size < screen_x < C.SCREEN_WIDTH + base_size):
            return

        center = (screen_x, screen_y)
        time_ms = pygame.time.get_ticks()

        # Pulsing animation
        pulse1 = math.sin(time_ms * 0.008) * 0.3 + 1.0  # Slow pulse
        pulse2 = math.sin(time_ms * 0.015) * 0.2 + 1.0  # Fast pulse
        rotation = time_ms * 0.002  # Rotation effect

        # Draw outer glow effect
        glow_size = int(base_size * 0.9)
        if glow_size > 0:
            glow_key = glow_size // 10 * 10  # Cache key rounding
            if glow_key not in self._portal_glow_surface_cache:
                s_size = glow_key * 2 + 4
                surf = pygame.Surface((s_size, s_size), pygame.SRCALPHA)
                pygame.draw.circle(
                    surf,
                    (0, 200, 255, 30),
                    (s_size // 2, s_size // 2),
                    glow_key,
                )
                self._portal_glow_surface_cache[glow_key] = surf

            cached_glow = self._portal_glow_surface_cache.get(glow_key)
            if cached_glow:
                glow_rect = cached_glow.get_rect(center=center)
                self.screen.blit(cached_glow, glow_rect)

        # Draw plasma rings - simplified for loop
        ring_configs = [
            (0.8 * pulse1, (0, 255, 255), 8),
            (0.6 * pulse2, (100, 255, 255), 6),
            (0.4 * pulse1, (200, 255, 255), 4),
            (0.2 * pulse2, (255, 255, 255), 3),
        ]

        for scale, color, width in ring_configs:
            size = int(base_size * scale)
            if size > 0:
                pygame.draw.circle(self.screen, color, center, size, width)
                # Inner glow (simple brighter line)
                inner_color = tuple(min(255, c + 50) for c in color)
                pygame.draw.circle(
                    self.screen,
                    inner_color,
                    center,
                    max(1, size - width // 2),
                    2,
                )

        # Rotating energy arcs
        arc_radius = base_size * 0.7 * pulse1
        for i in range(4):
            arc_angle = rotation + (i * math.pi / 2)
            # Pre-calculate cos/sin
            arc_cos = math.cos(arc_angle)
            arc_sin = math.sin(arc_angle)

            arc_start = (
                screen_x + arc_cos * arc_radius * 0.8,
                screen_y + arc_sin * arc_radius * 0.8,
            )
            arc_end = (
                screen_x + arc_cos * arc_radius,
                screen_y + arc_sin * arc_radius,
            )
            pygame.draw.line(self.screen, (255, 255, 255), arc_start, arc_end, 3)

        # Central energy core
        core_pulse = math.sin(time_ms * 0.02) * 0.5 + 1.0
        core_size = int(base_size * 0.1 * core_pulse)
        if core_size > 0:
            core_colors = [(255, 255, 255), (200, 255, 255), (100, 255, 255)]
            for i, color in enumerate(core_colors):
                s = core_size - i * 2
                if s > 0:
                    pygame.draw.circle(self.screen, color, center, s, 0)
