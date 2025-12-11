from __future__ import annotations

import math
import os
import random
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, cast

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


class GameRenderer:
    """Handles all rendering operations for the game"""

    def __init__(self, screen: pygame.Surface) -> None:
        """Initialize the game renderer with a screen surface.

        Args:
            screen: The pygame Surface to render to.
        """
        self.screen = screen

        # Load Intro Images
        self.intro_images: Dict[str, pygame.Surface] = {}
        self.intro_video = None
        self._load_assets()

        # Fonts
        self._init_fonts()

        # Cache static UI strings
        self.weapon_hints = " ".join(
            f"{weapon_data['key']}:{weapon_data['name']}" for weapon_data in C.WEAPONS.values()
        )

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
        self.effects_surface = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)

        # Menu Visual State
        self.title_drips: List[Dict[str, Any]] = []

    def _init_fonts(self) -> None:
        """Initialize fonts"""
        try:
            self.title_font = pygame.font.SysFont("impact", 100)
            self.font = pygame.font.SysFont("franklingothicmedium", 40)
            self.small_font = pygame.font.SysFont("franklingothicmedium", 28)
            self.tiny_font = pygame.font.SysFont("consolas", 20)
            self.subtitle_font = pygame.font.SysFont("georgia", 36)
        except Exception:  # noqa: BLE001
            self.title_font = pygame.font.Font(None, 80)
            self.font = pygame.font.Font(None, 48)
            self.small_font = pygame.font.Font(None, 32)
            self.tiny_font = pygame.font.Font(None, 24)
            self.subtitle_font = pygame.font.Font(None, 40)

    def _load_assets(self) -> None:
        """Load images and video"""
        try:
            # We assume this file is in src/renderer.py, so parent is src, parent.parent is root
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
                    new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
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
                    new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                    img = pygame.transform.scale(img, new_size)
                self.intro_images["deadfish"] = img

        except Exception as e:  # noqa: BLE001
            print(f"Failed to load assets: {e}")

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
            prompt_rect = prompt.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 150))
            self.screen.blit(prompt, prompt_rect)

        credit = self.tiny_font.render("A Jasper Production", True, C.DARK_GRAY)
        credit_rect = credit.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 50))
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

    def _draw_blood_drips(self, drips: List[Dict[str, Any]]) -> None:
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
                self.screen, drip["color"], (drip["x"], int(drip["y"])), drip["size"] + 1
            )

    def render_map_select(self, game: Game) -> None:
        """Render map select screen"""
        self.screen.fill(C.BLACK)

        title = self.subtitle_font.render("MISSION SETUP", True, C.RED)
        # Shadow
        for off in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            shadow = self.subtitle_font.render("MISSION SETUP", True, (50, 0, 0))
            s_rect = shadow.get_rect(center=(C.SCREEN_WIDTH // 2 + off[0], 100 + off[1]))
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
            "Click: Shoot | Z: Zoom | F: Bomb | Space: Shield",
        ]
        y = C.SCREEN_HEIGHT - 260
        for line in instructions:
            text = self.tiny_font.render(line, True, C.RED)
            text_rect = text.get_rect(center=(C.SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 30

        pygame.display.flip()

    def render_game(self, game: Game) -> None:
        """Render gameplay"""
        assert game.raycaster is not None
        assert game.player is not None

        # 1. 3D World (Raycaster)
        game.raycaster.render_floor_ceiling(self.screen, game.player, game.level)
        game.raycaster.render_3d(self.screen, game.player, game.bots, game.level)
        game.raycaster.render_projectiles(self.screen, game.player, game.projectiles)

        # 2. Effects
        self.effects_surface.fill((0, 0, 0, 0))
        self._render_particles(game.particles)
        self._render_particles(game.particles)
        self._render_low_health_tint(game.player)
        self._render_damage_flash(game.damage_flash_timer)
        self._render_shield_effect(game.player)
        self.screen.blit(self.effects_surface, (0, 0))

        # 3. UI / HUD
        self._render_crosshair()
        if game.player.shooting:
            self._render_muzzle_flash(game.player.current_weapon)
        self._render_secondary_charge(game.player)

        # 4. Portal
        self._render_portal(game.portal, game.player)

        # 5. Weapon & HUD
        self._render_weapon(game.player)
        self._render_hud(game)

        # 6. Damage Text (before pause overlay)
        self._render_damage_texts(game.damage_texts)

        # 7. Pause Menu (overlay on top)
        if game.paused:
            self._render_pause_menu()

        pygame.display.flip()

    def _render_damage_texts(self, texts: List[Dict[str, Any]]) -> None:
        """Render floating damage text indicators.

        Args:
            texts: List of damage text dictionaries with 'text', 'color', 'x', and 'y' keys.
        """
        for t in texts:
            surf = self.small_font.render(t["text"], True, t["color"])
            rect = surf.get_rect(center=(int(t["x"]), int(t["y"])))
            self.screen.blit(surf, rect)

    def _render_particles(self, particles: List[Dict[str, Any]]) -> None:
        """Render particle effects including lasers and explosion particles.

        Args:
            particles: List of particle dictionaries with type-specific properties.
        """
        for p in particles:
            if p.get("type") == "laser":
                alpha = int(255 * (p["timer"] / C.LASER_DURATION))
                start = p["start"]
                end = p["end"]
                color = (*p["color"], alpha)
                pygame.draw.line(self.effects_surface, color, start, end, p["width"])

                # Spread
                for i in range(5):
                    offset = (i - 2) * 20
                    target_end = (end[0] + offset, end[1])
                    pygame.draw.line(
                        self.effects_surface,
                        (*p["color"], max(0, alpha - 50)),
                        start,
                        target_end,
                        max(1, p["width"] // 2),
                    )
            elif "dx" in p:
                ratio = p["timer"] / C.PARTICLE_LIFETIME
                alpha = int(255 * ratio)
                alpha = max(0, min(255, alpha))
                try:
                    color = p["color"]
                    rgba = (*color, alpha) if len(color) == 3 else (*color[:3], alpha)
                    pygame.draw.circle(
                        self.effects_surface,
                        rgba,
                        (int(p["x"]), int(p["y"])),
                        int(p["size"]),
                    )
                except (ValueError, TypeError):
                    continue

    def _render_damage_flash(self, timer: int) -> None:
        """Render red screen flash effect when player takes damage.

        Args:
            timer: Current damage flash timer value.
        """
        if timer > 0:
            alpha = int(100 * (timer / 10.0))
            self.effects_surface.fill((255, 0, 0, alpha), special_flags=pygame.BLEND_RGBA_ADD)

    def _render_shield_effect(self, player: Player) -> None:
        """Render shield activation visual effects and status.

        Args:
            player: The player object to check shield state from.
        """
        if player.shield_active:
            # Simple fill
            pygame.draw.rect(
                self.effects_surface,
                (*C.SHIELD_COLOR, C.SHIELD_ALPHA),
                (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT),
            )
            # Border
            pygame.draw.rect(
                self.effects_surface, C.SHIELD_COLOR, (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT), 10
            )

            shield_text = self.title_font.render("SHIELD ACTIVE", True, C.SHIELD_COLOR)
            self.screen.blit(shield_text, (C.SCREEN_WIDTH // 2 - shield_text.get_width() // 2, 100))

            time_left = player.shield_timer / 60.0
            timer_text = self.small_font.render(f"{time_left:.1f}s", True, C.WHITE)
            self.screen.blit(timer_text, (C.SCREEN_WIDTH // 2 - timer_text.get_width() // 2, 160))

            if player.shield_timer < 120 and (player.shield_timer // 10) % 2 == 0:
                pygame.draw.rect(
                    self.effects_surface, (255, 0, 0, 50), (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT)
                )

        elif player.shield_timer == C.SHIELD_MAX_DURATION and player.shield_recharge_delay <= 0:
            ready_text = self.tiny_font.render("SHIELD READY", True, C.CYAN)
            self.screen.blit(ready_text, (20, C.SCREEN_HEIGHT - 120))

    def _render_low_health_tint(self, player: Player) -> None:
        """Render red screen tint when health is low."""
        if player.health < 50:
            # Alpha increases as health drops from 50 to 0
            # Max alpha at 0 health = 100 (pretty strong but see-through)
            alpha = int(100 * (1.0 - (player.health / 50.0)))
            self.effects_surface.fill((255, 0, 0, alpha), special_flags=pygame.BLEND_RGBA_ADD)

    def _render_crosshair(self) -> None:
        """Render the aiming crosshair at the center of the screen."""
        cx = C.SCREEN_WIDTH // 2
        cy = C.SCREEN_HEIGHT // 2
        size = 12
        pygame.draw.line(self.screen, C.RED, (cx - size, cy), (cx + size, cy), 2)
        pygame.draw.line(self.screen, C.RED, (cx, cy - size), (cx, cy + size), 2)
        pygame.draw.circle(self.screen, C.RED, (cx, cy), 2)

    def _render_muzzle_flash(self, weapon_name: str) -> None:
        """Render weapon-specific muzzle flash effects.

        Args:
            weapon_name: Name of the weapon being fired.
        """
        flash_x = C.SCREEN_WIDTH // 2
        flash_y = C.SCREEN_HEIGHT - 210

        if weapon_name == "plasma":
            pygame.draw.circle(self.screen, C.CYAN, (flash_x, flash_y), 30)
            pygame.draw.circle(self.screen, C.BLUE, (flash_x, flash_y), 20)
            pygame.draw.circle(self.screen, C.WHITE, (flash_x, flash_y), 10)
        elif weapon_name == "shotgun":
            pygame.draw.circle(self.screen, (255, 100, 0), (flash_x, flash_y), 50)
            pygame.draw.circle(self.screen, C.ORANGE, (flash_x, flash_y), 35)
            pygame.draw.circle(self.screen, C.YELLOW, (flash_x, flash_y), 15)
        else:
            pygame.draw.circle(self.screen, C.YELLOW, (flash_x, flash_y), 25)
            pygame.draw.circle(self.screen, C.ORANGE, (flash_x, flash_y), 15)
            pygame.draw.circle(self.screen, C.WHITE, (flash_x, flash_y), 8)

    def _render_secondary_charge(self, player: Player) -> None:
        """Render secondary weapon charge bar.

        Args:
            player: The player object to check secondary cooldown from.
        """
        charge_pct = 1.0 - (player.secondary_cooldown / C.SECONDARY_COOLDOWN)
        if charge_pct < 1.0:
            bar_w = 40
            bar_h = 4
            cx, cy = C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 30
            pygame.draw.rect(self.screen, C.DARK_GRAY, (cx - bar_w // 2, cy, bar_w, bar_h))
            pygame.draw.rect(
                self.screen, C.CYAN, (cx - bar_w // 2, cy, int(bar_w * charge_pct), bar_h)
            )

    def _render_portal(self, portal: Dict[str, Any] | None, player: Player) -> None:
        """Render portal visual effects if active.

        Args:
            portal: Portal dictionary with position and state, or None if inactive.
            player: The player object for relative positioning.
        """
        if portal:
            sx = portal["x"] - player.x
            sy = portal["y"] - player.y

            cs = math.cos(player.angle)
            sn = math.sin(player.angle)
            a = sy * cs - sx * sn
            b = sx * cs + sy * sn

            if b > 0.1:
                screen_x = int((0.5 * C.SCREEN_WIDTH) * (1 + a / b * 2.0))
                screen_y = C.SCREEN_HEIGHT // 2
                size = int(800 / b)

                if -size < screen_x < C.SCREEN_WIDTH + size:
                    color = (0, 255, 255)
                    # Draw rings
                    pygame.draw.circle(self.screen, color, (screen_x, screen_y), size // 2, 2)
                    pygame.draw.circle(self.screen, C.WHITE, (screen_x, screen_y), size // 4, 1)

    def _render_weapon(self, player: Player) -> None:
        """Render weapon model"""
        weapon = player.current_weapon
        cx = C.SCREEN_WIDTH // 2
        cy = C.SCREEN_HEIGHT

        # Bobbing
        bob_y = 0
        if player.is_moving:
            bob_y = int(math.sin(pygame.time.get_ticks() * 0.012) * 15)

        w_state = player.weapon_state[weapon]
        if w_state["reloading"]:
            w_data = C.WEAPONS.get(weapon, {})
            reload_max = cast("int", w_data.get("reload_time", 60))
            if reload_max > 0:
                pct = w_state["reload_timer"] / reload_max
                dip = math.sin(pct * math.pi) * 150
                cy += int(dip)

        cy += bob_y

        gun_metal = (40, 45, 50)
        gun_highlight = (70, 75, 80)
        gun_dark = (20, 25, 30)

        if weapon == "pistol":
            pygame.draw.polygon(
                self.screen,
                (30, 25, 20),
                [(cx - 30, cy), (cx + 30, cy), (cx + 35, cy - 100), (cx - 35, cy - 100)],
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
                pygame.draw.line(self.screen, gun_dark, (cx - 20, y_ser), (cx + 20, y_ser), 2)
            pygame.draw.rect(self.screen, (10, 10, 10), (cx - 8, slide_y - 5, 16, 10))
            pygame.draw.rect(self.screen, (10, 10, 10), (cx - 20, slide_y - 12, 5, 12))
            pygame.draw.rect(self.screen, (10, 10, 10), (cx + 15, slide_y - 12, 5, 12))
            pygame.draw.rect(self.screen, C.RED, (cx - 2, slide_y - 8, 4, 8))

        elif weapon == "shotgun":
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

        elif weapon == "rifle":
            pygame.draw.rect(self.screen, (20, 20, 20), (cx - 40, cy - 80, 30, 80))
            pygame.draw.polygon(
                self.screen,
                gun_metal,
                [(cx - 30, cy - 150), (cx + 30, cy - 150), (cx + 40, cy), (cx - 40, cy)],
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
                pygame.draw.line(self.screen, C.RED, (cx - 25, cy - 170), (cx + 25, cy - 170), 1)
                pygame.draw.line(self.screen, C.RED, (cx, cy - 195), (cx, cy - 145), 1)

        elif weapon == "plasma":
            pygame.draw.polygon(
                self.screen,
                (40, 40, 60),
                [(cx - 100, cy), (cx + 100, cy), (cx + 90, cy - 80), (cx - 90, cy - 80)],
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
            vent_color = (
                (0, 150 + pulse, 200) if not w_state["overheated"] else (200 + pulse, 50, 0)
            )
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
        # Laser weapon rendering is handled elsewhere in the rendering pipeline

    def _render_hud(self, game: Game) -> None:
        """Render the heads-up display including health, ammo, and game stats.

        Args:
            game: The game object containing player and game state.
        """
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
        health_color = (
            C.GREEN if health_percent > 0.5 else (C.ORANGE if health_percent > 0.25 else C.RED)
        )
        pygame.draw.rect(self.screen, health_color, (health_x, health_y, fill_width, health_height))
        pygame.draw.rect(self.screen, C.WHITE, (health_x, health_y, health_width, health_height), 2)

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
        for w in ["pistol", "rifle", "shotgun", "laser", "plasma"]:
            color = C.GRAY
            if w in game.unlocked_weapons:
                color = C.GREEN if w == game.player.current_weapon else C.WHITE

            key_display = C.WEAPONS[w]["key"]
            if w == "laser":
                key_display = "4"
            elif w == "plasma":
                key_display = "5"

            inv_txt = self.tiny_font.render(f"[{key_display}] {C.WEAPONS[w]['name']}", True, color)
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
        pygame.draw.rect(
            self.screen,
            C.CYAN,
            (shield_x, shield_y, int(shield_width * shield_pct), shield_height),
        )
        pygame.draw.rect(self.screen, C.WHITE, (shield_x, shield_y, shield_width, shield_height), 1)

        if game.player.shield_recharge_delay > 0:
            status_text = "RECHARGING" if game.player.shield_active else "COOLDOWN"
            status_surf = self.tiny_font.render(status_text, True, C.WHITE)
            self.screen.blit(status_surf, (shield_x + shield_width + 5, shield_y - 2))

        # Laser Charge
        laser_y = shield_y - 15
        laser_pct = 1.0 - (game.player.secondary_cooldown / C.SECONDARY_COOLDOWN)
        laser_pct = max(0, min(1, laser_pct))
        pygame.draw.rect(self.screen, C.DARK_GRAY, (shield_x, laser_y, shield_width, shield_height))
        pygame.draw.rect(
            self.screen,
            (255, 50, 50),
            (shield_x, laser_y, int(shield_width * laser_pct), shield_height),
        )

        controls_hint = self.tiny_font.render(
            "WASD:Move | 1-5:Wpn | R:Reload | F:Bomb | SPACE:Shield | ESC:Menu", True, C.WHITE
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

    def _render_pause_menu(self) -> None:
        """Render the pause menu overlay with resume, save, and quit options."""
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
            # Resume: 350, Save: 410, Controls: 470, Quit: 530
            rect = pygame.Rect(
                C.SCREEN_WIDTH // 2 - 100, 350 + i * 60, 200, 50
            )
            if rect.collidepoint(mouse_pos):
                color = C.YELLOW
                pygame.draw.rect(self.screen, (50, 0, 0), rect)
                pygame.draw.rect(self.screen, C.RED, rect, 2)
            
            text = self.subtitle_font.render(item, True, color)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

    def render_level_complete(self, game: Game) -> None:
        """Render the level complete screen with statistics.

        Args:
            game: The game object containing level and statistics data.
        """
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
        """Render the game over screen with final statistics.

        Args:
            game: The game object containing final statistics.
        """
        self.screen.fill(C.BLACK)
        title = self.title_font.render("SYSTEM FAILURE", True, C.RED)
        title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        completed_levels = max(0, game.level - 1)
        total_time = sum(game.level_times)
        avg_time = total_time / len(game.level_times) if game.level_times else 0

        stats = [
            (
                f"You survived {completed_levels} level{'s' if completed_levels != 1 else ''}",
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
        self, stats: List[Tuple[str, Tuple[int, int, int]]], start_y: int
    ) -> None:
        """Render a list of stat lines with specified colors.

        Args:
            stats: List of tuples containing (text, color) pairs.
            start_y: Starting Y coordinate for the first line.
        """
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
            text = self.subtitle_font.render("A Willy Wonk Production", True, (255, 182, 193))
            self.screen.blit(text, text.get_rect(center=(C.SCREEN_WIDTH // 2, 100)))
            if "willy" in self.intro_images:
                img = self.intro_images["willy"]
                r = img.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 30))
                self.screen.blit(img, r)
                pygame.draw.rect(self.screen, (255, 192, 203), r, 4, border_radius=10)

        elif intro_phase == 1:
            stylish = pygame.font.SysFont("impact", 70)
            pulse = abs(math.sin(elapsed * 0.003))
            color = (0, int(150 + 100 * pulse), int(200 + 55 * pulse))

            t2 = stylish.render("UPSTREAM DRIFT", True, color)
            self.screen.blit(
                t2, t2.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 - 180))
            )

            t1 = self.tiny_font.render("in association with", True, C.CYAN)
            self.screen.blit(
                t1, t1.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 - 230))
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
                        surf.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 50)),
                    )
                else:
                    self.intro_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            elif "deadfish" in self.intro_images:
                img = self.intro_images["deadfish"]
                self.screen.blit(
                    img, img.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 50))
                )

        elif intro_phase == 2:
            self._render_intro_slide(intro_step, elapsed)

        pygame.display.flip()

    def _render_intro_slide(self, step: int, elapsed: int) -> None:
        """Render intro slides with story text and effects.

        Args:
            step: Current intro slide step index.
            elapsed: Elapsed time in milliseconds for animations.
        """
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
            duration = int(slide["duration"])

            if slide["type"] == "distortion":
                font = (
                    pygame.font.SysFont("chiller", 70)
                    if pygame.font.match_font("chiller")
                    else self.title_font
                )
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
                lines = cast("List[str]", slide["lines"])
                show_count = int((elapsed / duration) * (len(lines) + 1))
                show_count = min(show_count, len(lines))
                y = C.SCREEN_HEIGHT // 2 - (len(lines) * 50) // 2
                for i in range(show_count):
                    s = self.subtitle_font.render(lines[i], True, C.RED)
                    self.screen.blit(s, s.get_rect(center=(C.SCREEN_WIDTH // 2, y)))
                    y += 50

            elif slide["type"] == "static":
                color = cast("Tuple[int, int, int]", slide.get("color", C.WHITE))
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

                # Add blood drip effect when color has fully faded to red
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
                        sub.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 60)),
                    )

    def render_key_config(self, game: Any) -> None:
        """Render the key configuration menu."""
        self.screen.fill(C.BLACK)
        
        # Title
        title = self.title_font.render("CONTROLS", True, C.RED)
        self.screen.blit(title, title.get_rect(center=(C.SCREEN_WIDTH // 2, 50)))
        
        # Scroll/List logic would be complex. Let's do a simple 2-column layout.
        bindings = game.input_manager.bindings
        start_y = 120
        col_1_x = C.SCREEN_WIDTH // 4
        col_2_x = C.SCREEN_WIDTH * 3 // 4
        
        # Actions to show (skip raw debug ones if any)
        actions = sorted(list(bindings.keys()))
        
        limit = 12 # Items per column
        
        for i, action in enumerate(actions):
            col = 0 if i < limit else 1
            idx = i if i < limit else i - limit
            x = col_1_x if col == 0 else col_2_x
            y = start_y + idx * 40
            
            # Action Name
            name_str = action.replace("_", " ").upper()
            color = C.WHITE
            if game.binding_action == action:
                color = C.YELLOW
                key_text = "PRESS ANY KEY..."
            else:
                key_text = game.input_manager.get_key_name(action)
                
            name_txt = self.tiny_font.render(f"{name_str}:", True, C.GRAY)
            key_txt = self.tiny_font.render(key_text, True, color)
            
            # Right align key, Left align name
            self.screen.blit(name_txt, (x - 150, y))
            self.screen.blit(key_txt, (x + 20, y))
            
            # Hitbox for clicking (stored in logic usually, but here just visual)
        
        # Back Button
        back_txt = self.subtitle_font.render("BACK", True, C.WHITE)
        back_rect = back_txt.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 60))
        self.screen.blit(back_txt, back_rect)
        if back_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(self.screen, C.RED, back_rect, 2)

    def _render_pause_menu(self) -> None:
        """Render the pause menu overlay."""
        s = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        self.screen.blit(s, (0, 0))

        title = self.title_font.render("PAUSED", True, C.RED)
        title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        # Menu Options
        # Updated list with CONTROLS
        menu_items = ["RESUME", "SAVE GAME", "CONTROLS", "QUIT TO MENU"]
        mouse_pos = pygame.mouse.get_pos()

        for i, item in enumerate(menu_items):
            color = C.WHITE
            # Resume: 350, Save: 410, Controls: 470, Quit: 530
            rect = pygame.Rect(
                C.SCREEN_WIDTH // 2 - 100,
                350 + i * 60,
                200,
                50,
            )
            
            if rect.collidepoint(mouse_pos):
                color = C.YELLOW
                pygame.draw.rect(self.screen, (50, 0, 0), rect)
                pygame.draw.rect(self.screen, C.RED, rect, 2)

            text = self.subtitle_font.render(item, True, color)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

