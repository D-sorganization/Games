"""
Player character for Wizard of Wor.
"""

import math
from typing import Any

import pygame
from bullet import Bullet
from constants import *
from effects import Footstep, MuzzleFlash


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
        self.rect = pygame.Rect(
            x - PLAYER_SIZE // 2, y - PLAYER_SIZE // 2, PLAYER_SIZE, PLAYER_SIZE,
        )
        self.shoot_cooldown = 0
        self.shoot_delay = 15  # Frames between shots
        self.animation_timer = 0
        self.step_frame = 0
        self.invulnerable_timer = 0
        self.footstep_timer = 0

    def update(self, keys: Any, dungeon: Any, effects: list[Any] | None = None) -> None:
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

        # Update walk animation
        if moved:
            self.animation_timer += 1
            if self.animation_timer >= PLAYER_ANIMATION_SPEED:
                self.animation_timer = 0
                self.step_frame = 1 - self.step_frame
            if self.footstep_timer <= 0 and effects is not None:
                effects.append(Footstep((self.x, self.y), self.color))
                self.footstep_timer = FOOTSTEP_INTERVAL
        else:
            self.animation_timer = 0
            self.step_frame = 0

        if self.footstep_timer > 0:
            self.footstep_timer -= 1

        # Update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1

    def shoot(self) -> tuple[Bullet, MuzzleFlash] | tuple[None, None]:
        """Create a bullet if cooldown allows."""
        if self.shoot_cooldown == 0 and self.alive:
            self.shoot_cooldown = self.shoot_delay
            # Spawn bullet slightly in front of player
            bullet_x = self.x + self.direction[0] * (PLAYER_SIZE // 2 + 5)
            bullet_y = self.y + self.direction[1] * (PLAYER_SIZE // 2 + 5)
            muzzle = MuzzleFlash((bullet_x, bullet_y))
            return Bullet(bullet_x, bullet_y, self.direction, YELLOW, True), muzzle
        return None, None

    def take_damage(self) -> bool:
        """Player takes damage, returns True if actually hurt."""
        if self.invulnerable_timer > 0:
            return False
        self.alive = False
        return True

    def grant_shield(self, frames: int) -> None:
        """Grant temporary invulnerability."""
        self.invulnerable_timer = max(self.invulnerable_timer, frames)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the player."""
        if self.alive:
            body_rect = pygame.Rect(self.rect)
            body_rect.inflate_ip(-4, -6)

            # Shield glow
            if self.invulnerable_timer > 0:
                flash = 120 + 80 * math.sin(self.invulnerable_timer / PLAYER_SHIELD_FLASH)
                glow_surface = pygame.Surface(
                    (body_rect.width + 10, body_rect.height + 10), pygame.SRCALPHA,
                )
                pygame.draw.ellipse(
                    glow_surface,
                    (PALE_YELLOW[0], PALE_YELLOW[1], PALE_YELLOW[2], int(flash)),
                    glow_surface.get_rect(),
                )
                screen.blit(
                    glow_surface,
                    (
                        body_rect.centerx - glow_surface.get_width() // 2,
                        body_rect.centery - glow_surface.get_height() // 2,
                    ),
                )

            pygame.draw.rect(screen, self.color, body_rect, border_radius=6)

            # Visor and armor highlights
            visor_width = body_rect.width // 2
            visor_rect = pygame.Rect(
                body_rect.centerx - visor_width // 2,
                body_rect.top + 2,
                visor_width,
                6,
            )
            pygame.draw.rect(screen, BLACK, visor_rect, border_radius=2)

            # Walking legs
            leg_offset = 3 if self.step_frame else -3
            if self.direction in (UP, DOWN):
                left_leg = (self.x - 4, self.y + leg_offset)
                right_leg = (self.x + 4, self.y - leg_offset)
            else:
                left_leg = (self.x + leg_offset, self.y + 4)
                right_leg = (self.x - leg_offset, self.y - 4)
            pygame.draw.line(
                screen,
                self.color,
                left_leg,
                (left_leg[0], left_leg[1] + 6),
                3,
            )
            pygame.draw.line(
                screen,
                self.color,
                right_leg,
                (right_leg[0], right_leg[1] + 6),
                3,
            )

            # Direction indicator
            indicator_offset = 9
            if self.direction == UP:
                indicator_pos = (self.x, self.y - indicator_offset)
            elif self.direction == DOWN:
                indicator_pos = (self.x, self.y + indicator_offset)
            elif self.direction == LEFT:
                indicator_pos = (self.x - indicator_offset, self.y)
            else:  # RIGHT
                indicator_pos = (self.x + indicator_offset, self.y)

            pygame.draw.circle(screen, WHITE, indicator_pos, 3)
