"""
Bullet/Projectile system for Wizard of Wor.
"""
import pygame
from typing import Tuple, Any
from constants import *


class Bullet:
    """Represents a bullet shot by player or enemy."""

    def __init__(self, x, y, direction, color=YELLOW, is_player_bullet=True):
        """Initialize bullet at position with direction."""
        self.x = x
        self.y = y
        self.direction = direction
        self.color = color
        self.is_player_bullet = is_player_bullet
        self.active = True
        self.rect = pygame.Rect(x - BULLET_SIZE // 2, y - BULLET_SIZE // 2,
                                BULLET_SIZE, BULLET_SIZE)

    def update(self, dungeon: Any) -> None:
        """Update bullet position."""
        if not self.active:
            return

        # Move bullet
        self.x += self.direction[0] * BULLET_SPEED
        self.y += self.direction[1] * BULLET_SPEED

        # Update rect
        self.rect.x = self.x - BULLET_SIZE // 2
        self.rect.y = self.y - BULLET_SIZE // 2

        # Check if bullet hit wall or went out of bounds
        if dungeon.is_wall(self.x, self.y):
            self.active = False
        elif self.x < GAME_AREA_X:
            self.active = False
        elif self.x > GAME_AREA_X + GAME_AREA_WIDTH:
            self.active = False
        elif self.y < GAME_AREA_Y:
            self.active = False
        elif self.y > GAME_AREA_Y + GAME_AREA_HEIGHT:
            self.active = False

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the bullet."""
        if self.active:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)),
                             BULLET_SIZE // 2)
