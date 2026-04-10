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
    from .player import Player

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

    def _render_health_bar(self, game: Game) -> None:
        """Render the player health bar."""
        ui_hud_views.render_health_bar(self, game)

    def _render_ammo_display(self, game: Game) -> None:
        """Render the ammo counter and weapon name."""
        ui_hud_views.render_ammo_display(self, game)

    def _render_weapon_slots(self, game: Game) -> None:
        """Render the weapon inventory slots."""
        ui_hud_views.render_weapon_slots(self, game)

    def _render_level_info(self, game: Game) -> None:
        """Render the level number, enemy count, kills, and controls hint."""
        ui_hud_views.render_level_info(self, game)

    def _render_minimap(self, game: Game) -> None:
        """Render the minimap."""
        ui_hud_views.render_minimap(self, game)

    def _render_status_bars(self, game: Game) -> None:
        """Render the shield bar, stamina bar, and laser charge."""
        ui_hud_views.render_status_bars(self, game)

    def _render_messages(self, game: Game) -> None:
        """Render floating damage texts and messages."""
        ui_hud_views.render_messages(self, game)

    def _render_pause_overlay(self, game: Game) -> None:
        """Render the pause menu overlay if the game is paused."""
        ui_hud_views.render_pause_overlay(self, game)

    def _render_damage_texts(self, texts: list[dict[str, Any]]) -> None:
        """Render floating damage text indicators."""
        ui_hud_views.render_damage_texts(self, texts)

    def _render_damage_flash(self, timer: int) -> None:
        """Render red screen flash effect when player takes damage."""
        ui_hud_views.render_damage_flash(self, timer)

    def _render_shield_effect(self, player: Player) -> None:
        """Render shield activation visual effects and status."""
        ui_hud_views.render_shield_effect(self, player)

    def _render_low_health_tint(self, player: Player) -> None:
        """Render red screen tint when health is low."""
        ui_hud_views.render_low_health_tint(self, player)

    def _render_crosshair(self) -> None:
        """Render the aiming crosshair at the center of the screen."""
        ui_hud_views.render_crosshair(self)

    def _render_secondary_charge(self, player: Player) -> None:
        """Render secondary weapon charge bar."""
        ui_hud_views.render_secondary_charge(self, player)

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
        """Return Zombie Survival-specific intro slide data."""
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
                "text": "ZOMBIE SURVIVAL",
                "sub": "UNDEAD NIGHTMARE",
                "duration": 4000,
                "color": C.WHITE,
            },
        ]

    def _get_game_name(self) -> str:
        """Return the game name for asset loading."""
        return "Zombie_Survival"

    def _get_game_title(self) -> str:
        """Return the Zombie Survival game title."""
        return "ZOMBIE SURVIVAL"

    def _get_subtitle_color(self) -> tuple[int, int, int]:
        """Return subtitle color for Zombie Survival (cyan)."""
        return C.CYAN

    def _get_constants_module(self) -> Any:
        """Return the Zombie Survival constants module."""
        return C

    def render_key_config(self, game: Any) -> None:
        """Render the key configuration menu."""
        ui_overlay_views.render_key_config(self, game)
