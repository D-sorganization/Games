from __future__ import annotations

import logging
import math
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

from games.shared.ui import Button
from games.shared.ui_renderer_base import UIRendererBase

from . import constants as C  # noqa: N812
from . import ui_menu_views, ui_overlay_views, ui_progress_views

try:
    import cv2

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

if TYPE_CHECKING:
    from .game import Game
    from .player import Player

logger = logging.getLogger(__name__)


class UIRenderer(UIRendererBase):
    """Handles all UI, HUD, and Menu rendering operations"""

    def __init__(self, screen: pygame.Surface) -> None:
        """Initialize the UI renderer"""
        super().__init__(screen, C.SCREEN_WIDTH, C.SCREEN_HEIGHT)
        self.intro_video: Any | None = None
        self.title_drips: list[dict[str, Any]] = []

        # Buttons
        self.start_button = Button(
            C.SCREEN_WIDTH // 2 - 250,
            C.SCREEN_HEIGHT - 120,
            500,
            70,
            "ENTER THE NIGHTMARE",
            C.DARK_RED,
        )

        # Particle surface
        self.particle_surface = pygame.Surface(
            (C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA
        )

        # Additional font aliases for Force_Field
        self._init_additional_fonts()

    def _init_additional_fonts(self) -> None:
        """Initialize additional fonts specific to Force_Field."""
        try:
            self.retro_title_font = pygame.font.SysFont("orbitron", 100, bold=True)
            self.retro_subtitle_font = pygame.font.SysFont("orbitron", 36, bold=True)
            self.retro_font = pygame.font.SysFont("exo", 40, bold=True)
            self.modern_font = pygame.font.SysFont("exo", 40, bold=True)
            self.modern_small_font = pygame.font.SysFont("exo", 28, bold=True)
            self.modern_tiny_font = pygame.font.SysFont("rajdhani", 20, bold=True)
        except (pygame.error, OSError):
            # Fallback to base fonts
            self.retro_title_font = self.title_font
            self.retro_subtitle_font = self.subtitle_font
            self.retro_font = self.font
            self.modern_font = self.font
            self.modern_small_font = self.small_font
            self.modern_tiny_font = self.tiny_font

    # ------------------------------------------------------------------
    # Law-of-Demeter delegate methods (avoid callers reaching into
    # internal attributes like intro_video and start_button directly).
    # ------------------------------------------------------------------

    def release_intro_video(self) -> None:
        """Release the intro video capture and clear the reference."""
        if self.intro_video:
            self.intro_video.release()
            self.intro_video = None

    def update_start_button(self, mouse_pos: tuple[int, int]) -> None:
        """Forward hover-update to the start button."""
        self.start_button.update(mouse_pos)

    def is_start_button_clicked(self, pos: tuple[int, int]) -> bool:
        """Return True if *pos* falls inside the start button."""
        return self.start_button.is_clicked(pos)

    def _get_base_dir(self) -> Path:
        """Override to handle frozen executables."""
        if getattr(sys, "frozen", False):
            return Path(sys._MEIPASS)  # type: ignore[attr-defined]
        return Path(__file__).resolve().parent.parent

    def render_menu(self) -> None:
        """Render main menu"""
        ui_menu_views.render_menu(self)

    def update_blood_drips(self, rect: pygame.Rect) -> None:
        """Spawn and update blood drips interacting with text rect"""
        ui_menu_views.update_blood_drips(self, rect)

    def _draw_blood_drips(self, drips: list[dict[str, Any]]) -> None:
        """Draw the blood drips"""
        ui_menu_views.draw_blood_drips(self, drips)

    def render_map_select(self, game: Game) -> None:
        """Render map select screen"""
        ui_menu_views.render_map_select(self, game)

    def render_hud(self, game: Game) -> None:
        """Render the heads-up display including health, ammo, and game stats."""
        if not (game.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        if not (game.raycaster is not None):
            raise ValueError("DbC Blocked: Precondition failed.")

        # Render overlays first
        self.overlay_surface.fill((0, 0, 0, 0))
        self._render_low_health_tint(game.player)
        self._render_damage_flash(game.damage_flash_timer)
        self._render_shield_effect(game.player)
        self.screen.blit(self.overlay_surface, (0, 0))

        # Crosshair
        self._render_crosshair()
        self._render_secondary_charge(game.player)

        # Floating damage/message texts
        self._render_messages(game)

        # Stacked status bars (health, shield, charge, stamina)
        self._render_health_bar(game)
        self._render_status_bars(game)

        # Controls hint
        self._render_controls_hint()

        # Pause Menu
        if game.paused:
            self._render_pause_overlay(game)

    # ------------------------------------------------------------------
    # HUD helper methods (extracted from render_hud)
    # ------------------------------------------------------------------

    def _render_health_bar(self, game: Game) -> None:
        """Render the player health bar at the bottom of the HUD."""
        player = _require_player(game)
        bar_height = 12
        bar_width = 150
        start_x = 20
        start_y = C.SCREEN_HEIGHT - 40  # Start from bottom

        health_y = start_y
        self._render_bar(
            start_x,
            health_y,
            bar_width,
            bar_height,
            player.health / player.max_health,
            C.RED if player.health <= 50 else C.GREEN,
            "HP",
        )

    def _render_status_bars(self, game: Game) -> None:
        """Render shield bar, secondary charge bar, and stamina bar."""
        player = _require_player(game)
        bar_height = 12
        bar_spacing = 8
        bar_width = 150
        start_x = 20
        start_y = C.SCREEN_HEIGHT - 40  # Start from bottom

        health_y = start_y

        # Shield Bar
        shield_y = health_y - (bar_height + bar_spacing)
        self._render_bar(
            start_x,
            shield_y,
            bar_width,
            bar_height,
            player.shield_timer / C.SHIELD_MAX_DURATION,
            C.CYAN,
            "SHLD",
        )
        # Shield Recharging/Cooldown Text
        if player.shield_recharge_delay > 0:
            status = "RECHRG" if player.shield_active else "COOL"
            txt = self.tiny_font.render(status, True, C.GRAY)
            self.screen.blit(txt, (start_x + bar_width + 5, shield_y - 2))

        # Secondary Charge
        charge_y = shield_y - (bar_height + bar_spacing)
        charge_pct = 1.0 - (player.secondary_cooldown / C.SECONDARY_COOLDOWN)
        self._render_bar(
            start_x,
            charge_y,
            bar_width,
            bar_height,
            max(0, min(1, charge_pct)),
            (255, 100, 100),
            "CHRG",
        )

        # Stamina
        stamina_y = charge_y - (bar_height + bar_spacing)
        self._render_bar(
            start_x,
            stamina_y,
            bar_width,
            bar_height,
            player.stamina / player.max_stamina,
            C.YELLOW,
            "STM",
        )

    def _render_messages(self, game: Game) -> None:
        """Render floating damage texts and messages."""
        self._render_damage_texts(game.damage_texts)

    def _render_pause_overlay(self, game: Game) -> None:
        """Render the pause menu overlay (delegates to _render_pause_menu)."""
        self._render_pause_menu(game)

    def _render_controls_hint(self) -> None:
        """Render the controls hint bar at the top of the screen."""
        msg = "WASD:Move|1-7:Wpn|R:Rel|Ctrl+C:Cheat|SPACE:Shield|M:Map|ESC:Menu"
        controls_hint = self.tiny_font.render(
            msg,
            True,
            C.WHITE,
        )
        controls_hint_rect = controls_hint.get_rect(topleft=(10, 10))
        bg_surface = pygame.Surface(
            (
                controls_hint_rect.width + C.HINT_BG_PADDING_H,
                controls_hint_rect.height + C.HINT_BG_PADDING_V,
            ),
            pygame.SRCALPHA,
        )
        bg_surface.fill(C.HINT_BG_COLOR)
        self.screen.blit(
            bg_surface,
            (
                controls_hint_rect.x - C.HINT_BG_PADDING_H // 2,
                controls_hint_rect.y - C.HINT_BG_PADDING_V // 2,
            ),
        )
        self.screen.blit(controls_hint, controls_hint_rect)

    def _render_damage_texts(self, texts: list[dict[str, Any]]) -> None:
        """Render floating damage text indicators with enhanced effects."""
        for t in texts:
            # Check for special effects
            is_large = t.get("size") == "large"
            has_glow = t.get("effect") == "glow"

            # Choose font based on size
            font = self.subtitle_font if is_large else self.small_font

            # Create text surface
            text_surf = font.render(t["text"], True, t["color"])

            # Add glow effect for special messages
            if has_glow:
                # Create glow surface
                glow_surf = font.render(t["text"], True, (255, 255, 255))

                # Draw glow in multiple positions for blur effect
                glow_positions = [
                    (-2, -2),
                    (-2, 2),
                    (2, -2),
                    (2, 2),
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1),
                ]
                for gx, gy in glow_positions:
                    glow_rect = glow_surf.get_rect(
                        center=(int(t["x"]) + gx, int(t["y"]) + gy)
                    )
                    glow_surf.set_alpha(50)  # Semi-transparent glow
                    self.screen.blit(glow_surf, glow_rect)

            # Draw main text
            rect = text_surf.get_rect(center=(int(t["x"]), int(t["y"])))
            self.screen.blit(text_surf, rect)

    def _render_damage_flash(self, timer: int) -> None:
        """Render red screen flash effect when player takes damage."""
        if timer > 0:
            alpha = int(100 * (timer / 10.0))
            self.overlay_surface.fill(
                (255, 0, 0, alpha), special_flags=pygame.BLEND_RGBA_ADD
            )

    def _render_shield_effect(self, player: Player) -> None:
        """Render shield activation visual effects and status."""
        if player.shield_active:
            # Simple fill
            pygame.draw.rect(
                self.overlay_surface,
                (*C.SHIELD_COLOR, C.SHIELD_ALPHA),
                (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT),
            )
            # Border
            pygame.draw.rect(
                self.overlay_surface,
                C.SHIELD_COLOR,
                (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT),
                10,
            )

            shield_text = self.title_font.render("SHIELD ACTIVE", True, C.SHIELD_COLOR)
            self.screen.blit(
                shield_text,
                (C.SCREEN_WIDTH // 2 - shield_text.get_width() // 2, 100),
            )

            time_left = player.shield_timer / 60.0
            timer_text = self.small_font.render(f"{time_left:.1f}s", True, C.WHITE)
            self.screen.blit(
                timer_text,
                (C.SCREEN_WIDTH // 2 - timer_text.get_width() // 2, 160),
            )

            if player.shield_timer < 120 and (player.shield_timer // 10) % 2 == 0:
                pygame.draw.rect(
                    self.overlay_surface,
                    (255, 0, 0, 50),
                    (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT),
                )

        elif (
            player.shield_timer == C.SHIELD_MAX_DURATION
            and player.shield_recharge_delay <= 0
        ):
            ready_text = self.tiny_font.render("SHIELD READY", True, C.CYAN)
            # Position above stamina bar (which ends at ~H-130)
            self.screen.blit(ready_text, (20, C.SCREEN_HEIGHT - 160))

    def _render_bar(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        pct: float,
        color: tuple[int, int, int],
        label: str,
    ) -> None:
        """Helper to render a labeled HUD bar."""
        # Background
        pygame.draw.rect(self.screen, C.DARK_GRAY, (x, y, w, h))
        # Fill
        fill_w = int(w * max(0.0, min(1.0, pct)))
        if fill_w > 0:
            pygame.draw.rect(self.screen, color, (x, y, fill_w, h))
        # Border
        pygame.draw.rect(self.screen, C.WHITE, (x, y, w, h), 1)
        # Label
        lbl = self.tiny_font.render(label, True, C.WHITE)
        # Place label to right of bar
        self.screen.blit(lbl, (x + w + 5, y - 2))

    def _render_low_health_tint(self, player: Player) -> None:
        """Render red screen tint when health is low."""
        if player.health < 50:
            alpha = int(100 * (1.0 - (player.health / 50.0)))
            self.overlay_surface.fill(
                (255, 0, 0, alpha), special_flags=pygame.BLEND_RGBA_ADD
            )

    def _render_crosshair(self) -> None:
        """Render the aiming crosshair at the center of the screen."""
        cx = C.SCREEN_WIDTH // 2
        cy = C.SCREEN_HEIGHT // 2
        size = 12
        pygame.draw.line(self.screen, C.RED, (cx - size, cy), (cx + size, cy), 2)
        pygame.draw.line(self.screen, C.RED, (cx, cy - size), (cx, cy + size), 2)
        pygame.draw.circle(self.screen, C.RED, (cx, cy), 2)

    def _render_secondary_charge(self, player: Player) -> None:
        """Render secondary weapon charge bar."""
        charge_pct = 1.0 - (player.secondary_cooldown / C.SECONDARY_COOLDOWN)
        if charge_pct < 1.0:
            bar_w = 40
            bar_h = 4
            cx, cy = C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 30
            pygame.draw.rect(
                self.screen, C.DARK_GRAY, (cx - bar_w // 2, cy, bar_w, bar_h)
            )
            pygame.draw.rect(
                self.screen,
                C.CYAN,
                (cx - bar_w // 2, cy, int(bar_w * charge_pct), bar_h),
            )

    def _render_pause_menu(self, game: Game) -> None:
        """Render the pause menu overlay."""
        ui_overlay_views.render_pause_menu(self, game)

    def render_level_complete(self, game: Game) -> None:
        """Render the level complete screen."""
        ui_progress_views.render_level_complete(self, game)

    def render_game_over(self, game: Game) -> None:
        """Render the game over screen."""
        ui_progress_views.render_game_over(self, game)

    def _render_stats_lines(
        self, stats: list[tuple[str, tuple[int, int, int]]], start_y: int
    ) -> None:
        """Render a list of stat lines."""
        ui_progress_views.render_stats_lines(self, stats, start_y)

    def render_intro(self, intro_phase: int, intro_step: int, elapsed: int) -> None:
        """Render intro"""
        self.screen.fill(C.BLACK)

        if intro_phase == 0:
            if "willy" in self.intro_images:
                img = self.intro_images["willy"]
                r = img.get_rect(
                    center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 30)
                )
                self.screen.blit(img, r)
                pygame.draw.rect(self.screen, (255, 192, 203), r, 4, border_radius=10)

            text = self.subtitle_font.render(
                "A Willy Wonk Production", True, (255, 182, 193)
            )
            self.screen.blit(text, text.get_rect(center=(C.SCREEN_WIDTH // 2, 100)))

        elif intro_phase == 1:
            stylish = pygame.font.SysFont("impact", 70)
            pulse = abs(math.sin(elapsed * 0.003))
            color = (0, int(150 + 100 * pulse), int(200 + 55 * pulse))

            t2 = stylish.render("UPSTREAM DRIFT", True, color)
            self.screen.blit(
                t2,
                t2.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 - 180)),
            )

            t1 = self.tiny_font.render("in association with", True, C.CYAN)
            self.screen.blit(
                t1,
                t1.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 - 230)),
            )

            if self.intro_video and self.intro_video.isOpened():
                ret, frame = self.intro_video.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = frame.swapaxes(0, 1)
                    surf = pygame.surfarray.make_surface(frame)
                    target_h = 400
                    scale = target_h / surf.get_height()
                    surf = pygame.transform.scale(
                        surf,
                        (int(surf.get_width() * scale), int(surf.get_height() * scale)),
                    )
                    self.screen.blit(
                        surf,
                        surf.get_rect(
                            center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 50)
                        ),
                    )
                else:
                    self.intro_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            elif "deadfish" in self.intro_images:
                img = self.intro_images["deadfish"]
                self.screen.blit(
                    img,
                    img.get_rect(
                        center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 50)
                    ),
                )

        elif intro_phase == 2:
            self._render_intro_slide(intro_step, elapsed)

        pygame.display.flip()

    def _get_intro_slides(self) -> list[dict[str, Any]]:
        """Return Force Field-specific intro slide data."""
        return [
            {
                "type": "distortion",
                "text": "FROM THE DEMENTED MIND",
                "text2": "OF JASPER",
                "duration": 8000,
            },
            {
                "type": "story",
                "lines": [
                    "They said the field would contain them.",
                    "They were wrong.",
                    "The specimens have breached the perimeter.",
                    "You are the last containment unit.",
                    "Objective: TERMINATE.",
                ],
                "duration": 10000,
            },
            {
                "type": "static",
                "text": "NO MERCY. NO ESCAPE.",
                "duration": 4000,
                "color": (200, 0, 0),
            },
            {
                "type": "static",
                "text": "FORCE FIELD",
                "sub": "THE ARENA AWAITS",
                "duration": 4000,
                "color": C.WHITE,
            },
        ]

    def _get_game_name(self) -> str:
        """Return the game name for asset loading."""
        return "Force_Field"

    def _get_game_title(self) -> str:
        """Return the Force Field game title."""
        return "FORCE FIELD"

    def _get_subtitle_color(self) -> tuple[int, int, int]:
        """Return subtitle color for Force Field (cyan)."""
        return C.CYAN

    def _get_constants_module(self) -> Any:
        """Return the Force Field constants module."""
        return C

    def render_key_config(self, game: Any) -> None:
        """Render the key configuration menu."""
        ui_overlay_views.render_key_config(self, game)


def _require_player(game: Game) -> Player:
    """Return the current player or raise when HUD rendering is unavailable."""
    if game.player is None:
        raise ValueError("DbC Blocked: Precondition failed.")
    return game.player
