from __future__ import annotations

import random
import pygame
from typing import TYPE_CHECKING
from .base import BaseBotStyleRenderer

if TYPE_CHECKING:
    from ..config import RaycasterConfig
    from ..interfaces import Bot


class ItemRenderer(BaseBotStyleRenderer):
    """Generic item visual style renderer."""

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
        """Render items based on their specific type."""
        if bot.enemy_type == "health_pack":
            self._render_health_pack(screen, cx, ry, rw, rh)
        elif bot.enemy_type == "ammo_box":
            self._render_ammo_box(screen, cx, ry, rw, rh)
        elif bot.enemy_type == "bomb_item":
            self._render_bomb_item(screen, cx, ry, rw, rh)
        else:
            # Fallback
            pygame.draw.rect(screen, color, (int(cx - rw/2), int(ry), int(rw), int(rh)))

    def _render_health_pack(self, screen: pygame.Surface, cx: float, y: float, rw: float, rh: float) -> None:
        """Render a health pack item."""
        size = rw
        rect_w = size * 0.8
        rect_h = size * 0.6
        kit_y = y + size * 0.4
        pygame.draw.rect(
            screen,
            (220, 220, 220),
            (int(cx - rect_w / 2), int(kit_y), int(rect_w), int(rect_h)),
            border_radius=4,
        )
        cross_thick = rect_w * 0.2
        pygame.draw.rect(
            screen,
            (200, 0, 0),
            (int(cx - cross_thick / 2), int(kit_y + 5), int(cross_thick), int(rect_h - 10)),
        )
        pygame.draw.rect(
            screen,
            (200, 0, 0),
            (
                int(cx - rect_w / 2 + 5),
                int(kit_y + rect_h / 2 - cross_thick / 2),
                int(rect_w - 10),
                int(cross_thick),
            ),
        )

    def _render_ammo_box(self, screen: pygame.Surface, cx: float, y: float, rw: float, rh: float) -> None:
        """Render an ammo box item."""
        size = rw
        rect_w = size * 0.8
        rect_h = size * 0.6
        box_y = y + size * 0.4
        rect = (int(cx - rect_w / 2), int(box_y), int(rect_w), int(rect_h))
        pygame.draw.rect(screen, (100, 100, 50), rect)
        pygame.draw.rect(
            screen,
            (200, 200, 0),
            (int(cx - rect_w / 2 + 2), int(box_y + 2), int(rect_w - 4), int(rect_h - 4)),
        )

    def _render_bomb_item(self, screen: pygame.Surface, cx: float, y: float, rw: float, rh: float) -> None:
        """Render a bomb item."""
        size = rw
        r = size * 0.4
        cy = y + size * 0.6
        pygame.draw.circle(screen, (30, 30, 30), (int(cx), int(cy)), int(r))
        # Fuse
        start_fuse = (int(cx), int(cy - r))
        end_fuse = (int(cx + r / 2), int(cy - r * 1.5))
        pygame.draw.line(screen, (200, 150, 0), start_fuse, end_fuse, 2)
        if random.random() < 0.5:
            spark_pos = (int(cx + r / 2), int(cy - r * 1.5))
            pygame.draw.circle(screen, (255, 100, 0), spark_pos, 2)
