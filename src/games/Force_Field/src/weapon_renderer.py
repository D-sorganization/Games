"""Weapon renderer — routes to per-weapon drawing methods via mixin.

The heavy per-weapon drawing code lives in `weapon_renderer_draw.py`
(WeaponRendererDrawMixin) so that this module stays under the 500-line
soft cap (issue #798).
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

from . import constants as C  # noqa: N812
from .weapon_renderer_draw import WeaponRendererDrawMixin

if TYPE_CHECKING:
    from .player import Player


class WeaponRenderer(WeaponRendererDrawMixin):
    """Handles weapon model and effect rendering."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font = pygame.font.SysFont("arial", 20, bold=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render_weapon(self, player: Player) -> tuple[int, int]:
        """Render weapon model and return its screen position (cx, cy)."""
        cx, cy = self._compute_weapon_position(player)
        self._dispatch_weapon_render(player, cx, cy)
        return cx, cy

    def render_muzzle_flash(
        self, weapon_name: str, weapon_pos: tuple[int, int]
    ) -> None:
        """Render weapon-specific muzzle flash effects."""
        flash_x = weapon_pos[0]
        flash_y = weapon_pos[1] - 210

        if weapon_name == "plasma":
            pygame.draw.circle(self.screen, C.CYAN, (flash_x, flash_y), 30)
            pygame.draw.circle(self.screen, C.BLUE, (flash_x, flash_y), 20)
            pygame.draw.circle(self.screen, C.WHITE, (flash_x, flash_y), 10)
        elif weapon_name == "pulse":
            pygame.draw.circle(self.screen, (100, 100, 255), (flash_x, flash_y), 25)
            pygame.draw.circle(self.screen, (200, 200, 255), (flash_x, flash_y), 15)
        elif weapon_name == "shotgun":
            pygame.draw.circle(self.screen, (255, 100, 0), (flash_x, flash_y), 50)
            pygame.draw.circle(self.screen, C.ORANGE, (flash_x, flash_y), 35)
            pygame.draw.circle(self.screen, C.YELLOW, (flash_x, flash_y), 15)
        elif weapon_name == "minigun":
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            pygame.draw.circle(
                self.screen, C.YELLOW, (flash_x + offset_x, flash_y + offset_y), 30
            )
            pygame.draw.circle(
                self.screen, C.WHITE, (flash_x + offset_x, flash_y + offset_y), 15
            )
        elif weapon_name == "bfg":
            self._render_bfg_flash(flash_x, flash_y)
        else:
            pygame.draw.circle(self.screen, C.YELLOW, (flash_x, flash_y), 25)
            pygame.draw.circle(self.screen, C.ORANGE, (flash_x, flash_y), 15)
            pygame.draw.circle(self.screen, C.WHITE, (flash_x, flash_y), 8)

    # ------------------------------------------------------------------
    # Position & dispatch
    # ------------------------------------------------------------------

    def _compute_weapon_position(self, player: Player) -> tuple[int, int]:
        """Calculate the weapon screen position from sway, bob, and reload dip."""
        from .custom_types import WeaponData

        weapon = player.current_weapon
        cx = C.SCREEN_WIDTH // 2 + int(player.sway_amount * -300.0)
        cy = C.SCREEN_HEIGHT
        bob_y = 0
        if player.is_moving:
            bob_y = int(math.sin(pygame.time.get_ticks() * 0.012) * 15)
            cx += int(math.cos(pygame.time.get_ticks() * 0.006) * 10)
        else:
            bob_y = int(math.sin(pygame.time.get_ticks() * 0.005) * 5)
            cx += int(math.cos(pygame.time.get_ticks() * 0.003) * 3)
        w_state = player.weapon_state[weapon]
        if w_state["reloading"]:
            w_data: WeaponData = C.WEAPONS.get(weapon, {})
            reload_max = int(w_data.get("reload_time", 60))
            if reload_max > 0:
                pct = w_state["reload_timer"] / reload_max
                cy += int(math.sin(pct * math.pi) * 150)
        cy += bob_y
        return cx, cy

    def _dispatch_weapon_render(self, player: Player, cx: int, cy: int) -> None:
        """Route rendering to the correct weapon draw method."""
        weapon = player.current_weapon
        gun_metal = (40, 45, 50)
        gun_highlight = (70, 75, 80)
        gun_dark = (20, 25, 30)
        w_state = player.weapon_state[weapon]
        if weapon == "pistol":
            self._render_pistol(cx, cy, player, gun_metal, gun_highlight, gun_dark)
        elif weapon == "shotgun":
            self._render_shotgun(
                cx, cy, gun_metal, gun_highlight, gun_dark
            )
        elif weapon == "rifle":
            self._render_rifle(cx, cy, player, gun_metal, gun_highlight)
        elif weapon == "minigun":
            self._render_minigun(cx, cy, player)
        elif weapon == "laser":
            self._render_laser(cx, cy, player)
        elif weapon == "plasma":
            self._render_plasma(cx, cy, player, w_state)
        elif weapon == "pulse":
            self._render_pulse(cx, cy, player, w_state)
        elif weapon == "rocket":
            self._render_rocket_launcher(
                cx, cy, player, gun_metal, gun_highlight, gun_dark
            )
        elif weapon == "bfg":
            self._render_bfg(cx, cy, player, gun_metal, gun_highlight, gun_dark)
