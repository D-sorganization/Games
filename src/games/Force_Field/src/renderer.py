from __future__ import annotations

import logging
import math
import random
from typing import TYPE_CHECKING, Any

import pygame

from games.shared.interfaces import Portal

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
        """Render gameplay.

        Preconditions (DbC):
            - ``game.raycaster`` is not None.
            - ``game.player`` is not None.

        Thin orchestrator: computes camera offsets, renders the 3D world,
        overlay effects, portal, weapon, HUD, and flips the display. Order
        of operations is preserved to keep the frame output identical.
        """
        if not (game.raycaster is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        if not (game.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")

        bob_offset, shake_x, shake_y = self._compute_camera_offsets(game)
        self._render_world(game, bob_offset, shake_y)
        self._render_effects_layer(game, shake_x, shake_y)
        self._render_portal(game.portal, game.player)  # type: ignore
        self._render_weapon_layer(game)
        self._render_hud_layer(game)

        pygame.display.flip()

    def _compute_camera_offsets(self, game: Game) -> tuple[float, int, int]:
        """Compute head-bob and screen-shake offsets for the current frame."""
        # Use player's bob_phase for consistent movement
        bob_offset = math.sin(game.player.bob_phase) * 10.0

        shake_x = 0
        shake_y = 0
        if game.screen_shake > 0:
            shake_x = int(random.uniform(-game.screen_shake, game.screen_shake))
            shake_y = int(random.uniform(-game.screen_shake, game.screen_shake))

        return bob_offset, shake_x, shake_y

    def _render_world(self, game: Game, bob_offset: float, shake_y: int) -> None:
        """Render the 3D world (floor/ceiling and raycast scene)."""
        # Raycaster handles its own blitting to screen. We simulate camera
        # shake on 2D elements only to avoid affecting aiming.
        game.raycaster.render_floor_ceiling(
            self.screen, game.player, game.level, view_offset_y=bob_offset + shake_y
        )
        game.raycaster.render_3d(
            self.screen,
            game.player,
            game.bots,
            game.level,
            view_offset_y=bob_offset + shake_y,
            projectiles=game.projectiles,
        )

    def _render_effects_layer(self, game: Game, shake_x: int, shake_y: int) -> None:
        """Render particles and damage flash to the effects surface, then blit."""
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

    def _render_weapon_layer(self, game: Game) -> None:
        """Render the weapon model and muzzle flash if firing."""
        # WeaponRenderer.render_weapon draws directly to screen and returns
        # the (cx, cy) position used to anchor the muzzle flash.
        weapon_pos = self.weapon_renderer.render_weapon(game.player)

        if game.player.shooting:
            self.weapon_renderer.render_muzzle_flash(
                game.player.current_weapon, weapon_pos
            )

    def _render_hud_layer(self, game: Game) -> None:
        """Render the minimap (if enabled) and HUD."""
        if game.show_minimap:
            game.raycaster.render_minimap(
                self.screen,
                game.player,
                game.bots,
                game.visited_cells,
                game.portal,
            )

        # HUD is intentionally static (no shake applied).
        game.ui_renderer.render_hud(game)

    def _render_particles(
        self, particles: list[Any], offset: tuple[int, int] = (0, 0)
    ) -> None:
        """Dispatch each particle to its type-specific sub-renderer."""
        ox, oy = offset
        for p in particles:
            if p.ptype == "laser":
                self._render_laser_particle(p, ox, oy)
            elif p.ptype == "normal":
                self._render_normal_particle(p, ox, oy)

    def _render_laser_particle(self, p: Any, ox: int, oy: int) -> None:
        """Draw a laser beam with fanned spread lines."""
        alpha = int(255 * (p.timer / C.LASER_DURATION))
        start = (p.start_pos[0] + ox, p.start_pos[1] + oy)
        end = (p.end_pos[0] + ox, p.end_pos[1] + oy)
        pygame.draw.line(self.effects_surface, (*p.color, alpha), start, end, p.width)
        for i in range(5):
            target_end = (end[0] + (i - 2) * 20, end[1])
            pygame.draw.line(
                self.effects_surface,
                (*p.color, max(0, alpha - 50)),
                start,
                target_end,
                max(1, p.width // 2),
            )

    def _render_normal_particle(self, p: Any, ox: int, oy: int) -> None:
        """Draw a fading circular explosion particle."""
        alpha = max(0, min(255, int(255 * p.timer / p.max_timer)))
        color = p.color
        rgba = (*color, alpha) if len(color) == 3 else (*color[:3], alpha)
        pygame.draw.circle(
            self.effects_surface,
            rgba,
            (int(p.x + ox), int(p.y + oy)),
            int(p.size),
        )

    def _render_portal(self, portal: Portal | None, player: Player) -> None:
        """Render portal visual effects if active.

        Thin orchestrator: projects the portal into screen space, then
        layers glow, rings, rotating arcs, and the core on top.

        Args:
            portal: Portal dictionary with position and state, or None if inactive.
            player: The player object for relative positioning.
        """
        if not portal:
            return

        projected = self._project_portal_to_screen(portal, player)
        if projected is None:
            return
        screen_x, screen_y, base_size = projected

        center = (screen_x, screen_y)
        time_ms = pygame.time.get_ticks()

        # Pulsing animation
        pulse1 = math.sin(time_ms * 0.008) * 0.3 + 1.0  # Slow pulse
        pulse2 = math.sin(time_ms * 0.015) * 0.2 + 1.0  # Fast pulse
        rotation = time_ms * 0.002  # Rotation effect

        self._draw_portal_glow(center, base_size)
        self._draw_portal_rings(center, base_size, pulse1, pulse2)
        self._draw_portal_arcs(screen_x, screen_y, base_size, pulse1, rotation)
        self._draw_portal_core(center, base_size, time_ms)

    def _project_portal_to_screen(
        self, portal: Portal, player: Player
    ) -> tuple[int, int, int] | None:
        """Project portal world position to screen coords + base size.

        Returns ``None`` if the portal is behind the camera or fully off-screen.
        """
        sx = portal["x"] - player.x
        sy = portal["y"] - player.y

        cs = math.cos(player.angle)
        sn = math.sin(player.angle)
        a = sy * cs - sx * sn
        b = sx * cs + sy * sn

        if b <= 0.1:
            return None

        screen_x = int((0.5 * C.SCREEN_WIDTH) * (1 + a / b * 2.0))
        screen_y = C.SCREEN_HEIGHT // 2
        base_size = int(800 / b)

        if not (-base_size < screen_x < C.SCREEN_WIDTH + base_size):
            return None

        return screen_x, screen_y, base_size

    def _draw_portal_glow(self, center: tuple[int, int], base_size: int) -> None:
        """Draw (and cache) the outer glow halo for the portal."""
        glow_size = int(base_size * 0.9)
        if glow_size <= 0:
            return

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

    def _draw_portal_rings(
        self,
        center: tuple[int, int],
        base_size: int,
        pulse1: float,
        pulse2: float,
    ) -> None:
        """Draw the four pulsing plasma rings with inner bright edges."""
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

    def _draw_portal_arcs(
        self,
        screen_x: int,
        screen_y: int,
        base_size: int,
        pulse1: float,
        rotation: float,
    ) -> None:
        """Draw the four rotating energy arcs around the portal."""
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

    def _draw_portal_core(
        self, center: tuple[int, int], base_size: int, time_ms: int
    ) -> None:
        """Draw the central pulsing energy core of the portal."""
        core_pulse = math.sin(time_ms * 0.02) * 0.5 + 1.0
        core_size = int(base_size * 0.1 * core_pulse)
        if core_size <= 0:
            return
        core_colors = [(255, 255, 255), (200, 255, 255), (100, 255, 255)]
        for i, color in enumerate(core_colors):
            s = core_size - i * 2
            if s > 0:
                pygame.draw.circle(self.screen, color, center, s, 0)
