from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from .base import BaseBotStyleRenderer

if TYPE_CHECKING:
    from ..config import RaycasterConfig
    from ..interfaces import Bot


class MinigunnerStyleRenderer(BaseBotStyleRenderer):
    """Minigunner visual style renderer."""

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
        """Render the minigunner enemy visual style."""
        body_y = ry + rh * 0.2
        self._render_armor(screen, cx, ry, rw, rh, body_y)
        self._render_minigun_weapon(screen, bot, cx, rw, rh, body_y)

    def _render_armor(
        self,
        screen: pygame.Surface,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        body_y: float,
    ) -> None:
        """Draw the body armor plate, helmet, and red visor stripe."""
        pygame.draw.rect(
            screen,
            (50, 50, 70),
            (int(cx - rw / 2), int(body_y), int(rw), int(rh * 0.5)),
        )
        head_size = rw * 0.7
        head_x = cx - head_size / 2
        head_y = ry
        pygame.draw.rect(
            screen,
            (30, 30, 40),
            (int(head_x), int(head_y), int(head_size), int(head_size)),
        )
        pygame.draw.rect(
            screen,
            (255, 0, 0),
            (int(head_x + 5), int(head_y + 10), int(head_size - 10), 5),
        )

    def _render_minigun_weapon(
        self,
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        rw: float,
        rh: float,
        body_y: float,
    ) -> None:
        """Draw the minigun barrel block and muzzle flash when shooting."""
        weapon_w = rw * 1.2
        weapon_h = rh * 0.2
        wx = cx - weapon_w / 2
        wy = body_y + rh * 0.2
        pygame.draw.rect(
            screen, (20, 20, 20), (int(wx), int(wy), int(weapon_w), int(weapon_h))
        )
        if getattr(bot, "shoot_animation", 0) > 0:
            pygame.draw.circle(
                screen,
                (255, 255, 0),
                (int(wx), int(wy + weapon_h / 2)),
                5 + random.randint(0, 5),
            )
