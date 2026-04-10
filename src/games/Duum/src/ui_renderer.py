from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Any

import pygame

from games.shared.ui import Button
from games.shared.ui_renderer_base import UIRendererBase

from . import constants as C  # noqa: N812
from . import ui_hud_views, ui_menu_views, ui_overlay_views, ui_progress_views

try:
    import cv2

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

if TYPE_CHECKING:
    from .game import Game

logger = logging.getLogger(__name__)


class UIRenderer(UIRendererBase):
    """Handles all UI, HUD, and Menu rendering operations"""

    def __init__(self, screen: pygame.Surface) -> None:
        """Initialize the UI renderer"""
        super().__init__(screen, C.SCREEN_WIDTH, C.SCREEN_HEIGHT)

        # Buttons
        self.start_button = Button(
            C.SCREEN_WIDTH // 2 - 250,
            C.SCREEN_HEIGHT - 120,
            500,
            70,
            "ENTER THE NIGHTMARE",
            C.DARK_RED,
        )

        # Generate vignette
        self._generate_vignette()

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

    def _generate_vignette(self) -> None:
        """Generate a static vignette surface."""
        w, h = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        vw, vh = w // 8, h // 8
        vig_small = pygame.Surface((vw, vh), pygame.SRCALPHA)

        cx, cy = vw // 2, vh // 2
        max_dist = math.sqrt(cx**2 + cy**2)

        vig_small.fill((0, 0, 0, 255))

        for y in range(vh):
            for x in range(vw):
                dx = x - cx
                dy = y - cy
                dist = math.sqrt(dx * dx + dy * dy)

                d = dist / max_dist
                val = max(0.0, d - 0.4)
                val = val / 0.6

                alpha = int(255 * (val**2))
                alpha = min(alpha, 255)

                vig_small.set_at((x, y), (0, 0, 0, alpha))

        self.vignette = pygame.transform.smoothscale(vig_small, (w, h))

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
        ui_hud_views.render_hud(self, game)

    def _render_pause_menu(self) -> None:
        """Render the pause menu overlay."""
        ui_overlay_views.render_pause_menu(self)

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
            text = self.subtitle_font.render(
                "A Willy Wonk Production", True, (255, 182, 193)
            )
            self.screen.blit(text, text.get_rect(center=(C.SCREEN_WIDTH // 2, 100)))
            if "willy" in self.intro_images:
                img = self.intro_images["willy"]
                r = img.get_rect(
                    center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 30)
                )
                self.screen.blit(img, r)
                pygame.draw.rect(self.screen, (255, 192, 203), r, 4, border_radius=10)

        elif intro_phase == 1:
            stylish = pygame.font.SysFont("impact", 70)
            pulse = abs(math.sin(elapsed * 0.003))
            color = (0, int(150 + 100 * pulse), int(200 + 55 * pulse))

            t2 = stylish.render("DUUM", True, color)
            self.screen.blit(
                t2,
                t2.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 - 180)),
            )

            t1 = self.tiny_font.render("a reimagining", True, C.RED)
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
        """Return Duum-specific intro slide data."""
        return [
            {
                "type": "distortion",
                "text": "THE GATE HAS OPENED",
                "text2": "HELL IS REBOOTING",
                "duration": 8000,
            },
            {
                "type": "story",
                "lines": [
                    "The Union Aerospace Corporation failed.",
                    "The demons have corrupted the source code.",
                    "You are the last patch.",
                    "Debug the system.",
                    "Terminate the processes.",
                ],
                "duration": 10000,
            },
            {
                "type": "static",
                "text": "RIP AND TEAR",
                "duration": 4000,
                "color": (200, 0, 0),
            },
            {
                "type": "static",
                "text": "DUUM",
                "sub": "IT RUNS ON EVERYTHING",
                "duration": 4000,
                "color": C.WHITE,
            },
        ]

    def _get_game_name(self) -> str:
        """Return the game name for asset loading."""
        return "Duum"

    def _get_game_title(self) -> str:
        """Return the Duum game title."""
        return "DUUM"

    def _get_subtitle_color(self) -> tuple[int, int, int]:
        """Return subtitle color for Duum (red)."""
        return C.RED

    def _get_constants_module(self) -> Any:
        """Return the Duum constants module."""
        return C

    def render_key_config(self, game: Any) -> None:
        """Render the key configuration menu."""
        ui_overlay_views.render_key_config(self, game)
