from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from .base import BaseBotStyleRenderer

if TYPE_CHECKING:
    from ..config import RaycasterConfig
    from ..interfaces import Bot


class BabyStyleRenderer(BaseBotStyleRenderer):
    """Baby visual style renderer."""

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
        """Render the baby enemy visual style."""
        head_size = rw
        head_y = ry
        self._render_body(screen, cx, ry, rw, rh, color)
        self._render_head(screen, cx, head_y, head_size, color)
        self._render_face(screen, bot, cx, head_y, head_size)

    def _render_body(
        self,
        screen: pygame.Surface,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        color: tuple[int, int, int],
    ) -> None:
        """Draw the rounded body rectangle."""
        body_rect = pygame.Rect(
            int(cx - rw / 2),
            int(ry + rh * 0.4),
            int(rw),
            int(rh * 0.6),
        )
        pygame.draw.rect(screen, color, body_rect, border_radius=int(rw * 0.4))

    def _render_head(
        self,
        screen: pygame.Surface,
        cx: float,
        head_y: float,
        head_size: float,
        color: tuple[int, int, int],
    ) -> None:
        """Draw the head circle floating above the body."""
        pygame.draw.circle(
            screen, color, (int(cx), int(head_y + head_size / 2)), int(head_size / 2)
        )

    def _render_face(
        self,
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        head_y: float,
        head_size: float,
    ) -> None:
        """Draw the baby eyes (white + dark pupils) and mouth."""
        eye_r = head_size * 0.15
        white = (255, 255, 255)
        black = (0, 0, 0)
        eye_y = int(head_y + head_size * 0.4)
        for x_sign in (-1, 1):
            eye_x = int(cx + x_sign * head_size * 0.2)
            pygame.draw.circle(screen, white, (eye_x, eye_y), int(eye_r))
            pygame.draw.circle(screen, black, (eye_x, eye_y), int(eye_r * 0.6))
        mouth_y = int(head_y + head_size * 0.75)
        if getattr(bot, "mouth_open", False):
            pygame.draw.circle(
                screen, (50, 0, 0), (int(cx), mouth_y), int(head_size * 0.1)
            )
        else:
            pygame.draw.line(
                screen,
                (50, 0, 0),
                (int(cx - 5), mouth_y),
                (int(cx + 5), mouth_y),
                2,
            )
