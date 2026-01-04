from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Any

import pygame

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .custom_types import WeaponData
    from .player import Player


class WeaponRenderer:
    """Handles weapon model and effect rendering"""

    def __init__(self, screen: pygame.Surface) -> None:
        """Initialize the weapon renderer"""
        self.screen = screen
        self.font = pygame.font.SysFont("arial", 20, bold=True)

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
        else:
            # Idle bob (breathing)
            bob_y = int(math.sin(pygame.time.get_ticks() * 0.005) * 5)
            # Gentle horizontal sway
            cx += int(math.cos(pygame.time.get_ticks() * 0.003) * 3)

        w_state = player.weapon_state[weapon]
        if w_state["reloading"]:
            w_data: WeaponData = C.WEAPONS.get(weapon, {})
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
            # Big Green Flash
            pygame.draw.circle(self.screen, (0, 255, 0), (flash_x, flash_y), 60)
            pygame.draw.circle(self.screen, (200, 255, 200), (flash_x, flash_y), 40)
            pygame.draw.circle(self.screen, C.WHITE, (flash_x, flash_y), 20)
            # Rays
            for _ in range(8):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.randint(50, 100)
                end_x = flash_x + math.cos(angle) * dist
                end_y = flash_y + math.sin(angle) * dist
                pygame.draw.line(
                    self.screen, (0, 255, 0), (flash_x, flash_y), (end_x, end_y), 3
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

    def _render_pulse(
        self, cx: int, cy: int, player: Player, w_state: dict[str, Any]
    ) -> None:
        # Futuristic Pulse Rifle Design
        # Base
        pygame.draw.rect(self.screen, (30, 30, 50), (cx - 40, cy - 150, 80, 150))

        # Barrel Section
        pygame.draw.polygon(
            self.screen,
            (50, 50, 80),
            [
                (cx - 20, cy - 150),
                (cx + 20, cy - 150),
                (cx + 15, cy - 280),
                (cx - 15, cy - 280),
            ],
        )

        # Energy Core (Pulsing Blue)
        pulse = int(50 * math.sin(pygame.time.get_ticks() * 0.02))
        core_color = (100 + pulse, 100 + pulse, 255)

        pygame.draw.rect(self.screen, core_color, (cx - 5, cy - 200, 10, 100))

        # Side Rails
        pygame.draw.rect(self.screen, (20, 20, 40), (cx - 30, cy - 260, 10, 100))
        pygame.draw.rect(self.screen, (20, 20, 40), (cx + 20, cy - 260, 10, 100))

        if player.shooting:
             pygame.draw.circle(self.screen, (200, 200, 255), (cx, cy - 280), 20)

    def _render_rocket_launcher(
        self,
        cx: int,
        cy: int,
        player: Player,
        gun_metal: tuple[int, int, int],
        gun_highlight: tuple[int, int, int],
        gun_dark: tuple[int, int, int],
    ) -> None:
        """Render an impressive rocket launcher with glowing effects"""
        time_ms = pygame.time.get_ticks()

        # Pulsing glow effect
        glow_pulse = math.sin(time_ms * 0.008) * 0.3 + 0.7

        # Main launcher body - large and imposing
        body_width = 120
        body_height = 80
        body_rect = (cx - body_width // 2, cy - 200, body_width, body_height)

        # Draw glow around launcher
        glow_surface = pygame.Surface(
            (body_width + 40, body_height + 40), pygame.SRCALPHA
        )
        glow_color = (255, 100, 0, int(30 * glow_pulse))
        pygame.draw.rect(
            glow_surface,
            glow_color,
            (20, 20, body_width, body_height),
            border_radius=10,
        )
        self.screen.blit(glow_surface, (cx - body_width // 2 - 20, cy - 220))

        # Main body
        pygame.draw.rect(self.screen, gun_dark, body_rect, border_radius=8)
        pygame.draw.rect(
            self.screen,
            gun_metal,
            (cx - body_width // 2 + 10, cy - 190, body_width - 20, body_height - 20),
            border_radius=5,
        )

        # Rocket tube - large bore
        tube_width = 80
        tube_height = 200
        tube_rect = (cx - tube_width // 2, cy - 350, tube_width, tube_height)

        # Tube exterior
        pygame.draw.rect(self.screen, gun_highlight, tube_rect, border_radius=40)

        # Tube interior (dark bore)
        bore_width = tube_width - 20
        pygame.draw.rect(
            self.screen,
            (10, 10, 10),
            (cx - bore_width // 2, cy - 340, bore_width, tube_height - 20),
            border_radius=30,
        )

        # Targeting system with glowing elements
        scope_y = cy - 280
        pygame.draw.rect(
            self.screen, gun_dark, (cx - 40, scope_y, 80, 30), border_radius=5
        )

        # Glowing targeting reticle
        reticle_brightness = int(150 + 105 * math.sin(time_ms * 0.015))
        reticle_color = (reticle_brightness, 0, 0)
        pygame.draw.circle(self.screen, reticle_color, (cx, scope_y + 15), 8)
        pygame.draw.circle(self.screen, (255, 0, 0), (cx, scope_y + 15), 4)

        # Side-mounted missile pods
        for side in [-1, 1]:
            pod_x = cx + side * 70
            pod_rect = (pod_x - 15, cy - 300, 30, 120)
            pygame.draw.rect(self.screen, gun_metal, pod_rect, border_radius=15)

            # Mini missiles in pods
            for i in range(3):
                missile_y = cy - 290 + i * 30
                missile_color = (200, 50, 50) if i % 2 == 0 else (150, 150, 150)
                pygame.draw.circle(self.screen, missile_color, (pod_x, missile_y), 8)
                pygame.draw.circle(self.screen, (255, 100, 100), (pod_x, missile_y), 4)

        # Grip and trigger assembly
        grip_points = [
            (cx - 30, cy - 120),
            (cx - 20, cy - 50),
            (cx - 40, cy - 30),
            (cx - 50, cy - 80),
        ]
        pygame.draw.polygon(self.screen, gun_dark, grip_points)

        # Trigger
        trigger_color = (200, 0, 0) if player.shooting else (100, 100, 100)
        pygame.draw.circle(self.screen, trigger_color, (cx - 35, cy - 60), 8)

        # Exhaust vents with heat glow
        for i in range(4):
            vent_x = cx - 50 + i * 25
            vent_y = cy - 160
            vent_heat = max(0, min(255, int(100 + 155 * math.sin(time_ms * 0.01 + i))))
            vent_color = (int(vent_heat), int(vent_heat // 3), 0)
            pygame.draw.rect(
                self.screen, vent_color, (vent_x, vent_y, 8, 20), border_radius=4
            )

        # Ammo counter display
        ammo_count = player.weapon_state["rocket"]["clip"]
        counter_color = (0, 255, 0) if ammo_count > 0 else (255, 0, 0)
        counter_text_str = f"AMMO: {ammo_count}"

        # Digital display background
        display_rect = pygame.Rect(cx + 30, cy - 320, 80, 25)
        pygame.draw.rect(self.screen, (10, 10, 10), display_rect, border_radius=3)
        pygame.draw.rect(self.screen, counter_color, display_rect, 2, border_radius=3)

        # Draw text
        text_surf = self.font.render(counter_text_str, True, counter_color)
        scale = min(0.8, (display_rect.width - 4) / max(1, text_surf.get_width()))
        if scale < 0.8:
            new_size = (
                int(text_surf.get_width() * scale),
                int(text_surf.get_height() * scale),
            )
            text_surf = pygame.transform.scale(text_surf, new_size)

        text_rect = text_surf.get_rect(center=display_rect.center)
        self.screen.blit(text_surf, text_rect)

        # Warning lights
        if ammo_count == 0:
            warning_brightness = int(255 * (math.sin(time_ms * 0.02) * 0.5 + 0.5))
            pygame.draw.circle(
                self.screen,
                (warning_brightness, 0, 0),
                (cx + 50, cy - 340),
                6,
            )
            pygame.draw.circle(
                self.screen,
                (warning_brightness, 0, 0),
                (cx + 70, cy - 340),
                6,
            )

    def _render_laser(self, cx: int, cy: int, player: Player) -> None:
        """Render a black gun model for the Laser"""
        # A sleek, black, futuristic rifle
        gun_color = (10, 10, 10)  # Almost black
        highlight = (40, 40, 40)

        # Main body
        pygame.draw.rect(self.screen, gun_color, (cx - 25, cy - 180, 50, 180))

        # Barrel (Longer)
        pygame.draw.rect(self.screen, (20, 20, 20), (cx - 15, cy - 250, 30, 250))

        # Side details (Vents)
        for i in range(5):
            y = cy - 140 + i * 20
            pygame.draw.rect(self.screen, highlight, (cx - 20, y, 40, 5))

        # Glowing bits
        pulse = int(127 + 127 * math.sin(pygame.time.get_ticks() * 0.01))
        energy_color = (pulse, 0, 0)  # Red pulse

        # Energy core
        pygame.draw.circle(self.screen, energy_color, (cx, cy - 100), 10)
        pygame.draw.rect(self.screen, energy_color, (cx - 2, cy - 240, 4, 140))

        if player.shooting:
            pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy - 255), 15)

    def _render_bfg(
        self,
        cx: int,
        cy: int,
        player: Player,
        gun_metal: tuple[int, int, int],
        gun_highlight: tuple[int, int, int],
        gun_dark: tuple[int, int, int],
    ) -> None:
        """Render the BFG 9000"""
        time_ms = pygame.time.get_ticks()

        # Massive bulk
        pygame.draw.rect(self.screen, gun_metal, (cx - 60, cy - 150, 120, 150))
        pygame.draw.rect(
            self.screen, gun_dark, (cx - 70, cy - 100, 140, 100), border_radius=10
        )

        # Glowing Energy Core
        pulse = int(127 + 127 * math.sin(time_ms * 0.005))
        core_color = (0, pulse, 0)
        pygame.draw.circle(self.screen, core_color, (cx, cy - 100), 40)
        pygame.draw.circle(self.screen, (200, 255, 200), (cx, cy - 100), 20)

        # Barrel
        pygame.draw.rect(self.screen, gun_highlight, (cx - 40, cy - 220, 80, 100))
        pygame.draw.circle(self.screen, (10, 50, 10), (cx, cy - 220), 35)

        # Energy buildup
        if player.shooting:
            pygame.draw.circle(
                self.screen, (0, 255, 0), (cx, cy - 220), 30 + random.randint(-5, 5)
            )

        # Side Vents
        for i in range(3):
            y_vent = cy - 80 + i * 20
            pygame.draw.rect(self.screen, core_color, (cx - 65, y_vent, 10, 10))
            pygame.draw.rect(self.screen, core_color, (cx + 55, y_vent, 10, 10))
