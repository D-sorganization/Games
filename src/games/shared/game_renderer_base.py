"""Base class for game renderers with common initialization."""

from __future__ import annotations

import pygame


class GameRendererBase:
    """Base class for game renderers with common setup."""

    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        """Initialize the game renderer base.

        Args:
            screen: Pygame surface to render to
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Optimization: Shared surface for alpha effects
        size = (screen_width, screen_height)
        self.effects_surface = pygame.Surface(size, pygame.SRCALPHA)
