import pygame
from typing import Tuple
from . import constants as C

class Button:
    """UI Button"""

    HOVER_BRIGHTNESS_OFFSET = 30  # Brightness increase for hover state

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color: Tuple[int, int, int],
    ):
        """Initialize button"""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self._color = color
        self.hover_color = tuple(min(255, c + self.HOVER_BRIGHTNESS_OFFSET) for c in color)
        self.hovered = False

    @property
    def color(self) -> Tuple[int, int, int]:
        """Get button color"""
        return self._color

    @color.setter
    def color(self, value: Tuple[int, int, int]) -> None:
        """Set button color and update hover color"""
        self._color = value
        self.hover_color = tuple(min(255, c + self.HOVER_BRIGHTNESS_OFFSET) for c in value)

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw button"""
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, C.WHITE, self.rect, 3)

        text_surface = font.render(self.text, True, C.WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def update(self, mouse_pos: Tuple[int, int]) -> None:
        """Update button hover state"""
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos: Tuple[int, int]) -> bool:
        """Check if button was clicked"""
        return self.rect.collidepoint(mouse_pos)
