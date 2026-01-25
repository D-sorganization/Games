from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from .base import BaseBotStyleRenderer

if TYPE_CHECKING:
    from ..config import RaycasterConfig
    from ..interfaces import Bot


class BallStyleRenderer(BaseBotStyleRenderer):
    """Ball visual style renderer."""

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
        # Stripes
        pygame.draw.line(
            screen, (0, 0, 0), (int(cx - r), int(cy)), (int(cx + r), int(cy)), 3
        )
