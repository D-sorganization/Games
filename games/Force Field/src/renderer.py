from __future__ import annotations

import logging
import math
import random
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, cast

import pygame

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .game import Game
    from .player import Player

logger = logging.getLogger(__name__)


class GameRenderer:
    """Handles 3D world rendering and game view composition"""

    def __init__(self, screen: pygame.Surface) -> None:
        """Initialize the game renderer with a screen surface."""
        self.screen = screen

        # Optimization: Shared surface for alpha effects
        self.effects_surface = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)

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
        if hasattr(game, "particle_system"):
             self._render_particles(game.particle_system.particles)
        else:
             # Fallback if refactor not complete or mixed state
             self._render_particles(getattr(game, "particles", []))
        self.screen.blit(self.effects_surface, (0, 0))

        # 3. Portal
        self._render_portal(game.portal, game.player)

        # 4. Weapon Model
        # 4. Weapon Model
        weapon_pos = self._render_weapon(game.player)
        if game.player.shooting:
            self._render_muzzle_flash(game.player.current_weapon, weapon_pos)

        # 5. UI / HUD
        if hasattr(game, "ui_renderer"):
            game.ui_renderer.render_hud(game)

        pygame.display.flip()

    def _render_particles(self, particles: List[Any]) -> None:
        """Render particle effects including lasers and explosion particles.

        Args:
            particles: List of Particle objects or dicts (legacy support).
        """
        for p in particles:
            # Handle Particle Object
            if hasattr(p, "ptype"):
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
                continue

            # Legacy Dict support
            if p.get("type") == "laser":
                alpha = int(255 * (p["timer"] / C.LASER_DURATION))
                start = p["start"]
                end = p["end"]
                color = (*p["color"], alpha)
                pygame.draw.line(self.effects_surface, color, start, end, p["width"])

                # Spread
                for i in range(5):
                    offset = (i - 2) * 20
                    target_end = (end[0] + offset, end[1])
                    pygame.draw.line(
                        self.effects_surface,
                        (*p["color"], max(0, alpha - 50)),
                        start,
                        target_end,
                        max(1, p["width"] // 2),
                    )
            elif "dx" in p:
                ratio = p["timer"] / C.PARTICLE_LIFETIME
                alpha = int(255 * ratio)
                alpha = max(0, min(255, alpha))
                try:
                    color = p["color"]
                    rgba = (*color, alpha) if len(color) == 3 else (*color[:3], alpha)
                    pygame.draw.circle(
                        self.effects_surface,
                        rgba,
                        (int(p["x"]), int(p["y"])),
                        int(p["size"]),
                    )
                except (ValueError, TypeError):
                    continue

    def _render_portal(self, portal: Dict[str, Any] | None, player: Player) -> None:
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
                    pygame.draw.circle(self.screen, color, (screen_x, screen_y), size // 2, 2)
                    pygame.draw.circle(self.screen, C.WHITE, (screen_x, screen_y), size // 4, 1)

    def _render_weapon(self, player: Player) -> Tuple[int, int]:
        """Render weapon model and return its screen position (cx, cy)"""
        weapon = player.current_weapon
        cx = C.SCREEN_WIDTH // 2
        cy = C.SCREEN_HEIGHT

        # Weapon Sway (Horizontal lag)
        # sway_amount is in radians. 0.1 rad is significant.
        # Scale it up to pixels.
        sway_x = int(player.sway_amount * -300.0)
        cx += sway_x

        # Bobbing
        bob_y = 0
        if player.is_moving:
            bob_y = int(math.sin(pygame.time.get_ticks() * 0.012) * 15)
            # Add some horizontal bob too
            bob_x = int(math.cos(pygame.time.get_ticks() * 0.006) * 10)
            cx += bob_x

        w_state = player.weapon_state[weapon]
        if w_state["reloading"]:
            w_data = C.WEAPONS.get(weapon, {})
            reload_max = cast("int", w_data.get("reload_time", 60))
            if reload_max > 0:
                pct = w_state["reload_timer"] / reload_max
                dip = math.sin(pct * math.pi) * 150
                cy += int(dip)

        cy += bob_y

        gun_metal = (40, 45, 50)
        gun_highlight = (70, 75, 80)
        gun_dark = (20, 25, 30)

        if weapon == "pistol":
            pygame.draw.polygon(
                self.screen,
                (30, 25, 20),
                [(cx - 30, cy), (cx + 30, cy), (cx + 35, cy - 100), (cx - 35, cy - 100)],
            )
            pygame.draw.rect(self.screen, gun_metal, (cx - 20, cy - 140, 40, 140))
            slide_y = cy - 180
            if player.shooting:
                slide_y += 20
            pygame.draw.polygon(
                self.screen,
                gun_highlight,
                [
                    (cx - 25, slide_y),
                    (cx + 25, slide_y),
                    (cx + 25, slide_y + 120),
                    (cx - 25, slide_y + 120),
                ],
            )
            for i in range(5):
                y_ser = slide_y + 80 + i * 8
                pygame.draw.line(self.screen, gun_dark, (cx - 20, y_ser), (cx + 20, y_ser), 2)
            pygame.draw.rect(self.screen, (10, 10, 10), (cx - 8, slide_y - 5, 16, 10))
            pygame.draw.rect(self.screen, (10, 10, 10), (cx - 20, slide_y - 12, 5, 12))
            pygame.draw.rect(self.screen, (10, 10, 10), (cx + 15, slide_y - 12, 5, 12))
            pygame.draw.rect(self.screen, C.RED, (cx - 2, slide_y - 8, 4, 8))

        elif weapon == "shotgun":
            pygame.draw.circle(self.screen, (20, 20, 20), (cx - 30, cy - 180), 22)
            pygame.draw.rect(self.screen, gun_metal, (cx - 52, cy - 180, 44, 200))
            pygame.draw.rect(self.screen, (10, 10, 10), (cx - 48, cy - 200, 36, 100))
            pygame.draw.circle(self.screen, (20, 20, 20), (cx + 30, cy - 180), 22)
            pygame.draw.rect(self.screen, gun_metal, (cx + 8, cy - 180, 44, 200))
            pygame.draw.rect(self.screen, (10, 10, 10), (cx + 12, cy - 200, 36, 100))
            pygame.draw.rect(self.screen, gun_dark, (cx - 8, cy - 180, 16, 180))
            pygame.draw.polygon(
                self.screen,
                (100, 60, 20),
                [(cx - 60, cy - 50), (cx + 60, cy - 50), (cx + 50, cy), (cx - 50, cy)],
            )

        elif weapon == "rifle":
            pygame.draw.rect(self.screen, (20, 20, 20), (cx - 40, cy - 80, 30, 80))
            pygame.draw.polygon(
                self.screen,
                gun_metal,
                [(cx - 30, cy - 150), (cx + 30, cy - 150), (cx + 40, cy), (cx - 40, cy)],
            )
            pygame.draw.rect(self.screen, gun_highlight, (cx - 20, cy - 220, 40, 100))
            for i in range(6):
                y_vent = cy - 210 + i * 15
                pygame.draw.ellipse(self.screen, (10, 10, 10), (cx - 10, y_vent, 20, 8))
            pygame.draw.rect(self.screen, (10, 10, 10), (cx - 5, cy - 240, 10, 40))
            pygame.draw.rect(self.screen, (10, 10, 10), (cx - 5, cy - 160, 10, 40))
            pygame.draw.circle(self.screen, (30, 30, 30), (cx, cy - 170), 30)
            pygame.draw.circle(self.screen, (0, 100, 0), (cx, cy - 170), 25)
            pygame.draw.circle(self.screen, (150, 255, 150), (cx - 10, cy - 180), 8)
            if player.zoomed:
                pygame.draw.line(self.screen, C.RED, (cx - 25, cy - 170), (cx + 25, cy - 170), 1)
                pygame.draw.line(self.screen, C.RED, (cx, cy - 195), (cx, cy - 145), 1)

        elif weapon == "plasma":
            pygame.draw.polygon(
                self.screen,
                (40, 40, 60),
                [(cx - 100, cy), (cx + 100, cy), (cx + 90, cy - 80), (cx - 90, cy - 80)],
            )
            pygame.draw.polygon(
                self.screen,
                (60, 60, 90),
                [
                    (cx - 70, cy - 80),
                    (cx + 70, cy - 80),
                    (cx + 50, cy - 250),
                    (cx - 50, cy - 250),
                ],
            )
            pulse = int(25 * math.sin(pygame.time.get_ticks() * 0.01))
            vent_color = (
                (0, 150 + pulse, 200) if not w_state["overheated"] else (200 + pulse, 50, 0)
            )
            pygame.draw.rect(self.screen, vent_color, (cx - 90, cy - 150, 20, 100))
            pygame.draw.rect(self.screen, vent_color, (cx + 70, cy - 150, 20, 100))
            core_width = 40 + pulse // 2
            pygame.draw.rect(self.screen, (20, 20, 30), (cx - 30, cy - 180, 60, 140))
            pygame.draw.rect(
                self.screen,
                vent_color,
                (cx - core_width // 2, cy - 190, core_width, 120),
                border_radius=10,
            )
            for i in range(5):
                y_coil = cy - 230 + i * 35
                width_coil = 80 - i * 5
                pygame.draw.rect(
                    self.screen,
                    (30, 30, 40),
                    (cx - width_coil // 2, y_coil, width_coil, 15),
                    border_radius=4,
                )
            if player.shooting:
                for _ in range(3):
                    lx1 = random.randint(cx - 40, cx + 40)
                    ly1 = random.randint(cy - 250, cy - 150)
                    lx2 = random.randint(cx - 40, cx + 40)
                    ly2 = random.randint(cy - 250, cy - 150)
                    pygame.draw.line(self.screen, C.WHITE, (lx1, ly1), (lx2, ly2), 2)

        return cx, cy

    def _render_muzzle_flash(self, weapon_name: str, weapon_pos: Tuple[int, int]) -> None:
        """Render weapon-specific muzzle flash effects."""
        flash_x = weapon_pos[0]
        # Base offset from weapon anchor (screen height)
        # Using the same offset logic as before (SCREEN_HEIGHT - 210 vs cy - 210)
        # assuming weapon_pos[1] corresponds to the weapon's base y (mostly SCREEN_HEIGHT + bob)
        flash_y = weapon_pos[1] - 210

        if weapon_name == "plasma":
            pygame.draw.circle(self.screen, C.CYAN, (flash_x, flash_y), 30)
            pygame.draw.circle(self.screen, C.BLUE, (flash_x, flash_y), 20)
            pygame.draw.circle(self.screen, C.WHITE, (flash_x, flash_y), 10)
        elif weapon_name == "shotgun":
            pygame.draw.circle(self.screen, (255, 100, 0), (flash_x, flash_y), 50)
            pygame.draw.circle(self.screen, C.ORANGE, (flash_x, flash_y), 35)
            pygame.draw.circle(self.screen, C.YELLOW, (flash_x, flash_y), 15)
        else:
            pygame.draw.circle(self.screen, C.YELLOW, (flash_x, flash_y), 25)
            pygame.draw.circle(self.screen, C.ORANGE, (flash_x, flash_y), 15)
            pygame.draw.circle(self.screen, C.WHITE, (flash_x, flash_y), 8)
