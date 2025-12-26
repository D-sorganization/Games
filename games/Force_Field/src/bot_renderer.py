from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .bot import Bot
    from .custom_types import EnemyData


class BotRenderer:
    """Handles rendering of bot sprites to 2D surfaces."""

    @staticmethod
    def render_sprite(
        screen: pygame.Surface,
        bot: Bot,
        sprite_x: int,
        sprite_y: int,
        sprite_size: float,
    ) -> None:
        """Render sprite based on visual style to the given surface.

        Args:
            screen: The surface to draw on.
            bot: The bot instance.
            sprite_x: X position on the surface.
            sprite_y: Y position on the surface.
            sprite_size: Size of the sprite (width/height).
        """
        center_x = sprite_x + sprite_size / 2
        type_data: EnemyData = bot.type_data
        base_color = type_data["color"]
        visual_style = type_data.get("visual_style", "monster")

        # Health Pack / Items
        if bot.enemy_type == "health_pack":
            BotRenderer._render_health_pack(
                screen, sprite_x, sprite_y, sprite_size, center_x
            )
            return

        if bot.enemy_type == "ammo_box":
            BotRenderer._render_ammo_box(
                screen, sprite_x, sprite_y, sprite_size, center_x
            )
            return

        if bot.enemy_type == "bomb_item":
            BotRenderer._render_bomb_item(
                screen, sprite_x, sprite_y, sprite_size, center_x
            )
            return

        if bot.enemy_type.startswith("pickup_"):
            BotRenderer._render_weapon_pickup(
                screen, bot, sprite_x, sprite_y, sprite_size, center_x
            )
            return

        render_height = sprite_size
        render_width = (
            sprite_size * 0.55 if visual_style == "monster" else sprite_size * 0.7
        )
        render_y = sprite_y

        if bot.dead:
            # Melting animation
            melt_pct = min(1.0, bot.death_timer / 60.0)

            # Interpolate Color to Goo
            goo_color = (50, 150, 50)
            base_color = tuple(
                int(c * (1 - melt_pct) + g * melt_pct)
                for c, g in zip(base_color, goo_color, strict=False)
            )  # type: ignore

            # Squish
            scale_y = 1.0 - (melt_pct * 0.85)
            scale_x = 1.0 + (melt_pct * 0.8)

            current_h = render_height * scale_y
            current_w = render_width * scale_x

            offset_y = (render_height - current_h) + (render_height * 0.05)
            render_y = int(sprite_y + offset_y)
            render_height = int(current_h)
            render_width = int(current_w)

            if bot.disintegrate_timer > 0:
                dis_pct = bot.disintegrate_timer / 100.0
                radius_mult = 1.0 - dis_pct
                if radius_mult <= 0:
                    return
                pygame.draw.ellipse(
                    screen,
                    base_color,
                    (
                        center_x - render_width / 2 * radius_mult,
                        render_y + render_height - 10,
                        render_width * radius_mult,
                        20 * radius_mult,
                    ),
                )
                return

        if visual_style == "baby":
            BotRenderer._render_baby(
                screen, bot, center_x, render_y, render_width, render_height, base_color
            )
            return

        if visual_style == "ball":
            BotRenderer._render_ball(
                screen, bot, center_x, render_y, render_width, render_height, base_color
            )
            return

        if visual_style == "beast":
            BotRenderer._render_beast(
                screen, bot, center_x, render_y, render_width, render_height, base_color
            )
            return

        if visual_style == "ghost":
            BotRenderer._render_ghost(
                screen, bot, center_x, render_y, render_width, render_height, base_color
            )
            return

        if bot.enemy_type == "minigunner":
            BotRenderer._render_minigunner(
                screen, bot, center_x, render_y, render_width, render_height, base_color
            )
            return

        # Monster Style (Default)
        BotRenderer._render_monster(
            screen, bot, center_x, render_y, render_width, render_height, base_color
        )

    @staticmethod
    def _render_health_pack(
        screen: pygame.Surface, x: int, y: int, size: float, cx: float
    ) -> None:
        """Render a health pack item."""
        time_ms = pygame.time.get_ticks()
        
        # Floating animation
        float_offset = math.sin(time_ms * 0.003) * 8
        
        # Pulsing glow effect
        glow_pulse = math.sin(time_ms * 0.008) * 0.3 + 0.7
        glow_size = size * 0.8 * glow_pulse
        
        # Draw glow
        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_color = (0, 255, 0, 40)
        pygame.draw.circle(glow_surface, glow_color, 
                         (glow_size, glow_size), int(glow_size))
        screen.blit(glow_surface, 
                   (cx - glow_size, y + size * 0.7 + float_offset - glow_size))
        
        # Main health pack
        rect_w = size * 0.4
        rect_h = size * 0.3
        kit_y = y + size * 0.7 + float_offset
        
        # Pulsing brightness
        brightness = int(220 + 35 * math.sin(time_ms * 0.01))
        
        pygame.draw.rect(
            screen,
            (brightness, brightness, brightness),
            (cx - rect_w / 2, kit_y, rect_w, rect_h),
            border_radius=4,
        )
        
        # Animated cross
        cross_thick = rect_w * 0.2
        cross_brightness = int(200 + 55 * math.sin(time_ms * 0.012))
        cross_color = (cross_brightness, 0, 0)
        
        pygame.draw.rect(
            screen,
            cross_color,
            (cx - cross_thick / 2, kit_y + 5, cross_thick, rect_h - 10),
        )
        pygame.draw.rect(
            screen,
            cross_color,
            (
                cx - rect_w / 2 + 5,
                kit_y + rect_h / 2 - cross_thick / 2,
                rect_w - 10,
                cross_thick,
            ),
        )

    @staticmethod
    def _render_ammo_box(
        screen: pygame.Surface, x: int, y: int, size: float, cx: float
    ) -> None:
        """Render an ammo box item."""
        time_ms = pygame.time.get_ticks()
        
        # Floating animation
        float_offset = math.sin(time_ms * 0.004) * 6
        
        # Rotation animation
        rotation_angle = time_ms * 0.001
        
        # Pulsing glow effect
        glow_pulse = math.sin(time_ms * 0.006) * 0.4 + 0.6
        glow_size = size * 0.7 * glow_pulse
        
        # Draw glow
        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_color = (255, 255, 0, 35)
        pygame.draw.circle(glow_surface, glow_color, 
                         (glow_size, glow_size), int(glow_size))
        screen.blit(glow_surface, 
                   (cx - glow_size, y + size * 0.7 + float_offset - glow_size))
        
        # Main ammo box
        rect_w = size * 0.4
        rect_h = size * 0.3
        box_y = y + size * 0.7 + float_offset
        
        # Pulsing colors
        base_brightness = int(100 + 50 * math.sin(time_ms * 0.008))
        highlight_brightness = int(200 + 55 * math.sin(time_ms * 0.01))
        
        rect = (cx - rect_w / 2, box_y, rect_w, rect_h)
        pygame.draw.rect(screen, (base_brightness, base_brightness, 50), rect)
        pygame.draw.rect(
            screen,
            (highlight_brightness, highlight_brightness, 0),
            (cx - rect_w / 2 + 2, box_y + 2, rect_w - 4, rect_h - 4),
        )
        
        # Add rotating sparkles
        for i in range(3):
            sparkle_angle = rotation_angle + (i * 2 * math.pi / 3)
            sparkle_radius = rect_w * 0.4
            sparkle_x = cx + math.cos(sparkle_angle) * sparkle_radius
            sparkle_y = box_y + rect_h / 2 + math.sin(sparkle_angle) * sparkle_radius * 0.5
            pygame.draw.circle(screen, (255, 255, 255), 
                             (int(sparkle_x), int(sparkle_y)), 2)

    @staticmethod
    def _render_bomb_item(
        screen: pygame.Surface, x: int, y: int, size: float, cx: float
    ) -> None:
        """Render a bomb item."""
        time_ms = pygame.time.get_ticks()
        
        # Floating animation
        float_offset = math.sin(time_ms * 0.005) * 5
        
        # Pulsing danger glow
        danger_pulse = math.sin(time_ms * 0.015) * 0.5 + 0.5
        glow_size = size * 0.6 * (0.8 + danger_pulse * 0.4)
        
        # Draw danger glow
        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_color = (255, 100, 0, int(60 * danger_pulse))
        pygame.draw.circle(glow_surface, glow_color, 
                         (glow_size, glow_size), int(glow_size))
        screen.blit(glow_surface, 
                   (cx - glow_size, y + size * 0.8 + float_offset - glow_size))
        
        # Main bomb
        r = size * 0.2
        cy = y + size * 0.8 + float_offset
        
        # Pulsing bomb body
        bomb_brightness = int(30 + 25 * math.sin(time_ms * 0.01))
        pygame.draw.circle(screen, (bomb_brightness, bomb_brightness, bomb_brightness), 
                         (int(cx), int(cy)), int(r))
        
        # Animated fuse
        fuse_flicker = math.sin(time_ms * 0.02) * 0.3 + 0.7
        start_fuse = (cx, cy - r)
        end_fuse = (cx + r / 2, cy - r * 1.5)
        fuse_color = (int(200 * fuse_flicker), int(150 * fuse_flicker), 0)
        pygame.draw.line(screen, fuse_color, start_fuse, end_fuse, 3)
        
        # Enhanced sparks with particles
        if random.random() < 0.7:  # More frequent sparks
            spark_pos = (int(cx + r / 2), int(cy - r * 1.5))
            spark_size = int(3 + 2 * math.sin(time_ms * 0.03))
            pygame.draw.circle(screen, (255, 200, 0), spark_pos, spark_size)
            
            # Add small spark particles
            for i in range(3):
                particle_x = spark_pos[0] + random.randint(-5, 5)
                particle_y = spark_pos[1] + random.randint(-3, 3)
                pygame.draw.circle(screen, (255, 150, 0), 
                                 (particle_x, particle_y), 1)

    @staticmethod
    def _render_weapon_pickup(
        screen: pygame.Surface, bot: Bot, x: int, y: int, size: float, cx: float
    ) -> None:
        """Render a weapon pickup item."""
        time_ms = pygame.time.get_ticks()
        
        # Floating animation
        float_offset = math.sin(time_ms * 0.0035) * 7
        
        # Rotation animation
        rotation_angle = time_ms * 0.002
        
        # Weapon-specific glow colors
        weapon_glows = {
            "minigun": (255, 100, 100),
            "shotgun": (255, 200, 0),
            "rifle": (100, 255, 100),
            "rocket": (255, 50, 255),
        }
        
        glow_color = (150, 150, 255)  # Default
        for weapon_type, color in weapon_glows.items():
            if weapon_type in bot.enemy_type:
                glow_color = color
                break
        
        # Pulsing glow effect
        glow_pulse = math.sin(time_ms * 0.007) * 0.4 + 0.6
        glow_size = size * 0.8 * glow_pulse
        
        # Draw glow
        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_rgba = (*glow_color, 45)
        pygame.draw.circle(glow_surface, glow_rgba, 
                         (glow_size, glow_size), int(glow_size))
        screen.blit(glow_surface, 
                   (cx - glow_size, y + size * 0.75 + float_offset - glow_size))
        
        # Main weapon body
        rect_w = size * 0.6
        rect_h = size * 0.2
        py = y + size * 0.75 + float_offset
        color = bot.type_data["color"]
        
        # Enhanced weapon body with rotation effect
        weapon_surface = pygame.Surface((rect_w * 1.5, rect_h * 1.5), pygame.SRCALPHA)
        weapon_rect = pygame.Rect(rect_w * 0.25, rect_h * 0.25, rect_w, rect_h)
        
        # Pulsing weapon color
        enhanced_color = tuple(min(255, c + int(50 * glow_pulse)) for c in color)
        pygame.draw.rect(weapon_surface, enhanced_color, weapon_rect, border_radius=3)
        
        # Rotate the weapon surface
        rotated_surface = pygame.transform.rotate(weapon_surface, 
                                                math.degrees(rotation_angle))
        rotated_rect = rotated_surface.get_rect(center=(cx, py))
        screen.blit(rotated_surface, rotated_rect)
        
        # Enhanced details
        detail_color = tuple(min(255, c + 100) for c in color)
        pygame.draw.line(
            screen, detail_color, 
            (cx - rect_w / 2, py), (cx + rect_w / 2, py), 3
        )
        
        if "minigun" in bot.enemy_type:
            # Add extra barrels with glow
            for i in range(3):
                barrel_y = py + 4 + i * 3
                barrel_brightness = int(200 + 55 * math.sin(time_ms * 0.01 + i))
                barrel_color = (barrel_brightness, barrel_brightness, barrel_brightness)
                pygame.draw.line(
                    screen, barrel_color,
                    (cx - rect_w / 2, barrel_y),
                    (cx + rect_w / 2, barrel_y), 2
                )
        
        # Add energy particles around weapon
        for i in range(4):
            particle_angle = rotation_angle * 2 + (i * math.pi / 2)
            particle_radius = rect_w * 0.6
            particle_x = cx + math.cos(particle_angle) * particle_radius
            particle_y = py + math.sin(particle_angle) * particle_radius * 0.3
            particle_size = int(2 + math.sin(time_ms * 0.02 + i) * 1)
            pygame.draw.circle(screen, glow_color, 
                             (int(particle_x), int(particle_y)), particle_size)

    @staticmethod
    def _render_baby(
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        color: tuple[int, int, int],
    ) -> None:
        """Render the baby enemy visual style."""
        # Body
        body_rect = pygame.Rect(
            int(cx - rw / 2),
            int(ry + rh * 0.4),
            int(rw),
            int(rh * 0.6),
        )
        pygame.draw.rect(screen, color, body_rect, border_radius=int(rw * 0.4))

        # Head (Floating slightly above)
        head_size = rw
        head_y = ry
        pygame.draw.circle(screen, color, (cx, head_y + head_size / 2), head_size / 2)

        # Face
        eye_r = head_size * 0.15
        pygame.draw.circle(
            screen,
            C.WHITE,
            (cx - head_size * 0.2, head_y + head_size * 0.4),
            eye_r,
        )
        pygame.draw.circle(
            screen,
            C.WHITE,
            (cx + head_size * 0.2, head_y + head_size * 0.4),
            eye_r,
        )

        # Pupils - dilated
        pygame.draw.circle(
            screen,
            C.BLACK,
            (cx - head_size * 0.2, head_y + head_size * 0.4),
            eye_r * 0.6,
        )
        pygame.draw.circle(
            screen,
            C.BLACK,
            (cx + head_size * 0.2, head_y + head_size * 0.4),
            eye_r * 0.6,
        )

        # Mouth
        if bot.mouth_open:
            pygame.draw.circle(
                screen,
                (50, 0, 0),
                (cx, head_y + head_size * 0.75),
                head_size * 0.1,
            )
        else:
            # Small flat mouth
            pygame.draw.line(
                screen,
                (50, 0, 0),
                (cx - 5, head_y + head_size * 0.75),
                (cx + 5, head_y + head_size * 0.75),
                2,
            )

    @staticmethod
    def _render_ball(
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        color: tuple[int, int, int],
    ) -> None:
        """Render the ball enemy visual style."""
        # Metallic Ball with rotation effect (stripes)
        r = rw / 2
        cy = ry + rh / 2
        pygame.draw.circle(screen, color, (int(cx), int(cy)), int(r))
        # Shine
        pygame.draw.circle(
            screen,
            (200, 200, 200),
            (int(cx - r * 0.3), int(cy - r * 0.3)),
            int(r * 0.3),
        )
        # Stripes (rotate based on bot angle/pos?)
        # Just horizontal lines for "fast" look
        pygame.draw.line(screen, (0, 0, 0), (cx - r, cy), (cx + r, cy), 3)

    @staticmethod
    def _render_beast(
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        color: tuple[int, int, int],
    ) -> None:
        """Render the beast enemy visual style."""
        # Large imposing figure
        # Main Body
        pygame.draw.rect(screen, color, (cx - rw / 2, ry + rh * 0.3, rw, rh * 0.7))
        # Head (Horns)
        head_size = rw * 0.8
        head_rect = (cx - head_size / 2, ry, head_size, head_size)
        pygame.draw.rect(screen, (100, 0, 0), head_rect)

        # Eyes
        pygame.draw.circle(
            screen,
            (255, 255, 0),
            (int(cx - head_size * 0.2), int(ry + head_size * 0.4)),
            5,
        )
        pygame.draw.circle(
            screen,
            (255, 255, 0),
            (int(cx + head_size * 0.2), int(ry + head_size * 0.4)),
            5,
        )

    @staticmethod
    def _render_ghost(
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        color: tuple[int, int, int],
    ) -> None:
        """Render the ghost enemy visual style."""
        # Ghost: Float, fade at bottom, semi-transparent
        offset_y = math.sin(pygame.time.get_ticks() * 0.005) * 10
        gy = ry + offset_y

        ghost_color = (*color, 150)  # RGBA

        # Head
        center = (int(cx), int(gy + rw / 2))
        pygame.draw.circle(screen, ghost_color, center, int(rw / 2))

        # Body (Rect)
        body_rect = pygame.Rect(cx - rw / 2, gy + rw / 2, rw, rh * 0.6)
        pygame.draw.rect(screen, ghost_color, body_rect)

        # Tattered bottom
        points = []
        points.append((cx - rw / 2, gy + rw / 2 + rh * 0.6))
        for i in range(5):
            x = cx - rw / 2 + (i + 1) * (rw / 5)
            y_base = gy + rw / 2 + rh * 0.6
            y = y_base + (rh * 0.2 if i % 2 == 0 else 0)
            points.append((x, y))
        points.append((cx + rw / 2, gy + rw / 2 + rh * 0.6))
        # Close shape
        points.append((cx + rw / 2, gy + rw / 2))
        points.append((cx - rw / 2, gy + rw / 2))

        pygame.draw.polygon(screen, ghost_color, points)

        # Eyes (Hollow)
        pygame.draw.circle(
            screen, (0, 0, 0), (int(cx - rw * 0.2), int(gy + rw * 0.4)), int(rw * 0.1)
        )
        pygame.draw.circle(
            screen, (0, 0, 0), (int(cx + rw * 0.2), int(gy + rw * 0.4)), int(rw * 0.1)
        )

    @staticmethod
    def _render_minigunner(
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        color: tuple[int, int, int],
    ) -> None:
        """Render the minigunner enemy visual style."""
        # Armored Heavy Soldier
        # Body armor
        body_x = cx - rw / 2
        body_y = ry + rh * 0.2
        pygame.draw.rect(screen, (50, 50, 70), (body_x, body_y, rw, rh * 0.5))

        # Helmet
        head_size = rw * 0.7
        head_x = cx - head_size / 2
        head_y = ry
        pygame.draw.rect(screen, (30, 30, 40), (head_x, head_y, head_size, head_size))
        # Visor
        pygame.draw.rect(
            screen, (255, 0, 0), (head_x + 5, head_y + 10, head_size - 10, 5)
        )

        # Minigun Weapon
        weapon_w = rw * 1.2
        weapon_h = rh * 0.2
        wx = cx - weapon_w / 2
        wy = body_y + rh * 0.2
        pygame.draw.rect(screen, (20, 20, 20), (wx, wy, weapon_w, weapon_h))
        # Barrels
        if bot.shoot_animation > 0:
            pygame.draw.circle(
                screen, C.YELLOW, (wx, wy + weapon_h / 2), 5 + random.randint(0, 5)
            )

    @staticmethod
    def _render_monster(
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        color: tuple[int, int, int],
    ) -> None:
        """Render the default monster visual style."""
        body_x = cx - rw / 2

        # 1. Body (Rounded Torso)
        torso_rect = pygame.Rect(
            int(body_x),
            int(ry + rh * 0.25),
            int(rw),
            int(rh * 0.5),
        )
        # Draw torso
        pygame.draw.ellipse(screen, color, torso_rect)

        # Muscle definition (Shadows)
        dark_color = tuple(max(0, c - 40) for c in color)
        light_color = tuple(min(255, c + 30) for c in color)

        # Highlight top
        pygame.draw.ellipse(
            screen,
            light_color,
            (
                body_x + rw * 0.2,
                ry + rh * 0.25,
                rw * 0.6,
                rh * 0.2,
            ),
        )

        # Ribs/Abs
        dark_color = tuple(max(0, c - 50) for c in color)
        for i in range(3):
            y_off = ry + rh * (0.35 + i * 0.1)
            pygame.draw.line(
                screen,
                dark_color,
                (body_x + 5, y_off),
                (body_x + rw - 5, y_off),
                2,
            )

        # 2. Head
        if not bot.dead or bot.death_timer < 30:
            head_size = int(rw * 0.6)
            head_y = int(ry + rh * 0.05)
            head_rect = pygame.Rect(cx - head_size // 2, head_y, head_size, head_size)
            pygame.draw.rect(screen, color, head_rect)

            # Glowing Eyes
            eye_color = (255, 50, 0)
            if bot.enemy_type == "boss":
                eye_color = (255, 255, 0)

            # Angry Eyes
            pygame.draw.polygon(
                screen,
                eye_color,
                [
                    (cx - head_size * 0.3, head_y + head_size * 0.3),
                    (cx - head_size * 0.1, head_y + head_size * 0.3),
                    (cx - head_size * 0.2, head_y + head_size * 0.45),
                ],
            )
            pygame.draw.polygon(
                screen,
                eye_color,
                [
                    (cx + head_size * 0.3, head_y + head_size * 0.3),
                    (cx + head_size * 0.1, head_y + head_size * 0.3),
                    (cx + head_size * 0.2, head_y + head_size * 0.45),
                ],
            )

            # Mouth
            mouth_y = head_y + head_size * 0.65
            mouth_w = head_size * 0.6
            if bot.mouth_open:
                pygame.draw.rect(
                    screen,
                    (50, 0, 0),
                    (cx - mouth_w / 2, mouth_y, mouth_w, head_size * 0.3),
                )
                # Teeth
                pygame.draw.line(
                    screen,
                    C.WHITE,
                    (cx - mouth_w / 2, mouth_y),
                    (cx - mouth_w / 4, mouth_y + 5),
                    2,
                )
                pygame.draw.line(
                    screen,
                    C.WHITE,
                    (cx - mouth_w / 4, mouth_y + 5),
                    (cx, mouth_y),
                    2,
                )
                pygame.draw.line(
                    screen,
                    C.WHITE,
                    (cx, mouth_y),
                    (cx + mouth_w / 4, mouth_y + 5),
                    2,
                )
                pygame.draw.line(
                    screen,
                    C.WHITE,
                    (cx + mouth_w / 4, mouth_y + 5),
                    (cx + mouth_w / 2, mouth_y),
                    2,
                )
            else:
                pygame.draw.line(
                    screen,
                    (200, 200, 200),
                    (cx - mouth_w / 2, mouth_y + 5),
                    (cx + mouth_w / 2, mouth_y + 5),
                    3,
                )
                for i in range(4):
                    x_off = cx - mouth_w / 2 + (i + 1) * (mouth_w / 5)
                    start_p = (x_off, mouth_y)
                    end_p = (x_off, mouth_y + 10)
                    pygame.draw.line(screen, (50, 0, 0), start_p, end_p, 1)

        # 3. Arms
        if not bot.dead:
            arm_y = ry + rh * 0.3
            # Left
            start_arm = (body_x, arm_y + 10)
            end_arm = (body_x - 15, arm_y + 30)
            pygame.draw.line(screen, color, start_arm, end_arm, 6)
            pygame.draw.polygon(
                screen,
                (200, 200, 200),
                [
                    (body_x - 15, arm_y + 30),
                    (body_x - 20, arm_y + 40),
                    (body_x - 5, arm_y + 35),
                ],
            )
            # Right
            weapon_x = body_x + rw
            pygame.draw.line(
                screen,
                color,
                (weapon_x, arm_y + 10),
                (weapon_x + 15, arm_y + 30),
                6,
            )
            pygame.draw.rect(screen, (30, 30, 30), (weapon_x + 10, arm_y + 25, 25, 10))
            if bot.shoot_animation > 0.5:
                pygame.draw.circle(
                    screen,
                    C.YELLOW,
                    (weapon_x + 35, arm_y + 30),
                    8 + random.randint(0, 4),
                )
                pygame.draw.circle(screen, C.WHITE, (weapon_x + 35, arm_y + 30), 4)

        # 4. Legs
        if not bot.dead:
            leg_w = rw * 0.3
            leg_h = rh * 0.25
            leg_y = ry + rh * 0.75
            pygame.draw.rect(screen, color, (body_x + 5, leg_y, leg_w, leg_h))
            pygame.draw.rect(
                screen,
                color,
                (body_x + rw - 5 - leg_w, leg_y, leg_w, leg_h),
            )
