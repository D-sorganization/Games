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
            screen, color, (int(cx), int(head_y + head_size / 2)), int(head_size / 2)
        )

        # Face
        eye_r = head_size * 0.15
        white = (255, 255, 255)
        black = (0, 0, 0)

        pygame.draw.circle(
            screen,
            white,
            (int(cx - head_size * 0.2), int(head_y + head_size * 0.4)),
            int(eye_r),
        )
        pygame.draw.circle(
            screen,
            white,
            (int(cx + head_size * 0.2), int(head_y + head_size * 0.4)),
            int(eye_r),
        )

        # Pupils - dilated
        pygame.draw.circle(
            screen,
            black,
            (int(cx - head_size * 0.2), int(head_y + head_size * 0.4)),
            int(eye_r * 0.6),
        )
        pygame.draw.circle(
            screen,
            black,
            (int(cx + head_size * 0.2), int(head_y + head_size * 0.4)),
            int(eye_r * 0.6),
        )

        # Mouth
        if getattr(bot, "mouth_open", False):
            pygame.draw.circle(
                screen,
                (50, 0, 0),
                (int(cx), int(head_y + head_size * 0.75)),
                int(head_size * 0.1),
            )
        else:
            # Small flat mouth
            pygame.draw.line(
                screen,
                (50, 0, 0),
                (int(cx - 5), int(head_y + head_size * 0.75)),
                (int(cx + 5), int(head_y + head_size * 0.75)),
                2,
            )
