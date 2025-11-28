"""
Player character for Wizard of Wor.
"""
from typing import Any

import pygame
from bullet import Bullet
from constants import *


class Player:
    """Player character that can move and shoot."""

    def __init__(self, x, y):
        """Initialize player at position."""
        self.x = x
        self.y = y
        self.direction = RIGHT
        self.speed = PLAYER_SPEED
        self.color = GREEN
        self.alive = True
        self.rect = pygame.Rect(x - PLAYER_SIZE // 2, y - PLAYER_SIZE // 2,
                               PLAYER_SIZE, PLAYER_SIZE)
        self.shoot_cooldown = 0
        self.shoot_delay = 15  # Frames between shots

    def update(self, keys: Any, dungeon: Any) -> None:
        """Update player based on keyboard input."""
        if not self.alive:
            return

        # Store old position
        old_x, old_y = self.x, self.y

        # Movement
        moved = False
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.y -= self.speed
            self.direction = UP
            moved = True
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.y += self.speed
            self.direction = DOWN
            moved = True

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.x -= self.speed
            self.direction = LEFT
            moved = True
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.x += self.speed
            self.direction = RIGHT
            moved = True

        # Update rect
        self.rect.x = self.x - PLAYER_SIZE // 2
        self.rect.y = self.y - PLAYER_SIZE // 2

        # Check collision with walls
        if moved and not dungeon.can_move_to(self.rect):
            self.x, self.y = old_x, old_y
            self.rect.x = self.x - PLAYER_SIZE // 2
            self.rect.y = self.y - PLAYER_SIZE // 2

        # Update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def shoot(self) -> Bullet | None:
        """Create a bullet if cooldown allows."""
        if self.shoot_cooldown == 0 and self.alive:
            self.shoot_cooldown = self.shoot_delay
            # Spawn bullet slightly in front of player
            bullet_x = self.x + self.direction[0] * (PLAYER_SIZE // 2 + 5)
            bullet_y = self.y + self.direction[1] * (PLAYER_SIZE // 2 + 5)
            return Bullet(bullet_x, bullet_y, self.direction, YELLOW, True)
        return None

    def take_damage(self) -> None:
        """Player takes damage."""
        self.alive = False

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the player."""
        if self.alive:
            # Draw player body
            pygame.draw.rect(screen, self.color, self.rect)

            # Draw direction indicator
            indicator_offset = 8
            if self.direction == UP:
                indicator_pos = (self.x, self.y - indicator_offset)
            elif self.direction == DOWN:
                indicator_pos = (self.x, self.y + indicator_offset)
            elif self.direction == LEFT:
                indicator_pos = (self.x - indicator_offset, self.y)
            else:  # RIGHT
                indicator_pos = (self.x + indicator_offset, self.y)

            pygame.draw.circle(screen, WHITE, indicator_pos, 3)
