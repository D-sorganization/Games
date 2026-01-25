from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import pygame

if TYPE_CHECKING:
    from ..config import RaycasterConfig
    from ..interfaces import Bot


class BaseBotStyleRenderer(Protocol):
    """Protocol for specific bot visual style renderers."""

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
        """Render the bot sprite."""
        ...
