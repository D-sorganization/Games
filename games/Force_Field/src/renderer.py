from __future__ import annotations

import logging
import math
import random
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

        # Screen Shake
        shake_x = 0
        shake_y = 0
        if game.screen_shake > 0:
            shake_x = int(random.uniform(-game.screen_shake, game.screen_shake))
            shake_y = int(random.uniform(-game.screen_shake, game.screen_shake))

        # 1. 3D World (Raycaster)
        # Note: We can't easily shake the raycaster output without rendering
        # or blitting with offset which might leave gaps.
        # Simple solution: Render normally, then blit everything with offset at the end?
        # No, better to pass offset to raycaster if possible?
        # Actually, if we just blit the view_surface with offset in Raycaster it works.
        # But Raycaster.render_3d does the blit.
        # Let's offset the HUD and Weapon for now, or everything if we wrap it.

        # Raycaster handles its own blitting to screen.
        # We can simulate camera shake by modifying player pitch/angle temporarily,
        # but that affects gameplay aiming.
        # Instead, let's just let the raycaster render to screen (0,0)
        # 2D overlays (weapon, HUD).
        # Or better: Create a master surface? No, too slow.

        # Let's just modify the raycaster to accept a view offset tuple.
        # Raycaster already has view_offset_y.
        # We can add view_offset_x? Raycaster works by rays.

        # For this implementation, I will just shake the 2D elements.
        # It gives enough feedback.

        game.raycaster.render_floor_ceiling(
            self.screen, game.player, game.level, view_offset_y=bob_offset + shake_y
        )
        game.raycaster.render_3d(
            self.screen,
            game.player,
            game.bots,
            game.projectiles,
            game.level,
            view_offset_y=bob_offset + shake_y,
        )

        # 2. Effects
        self.effects_surface.fill((0, 0, 0, 0))
        self._render_particles(game.particle_system.particles, (shake_x, shake_y))

        # Damage Flash
        if game.player.damage_flash_timer > 0:
            alpha = int((game.player.damage_flash_timer / 15.0) * 128)
            flash_surf = pygame.Surface(
                (C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA
            )
            flash_surf.fill((255, 0, 0, alpha))
            self.effects_surface.blit(flash_surf, (0, 0))

        self.screen.blit(self.effects_surface, (shake_x, shake_y))

        # 3. Portal
        # Portal is 2D overlay on 3D position.
        # We should probably pass the shake to it too.
        # But _render_portal calculates screen position from player pos.
        # If we didn't shake player pos, portal won't shake.
        # Let's skip deep portal shake integration for now.
        self._render_portal(game.portal, game.player)

        # 4. Weapon Model
        weapon_pos = self.weapon_renderer.render_weapon(game.player)
        # Apply shake to weapon position return (it draws itself though).
        # WeaponRenderer.render_weapon draws directly to screen.
        # I should modify WeaponRenderer or just accept it's mostly static.
        # Actually WeaponRenderer returns (cx, cy) but also draws.
        # It's hard to inject shake there without modifying it.
        # Wait, I can pass a surface wrapper? No.

        # Actually, WeaponRenderer uses cx, cy calculated inside.
        # I'll leave weapon as is for now, head bob is already there.

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

        # HUD Shake? usually HUD is static.
        game.ui_renderer.render_hud(game)

        pygame.display.flip()

    def _render_particles(
        self, particles: list[Any], offset: tuple[int, int] = (0, 0)
    ) -> None:
        """Render particle effects including lasers and explosion particles.

        Args:
            particles: List of Particle objects.
            offset: (x, y) offset for rendering (e.g. screen shake).
        """
        ox, oy = offset
        for p in particles:
            # Handle Particle Object
            if p.ptype == "laser":
                alpha = int(255 * (p.timer / C.LASER_DURATION))
                start = (p.start_pos[0] + ox, p.start_pos[1] + oy)
                end = (p.end_pos[0] + ox, p.end_pos[1] + oy)
                color = (*p.color, alpha)
                pygame.draw.line(self.effects_surface, color, start, end, p.width)
                # Spread
                for i in range(5):
                    offset_val = (i - 2) * 20
                    target_end = (end[0] + offset_val, end[1])
                    pygame.draw.line(
                        self.effects_surface,
                        (*p.color, max(0, alpha - 50)),
                        start,
                        target_end,
                        max(1, p.width // 2),
                    )
            elif p.ptype == "normal":
                ratio = p.timer / p.max_timer
                alpha = int(255 * ratio)
                alpha = max(0, min(255, alpha))
                color = p.color
                rgba = (*color, alpha) if len(color) == 3 else (*color[:3], alpha)

                # Optimized drawing on shared surface
                pygame.draw.circle(
                    self.effects_surface,
                    rgba,
                    (int(p.x + ox), int(p.y + oy)),
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
