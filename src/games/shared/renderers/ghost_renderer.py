from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from .base import BaseBotStyleRenderer

if TYPE_CHECKING:
    from ..config import RaycasterConfig
    from ..interfaces import Bot


class GhostStyleRenderer(BaseBotStyleRenderer):
    """Ghost visual style renderer."""

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
        """Render the ghost visual style."""
        time_ms = pygame.time.get_ticks()
        gy = ry + math.sin(time_ms * 0.005) * 10
        ghost_color = (*color, 150)
        self._render_ghost_body(screen, cx, gy, rw, rh, ghost_color)
        self._render_ghost_tattered_hem(screen, cx, gy, rw, rh, ghost_color)
        self._render_ghost_eyes(screen, cx, gy, rw)

    def _render_ghost_body(
        self,
        screen: pygame.Surface,
        cx: float,
        gy: float,
        rw: float,
        rh: float,
        ghost_color: tuple[int, ...],
    ) -> None:
        """Draw the ghost head circle and rectangular body."""
        pygame.draw.circle(
            screen, ghost_color, (int(cx), int(gy + rw / 2)), int(rw / 2)
        )
        body_rect = pygame.Rect(
            int(cx - rw / 2), int(gy + rw / 2), int(rw), int(rh * 0.6)
        )
        pygame.draw.rect(screen, ghost_color, body_rect)

    def _render_ghost_tattered_hem(
        self,
        screen: pygame.Surface,
        cx: float,
        gy: float,
        rw: float,
        rh: float,
        ghost_color: tuple[int, ...],
    ) -> None:
        """Draw the jagged tattered bottom hem polygon."""
        base_y = gy + rw / 2 + rh * 0.6
        points = [(cx - rw / 2, base_y)]
        for i in range(5):
            x = cx - rw / 2 + (i + 1) * (rw / 5)
            y = base_y + (rh * 0.2 if i % 2 == 0 else 0)
            points.append((x, y))
        points.extend(
            [
                (cx + rw / 2, base_y),
                (cx + rw / 2, gy + rw / 2),
                (cx - rw / 2, gy + rw / 2),
            ]
        )
        pygame.draw.polygon(screen, ghost_color, points)

    def _render_ghost_eyes(
        self, screen: pygame.Surface, cx: float, gy: float, rw: float
    ) -> None:
        """Draw two hollow black eyes."""
        eye_r = int(rw * 0.1)
        eye_y = int(gy + rw * 0.4)
        for x_sign in (-1, 1):
            pygame.draw.circle(
                screen, (0, 0, 0), (int(cx + x_sign * rw * 0.2), eye_y), eye_r
            )
