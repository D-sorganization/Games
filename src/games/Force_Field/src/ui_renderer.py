from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

from games.shared.ui import Button
from games.shared.ui_renderer_base import UIRendererBase

from . import constants as C  # noqa: N812
from . import ui_hud_views, ui_menu_views, ui_overlay_views, ui_progress_views

if TYPE_CHECKING:
    from .game import Game

logger = logging.getLogger(__name__)


class UIRenderer(UIRendererBase):
    """Handles all UI, HUD, and Menu rendering operations"""

    def __init__(self, screen: pygame.Surface) -> None:
        """Initialize the UI renderer"""
        super().__init__(screen, C.SCREEN_WIDTH, C.SCREEN_HEIGHT)
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
        ui_hud_views.render_hud(self, game)

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
