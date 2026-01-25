from __future__ import annotations

import pygame
from typing import TYPE_CHECKING
from .base import BaseBotStyleRenderer

if TYPE_CHECKING:
    from ..config import RaycasterConfig
    from ..interfaces import Bot


class WeaponPickupRenderer(BaseBotStyleRenderer):
    """Weapon pickup visual style renderer."""

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
        """Render a weapon pickup item."""
        rect_w = rw * 0.8
        rect_h = rh * 0.3
        py = ry + rh * 0.7
        pygame.draw.rect(screen, color, (int(cx - rect_w / 2), int(py), int(rect_w), int(rect_h)))
        # Details
        pygame.draw.line(
            screen, (255, 255, 255), (int(cx - rect_w / 2), int(py)), (int(cx + rect_w / 2), int(py)), 2
        )
        if "minigun" in bot.enemy_type:
            pygame.draw.line(
                screen,
                (200, 200, 200),
                (int(cx - rect_w / 2), int(py + 4)),
                (int(cx + rect_w / 2), int(py + 4)),
                2,
            )
