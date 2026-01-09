from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Any

import pygame

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .player import Player


class WeaponRenderer:
    """Handles weapon model and effect rendering"""

    def __init__(self, screen: pygame.Surface) -> None:
        """Initialize the weapon renderer"""
        self.screen = screen

    def render_weapon(self, player: Player) -> tuple[int, int]:
        """Render weapon model and return its screen position (cx, cy)"""
        weapon = player.current_weapon
        cx = C.SCREEN_WIDTH // 2
        cy = C.SCREEN_HEIGHT

        # Weapon Sway (Horizontal lag)
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
            reload_max = int(w_data.get("reload_time", 60))
            if reload_max > 0:
                pct = w_state["reload_timer"] / reload_max
                dip = math.sin(pct * math.pi) * 150
                cy += int(dip)

        cy += bob_y

        gun_metal = (40, 45, 50)
        gun_highlight = (70, 75, 80)
        gun_dark = (20, 25, 30)

        if weapon == "pistol":
            self._render_pistol(cx, cy, player, gun_metal, gun_highlight, gun_dark)

        elif weapon == "shotgun":
            self._render_shotgun(cx, cy, gun_metal, gun_dark)

        elif weapon == "rifle":
            self._render_rifle(cx, cy, player, gun_metal, gun_highlight)

        elif weapon == "minigun":
            self._render_minigun(cx, cy, player)

        elif weapon == "plasma":
            self._render_plasma(cx, cy, player, w_state)

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
        else:
            pygame.draw.circle(self.screen, C.YELLOW, (flash_x, flash_y), 25)
            pygame.draw.circle(self.screen, C.ORANGE, (flash_x, flash_y), 15)
            pygame.draw.circle(self.screen, C.WHITE, (flash_x, flash_y), 8)

    def _render_pistol(
        self,
        cx: int,
        cy: int,
        player: Player,
        gun_metal: tuple[int, int, int],
        gun_highlight: tuple[int, int, int],
        gun_dark: tuple[int, int, int],
    ) -> None:
        pygame.draw.polygon(
            self.screen,
            (30, 25, 20),
            [
                (cx - 30, cy),
                (cx + 30, cy),
                (cx + 35, cy - 100),
                (cx - 35, cy - 100),
            ],
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
            start_pos = (cx - 20, y_ser)
            end_pos = (cx + 20, y_ser)
            pygame.draw.line(self.screen, gun_dark, start_pos, end_pos, 2)
        pygame.draw.rect(self.screen, (10, 10, 10), (cx - 8, slide_y - 5, 16, 10))
        pygame.draw.rect(self.screen, (10, 10, 10), (cx - 20, slide_y - 12, 5, 12))
        pygame.draw.rect(self.screen, (10, 10, 10), (cx + 15, slide_y - 12, 5, 12))
        pygame.draw.rect(self.screen, C.RED, (cx - 2, slide_y - 8, 4, 8))

    def _render_shotgun(
        self,
        cx: int,
        cy: int,
        gun_metal: tuple[int, int, int],
        gun_dark: tuple[int, int, int],
    ) -> None:
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

    def _render_rifle(
        self,
        cx: int,
        cy: int,
        player: Player,
        gun_metal: tuple[int, int, int],
        gun_highlight: tuple[int, int, int],
    ) -> None:
        pygame.draw.rect(self.screen, (20, 20, 20), (cx - 40, cy - 80, 30, 80))
        pygame.draw.polygon(
            self.screen,
            gun_metal,
            [
                (cx - 30, cy - 150),
                (cx + 30, cy - 150),
                (cx + 40, cy),
                (cx - 40, cy),
            ],
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
            pygame.draw.line(
                self.screen,
                C.RED,
                (cx - 25, cy - 170),
                (cx + 25, cy - 170),
                1,
            )
            pygame.draw.line(self.screen, C.RED, (cx, cy - 195), (cx, cy - 145), 1)

    def _render_minigun(self, cx: int, cy: int, player: Player) -> None:
        # Rotate barrels
        rot = 0
        if player.shooting:
            rot = int((pygame.time.get_ticks() * 0.5) % 20)

        pygame.draw.rect(self.screen, (20, 20, 20), (cx - 40, cy - 100, 80, 100))
        # Barrels
        barrel_color = (60, 60, 60)
        for i in range(3):
            bx = cx - 30 + i * 30 + rot - 10
            if bx > cx + 30:
                bx -= 80  # wrap
            pygame.draw.rect(self.screen, barrel_color, (bx, cy - 200, 15, 120))

        pygame.draw.rect(self.screen, (30, 30, 30), (cx - 50, cy - 80, 100, 30))

    def _render_plasma(
        self, cx: int, cy: int, player: Player, w_state: dict[str, Any]
    ) -> None:
        pygame.draw.polygon(
            self.screen,
            (40, 40, 60),
            [
                (cx - 100, cy),
                (cx + 100, cy),
                (cx + 90, cy - 80),
                (cx - 90, cy - 80),
            ],
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
        heat_color = (0, 150 + pulse, 200)
        overheat_color = (200 + pulse, 50, 0)
        vent_color = heat_color if not w_state["overheated"] else overheat_color
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
