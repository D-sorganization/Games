from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseBotStyleRenderer


class BotStyleRendererFactory:
    """Factory for registering and retrieving bot renderers."""

    _renderers: dict[str, BaseBotStyleRenderer] = {}

    @classmethod
    def register_renderer(cls, name: str, renderer: BaseBotStyleRenderer) -> None:
        """Register a renderer for a specific style."""
        cls._renderers[name] = renderer

    @classmethod
    def get_renderer(cls, name: str) -> BaseBotStyleRenderer | None:
        """Get a renderer by name."""
        return cls._renderers.get(name)
