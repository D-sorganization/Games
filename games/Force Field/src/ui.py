from __future__ import annotations

from typing import List, Tuple, Dict, Union
import random
import math

import pygame

from . import constants as C  # noqa: N812


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


class BloodButton(Button):
    """Button with a dripping blood effect"""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color: Tuple[int, int, int] = (139, 0, 0),  # Dark Red default
    ):
        """Initialize BloodButton"""
        super().__init__(x, y, width, height, text, color)
        self.drips: List[Dict[str, Union[float, int]]] = []
        self._generate_drips()
        self.pulse_timer = 0.0

    def _generate_drips(self) -> None:
        """Generate random blood drips"""
        self.drips = []
        # Create drips along the bottom edge
        # Spaced every 15 pixels with +/-5 variation
        num_drips = self.rect.width // 15
        for i in range(num_drips):
            x_offset = i * 15 + random.randint(-5, 5)
            if 0 <= x_offset <= self.rect.width:
                self.drips.append({
                    "x": x_offset,
                    "length": random.randint(5, 20),
                    "max_length": random.randint(15, 40),
                    "speed": random.uniform(0.2, 0.5),
                    "width": random.randint(6, 12),
                    "timer": random.uniform(0, math.pi * 2)  # Phase offset for sine wave animation (not a countdown timer)

                })

    def update(self, mouse_pos: Tuple[int, int]) -> None:
        """Update button state and animation"""
        super().update(mouse_pos)
        self.pulse_timer += 0.1
        
        # Animate drips
        for drip in self.drips:
            # Oscillate length
            drip["length"] = drip["max_length"] * (0.7 + 0.3 * math.sin(self.pulse_timer * drip["speed"] + drip["timer"]))

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw blood button"""
        # Determine color (pulse if hovered)
        base_color = self.color
        if self.hovered:
            # Pulse brighter red
            pulse = (math.sin(self.pulse_timer * 2) + 1) / 2  # 0 to 1
            r = min(255, base_color[0] + int(50 * pulse))
            current_color = (r, base_color[1], base_color[2])
        else:
            current_color = base_color

        # Draw drips first (behind the main rect effectively, or joined)
        # We want them to look like part of the button
        
        # Main body
        pygame.draw.rect(screen, current_color, self.rect, border_radius=5)
        
        # Draw drips
        for drip in self.drips:
            drip_x = self.rect.x + drip["x"]
            drip_y = self.rect.bottom
            drip_h = drip["length"]
            drip_w = drip["width"]
            
            # Draw rect for the flow
            pygame.draw.rect(screen, current_color, (drip_x - drip_w//2, drip_y - 2, drip_w, drip_h + 2))
            # Draw circle for the drop at end
            pygame.draw.circle(screen, current_color, (int(drip_x), int(drip_y + drip_h)), int(drip_w // 2))

        # Add a "glossy" highlight on top
        highlight_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.rect.height // 2)
        highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(highlight_surf, (255, 255, 255, 30), highlight_surf.get_rect(), border_top_left_radius=5, border_top_right_radius=5)
        screen.blit(highlight_surf, highlight_rect)

        # Border
        pygame.draw.rect(screen, (50, 0, 0), self.rect, 2, border_radius=5)

        # Text with shadow
        text_surf = font.render(self.text, True, C.WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        
        # Shadow
        shadow_surf = font.render(self.text, True, (0, 0, 0))
        shadow_rect = text_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        screen.blit(shadow_surf, shadow_rect)
        
        screen.blit(text_surf, text_rect)
