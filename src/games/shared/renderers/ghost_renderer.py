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
        # Ghost: Float, fade at bottom, semi-transparent
        time_ms = pygame.time.get_ticks()
        offset_y = math.sin(time_ms * 0.005) * 10
        gy = ry + offset_y

        # Note: Pygame 2.0+ supports RGBA for basic draw functions, but let's be safe
        # Create a temp surface for transparency if needed, or just use solid for now
        # as per original code (didn't handle alpha correctly in draw.circle)
        ghost_color = (*color, 150)

        # Head
        center = (int(cx), int(gy + rw / 2))
        pygame.draw.circle(screen, ghost_color, center, int(rw / 2))

        # Body (Rect)
        body_rect = pygame.Rect(
            int(cx - rw / 2), int(gy + rw / 2), int(rw), int(rh * 0.6)
        )
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
