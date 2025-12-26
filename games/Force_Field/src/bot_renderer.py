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
        pygame.draw.circle(
            glow_surface, glow_color, (glow_size, glow_size), int(glow_size)
        )
        screen.blit(
            glow_surface, (cx - glow_size, y + size * 0.7 + float_offset - glow_size)
        )

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
        pygame.draw.circle(
            glow_surface, glow_color, (glow_size, glow_size), int(glow_size)
        )
        screen.blit(
            glow_surface, (cx - glow_size, y + size * 0.7 + float_offset - glow_size)
        )

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
            sparkle_y = (
                box_y + rect_h / 2 + math.sin(sparkle_angle) * sparkle_radius * 0.5
            )
            pygame.draw.circle(
                screen, (255, 255, 255), (int(sparkle_x), int(sparkle_y)), 2
            )

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
        pygame.draw.circle(
            glow_surface, glow_color, (glow_size, glow_size), int(glow_size)
        )
        screen.blit(
            glow_surface, (cx - glow_size, y + size * 0.8 + float_offset - glow_size)
        )

        # Main bomb
        r = size * 0.2
        cy = y + size * 0.8 + float_offset

        # Pulsing bomb body
        bomb_brightness = int(30 + 25 * math.sin(time_ms * 0.01))
        pygame.draw.circle(
            screen,
            (bomb_brightness, bomb_brightness, bomb_brightness),
            (int(cx), int(cy)),
            int(r),
        )

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
            for _ in range(3):
                particle_x = spark_pos[0] + random.randint(-5, 5)
                particle_y = spark_pos[1] + random.randint(-3, 3)
                pygame.draw.circle(screen, (255, 150, 0), (particle_x, particle_y), 1)

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
        pygame.draw.circle(
            glow_surface, glow_rgba, (glow_size, glow_size), int(glow_size)
        )
        screen.blit(
            glow_surface, (cx - glow_size, y + size * 0.75 + float_offset - glow_size)
        )

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
        rotated_surface = pygame.transform.rotate(
            weapon_surface, math.degrees(rotation_angle)
        )
        rotated_rect = rotated_surface.get_rect(center=(cx, py))
        screen.blit(rotated_surface, rotated_rect)

        # Enhanced details
        detail_color = tuple(min(255, c + 100) for c in color)
        pygame.draw.line(
            screen, detail_color, (cx - rect_w / 2, py), (cx + rect_w / 2, py), 3
        )

        if "minigun" in bot.enemy_type:
            # Add extra barrels with glow
            for i in range(3):
                barrel_y = py + 4 + i * 3
                barrel_brightness = int(200 + 55 * math.sin(time_ms * 0.01 + i))
                barrel_color = (barrel_brightness, barrel_brightness, barrel_brightness)
                pygame.draw.line(
                    screen,
                    barrel_color,
                    (cx - rect_w / 2, barrel_y),
                    (cx + rect_w / 2, barrel_y),
                    2,
                )

        # Add energy particles around weapon
        for i in range(4):
            particle_angle = rotation_angle * 2 + (i * math.pi / 2)
            particle_radius = rect_w * 0.6
            particle_x = cx + math.cos(particle_angle) * particle_radius
            particle_y = py + math.sin(particle_angle) * particle_radius * 0.3
            particle_size = int(2 + math.sin(time_ms * 0.02 + i) * 1)
            pygame.draw.circle(
                screen, glow_color, (int(particle_x), int(particle_y)), particle_size
            )

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
        """Render the ball enemy visual style with enhanced graphics."""
        time_ms = pygame.time.get_ticks()

        # Spinning animation
        rotation_speed = time_ms * 0.01

        # Pulsing size for energy effect
        pulse = 1.0 + math.sin(time_ms * 0.008) * 0.1
        r = (rw / 2) * pulse
        cy = ry + rh / 2

        # Energy field glow
        glow_size = r * 2.5
        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_alpha = int(30 + 25 * math.sin(time_ms * 0.015))
        glow_color = (0, 100, 255, glow_alpha)
        pygame.draw.circle(
            glow_surface, glow_color, (glow_size, glow_size), int(glow_size)
        )
        screen.blit(glow_surface, (cx - glow_size, cy - glow_size))

        # Enhanced metallic ball with gradient
        enhanced_color = tuple(min(255, c + 50) for c in color)
        dark_color = tuple(max(0, c - 60) for c in color)

        # Main ball body
        pygame.draw.circle(screen, enhanced_color, (int(cx), int(cy)), int(r))

        # Metallic shine effect
        shine_offset_x = math.cos(rotation_speed * 0.5) * r * 0.3
        shine_offset_y = math.sin(rotation_speed * 0.5) * r * 0.3
        shine_pos = (int(cx + shine_offset_x), int(cy + shine_offset_y))
        pygame.draw.circle(screen, (255, 255, 255), shine_pos, int(r * 0.4))
        pygame.draw.circle(screen, (200, 200, 255), shine_pos, int(r * 0.25))

        # Rotating energy rings
        for ring in range(3):
            ring_radius = r * (0.8 + ring * 0.3)
            ring_angle = rotation_speed + ring * (2 * math.pi / 3)

            # Calculate ring points
            ring_points = []
            for i in range(12):
                point_angle = ring_angle + (i * 2 * math.pi / 12)
                point_x = cx + math.cos(point_angle) * ring_radius
                point_y = (
                    cy + math.sin(point_angle) * ring_radius * 0.3
                )  # Flatten for 3D effect
                ring_points.append((point_x, point_y))

            # Draw energy ring
            if len(ring_points) > 2:
                ring_color = (0, 150 + ring * 30, 255)
                for i in range(len(ring_points)):
                    start_point = ring_points[i]
                    end_point = ring_points[(i + 1) % len(ring_points)]
                    pygame.draw.line(screen, ring_color, start_point, end_point, 2)

        # Rotating stripes for speed effect
        stripe_count = 8
        for i in range(stripe_count):
            stripe_angle = rotation_speed * 2 + (i * 2 * math.pi / stripe_count)
            stripe_start = (
                cx + math.cos(stripe_angle) * r * 0.7,
                cy + math.sin(stripe_angle) * r * 0.7,
            )
            stripe_end = (
                cx + math.cos(stripe_angle + math.pi) * r * 0.7,
                cy + math.sin(stripe_angle + math.pi) * r * 0.7,
            )

            # Alternating stripe colors for depth
            stripe_color = dark_color if i % 2 == 0 else enhanced_color
            pygame.draw.line(screen, stripe_color, stripe_start, stripe_end, 3)

        # Central core with pulsing energy
        core_size = int(r * 0.3 * (1.0 + math.sin(time_ms * 0.02) * 0.3))
        core_brightness = int(150 + 105 * math.sin(time_ms * 0.025))
        core_color = (core_brightness, core_brightness, 255)
        pygame.draw.circle(screen, core_color, (int(cx), int(cy)), core_size)

        # Energy sparks around the ball
        if random.random() < 0.3:  # 30% chance per frame
            for _ in range(3):
                spark_angle = random.uniform(0, 2 * math.pi)
                spark_distance = r + random.randint(5, 15)
                spark_x = cx + math.cos(spark_angle) * spark_distance
                spark_y = cy + math.sin(spark_angle) * spark_distance
                spark_size = random.randint(1, 3)
                pygame.draw.circle(
                    screen, (255, 255, 255), (int(spark_x), int(spark_y)), spark_size
                )

        # Speed trail effect
        trail_length = 5
        for i in range(trail_length):
            trail_alpha = 255 - (i * 40)
            if trail_alpha > 0:
                trail_offset = i * 3
                trail_pos = (int(cx - trail_offset), int(cy))
                trail_size = int(r * (1.0 - i * 0.1))
                if trail_size > 0:
                    trail_surface = pygame.Surface(
                        (trail_size * 2, trail_size * 2), pygame.SRCALPHA
                    )
                    trail_color = (*enhanced_color, trail_alpha)
                    pygame.draw.circle(
                        trail_surface, trail_color, (trail_size, trail_size), trail_size
                    )
                    screen.blit(
                        trail_surface,
                        (trail_pos[0] - trail_size, trail_pos[1] - trail_size),
                    )

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
        """Render the beast enemy visual style with enhanced graphics."""
        time_ms = pygame.time.get_ticks()

        # Breathing animation
        breath_scale = 1.0 + math.sin(time_ms * 0.006) * 0.15
        current_rw = rw * breath_scale
        current_rh = rh * breath_scale

        # Menacing red glow
        glow_size = current_rw * 1.5
        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_alpha = int(40 + 30 * math.sin(time_ms * 0.012))
        glow_color = (150, 0, 0, glow_alpha)
        pygame.draw.circle(
            glow_surface, glow_color, (glow_size, glow_size), int(glow_size)
        )
        screen.blit(glow_surface, (cx - glow_size, ry + current_rh * 0.5 - glow_size))

        # Enhanced color for beast
        beast_color = tuple(min(255, c + 30) for c in color)
        dark_beast = tuple(max(0, c - 40) for c in beast_color)

        # Main Body - larger and more imposing
        body_rect = (
            cx - current_rw / 2,
            ry + current_rh * 0.25,
            current_rw,
            current_rh * 0.6,
        )
        pygame.draw.rect(
            screen, beast_color, body_rect, border_radius=int(current_rw * 0.1)
        )

        # Body armor plating
        for i in range(3):
            plate_y = ry + current_rh * (0.3 + i * 0.15)
            plate_rect = (
                cx - current_rw * 0.4,
                plate_y,
                current_rw * 0.8,
                current_rh * 0.08,
            )
            pygame.draw.rect(screen, dark_beast, plate_rect, border_radius=2)
            # Highlight on armor
            highlight_rect = (
                cx - current_rw * 0.35,
                plate_y + 2,
                current_rw * 0.7,
                current_rh * 0.04,
            )
            pygame.draw.rect(screen, beast_color, highlight_rect, border_radius=1)

        # Enhanced Head with horns
        head_size = current_rw * 0.9
        head_rect = (cx - head_size / 2, ry, head_size, head_size * 0.8)
        pygame.draw.rect(
            screen, (120, 0, 0), head_rect, border_radius=int(head_size * 0.1)
        )

        # Head ridges/scars
        for ridge in range(2):
            ridge_y = ry + head_size * (0.2 + ridge * 0.3)
            pygame.draw.line(
                screen,
                (80, 0, 0),
                (cx - head_size * 0.3, ridge_y),
                (cx + head_size * 0.3, ridge_y),
                3,
            )

        # Demonic horns
        horn_height = head_size * 0.4
        # Left horn
        pygame.draw.polygon(
            screen,
            (60, 60, 60),
            [
                (cx - head_size * 0.3, ry),
                (cx - head_size * 0.35, ry - horn_height),
                (cx - head_size * 0.25, ry - horn_height * 0.8),
                (cx - head_size * 0.2, ry),
            ],
        )
        # Right horn
        pygame.draw.polygon(
            screen,
            (60, 60, 60),
            [
                (cx + head_size * 0.3, ry),
                (cx + head_size * 0.35, ry - horn_height),
                (cx + head_size * 0.25, ry - horn_height * 0.8),
                (cx + head_size * 0.2, ry),
            ],
        )

        # Enhanced glowing eyes with animation
        eye_brightness = int(200 + 55 * math.sin(time_ms * 0.02))
        eye_glow_size = head_size * 0.12

        for eye_offset in [-0.25, 0.25]:
            eye_x = cx + head_size * eye_offset
            eye_y = ry + head_size * 0.35

            # Eye glow
            eye_glow_surf = pygame.Surface(
                (eye_glow_size * 4, eye_glow_size * 4), pygame.SRCALPHA
            )
            pygame.draw.circle(
                eye_glow_surf,
                (255, 255, 0, 80),
                (eye_glow_size * 2, eye_glow_size * 2),
                int(eye_glow_size * 2),
            )
            screen.blit(
                eye_glow_surf, (eye_x - eye_glow_size * 2, eye_y - eye_glow_size * 2)
            )

            # Main eye
            pygame.draw.circle(
                screen,
                (255, eye_brightness, 0),
                (int(eye_x), int(eye_y)),
                int(eye_glow_size),
            )
            # Eye pupil
            pygame.draw.circle(
                screen,
                (255, 255, 255),
                (int(eye_x), int(eye_y)),
                int(eye_glow_size * 0.4),
            )

        # Snarling mouth
        mouth_y = ry + head_size * 0.6
        mouth_w = head_size * 0.6
        pygame.draw.rect(
            screen,
            (20, 0, 0),
            (cx - mouth_w / 2, mouth_y, mouth_w, head_size * 0.2),
            border_radius=5,
        )

        # Large fangs
        fang_positions = [
            (cx - mouth_w * 0.3, mouth_y),
            (cx - mouth_w * 0.1, mouth_y),
            (cx + mouth_w * 0.1, mouth_y),
            (cx + mouth_w * 0.3, mouth_y),
        ]

        for fang_x, fang_y in fang_positions:
            pygame.draw.polygon(
                screen,
                (240, 240, 240),
                [(fang_x - 3, fang_y), (fang_x + 3, fang_y), (fang_x, fang_y + 12)],
            )

        # Enhanced clawed arms
        if not bot.dead:
            arm_y = ry + current_rh * 0.35
            arm_thickness = int(current_rw * 0.2)

            # Left arm - more muscular
            left_shoulder = (cx - current_rw * 0.4, arm_y)
            left_hand = (cx - current_rw * 0.8, arm_y + current_rh * 0.3)
            pygame.draw.line(
                screen, beast_color, left_shoulder, left_hand, arm_thickness
            )

            # Left claws
            for claw in range(4):
                claw_angle = -0.5 + claw * 0.3
                claw_end = (
                    left_hand[0] + math.cos(claw_angle) * 15,
                    left_hand[1] + math.sin(claw_angle) * 15,
                )
                pygame.draw.line(screen, (200, 200, 200), left_hand, claw_end, 3)

            # Right arm
            right_shoulder = (cx + current_rw * 0.4, arm_y)
            right_hand = (cx + current_rw * 0.8, arm_y + current_rh * 0.3)
            pygame.draw.line(
                screen, beast_color, right_shoulder, right_hand, arm_thickness
            )

            # Right claws
            for claw in range(4):
                claw_angle = 2.6 + claw * 0.3
                claw_end = (
                    right_hand[0] + math.cos(claw_angle) * 15,
                    right_hand[1] + math.sin(claw_angle) * 15,
                )
                pygame.draw.line(screen, (200, 200, 200), right_hand, claw_end, 3)

        # Enhanced legs - more powerful
        if not bot.dead:
            leg_w = current_rw * 0.3
            leg_h = current_rh * 0.35
            leg_y = ry + current_rh * 0.65

            # Left leg with muscle definition
            left_leg_rect = (cx - current_rw * 0.3, leg_y, leg_w, leg_h)
            pygame.draw.rect(screen, beast_color, left_leg_rect, border_radius=5)
            pygame.draw.rect(
                screen,
                dark_beast,
                (cx - current_rw * 0.25, leg_y + leg_h * 0.3, leg_w * 0.8, leg_h * 0.4),
                border_radius=3,
            )

            # Right leg
            right_leg_rect = (cx + current_rw * 0.05, leg_y, leg_w, leg_h)
            pygame.draw.rect(screen, beast_color, right_leg_rect, border_radius=5)
            pygame.draw.rect(
                screen,
                dark_beast,
                (cx + current_rw * 0.1, leg_y + leg_h * 0.3, leg_w * 0.8, leg_h * 0.4),
                border_radius=3,
            )

            # Clawed feet
            for foot_x in [cx - current_rw * 0.15, cx + current_rw * 0.2]:
                foot_y = leg_y + leg_h
                pygame.draw.ellipse(
                    screen, (40, 40, 40), (foot_x - 8, foot_y - 3, 16, 8)
                )
                # Foot claws
                for toe in range(3):
                    toe_x = foot_x - 6 + toe * 6
                    pygame.draw.line(
                        screen, (180, 180, 180), (toe_x, foot_y), (toe_x, foot_y + 8), 2
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
        """Render the ghost enemy visual style with enhanced graphics."""
        time_ms = pygame.time.get_ticks()

        # Enhanced floating animation with multiple wave components
        float_primary = math.sin(time_ms * 0.005) * 12
        float_secondary = math.sin(time_ms * 0.008) * 6
        offset_y = float_primary + float_secondary
        gy = ry + offset_y

        # Ghostly transparency and glow
        base_alpha = 120 + int(35 * math.sin(time_ms * 0.01))
        ghost_color = (*color, base_alpha)

        # Ethereal glow around ghost
        glow_size = rw * 1.4
        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_alpha = int(20 + 15 * math.sin(time_ms * 0.012))
        glow_rgba = (200, 200, 255, glow_alpha)
        pygame.draw.circle(
            glow_surface, glow_rgba, (glow_size, glow_size), int(glow_size)
        )
        screen.blit(glow_surface, (cx - glow_size, gy + rw / 2 - glow_size))

        # Enhanced head with better shape
        head_radius = rw / 2

        # Create ghost surface for transparency
        ghost_surface = pygame.Surface((rw * 2, rh * 1.5), pygame.SRCALPHA)

        # Head with subtle gradient
        pygame.draw.circle(
            ghost_surface, ghost_color, (int(rw), int(head_radius)), int(head_radius)
        )

        # Head highlight for ethereal effect
        highlight_color = (*color, int(base_alpha * 0.6))
        pygame.draw.circle(
            ghost_surface,
            highlight_color,
            (int(rw - head_radius * 0.3), int(head_radius * 0.7)),
            int(head_radius * 0.4),
        )

        # Enhanced body with flowing shape
        body_width = rw
        body_height = rh * 0.7
        body_rect = pygame.Rect(
            rw - body_width / 2, head_radius, body_width, body_height
        )
        pygame.draw.rect(ghost_surface, ghost_color, body_rect)

        # Flowing tattered bottom with more organic shape
        tatter_points = []
        tatter_points.append((rw - body_width / 2, head_radius + body_height))

        # Create more natural flowing tatters
        tatter_count = 7
        for i in range(tatter_count + 1):
            x_ratio = i / tatter_count
            x = rw - body_width / 2 + x_ratio * body_width

            # Varying tatter lengths with wave motion
            base_tatter_length = body_height * 0.4
            wave_offset = math.sin(time_ms * 0.01 + i * 0.8) * body_height * 0.2
            length_variation = math.sin(i * 1.5) * body_height * 0.15

            y = (
                head_radius
                + body_height
                + base_tatter_length
                + wave_offset
                + length_variation
            )
            tatter_points.append((x, y))

        tatter_points.append((rw + body_width / 2, head_radius + body_height))
        tatter_points.append((rw + body_width / 2, head_radius))
        tatter_points.append((rw - body_width / 2, head_radius))

        if len(tatter_points) > 2:
            pygame.draw.polygon(ghost_surface, ghost_color, tatter_points)

        # Enhanced hollow eyes with eerie glow
        eye_size = int(rw * 0.12)
        eye_glow_size = eye_size * 2

        for eye_x_offset in [-0.25, 0.25]:
            eye_x = int(rw + rw * eye_x_offset)
            eye_y = int(head_radius * 0.8)

            # Eye glow
            eye_glow_surf = pygame.Surface(
                (eye_glow_size * 2, eye_glow_size * 2), pygame.SRCALPHA
            )
            glow_brightness = int(60 + 40 * math.sin(time_ms * 0.015 + eye_x_offset))
            pygame.draw.circle(
                eye_glow_surf,
                (0, 255, 255, glow_brightness),
                (eye_glow_size, eye_glow_size),
                eye_glow_size,
            )
            ghost_surface.blit(
                eye_glow_surf, (eye_x - eye_glow_size, eye_y - eye_glow_size)
            )

            # Main eye socket (darker)
            pygame.draw.circle(ghost_surface, (0, 0, 0, 200), (eye_x, eye_y), eye_size)

            # Glowing pupil
            pupil_brightness = int(150 + 105 * math.sin(time_ms * 0.02))
            pupil_color = (0, pupil_brightness, 255, 180)
            pygame.draw.circle(
                ghost_surface, pupil_color, (eye_x, eye_y), int(eye_size * 0.6)
            )

        # Spectral mouth
        mouth_y = int(head_radius * 1.3)
        mouth_width = int(rw * 0.3)
        mouth_height = int(rw * 0.15)

        # Dark mouth opening
        mouth_rect = (rw - mouth_width // 2, mouth_y, mouth_width, mouth_height)
        pygame.draw.ellipse(ghost_surface, (0, 0, 0, 150), mouth_rect)

        # Ghostly breath effect
        if random.random() < 0.1:  # 10% chance per frame
            for _ in range(3):
                breath_x = rw + random.randint(-mouth_width // 2, mouth_width // 2)
                breath_y = mouth_y + mouth_height + random.randint(0, 10)
                breath_size = random.randint(2, 5)
                breath_alpha = random.randint(30, 80)
                pygame.draw.circle(
                    ghost_surface,
                    (200, 200, 255, breath_alpha),
                    (breath_x, breath_y),
                    breath_size,
                )

        # Blit the ghost surface to the main screen
        screen.blit(ghost_surface, (cx - rw, gy - head_radius))

        # Add floating spirit particles around ghost
        if random.random() < 0.2:  # 20% chance per frame
            for _ in range(2):
                particle_angle = random.uniform(0, 2 * math.pi)
                particle_distance = rw * 0.8 + random.randint(0, int(rw * 0.4))
                particle_x = cx + math.cos(particle_angle) * particle_distance
                particle_y = (
                    gy + rw / 2 + math.sin(particle_angle) * particle_distance * 0.5
                )

                particle_surface = pygame.Surface((6, 6), pygame.SRCALPHA)
                particle_alpha = random.randint(40, 120)
                pygame.draw.circle(
                    particle_surface, (150, 150, 255, particle_alpha), (3, 3), 3
                )
                screen.blit(particle_surface, (particle_x - 3, particle_y - 3))

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
        """Render the minigunner enemy visual style with enhanced graphics."""
        time_ms = pygame.time.get_ticks()

        # Heavy armor colors
        armor_color = (60, 60, 80)
        armor_highlight = (90, 90, 110)
        armor_shadow = (30, 30, 40)

        # Breathing animation for intimidation
        breath_scale = 1.0 + math.sin(time_ms * 0.004) * 0.05
        current_rw = rw * breath_scale
        current_rh = rh * breath_scale

        # Menacing red glow from visor
        glow_size = current_rw * 1.2
        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_alpha = int(25 + 20 * math.sin(time_ms * 0.01))
        glow_color = (150, 0, 0, glow_alpha)
        pygame.draw.circle(
            glow_surface, glow_color, (glow_size, glow_size), int(glow_size)
        )
        screen.blit(glow_surface, (cx - glow_size, ry + current_rh * 0.4 - glow_size))

        # Enhanced body armor with plating
        body_x = cx - current_rw / 2
        body_y = ry + current_rh * 0.2
        body_width = current_rw
        body_height = current_rh * 0.6

        # Main armor body
        main_armor = pygame.Rect(body_x, body_y, body_width, body_height)
        pygame.draw.rect(
            screen, armor_color, main_armor, border_radius=int(current_rw * 0.1)
        )

        # Armor plating details
        plate_count = 4
        for i in range(plate_count):
            plate_y = body_y + i * (body_height / plate_count)
            plate_height = body_height / plate_count - 2

            # Main plate
            plate_rect = (body_x + 4, plate_y + 1, body_width - 8, plate_height)
            pygame.draw.rect(screen, armor_highlight, plate_rect, border_radius=2)

            # Plate shadow/depth
            shadow_rect = (body_x + 6, plate_y + 3, body_width - 12, plate_height - 4)
            pygame.draw.rect(screen, armor_shadow, shadow_rect, border_radius=1)

        # Chest power core
        core_size = int(current_rw * 0.15)
        core_x = int(cx)
        core_y = int(body_y + body_height * 0.3)
        core_brightness = int(100 + 155 * math.sin(time_ms * 0.02))
        core_color = (core_brightness, 0, 0)
        pygame.draw.circle(screen, core_color, (core_x, core_y), core_size)
        pygame.draw.circle(
            screen, (255, 100, 100), (core_x, core_y), int(core_size * 0.6)
        )

        # Enhanced helmet with better proportions
        head_size = current_rw * 0.8
        head_x = cx - head_size / 2
        head_y = ry

        # Main helmet
        helmet_rect = (head_x, head_y, head_size, head_size * 0.9)
        pygame.draw.rect(
            screen, armor_shadow, helmet_rect, border_radius=int(head_size * 0.1)
        )

        # Helmet highlight
        highlight_rect = (head_x + 3, head_y + 3, head_size - 6, head_size * 0.4)
        pygame.draw.rect(
            screen, armor_color, highlight_rect, border_radius=int(head_size * 0.08)
        )

        # Enhanced visor with animation
        visor_width = head_size * 0.8
        visor_height = head_size * 0.2
        visor_x = head_x + (head_size - visor_width) / 2
        visor_y = head_y + head_size * 0.3

        # Visor glow effect
        visor_brightness = int(200 + 55 * math.sin(time_ms * 0.015))
        visor_color = (visor_brightness, 0, 0)

        # Main visor
        visor_rect = (visor_x, visor_y, visor_width, visor_height)
        pygame.draw.rect(screen, visor_color, visor_rect, border_radius=3)

        # Visor scan lines
        for scan_line in range(3):
            line_y = visor_y + 3 + scan_line * 4
            line_brightness = int(visor_brightness * 0.7)
            pygame.draw.line(
                screen,
                (line_brightness, 0, 0),
                (visor_x + 2, line_y),
                (visor_x + visor_width - 2, line_y),
                1,
            )

        # Helmet vents
        vent_count = 3
        for vent in range(vent_count):
            vent_x = head_x + head_size * 0.1 + vent * (head_size * 0.25)
            vent_y = head_y + head_size * 0.7
            pygame.draw.rect(screen, (20, 20, 20), (vent_x, vent_y, 8, 3))

        # Enhanced minigun weapon system
        weapon_scale = 1.0 + (
            bot.shoot_animation * 0.1 if bot.shoot_animation > 0 else 0
        )
        weapon_w = current_rw * 1.4 * weapon_scale
        weapon_h = current_rh * 0.25
        wx = cx - weapon_w / 2
        wy = body_y + body_height * 0.4

        # Main weapon body
        weapon_body = (wx, wy, weapon_w, weapon_h)
        pygame.draw.rect(screen, (25, 25, 25), weapon_body, border_radius=3)

        # Weapon details
        pygame.draw.rect(
            screen,
            (50, 50, 50),
            (wx + 5, wy + 3, weapon_w - 10, weapon_h - 6),
            border_radius=2,
        )

        # Multiple rotating barrels
        barrel_count = 6
        barrel_radius = weapon_h * 0.8
        barrel_center_x = wx + weapon_w * 0.8
        barrel_center_y = wy + weapon_h / 2

        # Barrel rotation based on shooting
        barrel_rotation = time_ms * 0.02
        if bot.shoot_animation > 0:
            barrel_rotation = time_ms * 0.1  # Faster rotation when shooting

        for i in range(barrel_count):
            barrel_angle = barrel_rotation + (i * 2 * math.pi / barrel_count)
            barrel_x = barrel_center_x + math.cos(barrel_angle) * (barrel_radius * 0.3)
            barrel_y = barrel_center_y + math.sin(barrel_angle) * (barrel_radius * 0.3)

            # Individual barrel
            pygame.draw.circle(screen, (40, 40, 40), (int(barrel_x), int(barrel_y)), 4)
            pygame.draw.circle(screen, (60, 60, 60), (int(barrel_x), int(barrel_y)), 2)

        # Central barrel hub
        pygame.draw.circle(
            screen,
            (30, 30, 30),
            (int(barrel_center_x), int(barrel_center_y)),
            int(barrel_radius * 0.2),
        )

        # Enhanced muzzle flash with multiple effects
        if bot.shoot_animation > 0:
            flash_intensity = bot.shoot_animation

            # Main muzzle flash
            flash_size = int(15 + flash_intensity * 10)
            flash_colors = [
                (255, 255, 200, int(200 * flash_intensity)),
                (255, 200, 0, int(150 * flash_intensity)),
                (255, 100, 0, int(100 * flash_intensity)),
            ]

            flash_x = int(barrel_center_x + barrel_radius * 0.6)
            flash_y = int(barrel_center_y)

            for i, flash_color in enumerate(flash_colors):
                current_size = flash_size - i * 4
                if current_size > 0:
                    flash_surface = pygame.Surface(
                        (current_size * 2, current_size * 2), pygame.SRCALPHA
                    )
                    pygame.draw.circle(
                        flash_surface,
                        flash_color,
                        (current_size, current_size),
                        current_size,
                    )
                    screen.blit(
                        flash_surface, (flash_x - current_size, flash_y - current_size)
                    )

            # Muzzle sparks
            for _ in range(8):
                spark_x = flash_x + random.randint(-8, 15)
                spark_y = flash_y + random.randint(-5, 5)
                spark_size = random.randint(1, 3)
                pygame.draw.circle(
                    screen, (255, 255, 100), (spark_x, spark_y), spark_size
                )

            # Shell casings effect
            for _ in range(3):
                casing_x = int(barrel_center_x - 10 + random.randint(-5, 5))
                casing_y = int(barrel_center_y + 10 + random.randint(-3, 8))
                pygame.draw.rect(screen, (200, 150, 50), (casing_x, casing_y, 3, 6))

        # Enhanced legs with hydraulics
        if not bot.dead:
            leg_w = current_rw * 0.28
            leg_h = current_rh * 0.35
            leg_y = ry + current_rh * 0.65

            # Left leg with hydraulic details
            left_leg_x = cx - current_rw * 0.35
            pygame.draw.rect(
                screen, armor_color, (left_leg_x, leg_y, leg_w, leg_h), border_radius=4
            )

            # Hydraulic pistons
            piston_rect = (left_leg_x + 3, leg_y + leg_h * 0.2, leg_w - 6, leg_h * 0.3)
            pygame.draw.rect(screen, armor_shadow, piston_rect, border_radius=2)
            pygame.draw.rect(
                screen,
                (100, 100, 100),
                (left_leg_x + 5, leg_y + leg_h * 0.25, leg_w - 10, leg_h * 0.2),
            )

            # Right leg
            right_leg_x = cx + current_rw * 0.07
            pygame.draw.rect(
                screen, armor_color, (right_leg_x, leg_y, leg_w, leg_h), border_radius=4
            )

            # Right leg hydraulics
            piston_rect = (right_leg_x + 3, leg_y + leg_h * 0.2, leg_w - 6, leg_h * 0.3)
            pygame.draw.rect(screen, armor_shadow, piston_rect, border_radius=2)
            pygame.draw.rect(
                screen,
                (100, 100, 100),
                (right_leg_x + 5, leg_y + leg_h * 0.25, leg_w - 10, leg_h * 0.2),
            )

            # Heavy boots
            for boot_x in [left_leg_x, right_leg_x]:
                boot_y = leg_y + leg_h - 5
                boot_rect = (boot_x - 2, boot_y, leg_w + 4, 12)
                pygame.draw.rect(screen, (40, 40, 40), boot_rect, border_radius=2)
                pygame.draw.rect(
                    screen,
                    (60, 60, 60),
                    (boot_x, boot_y + 2, leg_w, 8),
                    border_radius=1,
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
        """Render the default monster visual style with enhanced graphics."""
        time_ms = pygame.time.get_ticks()

        # Enhanced color variations based on enemy type
        if bot.enemy_type == "boss":
            base_color = tuple(min(255, c + 50) for c in color)
            glow_color = (255, 255, 0)
        else:
            base_color = color
            glow_color = (255, 100, 100)

        # Breathing/pulsing animation
        pulse = math.sin(time_ms * 0.008) * 0.1 + 1.0
        current_rw = rw * pulse
        current_rh = rh * pulse

        # Add menacing glow around monster
        if not bot.dead:
            glow_size = current_rw * 1.3
            glow_surface = pygame.Surface(
                (glow_size * 2, glow_size * 2), pygame.SRCALPHA
            )
            glow_alpha = int(30 + 20 * math.sin(time_ms * 0.01))
            glow_rgba = (*glow_color, glow_alpha)
            pygame.draw.circle(
                glow_surface, glow_rgba, (glow_size, glow_size), int(glow_size)
            )
            screen.blit(
                glow_surface,
                (cx - glow_size, ry + current_rh * 0.5 - glow_size),
            )

        # 1. Enhanced Body (Rounded Torso with muscle definition)
        current_body_x = cx - current_rw / 2
        torso_rect = pygame.Rect(
            int(current_body_x),
            int(ry + current_rh * 0.25),
            int(current_rw),
            int(current_rh * 0.5),
        )

        # Main body with gradient effect
        pygame.draw.ellipse(screen, base_color, torso_rect)

        # Enhanced muscle definition with multiple shadow layers
        dark_color = tuple(max(0, c - 60) for c in base_color)
        light_color = tuple(min(255, c + 40) for c in base_color)
        mid_color = tuple(max(0, c - 20) for c in base_color)

        # Highlight top (chest muscles)
        highlight_rect = (
            current_body_x + current_rw * 0.15,
            ry + current_rh * 0.25,
            current_rw * 0.7,
            current_rh * 0.15,
        )
        pygame.draw.ellipse(screen, light_color, highlight_rect)

        # Enhanced abs/ribs with better definition
        for i in range(4):
            y_off = ry + current_rh * (0.32 + i * 0.08)
            # Main shadow line
            pygame.draw.line(
                screen,
                dark_color,
                (current_body_x + current_rw * 0.1, y_off),
                (current_body_x + current_rw * 0.9, y_off),
                3,
            )
            # Highlight line above
            pygame.draw.line(
                screen,
                mid_color,
                (current_body_x + current_rw * 0.15, y_off - 2),
                (current_body_x + current_rw * 0.85, y_off - 2),
                1,
            )

        # 2. Enhanced Head with better proportions
        if not bot.dead or bot.death_timer < 30:
            head_size = int(current_rw * 0.7)
            head_y = int(ry + current_rh * 0.02)

            # Head with rounded corners and gradient
            head_rect = pygame.Rect(cx - head_size // 2, head_y, head_size, head_size)
            pygame.draw.rect(
                screen, base_color, head_rect, border_radius=head_size // 6
            )

            # Head highlight
            highlight_head = pygame.Rect(
                cx - head_size // 3, head_y + 2, head_size // 1.5, head_size // 3
            )
            pygame.draw.rect(
                screen, light_color, highlight_head, border_radius=head_size // 8
            )

            # Enhanced Glowing Eyes with animation
            eye_brightness = int(200 + 55 * math.sin(time_ms * 0.015))
            eye_color = (eye_brightness, 50, 0)
            if bot.enemy_type == "boss":
                eye_color = (255, eye_brightness, 0)

            # Eye glow effect
            eye_glow_size = head_size * 0.15
            for eye_x_offset in [-0.25, 0.25]:
                eye_x = cx + head_size * eye_x_offset
                eye_y = head_y + head_size * 0.35

                # Outer glow
                glow_surf = pygame.Surface(
                    (eye_glow_size * 4, eye_glow_size * 4), pygame.SRCALPHA
                )
                pygame.draw.circle(
                    glow_surf,
                    (*eye_color, 60),
                    (eye_glow_size * 2, eye_glow_size * 2),
                    int(eye_glow_size * 2),
                )
                screen.blit(
                    glow_surf, (eye_x - eye_glow_size * 2, eye_y - eye_glow_size * 2)
                )

                # Main eye
                pygame.draw.circle(
                    screen, eye_color, (int(eye_x), int(eye_y)), int(head_size * 0.08)
                )
                # Eye pupil
                pygame.draw.circle(
                    screen,
                    (255, 255, 255),
                    (int(eye_x), int(eye_y)),
                    int(head_size * 0.03),
                )

            # Enhanced Mouth with better animation
            mouth_y = head_y + head_size * 0.65
            mouth_w = head_size * 0.7

            if bot.mouth_open:
                # Open mouth with depth
                mouth_rect = (cx - mouth_w / 2, mouth_y, mouth_w, head_size * 0.25)
                pygame.draw.rect(screen, (20, 0, 0), mouth_rect, border_radius=5)

                # Inner mouth darkness
                inner_mouth = (
                    cx - mouth_w / 2 + 3,
                    mouth_y + 3,
                    mouth_w - 6,
                    head_size * 0.25 - 6,
                )
                pygame.draw.rect(screen, (5, 0, 0), inner_mouth, border_radius=3)

                # Enhanced teeth with better spacing
                tooth_count = 6
                for i in range(tooth_count):
                    tooth_x = cx - mouth_w / 2 + (i + 0.5) * (mouth_w / tooth_count)
                    # Upper teeth
                    pygame.draw.polygon(
                        screen,
                        (240, 240, 240),
                        [
                            (tooth_x - 2, mouth_y),
                            (tooth_x + 2, mouth_y),
                            (tooth_x, mouth_y + 8),
                        ],
                    )
                    # Lower teeth
                    pygame.draw.polygon(
                        screen,
                        (220, 220, 220),
                        [
                            (tooth_x - 1.5, mouth_y + head_size * 0.25),
                            (tooth_x + 1.5, mouth_y + head_size * 0.25),
                            (tooth_x, mouth_y + head_size * 0.25 - 6),
                        ],
                    )
            else:
                # Closed mouth with better definition
                pygame.draw.line(
                    screen,
                    (150, 150, 150),
                    (cx - mouth_w / 2, mouth_y + 3),
                    (cx + mouth_w / 2, mouth_y + 3),
                    4,
                )
                # Mouth shadow
                pygame.draw.line(
                    screen,
                    dark_color,
                    (cx - mouth_w / 2, mouth_y + 6),
                    (cx + mouth_w / 2, mouth_y + 6),
                    2,
                )

        # 3. Enhanced Arms with better proportions and animation
        if not bot.dead:
            arm_y = ry + current_rh * 0.3
            arm_thickness = int(current_rw * 0.15)

            # Left arm with shoulder joint
            shoulder_left = (current_body_x + current_rw * 0.1, arm_y + 5)
            hand_left = (current_body_x - 20, arm_y + 35)

            # Arm segments for better articulation
            elbow_left = (shoulder_left[0] - 8, shoulder_left[1] + 15)

            # Upper arm
            pygame.draw.line(
                screen, base_color, shoulder_left, elbow_left, arm_thickness
            )
            # Lower arm
            pygame.draw.line(
                screen, base_color, elbow_left, hand_left, arm_thickness - 2
            )

            # Enhanced hand/claw
            pygame.draw.polygon(
                screen,
                (180, 180, 180),
                [
                    (hand_left[0] - 3, hand_left[1] - 5),
                    (hand_left[0] + 3, hand_left[1] - 5),
                    (hand_left[0] + 8, hand_left[1] + 5),
                    (hand_left[0] - 8, hand_left[1] + 5),
                ],
            )

            # Claws
            for claw_i in range(3):
                claw_x = hand_left[0] - 6 + claw_i * 4
                pygame.draw.line(
                    screen,
                    (200, 200, 200),
                    (claw_x, hand_left[1] + 5),
                    (claw_x - 2, hand_left[1] + 12),
                    2,
                )

            # Right arm (weapon arm) with enhanced weapon
            shoulder_right = (current_body_x + current_rw * 0.9, arm_y + 5)
            weapon_pos = (current_body_x + current_rw + 25, arm_y + 30)

            # Upper arm
            elbow_right = (shoulder_right[0] + 8, shoulder_right[1] + 15)
            pygame.draw.line(
                screen, base_color, shoulder_right, elbow_right, arm_thickness
            )
            # Lower arm
            pygame.draw.line(
                screen, base_color, elbow_right, weapon_pos, arm_thickness - 2
            )

            # Enhanced weapon with better details
            weapon_rect = (weapon_pos[0] - 5, weapon_pos[1] - 5, 30, 12)
            pygame.draw.rect(screen, (40, 40, 40), weapon_rect, border_radius=2)
            # Weapon highlight
            pygame.draw.rect(
                screen,
                (80, 80, 80),
                (weapon_pos[0] - 3, weapon_pos[1] - 3, 26, 8),
                border_radius=1,
            )

            # Enhanced muzzle flash with animation
            if bot.shoot_animation > 0.5:
                flash_size = 12 + random.randint(0, 8)
                flash_colors = [(255, 255, 200), (255, 200, 0), (255, 100, 0)]

                for i, flash_color in enumerate(flash_colors):
                    current_size = flash_size - i * 3
                    if current_size > 0:
                        pygame.draw.circle(
                            screen,
                            flash_color,
                            (weapon_pos[0] + 30, weapon_pos[1]),
                            current_size,
                        )

                # Sparks
                for _ in range(5):
                    spark_x = weapon_pos[0] + 30 + random.randint(-3, 8)
                    spark_y = weapon_pos[1] + random.randint(-3, 3)
                    pygame.draw.circle(screen, (255, 255, 0), (spark_x, spark_y), 1)

        # 4. Enhanced Legs with better proportions
        if not bot.dead:
            leg_w = current_rw * 0.25
            leg_h = current_rh * 0.3
            leg_y = ry + current_rh * 0.7

            # Left leg with thigh and shin
            left_leg_x = current_body_x + current_rw * 0.2
            pygame.draw.rect(
                screen,
                base_color,
                (left_leg_x, leg_y, leg_w, leg_h * 0.6),
                border_radius=3,
            )
            pygame.draw.rect(
                screen,
                mid_color,
                (left_leg_x, leg_y + leg_h * 0.5, leg_w, leg_h * 0.5),
                border_radius=2,
            )

            # Right leg
            right_leg_x = current_body_x + current_rw * 0.55
            pygame.draw.rect(
                screen,
                base_color,
                (right_leg_x, leg_y, leg_w, leg_h * 0.6),
                border_radius=3,
            )
            pygame.draw.rect(
                screen,
                mid_color,
                (right_leg_x, leg_y + leg_h * 0.5, leg_w, leg_h * 0.5),
                border_radius=2,
            )

            # Feet
            pygame.draw.ellipse(
                screen, (60, 60, 60), (left_leg_x - 2, leg_y + leg_h - 5, leg_w + 8, 8)
            )
            pygame.draw.ellipse(
                screen, (60, 60, 60), (right_leg_x - 2, leg_y + leg_h - 5, leg_w + 8, 8)
            )
