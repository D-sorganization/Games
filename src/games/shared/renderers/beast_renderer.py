from __future__ import annotations

import pygame
from typing import TYPE_CHECKING
from .base import BaseBotStyleRenderer

if TYPE_CHECKING:
    from ..config import RaycasterConfig
    from ..interfaces import Bot


class BeastStyleRenderer(BaseBotStyleRenderer):
    """Beast visual style renderer."""

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
        """Render the beast enemy visual style."""
        # Large imposing figure
        # Main Body
        pygame.draw.rect(screen, color, (int(cx - rw / 2), int(ry + rh * 0.3), int(rw), int(rh * 0.7)))
        
        # Head (Horns)
        head_size = rw * 0.8
        head_rect = (int(cx - head_size / 2), int(ry), int(head_size), int(head_size))
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
        
        # Horns (Poly)
        pygame.draw.polygon(screen, (50, 50, 50), [
            (int(cx - head_size * 0.4), int(ry)),
            (int(cx - head_size * 0.6), int(ry - 20)),
            (int(cx - head_size * 0.2), int(ry + 10))
        ])
        pygame.draw.polygon(screen, (50, 50, 50), [
            (int(cx + head_size * 0.4), int(ry)),
            (int(cx + head_size * 0.6), int(ry - 20)),
            (int(cx + head_size * 0.2), int(ry + 10))
        ])
