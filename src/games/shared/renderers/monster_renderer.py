from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from .base import BaseBotStyleRenderer

if TYPE_CHECKING:
    from ..config import RaycasterConfig
    from ..interfaces import Bot


class MonsterStyleRenderer(BaseBotStyleRenderer):
    """Monster visual style renderer."""

    def render(
        self,
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        color: tuple[int, int, int],
        config: RaycasterConfig,
    ) -> None:
        """Render the default monster visual style."""
        body_x = cx - rw / 2
        self._render_body(screen, bot, body_x, ry, rw, rh, color)

        if not bot.dead or bot.death_timer < 30:
            self._render_head(screen, bot, cx, ry, rw, rh, color)

        if not bot.dead:
            self._render_arms(screen, bot, body_x, ry, rw, rh, color)
            self._render_legs(screen, body_x, ry, rw, rh, color)

    def _render_body(
        self,
        screen: pygame.Surface,
        bot: Bot,
        body_x: float,
        ry: float,
        rw: float,
        rh: float,
        color: tuple[int, int, int],
    ) -> None:
        """Render monster torso and torso details."""
        torso_rect = pygame.Rect(
            int(body_x), int(ry + rh * 0.25), int(rw), int(rh * 0.5)
        )
        pygame.draw.ellipse(screen, color, torso_rect)

        light_color = tuple(min(255, c + 30) for c in color)
        pygame.draw.ellipse(
            screen,
            light_color,
            (
                int(body_x + rw * 0.2),
                int(ry + rh * 0.25),
                int(rw * 0.6),
                int(rh * 0.2),
            ),
        )

        dark_line_color = tuple(max(0, c - 50) for c in color)
        for i in range(3):
            y_off = ry + rh * (0.35 + i * 0.1)
            pygame.draw.line(
                screen,
                dark_line_color,
                (int(body_x + 5), int(y_off)),
                (int(body_x + rw - 5), int(y_off)),
                2,
            )

    def _render_head(
        self,
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        color: tuple[int, int, int],
    ) -> None:
        """Render the monster head and facial features."""
        head_size = int(rw * 0.6)
        head_y = int(ry + rh * 0.05)
        head_rect = pygame.Rect(
            int(cx - head_size // 2),
            int(head_y),
            int(head_size),
            int(head_size),
        )
        pygame.draw.rect(screen, color, head_rect)

        eye_color = (255, 50, 0)
        if bot.enemy_type == "boss":
            eye_color = (255, 255, 0)

        pygame.draw.polygon(
            screen,
            eye_color,
            [
                (int(cx - head_size * 0.3), int(head_y + head_size * 0.3)),
                (int(cx - head_size * 0.1), int(head_y + head_size * 0.3)),
                (int(cx - head_size * 0.2), int(head_y + head_size * 0.45)),
            ],
        )
        pygame.draw.polygon(
            screen,
            eye_color,
            [
                (int(cx + head_size * 0.3), int(head_y + head_size * 0.3)),
                (int(cx + head_size * 0.1), int(head_y + head_size * 0.3)),
                (int(cx + head_size * 0.2), int(head_y + head_size * 0.45)),
            ],
        )

        mouth_y = head_y + head_size * 0.65
        mouth_w = head_size * 0.6
        if getattr(bot, "mouth_open", False):
            pygame.draw.rect(
                screen,
                (50, 0, 0),
                (
                    int(cx - mouth_w / 2),
                    int(mouth_y),
                    int(mouth_w),
                    int(head_size * 0.3),
                ),
            )
        else:
            pygame.draw.line(
                screen,
                (200, 200, 200),
                (int(cx - mouth_w / 2), int(mouth_y + 5)),
                (int(cx + mouth_w / 2), int(mouth_y + 5)),
                3,
            )

    def _render_arms(
        self,
        screen: pygame.Surface,
        bot: Bot,
        body_x: float,
        ry: float,
        rw: float,
        rh: float,
        color: tuple[int, int, int],
    ) -> None:
        """Render monster arms and muzzle glow."""
        arm_y = ry + rh * 0.3
        start_arm = (int(body_x), int(arm_y + 10))
        end_arm = (int(body_x - 15), int(arm_y + 30))
        pygame.draw.line(screen, color, start_arm, end_arm, 6)

        weapon_x = body_x + rw
        pygame.draw.line(
            screen,
            color,
            (int(weapon_x), int(arm_y + 10)),
            (int(weapon_x + 15), int(arm_y + 30)),
            6,
        )
        pygame.draw.rect(
            screen, (30, 30, 30), (int(weapon_x + 10), int(arm_y + 25), 25, 10)
        )
        if getattr(bot, "shoot_animation", 0) > 0.5:
            pygame.draw.circle(
                screen,
                (255, 255, 0),
                (int(weapon_x + 35), int(arm_y + 30)),
                8 + random.randint(0, 4),
            )

    def _render_legs(
        self,
        screen: pygame.Surface,
        body_x: float,
        ry: float,
        rw: float,
        rh: float,
        color: tuple[int, int, int],
    ) -> None:
        """Render monster legs."""
        leg_w = rw * 0.3
        leg_h = rh * 0.25
        leg_y = ry + rh * 0.75
        pygame.draw.rect(
            screen, color, (int(body_x + 5), int(leg_y), int(leg_w), int(leg_h))
        )
        pygame.draw.rect(
            screen,
            color,
            (
                int(body_x + rw - 5 - leg_w),
                int(leg_y),
                int(leg_w),
                int(leg_h),
            ),
        )
