from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Any

import pygame

from games.shared.ui import Button
from games.shared.ui_renderer_base import UIRendererBase

from . import constants as C  # noqa: N812
from . import ui_menu_views, ui_overlay_views, ui_progress_views
from .custom_types import DamageText

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

        # Vignette
        self.screen.blit(self.vignette, (0, 0))

        # Crosshair
        self._render_crosshair()
        self._render_secondary_charge(game.player)

        # HUD elements
        self._render_messages(game)
        self._render_health_bar(game)
        self._render_ammo_display(game)
        self._render_weapon_slots(game)
        self._render_level_info(game)
        self._render_minimap(game)
        self._render_status_bars(game)
        self._render_controls_hint(game)
        self._render_pause_overlay(game)

    def _render_health_bar(self, game: Game) -> None:
        """Render the player health bar."""
        hud_bottom = C.SCREEN_HEIGHT - 80
        health_width = 150
        health_height = 25
        health_x = 20
        health_y = hud_bottom

        pygame.draw.rect(
            self.screen, C.DARK_GRAY, (health_x, health_y, health_width, health_height)
        )
        health_percent = max(0, game.player.health / game.player.max_health)
        fill_width = int(health_width * health_percent)
        health_color = C.RED
        if health_percent > 0.5:
            health_color = C.GREEN
        elif health_percent > 0.25:
            health_color = C.ORANGE
        health_rect = (health_x, health_y, fill_width, health_height)
        pygame.draw.rect(self.screen, health_color, health_rect)
        pygame.draw.rect(
            self.screen,
            C.WHITE,
            (health_x, health_y, health_width, health_height),
            2,
        )

    def _render_ammo_display(self, game: Game) -> None:
        """Render the ammo counter and weapon name."""
        hud_bottom = C.SCREEN_HEIGHT - 80

        w_state = game.player.weapon_state[game.player.current_weapon]
        w_name = C.WEAPONS[game.player.current_weapon]["name"]

        status_text = ""
        status_color = C.WHITE
        if w_state["reloading"]:
            status_text = "RELOADING..."
            status_color = C.YELLOW
        elif w_state["overheated"]:
            status_text = "OVERHEATED!"
            status_color = C.RED

        if status_text:
            txt = self.small_font.render(status_text, True, status_color)
            tr = txt.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 60))
            self.screen.blit(txt, tr)

        ammo_val = game.player.ammo[game.player.current_weapon]
        ammo_text = f"{w_name}: {w_state['clip']} / {ammo_val}"
        bomb_text = f"BOMBS: {game.player.bombs}"

        at = self.font.render(ammo_text, True, C.WHITE)
        bt = self.font.render(bomb_text, True, C.ORANGE)
        at_rect = at.get_rect(bottomright=(C.SCREEN_WIDTH - 20, hud_bottom + 25))
        bt_rect = bt.get_rect(bottomright=(C.SCREEN_WIDTH - 20, hud_bottom - 15))
        self.screen.blit(at, at_rect)
        self.screen.blit(bt, bt_rect)

    def _render_weapon_slots(self, game: Game) -> None:
        """Render the weapon inventory slots."""
        hud_bottom = C.SCREEN_HEIGHT - 80

        inv_y = hud_bottom - 80
        for w in ["pistol", "rifle", "shotgun", "laser", "plasma", "rocket", "minigun"]:
            color = C.GRAY
            if w in game.unlocked_weapons:
                color = C.GREEN if w == game.player.current_weapon else C.WHITE

            key_display = C.WEAPONS[w]["key"]
            # Just use key from dict

            text_str = f"[{key_display}] {C.WEAPONS[w]['name']}"
            inv_txt = self.tiny_font.render(text_str, True, color)
            inv_rect = inv_txt.get_rect(bottomright=(C.SCREEN_WIDTH - 20, inv_y))
            self.screen.blit(inv_txt, inv_rect)
            inv_y -= 25

    def _render_level_info(self, game: Game) -> None:
        """Render level number, enemy count, and score."""
        level_text = self.small_font.render(f"Level: {game.level}", True, C.YELLOW)
        level_rect = level_text.get_rect(topright=(C.SCREEN_WIDTH - 20, 20))
        self.screen.blit(level_text, level_rect)

        bots_alive = sum(
            1
            for bot in game.bots
            if bot.alive
            and bot.enemy_type != "health_pack"
            and C.ENEMY_TYPES[bot.enemy_type].get("visual_style") != "item"
        )
        kills_text = self.small_font.render(f"Enemies: {bots_alive}", True, C.RED)
        kills_rect = kills_text.get_rect(topright=(C.SCREEN_WIDTH - 20, 50))
        self.screen.blit(kills_text, kills_rect)

        # Score
        score = game.kills * 100
        score_text = self.small_font.render(f"Score: {score}", True, C.YELLOW)
        score_rect = score_text.get_rect(topright=(C.SCREEN_WIDTH - 20, 80))
        self.screen.blit(score_text, score_rect)

    def _render_minimap(self, game: Game) -> None:
        """Render the minimap if enabled."""
        if game.show_minimap:
            game.raycaster.render_minimap(
                self.screen, game.player, game.bots, game.visited_cells, game.portal
            )

    def _render_status_bars(self, game: Game) -> None:
        """Render shield bar, stamina bar, and laser charge bar."""
        hud_bottom = C.SCREEN_HEIGHT - 80
        health_x = 20
        health_y = hud_bottom

        shield_width = 150
        shield_height = 10
        shield_x = health_x
        shield_y = health_y - 20

        shield_pct = game.player.shield_timer / C.SHIELD_MAX_DURATION
        pygame.draw.rect(
            self.screen, C.DARK_GRAY, (shield_x, shield_y, shield_width, shield_height)
        )
        shield_rect = (
            shield_x,
            shield_y,
            int(shield_width * shield_pct),
            shield_height,
        )
        pygame.draw.rect(self.screen, C.CYAN, shield_rect)
        border_rect = (shield_x, shield_y, shield_width, shield_height)
        pygame.draw.rect(self.screen, C.WHITE, border_rect, 1)

        if game.player.shield_recharge_delay > 0:
            status_text = "RECHARGING" if game.player.shield_active else "COOLDOWN"
            status_surf = self.tiny_font.render(status_text, True, C.WHITE)
            self.screen.blit(status_surf, (shield_x + shield_width + 5, shield_y - 2))

        # Laser Charge
        laser_y = shield_y - 15
        laser_pct = 1.0 - (game.player.secondary_cooldown / C.SECONDARY_COOLDOWN)
        laser_pct = max(0, min(1, laser_pct))
        bg_rect = (shield_x, laser_y, shield_width, shield_height)
        pygame.draw.rect(self.screen, C.DARK_GRAY, bg_rect)
        pygame.draw.rect(
            self.screen,
            (255, 50, 50),
            (shield_x, laser_y, int(shield_width * laser_pct), shield_height),
        )

        # Stamina Bar
        stamina_y = laser_y - 15
        stamina_pct = game.player.stamina / game.player.max_stamina
        pygame.draw.rect(
            self.screen, C.DARK_GRAY, (shield_x, stamina_y, shield_width, shield_height)
        )
        pygame.draw.rect(
            self.screen,
            (255, 255, 0),
            (shield_x, stamina_y, int(shield_width * stamina_pct), shield_height),
        )
        if stamina_pct < 1.0:
            s_txt = self.tiny_font.render("STAMINA", True, C.WHITE)
            self.screen.blit(s_txt, (shield_x + shield_width + 5, stamina_y - 2))

    def _render_messages(self, game: Game) -> None:
        """Render floating damage texts and messages."""
        self._render_damage_texts(game.damage_texts)

    def _render_controls_hint(self, game: Game) -> None:
        """Render the controls hint text at the top of the screen."""
        controls_hint = self.tiny_font.render(
            "WASD:Move | 1-5:Wpn | R:Reload | F:Bomb | SPACE:Shield | M:Map | ESC:Menu",
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

    def _render_pause_overlay(self, game: Game) -> None:
        """Render the pause menu overlay if the game is paused."""
        if game.paused:
            self._render_pause_menu()

    def _render_damage_texts(self, texts: list[DamageText]) -> None:
        """Render floating damage text indicators."""
        for t in texts:
            surf = self.small_font.render(t["text"], True, t["color"])
            rect = surf.get_rect(center=(int(t["x"]), int(t["y"])))
            self.screen.blit(surf, rect)

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
            self.screen.blit(ready_text, (20, C.SCREEN_HEIGHT - 120))

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

        # Enhanced crosshair with outline and gap
        gap = 5
        length = 10
        color = (255, 255, 255)
        outline = (0, 0, 0)

        # Draw outline (thicker lines behind)
        ln, gp = length, gap
        pygame.draw.line(self.screen, outline, (cx - ln - 2, cy), (cx - gp + 2, cy), 4)
        pygame.draw.line(self.screen, outline, (cx + gp - 2, cy), (cx + ln + 2, cy), 4)
        pygame.draw.line(self.screen, outline, (cx, cy - ln - 2), (cx, cy - gp + 2), 4)
        pygame.draw.line(self.screen, outline, (cx, cy + gp - 2), (cx, cy + ln + 2), 4)

        # Draw main lines
        pygame.draw.line(self.screen, color, (cx - length, cy), (cx - gap, cy), 2)
        pygame.draw.line(self.screen, color, (cx + gap, cy), (cx + length, cy), 2)
        pygame.draw.line(self.screen, color, (cx, cy - length), (cx, cy - gap), 2)
        pygame.draw.line(self.screen, color, (cx, cy + gap), (cx, cy + length), 2)

        # Center dot
        pygame.draw.circle(self.screen, outline, (cx, cy), 3)
        pygame.draw.circle(self.screen, color, (cx, cy), 1)

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
