"""Weapon-specific drawing routines extracted from WeaponRenderer.

This module is imported as a mixin by `weapon_renderer` to keep the class under
the 500-line soft cap (issue #798).
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from .player import Player


class WeaponRendererDrawMixin:
    """Mixin providing per-weapon pygame drawing methods."""

    # ------------------------------------------------------------------
    # Muzzle flash
    # ------------------------------------------------------------------

    def _render_bfg_flash(self, flash_x: int, flash_y: int) -> None:
        """Draw the BFG muzzle flash (green energy burst)."""
        for radius, color in [
            (60, (0, 255, 0)),
            (40, (100, 255, 100)),
            (20, (200, 255, 200)),
        ]:
            pygame.draw.circle(self.screen, color, (flash_x, flash_y), radius)

    # ------------------------------------------------------------------
    # Pistol
    # ------------------------------------------------------------------

    def _render_pistol(
        self,
        cx: int,
        cy: int,
        player: Player,
        gun_metal: tuple[int, int, int],
        gun_highlight: tuple[int, int, int],
        gun_dark: tuple[int, int, int],
    ) -> None:
        """Draw a classic pistol with optional slide-back animation."""
        w_state = player.weapon_state["pistol"]
        slide_offset = 10 if w_state["reloading"] else 0

        self._render_pistol_slide(
            cx, cy, gun_metal, gun_highlight, gun_dark, slide_offset
        )

        # Grip
        pygame.draw.rect(self.screen, gun_dark, (cx - 15, cy - 80, 30, 80))
        pygame.draw.rect(self.screen, gun_metal, (cx - 12, cy - 75, 24, 70))

        # Trigger guard
        pygame.draw.arc(
            self.screen,
            gun_highlight,
            (cx - 10, cy - 90, 20, 20),
            0,
            math.pi,
            2,
        )

        # Sights
        pygame.draw.line(
            self.screen, gun_highlight, (cx - 8, cy - 175), (cx - 8, cy - 170), 2
        )
        pygame.draw.line(
            self.screen, gun_highlight, (cx + 8, cy - 175), (cx + 8, cy - 170), 2
        )

    def _render_pistol_slide(
        self,
        cx: int,
        cy: int,
        gun_metal: tuple[int, int, int],
        gun_highlight: tuple[int, int, int],
        gun_dark: tuple[int, int, int],
        slide_offset: int,
    ) -> None:
        """Draw the pistol slide (recoils when reloading)."""
        # Main slide body
        pygame.draw.rect(
            self.screen,
            gun_metal,
            (cx - 20, cy - 140 - slide_offset, 40, 60),
        )
        pygame.draw.rect(
            self.screen,
            gun_highlight,
            (cx - 20, cy - 140 - slide_offset, 40, 60),
            2,
        )

        # Barrel
        pygame.draw.rect(
            self.screen,
            gun_dark,
            (cx - 8, cy - 170 - slide_offset, 16, 30),
        )

        # Ejection port
        pygame.draw.rect(
            self.screen,
            (10, 10, 10),
            (cx - 12, cy - 130 - slide_offset, 24, 8),
        )

        # Front sight
        pygame.draw.line(
            self.screen,
            gun_highlight,
            (cx, cy - 170 - slide_offset),
            (cx, cy - 165 - slide_offset),
            3,
        )

    # ------------------------------------------------------------------
    # Shotgun
    # ------------------------------------------------------------------

    def _render_shotgun(
        self,
        cx: int,
        cy: int,
        gun_metal: tuple[int, int, int],
        gun_highlight: tuple[int, int, int],
        gun_dark: tuple[int, int, int],
    ) -> None:
        """Draw a double-barrel shotgun."""
        # Stock
        pygame.draw.rect(self.screen, gun_dark, (cx - 25, cy - 100, 50, 100))
        pygame.draw.rect(self.screen, gun_metal, (cx - 22, cy - 95, 44, 90))

        # Receiver
        pygame.draw.rect(self.screen, gun_metal, (cx - 30, cy - 140, 60, 40))
        pygame.draw.rect(self.screen, gun_highlight, (cx - 30, cy - 140, 60, 40), 2)

        # Barrels (side by side)
        pygame.draw.rect(self.screen, gun_dark, (cx - 20, cy - 200, 15, 60))
        pygame.draw.rect(self.screen, gun_dark, (cx + 5, cy - 200, 15, 60))

        # Pump handle
        pygame.draw.rect(self.screen, gun_dark, (cx - 25, cy - 130, 50, 15))

        # Trigger guard
        pygame.draw.arc(
            self.screen,
            gun_highlight,
            (cx - 10, cy - 110, 20, 20),
            0,
            math.pi,
            2,
        )

        # Sights
        pygame.draw.line(
            self.screen, gun_highlight, (cx - 15, cy - 200), (cx - 15, cy - 195), 2
        )
        pygame.draw.line(
            self.screen, gun_highlight, (cx + 15, cy - 200), (cx + 15, cy - 195), 2
        )

    # ------------------------------------------------------------------
    # Rifle
    # ------------------------------------------------------------------

    def _render_rifle(
        self,
        cx: int,
        cy: int,
        player: Player,
        gun_metal: tuple[int, int, int],
        gun_highlight: tuple[int, int, int],
    ) -> None:
        """Draw an assault rifle with optional magazine-out animation."""
        w_state = player.weapon_state["rifle"]
        mag_offset = 15 if w_state["reloading"] else 0

        # Stock
        pygame.draw.rect(self.screen, (30, 35, 40), (cx - 20, cy - 80, 40, 80))

        # Receiver
        pygame.draw.rect(self.screen, gun_metal, (cx - 25, cy - 130, 50, 50))
        pygame.draw.rect(self.screen, gun_highlight, (cx - 25, cy - 130, 50, 50), 2)

        # Barrel
        pygame.draw.rect(self.screen, gun_metal, (cx - 12, cy - 180, 24, 50))
        pygame.draw.rect(self.screen, (50, 55, 60), (cx - 10, cy - 178, 20, 46))

        # Handguard
        pygame.draw.rect(self.screen, (35, 40, 45), (cx - 18, cy - 150, 36, 30))

        # Magazine (drops when reloading)
        pygame.draw.rect(
            self.screen,
            (20, 20, 20),
            (cx - 10, cy - 80 + mag_offset, 20, 40),
        )
        if w_state["reloading"]:
            # Falling magazine trail
            pygame.draw.line(
                self.screen,
                (20, 20, 20),
                (cx - 10, cy - 80),
                (cx - 10, cy - 80 + mag_offset),
                20,
            )

        # Trigger guard
        pygame.draw.arc(
            self.screen,
            gun_highlight,
            (cx - 10, cy - 100, 20, 20),
            0,
            math.pi,
            2,
        )

        # Sights
        pygame.draw.line(
            self.screen, gun_highlight, (cx - 12, cy - 180), (cx - 12, cy - 175), 2
        )
        pygame.draw.line(
            self.screen, gun_highlight, (cx + 12, cy - 180), (cx + 12, cy - 175), 2
        )

    # ------------------------------------------------------------------
    # Minigun
    # ------------------------------------------------------------------

    def _render_minigun(self, cx: int, cy: int, player: Player) -> None:
        """Draw a minigun with spinning barrels."""
        time_ms = pygame.time.get_ticks()
        rotation = (time_ms * 0.01) % (2 * math.pi)

        # Main body
        pygame.draw.rect(self.screen, (50, 50, 50), (cx - 40, cy - 150, 80, 150))
        pygame.draw.rect(self.screen, (70, 70, 70), (cx - 40, cy - 150, 80, 150), 2)

        # Motor housing
        pygame.draw.circle(self.screen, (60, 60, 60), (cx, cy - 100), 35)

        # Barrels (6 barrels in a circle)
        barrel_radius = 25
        for i in range(6):
            angle = rotation + (i * math.pi / 3)
            bx = cx + int(barrel_radius * math.cos(angle))
            by = (cy - 100) + int(barrel_radius * math.sin(angle))
            pygame.draw.line(self.screen, (80, 80, 80), (cx, cy - 100), (bx, by), 6)

        # Front assembly
        pygame.draw.circle(self.screen, (70, 70, 70), (cx, cy - 100), 15)

        # Ammo belt
        pygame.draw.rect(self.screen, (30, 30, 30), (cx + 30, cy - 80, 40, 60))
        pygame.draw.rect(self.screen, (50, 50, 50), (cx + 30, cy - 80, 40, 60), 2)

        # Spinning indicator
        if player.shooting:
            pygame.draw.circle(self.screen, (255, 100, 0), (cx, cy - 100), 10)

    # ------------------------------------------------------------------
    # Plasma
    # ------------------------------------------------------------------

    def _render_plasma(self, cx: int, cy: int, player: Player, w_state: dict) -> None:
        """Draw a plasma rifle with pulsing energy core."""
        time_ms = pygame.time.get_ticks()
        pulse = int(127 + 127 * math.sin(time_ms * 0.01))

        # Main body
        pygame.draw.rect(self.screen, (40, 50, 60), (cx - 30, cy - 150, 60, 150))
        pygame.draw.rect(self.screen, (60, 70, 80), (cx - 30, cy - 150, 60, 150), 2)

        # Energy core (pulsing)
        core_color = (0, pulse, pulse)
        pygame.draw.circle(self.screen, core_color, (cx, cy - 100), 20)
        pygame.draw.circle(self.screen, (100, 255, 255), (cx, cy - 100), 10)

        # Barrel
        pygame.draw.rect(self.screen, (30, 40, 50), (cx - 15, cy - 200, 30, 50))

        # Cooling vents
        for i in range(4):
            vent_y = cy - 140 + i * 20
            vent_color = (0, int(pulse * 0.7), int(pulse * 0.7))
            pygame.draw.rect(self.screen, vent_color, (cx - 25, vent_y, 8, 12))
            pygame.draw.rect(self.screen, vent_color, (cx + 17, vent_y, 8, 12))

        if player.shooting:
            pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy - 200), 15)

    def _render_plasma_core(
        self,
        cx: int,
        cy: int,
        core_color: tuple[int, int, int],
        inner_color: tuple[int, int, int],
    ) -> None:
        """Shared plasma energy core drawing."""
        pygame.draw.circle(self.screen, core_color, (cx, cy), 20)
        pygame.draw.circle(self.screen, inner_color, (cx, cy), 10)

    # ------------------------------------------------------------------
    # Pulse
    # ------------------------------------------------------------------

    def _render_pulse(self, cx: int, cy: int, player: Player, w_state: dict) -> None:
        """Draw a pulse rifle with charging animation."""
        time_ms = pygame.time.get_ticks()
        charge = w_state["charge"] if "charge" in w_state else 0

        # Main body
        pygame.draw.rect(self.screen, (50, 50, 70), (cx - 25, cy - 140, 50, 140))
        pygame.draw.rect(self.screen, (70, 70, 90), (cx - 25, cy - 140, 50, 140), 2)

        # Charge indicator
        charge_pct = min(1.0, charge / 100)
        charge_color = (
            int(255 * charge_pct),
            int(255 * (1 - charge_pct)),
            0,
        )
        pygame.draw.rect(
            self.screen,
            charge_color,
            (cx - 20, cy - 130, 40, 10),
        )

        # Barrel
        pygame.draw.rect(self.screen, (40, 40, 60), (cx - 12, cy - 180, 24, 40))

        # Energy coils
        pulse = int(127 + 127 * math.sin(time_ms * 0.02))
        coil_color = (pulse, pulse, 255)
        for i in range(3):
            coil_y = cy - 120 + i * 25
            pygame.draw.circle(self.screen, coil_color, (cx, coil_y), 8)

        if player.shooting:
            pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy - 180), 12)

    # ------------------------------------------------------------------
    # Rocket launcher
    # ------------------------------------------------------------------

    def _render_rocket_launcher(
        self,
        cx: int,
        cy: int,
        player: Player,
        gun_metal: tuple[int, int, int],
        gun_highlight: tuple[int, int, int],
        gun_dark: tuple[int, int, int],
    ) -> None:
        """Draw a rocket launcher with animated heat vents."""
        time_ms = pygame.time.get_ticks()

        self._render_launcher_body(cx, cy, gun_metal, gun_highlight, gun_dark)
        self._render_tube(cx, cy, gun_metal, gun_dark)
        self._render_pods(cx, cy, gun_dark, time_ms)
        self._render_grip_and_vents(cx, cy, gun_dark, time_ms)
        self._render_ammo_display(cx, cy, player, time_ms)

    def _render_launcher_body(
        self,
        cx: int,
        cy: int,
        gun_metal: tuple[int, int, int],
        gun_highlight: tuple[int, int, int],
        gun_dark: tuple[int, int, int],
    ) -> None:
        """Draw the main launcher housing."""
        pygame.draw.rect(self.screen, gun_metal, (cx - 35, cy - 140, 70, 140))
        pygame.draw.rect(self.screen, gun_highlight, (cx - 35, cy - 140, 70, 140), 2)

        # Shoulder stock
        pygame.draw.rect(self.screen, gun_dark, (cx - 40, cy - 100, 80, 60))

    def _render_tube(
        self,
        cx: int,
        cy: int,
        gun_metal: tuple[int, int, int],
        gun_dark: tuple[int, int, int],
    ) -> None:
        """Draw the launch tube."""
        pygame.draw.rect(self.screen, gun_dark, (cx - 20, cy - 220, 40, 80))
        pygame.draw.rect(self.screen, gun_metal, (cx - 18, cy - 218, 36, 76), 2)

        # Tube rings
        for y in (cy - 200, cy - 180, cy - 160):
            pygame.draw.rect(self.screen, gun_metal, (cx - 22, y, 44, 8))

    def _render_pods(
        self,
        cx: int,
        cy: int,
        gun_dark: tuple[int, int, int],
        time_ms: int,
    ) -> None:
        """Draw side ammo pods with heat indicators."""
        pod_heat = int(127 + 127 * math.sin(time_ms * 0.005))
        pod_color = (pod_heat, pod_heat // 2, 0)

        # Left pod
        pygame.draw.rect(self.screen, gun_dark, (cx - 55, cy - 120, 20, 60))
        pygame.draw.rect(self.screen, pod_color, (cx - 55, cy - 120, 20, 60), 2)

        # Right pod
        pygame.draw.rect(self.screen, gun_dark, (cx + 35, cy - 120, 20, 60))
        pygame.draw.rect(self.screen, pod_color, (cx + 35, cy - 120, 20, 60), 2)

    def _render_grip_and_vents(
        self,
        cx: int,
        cy: int,
        gun_dark: tuple[int, int, int],
        time_ms: int,
    ) -> None:
        """Draw grip and heat vents."""
        # Grip
        pygame.draw.rect(self.screen, gun_dark, (cx - 15, cy - 80, 30, 60))

        # Heat vents
        for i in range(4):
            vent_x = cx - 50 + i * 25
            vent_y = cy - 160
            vent_heat = max(0, min(255, int(100 + 155 * math.sin(time_ms * 0.01 + i))))
            vent_color = (int(vent_heat), int(vent_heat // 3), 0)
            pygame.draw.rect(
                self.screen, vent_color, (vent_x, vent_y, 8, 20), border_radius=4
            )

    def _render_ammo_display(
        self,
        cx: int,
        cy: int,
        player: Player,
        time_ms: int,
    ) -> None:
        """Draw the ammo counter and warning lights."""
        ammo_count = player.weapon_state["rocket"]["clip"]
        counter_color = (0, 255, 0) if ammo_count > 0 else (255, 0, 0)
        display_rect = pygame.Rect(cx + 30, cy - 320, 80, 25)
        pygame.draw.rect(self.screen, (10, 10, 10), display_rect, border_radius=3)
        pygame.draw.rect(self.screen, counter_color, display_rect, 2, border_radius=3)
        text_surf = self.font.render(f"AMMO: {ammo_count}", True, counter_color)
        scale = min(0.8, (display_rect.width - 4) / max(1, text_surf.get_width()))
        if scale < 0.8:
            new_size = (
                int(text_surf.get_width() * scale),
                int(text_surf.get_height() * scale),
            )
            text_surf = pygame.transform.scale(text_surf, new_size)
        self.screen.blit(text_surf, text_surf.get_rect(center=display_rect.center))
        if ammo_count == 0:
            warning_brightness = int(255 * (math.sin(time_ms * 0.02) * 0.5 + 0.5))
            for warn_x in (cx + 50, cx + 70):
                pygame.draw.circle(
                    self.screen, (warning_brightness, 0, 0), (warn_x, cy - 340), 6
                )

    # ------------------------------------------------------------------
    # Laser
    # ------------------------------------------------------------------

    def _render_laser(self, cx: int, cy: int, player: Player) -> None:
        """Render a black gun model for the Laser."""
        gun_color = (10, 10, 10)
        highlight = (40, 40, 40)

        # Main body
        pygame.draw.rect(self.screen, gun_color, (cx - 25, cy - 180, 50, 180))

        # Barrel
        pygame.draw.rect(self.screen, (20, 20, 20), (cx - 15, cy - 250, 30, 250))

        # Side details (Vents)
        for i in range(5):
            y = cy - 140 + i * 20
            pygame.draw.rect(self.screen, highlight, (cx - 20, y, 40, 5))

        # Glowing bits
        pulse = int(127 + 127 * math.sin(pygame.time.get_ticks() * 0.01))
        energy_color = (pulse, 0, 0)

        # Energy core
        pygame.draw.circle(self.screen, energy_color, (cx, cy - 100), 10)
        pygame.draw.rect(self.screen, energy_color, (cx - 2, cy - 240, 4, 140))

        if player.shooting:
            pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy - 255), 15)

    # ------------------------------------------------------------------
    # BFG
    # ------------------------------------------------------------------

    def _render_bfg(
        self,
        cx: int,
        cy: int,
        player: Player,
        gun_metal: tuple[int, int, int],
        gun_highlight: tuple[int, int, int],
        gun_dark: tuple[int, int, int],
    ) -> None:
        """Render the BFG 9000."""
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
