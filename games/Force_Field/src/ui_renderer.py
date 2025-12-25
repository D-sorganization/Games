from __future__ import annotations

import logging
import math
import os
import random
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pygame

from . import constants as C  # noqa: N812
from .ui import Button

try:
    import cv2

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

if TYPE_CHECKING:
    from .game import Game
    from .player import Player

logger = logging.getLogger(__name__)


class UIRenderer:
    """Handles all UI, HUD, and Menu rendering operations"""

    def __init__(self, screen: pygame.Surface) -> None:
        """Initialize the UI renderer"""
        self.screen = screen

        # Load Intro Images
        self.intro_images: dict[str, pygame.Surface] = {}
        self.intro_video: Any | None = None
        self._load_assets()

        # Fonts
        self._init_fonts()

        # Buttons
        self.start_button = Button(
            C.SCREEN_WIDTH // 2 - 250,
            C.SCREEN_HEIGHT - 120,
            500,
            70,
            "ENTER THE NIGHTMARE",
            C.DARK_RED,
        )

        # Optimization: Shared surface for alpha effects
        size = (C.SCREEN_WIDTH, C.SCREEN_HEIGHT)
        self.overlay_surface = pygame.Surface(size, pygame.SRCALPHA)

        # Menu Visual State
        self.title_drips: list[dict[str, Any]] = []

    def _init_fonts(self) -> None:
        """Initialize fonts"""
        try:
            self.title_font = pygame.font.SysFont("impact", 100)
            self.font = pygame.font.SysFont("franklingothicmedium", 40)
            self.small_font = pygame.font.SysFont("franklingothicmedium", 28)
            self.tiny_font = pygame.font.SysFont("consolas", 20)
            self.subtitle_font = pygame.font.SysFont("georgia", 36)
            # 'chiller' is a non-standard font used for intro slides.
            # If unavailable, it falls back to title_font in the exception handler.
            self.chiller_font = pygame.font.SysFont("chiller", 70)
        except Exception:  # noqa: BLE001
            self.title_font = pygame.font.Font(None, 80)
            self.font = pygame.font.Font(None, 48)
            self.small_font = pygame.font.Font(None, 32)
            self.tiny_font = pygame.font.Font(None, 24)
            self.subtitle_font = pygame.font.Font(None, 40)
            self.chiller_font = self.title_font

    def _load_assets(self) -> None:
        """Load images and video"""
        try:
            if getattr(sys, "frozen", False):
                base_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]
            else:
                base_dir = Path(__file__).resolve().parent.parent

            self.assets_dir = str(base_dir / "assets")
            pics_dir = str(base_dir / "pics")

            # Willy Wonk
            willy_path = os.path.join(pics_dir, "WillyWonk.JPG")
            if os.path.exists(willy_path):
                img = pygame.image.load(willy_path)
                img = pygame.transform.rotate(img, -90)
                scale = min(500 / img.get_height(), 800 / img.get_width())
                if scale < 1:
                    new_size = (
                        int(img.get_width() * scale),
                        int(img.get_height() * scale),
                    )
                    img = pygame.transform.scale(img, new_size)
                self.intro_images["willy"] = img

            # Setup Video
            video_path = os.path.join(pics_dir, "DeadFishSwimming.mp4")
            if HAS_CV2 and os.path.exists(video_path):
                self.intro_video = cv2.VideoCapture(video_path)

            # Fallback Image
            deadfish_path = os.path.join(pics_dir, "DeadFishSwimming_0.JPG")
            if os.path.exists(deadfish_path):
                img = pygame.image.load(deadfish_path)
                scale = min(500 / img.get_height(), 800 / img.get_width())
                if scale < 1:
                    new_size = (
                        int(img.get_width() * scale),
                        int(img.get_height() * scale),
                    )
                    img = pygame.transform.scale(img, new_size)
                self.intro_images["deadfish"] = img

        except Exception:
            logger.exception("Failed to load assets")

    def render_menu(self) -> None:
        """Render main menu"""
        self.screen.fill(C.BLACK)

        title = self.title_font.render("FORCE FIELD", True, C.RED)
        title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 100))

        sub = self.subtitle_font.render("THE ARENA AWAITS", True, C.WHITE)
        sub_rect = sub.get_rect(center=(C.SCREEN_WIDTH // 2, 160))

        self.screen.blit(title, title_rect)
        self.screen.blit(sub, sub_rect)

        self.update_blood_drips(title_rect)
        self._draw_blood_drips(self.title_drips)

        if (pygame.time.get_ticks() // 500) % 2 == 0:
            prompt = self.font.render("CLICK TO BEGIN", True, C.GRAY)
            center_pos = (C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 150)
            prompt_rect = prompt.get_rect(center=center_pos)
            self.screen.blit(prompt, prompt_rect)

        credit = self.tiny_font.render("A Jasper Production", True, C.DARK_GRAY)
        center_pos = (C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 50)
        credit_rect = credit.get_rect(center=center_pos)
        self.screen.blit(credit, credit_rect)
        pygame.display.flip()

    def update_blood_drips(self, rect: pygame.Rect) -> None:
        """Spawn and update blood drips interacting with text rect"""
        # Spawn
        if random.random() < 0.3:
            x = random.randint(rect.left, rect.right)
            self.title_drips.append(
                {
                    "x": x,
                    "y": rect.top,
                    "start_y": rect.top,
                    "speed": random.uniform(0.5, 2.0),
                    "size": random.randint(2, 4),
                    "color": (random.randint(180, 255), 0, 0),
                }
            )

        # Update
        for drip in self.title_drips[:]:
            drip["y"] += drip["speed"]
            drip["speed"] *= 1.02
            if drip["y"] > C.SCREEN_HEIGHT:
                self.title_drips.remove(drip)

    def _draw_blood_drips(self, drips: list[dict[str, Any]]) -> None:
        """Draw the blood drips"""
        for drip in drips:
            pygame.draw.line(
                self.screen,
                drip["color"],
                (drip["x"], drip["start_y"]),
                (drip["x"], drip["y"]),
                drip["size"],
            )
            pygame.draw.circle(
                self.screen,
                drip["color"],
                (drip["x"], int(drip["y"])),
                drip["size"] + 1,
            )

    def render_map_select(self, game: Game) -> None:
        """Render map select screen"""
        self.screen.fill(C.BLACK)

        title = self.subtitle_font.render("MISSION SETUP", True, C.RED)
        # Shadow
        for off in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            shadow = self.subtitle_font.render("MISSION SETUP", True, (50, 0, 0))
            cx = C.SCREEN_WIDTH // 2 + off[0]
            cy = 100 + off[1]
            s_rect = shadow.get_rect(center=(cx, cy))
            self.screen.blit(shadow, s_rect)

        title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        mouse_pos = pygame.mouse.get_pos()
        start_y = 200
        line_height = 80

        settings = [
            ("Map Size", str(game.selected_map_size)),
            ("Difficulty", game.selected_difficulty),
            ("Start Level", str(game.selected_start_level)),
            ("Lives", str(game.selected_lives)),
        ]

        for i, (label, value) in enumerate(settings):
            y = start_y + i * line_height
            color = C.WHITE
            if abs(mouse_pos[1] - y) < 20:
                color = C.YELLOW

            label_surf = self.subtitle_font.render(f"{label}:", True, C.GRAY)
            label_rect = label_surf.get_rect(right=C.SCREEN_WIDTH // 2 - 20, centery=y)

            val_surf = self.subtitle_font.render(value, True, color)
            val_rect = val_surf.get_rect(left=C.SCREEN_WIDTH // 2 + 20, centery=y)

            self.screen.blit(label_surf, label_rect)
            self.screen.blit(val_surf, val_rect)

        self.start_button.draw(self.screen, self.font)

        instructions = [
            "",
            "",
            "WASD: Move | Shift: Sprint | Mouse: Look | 1-4: Weapons",
            "Ctrl: Shoot | Z: Zoom | F: Bomb | Space: Shield",
        ]
        y = C.SCREEN_HEIGHT - 260
        for line in instructions:
            text = self.tiny_font.render(line, True, C.RED)
            text_rect = text.get_rect(center=(C.SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 30

        pygame.display.flip()

    def render_hud(self, game: Game) -> None:
        """Render the heads-up display including health, ammo, and game stats."""
        assert game.player is not None
        assert game.raycaster is not None

        # Render overlays first
        self.overlay_surface.fill((0, 0, 0, 0))
        self._render_low_health_tint(game.player)
        self._render_damage_flash(game.damage_flash_timer)
        self._render_shield_effect(game.player)
        self.screen.blit(self.overlay_surface, (0, 0))

        # Crosshair
        self._render_crosshair()
        self._render_secondary_charge(game.player)

        # Damage texts
        self._render_damage_texts(game.damage_texts)

        hud_bottom = C.SCREEN_HEIGHT - 80
        health_width = 150
        health_height = 25
        health_x = 20
        health_y = hud_bottom

        # Health
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

        # Ammo / State
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

        # Inventory
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

        # Stats
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

        if game.show_minimap:
            game.raycaster.render_minimap(
                self.screen, game.player, game.bots, game.visited_cells, game.portal
            )

        # Shield Bar
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

        # Pause Menu
        if game.paused:
            self._render_pause_menu()

    def _render_damage_texts(self, texts: list[dict[str, Any]]) -> None:
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

    def _render_pause_menu(self) -> None:
        """Render the pause menu overlay."""
        overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        title = self.title_font.render("PAUSED", True, C.RED)
        title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        menu_items = ["RESUME", "SAVE GAME", "CONTROLS", "QUIT TO MENU"]
        mouse_pos = pygame.mouse.get_pos()

        for i, item in enumerate(menu_items):
            color = C.WHITE
            rect = pygame.Rect(C.SCREEN_WIDTH // 2 - 100, 350 + i * 60, 200, 50)
            if rect.collidepoint(mouse_pos):
                color = C.YELLOW
                pygame.draw.rect(self.screen, (50, 0, 0), rect)
                pygame.draw.rect(self.screen, C.RED, rect, 2)

            text = self.subtitle_font.render(item, True, color)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

    def render_level_complete(self, game: Game) -> None:
        """Render the level complete screen."""
        self.screen.fill(C.BLACK)
        title = self.title_font.render("SECTOR CLEARED", True, C.GREEN)
        title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        level_time = game.level_times[-1] if game.level_times else 0
        total_time = sum(game.level_times)
        stats = [
            (f"Level {game.level} cleared!", C.WHITE),
            (f"Time: {level_time:.1f}s", C.GREEN),
            (f"Total Time: {total_time:.1f}s", C.GREEN),
            (f"Total Kills: {game.kills}", C.WHITE),
            ("", C.WHITE),
            ("Next level: Enemies get stronger!", C.YELLOW),
            ("", C.WHITE),
            ("Press SPACE for next level", C.WHITE),
            ("Press ESC for menu", C.WHITE),
        ]
        self._render_stats_lines(stats, 250)
        pygame.display.flip()

    def render_game_over(self, game: Game) -> None:
        """Render the game over screen."""
        self.screen.fill(C.BLACK)
        title = self.title_font.render("SYSTEM FAILURE", True, C.RED)
        title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        completed_levels = max(0, game.level - 1)
        total_time = sum(game.level_times)
        avg_time = total_time / len(game.level_times) if game.level_times else 0

        stats = [
            (
                f"You survived {completed_levels} "
                f"level{'s' if completed_levels != 1 else ''}",
                C.WHITE,
            ),
            (f"Total Kills: {game.kills}", C.WHITE),
            (f"Total Time: {total_time:.1f}s", C.GREEN),
            (
                (f"Average Time/Level: {avg_time:.1f}s", C.GREEN)
                if game.level_times
                else ("", C.WHITE)
            ),
            ("", C.WHITE),
            ("Press SPACE to restart", C.WHITE),
            ("Press ESC for menu", C.WHITE),
        ]
        self._render_stats_lines(stats, 250)
        pygame.display.flip()

    def _render_stats_lines(
        self, stats: list[tuple[str, tuple[int, int, int]]], start_y: int
    ) -> None:
        """Render a list of stat lines."""
        y = start_y
        for line, color in stats:
            if line:
                text = self.small_font.render(line, True, color)
                text_rect = text.get_rect(center=(C.SCREEN_WIDTH // 2, y))
                self.screen.blit(text, text_rect)
            y += 40

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

    def _render_intro_slide(self, step: int, elapsed: int) -> None:
        """Render intro slides."""
        slides = [
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

        if step < len(slides):
            slide = slides[step]
            duration = int(cast("int", slide["duration"]))

            if slide["type"] == "distortion":
                font = self.chiller_font
                lines = [str(slide["text"])]
                if "text2" in slide:
                    lines.append(str(slide["text2"]))

                start_y = C.SCREEN_HEIGHT // 2 - (len(lines) * 80) // 2
                for i, text in enumerate(lines):
                    total_w = sum([font.size(c)[0] for c in text])
                    start_x = (C.SCREEN_WIDTH - total_w) // 2
                    y = start_y + i * 100
                    x_off = 0
                    for idx, char in enumerate(text):
                        tf = pygame.time.get_ticks() * 0.003 + idx * 0.2
                        jx = math.sin(tf * 2.0) * 2
                        jy = math.cos(tf * 1.5) * 4
                        c_val = int(120 + 135 * abs(math.sin(tf * 0.8)))

                        self.screen.blit(
                            font.render(char, True, (50, 0, 0)),
                            (start_x + x_off + jx + 2, y + jy + 2),
                        )
                        self.screen.blit(
                            font.render(char, True, (c_val, 0, 0)),
                            (start_x + x_off + jx, y + jy),
                        )
                        x_off += font.size(char)[0]

            elif slide["type"] == "story":
                lines = cast("list[str]", slide["lines"])
                show_count = int((elapsed / duration) * (len(lines) + 1))
                show_count = min(show_count, len(lines))
                y = C.SCREEN_HEIGHT // 2 - (len(lines) * 50) // 2
                for i in range(show_count):
                    s = self.subtitle_font.render(lines[i], True, C.RED)
                    self.screen.blit(s, s.get_rect(center=(C.SCREEN_WIDTH // 2, y)))
                    y += 50

            elif slide["type"] == "static":
                color = cast("tuple[int, int, int]", slide.get("color", C.WHITE))
                if slide["text"] == "FORCE FIELD":
                    fade = min(1.0, elapsed / duration)
                    r = int(255 + (255 - 255) * fade)
                    g = int(255 + (0 - 255) * fade)
                    b = int(255 + (0 - 255) * fade)
                    color = (r, g, b)

                txt = self.title_font.render(str(slide["text"]), True, color)
                rect = txt.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2))
                if slide["text"] == "FORCE FIELD":
                    rect.centery = 100  # Match Main Menu title position
                self.screen.blit(txt, rect)

                if (
                    slide["text"] == "FORCE FIELD"
                    and color[0] > 250
                    and color[1] < 10
                    and color[2] < 10
                ):
                    self.update_blood_drips(rect)
                    self._draw_blood_drips(self.title_drips)

                if "sub" in slide:
                    sub = self.subtitle_font.render(str(slide["sub"]), True, C.CYAN)
                    self.screen.blit(
                        sub,
                        sub.get_rect(
                            center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 60)
                        ),
                    )

    def render_key_config(self, game: Any) -> None:
        """Render the key configuration menu."""
        self.screen.fill(C.BLACK)

        title = self.title_font.render("CONTROLS", True, C.RED)
        self.screen.blit(title, title.get_rect(center=(C.SCREEN_WIDTH // 2, 50)))

        bindings = game.input_manager.bindings
        start_y = 120
        col_1_x = C.SCREEN_WIDTH // 4
        col_2_x = C.SCREEN_WIDTH * 3 // 4

        actions = sorted(bindings.keys())

        limit = 12

        for i, action in enumerate(actions):
            col = 0 if i < limit else 1
            idx = i if i < limit else i - limit
            x = col_1_x if col == 0 else col_2_x
            y = start_y + idx * 40

            name_str = action.replace("_", " ").upper()
            color = C.WHITE
            if game.binding_action == action:
                color = C.YELLOW
                key_text = "PRESS ANY KEY..."
            else:
                key_text = game.input_manager.get_key_name(action)

            name_txt = self.tiny_font.render(f"{name_str}:", True, C.GRAY)
            key_txt = self.tiny_font.render(key_text, True, color)

            self.screen.blit(name_txt, (x - 150, y))
            self.screen.blit(key_txt, (x + 20, y))

        back_txt = self.subtitle_font.render("BACK", True, C.WHITE)
        back_rect = back_txt.get_rect(
            center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 60)
        )
        self.screen.blit(back_txt, back_rect)
        if back_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(self.screen, C.RED, back_rect, 2)

        pygame.display.flip()
