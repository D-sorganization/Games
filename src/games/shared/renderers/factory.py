from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    import pygame

    from ..config import RaycasterConfig
    from ..interfaces import Bot
    from .base import BaseBotStyleRenderer


class BotStyleRendererFactory:
    """Factory for managing and accessing bot style renderers."""

    _renderers: ClassVar[dict[str, BaseBotStyleRenderer]] = {}

    @classmethod
    def register_renderer(cls, style_name: str, renderer: BaseBotStyleRenderer) -> None:
        """Register a renderer for a specific style.

        Args:
            style_name: The name of the visual style (e.g., 'monster', 'beast').
            renderer: The renderer instance to handle this style.
        """
        cls._renderers[style_name] = renderer

    @classmethod
    def get_renderer(cls, style_name: str) -> BaseBotStyleRenderer | None:
        """Get a renderer for a specific style.

        Args:
            style_name: The name of the visual style.

        Returns:
            The requested renderer or None if not found.
        """
        return cls._renderers.get(style_name)

    @classmethod
    def render(
        cls,
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        color: tuple[int, int, int],
        config: RaycasterConfig,
    ) -> None:
        """Delegate rendering to the appropriate specialized renderer.

        Determines the visual style from the bot's type data and delegates
        to the registered renderer for that style.
        """
        visual_style = bot.type_data.get("visual_style", "monster")
        renderer = cls.get_renderer(visual_style)

        if renderer:
            renderer.render(screen, bot, cx, ry, rw, rh, color, config)
