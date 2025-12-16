from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

import pygame

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .bot import Bot


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
        type_data: Dict[str, Any] = bot.type_data
        base_color = type_data["color"]
        visual_style = type_data.get("visual_style", "monster")

        # Health Pack / Items
        if bot.enemy_type == "health_pack":
            BotRenderer._render_health_pack(screen, sprite_x, sprite_y, sprite_size, center_x)
            return

        if bot.enemy_type == "ammo_box":
             BotRenderer._render_ammo_box(screen, sprite_x, sprite_y, sprite_size, center_x)
             return

        if bot.enemy_type == "bomb_item":
             BotRenderer._render_bomb_item(screen, sprite_x, sprite_y, sprite_size, center_x)
             return

        if bot.enemy_type.startswith("pickup_"):
            BotRenderer._render_weapon_pickup(screen, bot, sprite_x, sprite_y, sprite_size, center_x)
            return

        render_height = sprite_size
        render_width = sprite_size * 0.55 if visual_style == "monster" else sprite_size * 0.7
        render_y = sprite_y

        if bot.dead:
            # Melting animation
            melt_pct = min(1.0, bot.death_timer / 60.0)

            # Interpolate Color to Goo
            goo_color = (50, 150, 50)
            base_color = tuple(
                int(c * (1 - melt_pct) + g * melt_pct) for c, g in zip(base_color, goo_color)
            )

            # Squish
            scale_y = 1.0 - (melt_pct * 0.85)
            scale_x = 1.0 + (melt_pct * 0.8)

            current_h = render_height * scale_y
            current_w = render_width * scale_x

            render_y = int(sprite_y + (render_height - current_h) + (render_height * 0.05))
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

        # Monster Style (Default)
        BotRenderer._render_monster(
            screen, bot, center_x, render_y, render_width, render_height, base_color
        )

    @staticmethod
    def _render_health_pack(
        screen: pygame.Surface, x: int, y: int, size: float, cx: float
    ) -> None:
        rect_w = size * 0.4
        rect_h = size * 0.3
        kit_y = y + size * 0.7
        pygame.draw.rect(
            screen,
            (220, 220, 220),
            (cx - rect_w / 2, kit_y, rect_w, rect_h),
            border_radius=4,
        )
        cross_thick = rect_w * 0.2
        pygame.draw.rect(
            screen,
            (200, 0, 0),
            (cx - cross_thick / 2, kit_y + 5, cross_thick, rect_h - 10),
        )
        pygame.draw.rect(
            screen,
            (200, 0, 0),
            (
                cx - rect_w / 2 + 5,
                kit_y + rect_h / 2 - cross_thick / 2,
                rect_w - 10,
                cross_thick,
            ),
        )

    @staticmethod
    def _render_ammo_box(screen: pygame.Surface, x: int, y: int, size: float, cx: float) -> None:
        rect_w = size * 0.4
        rect_h = size * 0.3
        box_y = y + size * 0.7
        pygame.draw.rect(screen, (100, 100, 50), (cx - rect_w/2, box_y, rect_w, rect_h))
        pygame.draw.rect(screen, (200, 200, 0), (cx - rect_w/2 + 2, box_y + 2, rect_w - 4, rect_h - 4))

    @staticmethod
    def _render_bomb_item(screen: pygame.Surface, x: int, y: int, size: float, cx: float) -> None:
         r = size * 0.2
         cy = y + size * 0.8
         pygame.draw.circle(screen, (30, 30, 30), (int(cx), int(cy)), int(r))
         # Fuse
         pygame.draw.line(screen, (200, 150, 0), (cx, cy-r), (cx + r/2, cy-r*1.5), 2)
         if random.random() < 0.5:
             pygame.draw.circle(screen, (255, 100, 0), (int(cx + r/2), int(cy-r*1.5)), 2)

    @staticmethod
    def _render_weapon_pickup(screen: pygame.Surface, bot: Bot, x: int, y: int, size: float, cx: float) -> None:
        # Simple placeholder for weapon pickups
        rect_w = size * 0.6
        rect_h = size * 0.2
        py = y + size * 0.75
        color = bot.type_data["color"]
        pygame.draw.rect(screen, color, (cx - rect_w/2, py, rect_w, rect_h))
        # Label/Detail
        pygame.draw.line(screen, (255, 255, 255), (cx - rect_w/2, py), (cx + rect_w/2, py), 2)

    @staticmethod
    def _render_baby(
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        color: Tuple[int, int, int],
    ) -> None:
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
        pygame.draw.circle(
            screen, color, (cx, head_y + head_size / 2), head_size / 2
        )

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
        color: Tuple[int, int, int],
    ) -> None:
         # Metallic Ball with rotation effect (stripes)
         r = rw / 2
         cy = ry + rh / 2
         pygame.draw.circle(screen, color, (int(cx), int(cy)), int(r))
         # Shine
         pygame.draw.circle(screen, (200, 200, 200), (int(cx - r*0.3), int(cy - r*0.3)), int(r*0.3))
         # Stripes (rotate based on bot angle/pos?)
         # Just horizontal lines for "fast" look
         pygame.draw.line(screen, (0, 0, 0), (cx-r, cy), (cx+r, cy), 3)

    @staticmethod
    def _render_beast(
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        color: Tuple[int, int, int],
    ) -> None:
         # Large imposing figure
         # Main Body
         pygame.draw.rect(screen, color, (cx - rw/2, ry + rh*0.3, rw, rh*0.7))
         # Head (Horns)
         head_size = rw * 0.8
         pygame.draw.rect(screen, (100, 0, 0), (cx - head_size/2, ry, head_size, head_size))

         # Eyes
         pygame.draw.circle(screen, (255, 255, 0), (int(cx - head_size*0.2), int(ry + head_size*0.4)), 5)
         pygame.draw.circle(screen, (255, 255, 0), (int(cx + head_size*0.2), int(ry + head_size*0.4)), 5)

    @staticmethod
    def _render_monster(
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        color: Tuple[int, int, int],
    ) -> None:
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
                    pygame.draw.line(screen, (50, 0, 0), (x_off, mouth_y), (x_off, mouth_y + 10), 1)

        # 3. Arms
        if not bot.dead:
            arm_y = ry + rh * 0.3
            # Left
            pygame.draw.line(screen, color, (body_x, arm_y + 10), (body_x - 15, arm_y + 30), 6)
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
