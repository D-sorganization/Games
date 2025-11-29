"""
Enemy characters for Wizard of Wor.
"""

import math
import random
from typing import Any

import pygame
from bullet import Bullet
from constants import *


class Enemy:
    """Base enemy class."""

    def __init__(self, x, y, speed, color, points, enemy_type):
        """Initialize enemy."""
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.points = points
        self.enemy_type = enemy_type
        self.alive = True
        self.visible = True  # Some enemies can become invisible
        self.rect = pygame.Rect(
            x - ENEMY_SIZE // 2,
            y - ENEMY_SIZE // 2,
            ENEMY_SIZE,
            ENEMY_SIZE,
        )
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.move_timer = 0
        self.direction_change_interval = random.randint(30, 90)
        self.shoot_timer = random.randint(60, 180)
        self.can_shoot = True
        self.animation_timer = 0
        self.step_frame = 0
        self.invisibility_cooldown = 0
        self.invisibility_time = 0
        self.spawn_flash = 36

    def update(self, dungeon: Any, player_pos: tuple[float, float]) -> None:
        """Update enemy position and behavior."""
        if not self.alive:
            return

        # Store old position
        old_x, old_y = self.x, self.y

        # Randomly change direction
        self.move_timer += 1
        if self.move_timer >= self.direction_change_interval:
            self.move_timer = 0
            self.direction_change_interval = random.randint(30, 90)

            # Sometimes move toward player
            if random.random() < 0.3:  # 30% chance to chase player
                dx = player_pos[0] - self.x
                dy = player_pos[1] - self.y

                if abs(dx) > abs(dy):
                    self.direction = RIGHT if dx > 0 else LEFT
                else:
                    self.direction = DOWN if dy > 0 else UP
            else:
                self.direction = random.choice([UP, DOWN, LEFT, RIGHT])

        # Move in current direction
        self.x += self.direction[0] * self.speed
        self.y += self.direction[1] * self.speed

        # Update rect
        self.rect.x = self.x - ENEMY_SIZE // 2
        self.rect.y = self.y - ENEMY_SIZE // 2

        # Check collision with walls
        if not dungeon.can_move_to(self.rect):
            self.x, self.y = old_x, old_y
            self.rect.x = self.x - ENEMY_SIZE // 2
            self.rect.y = self.y - ENEMY_SIZE // 2
            # Change direction when hitting wall
            self.direction = random.choice([UP, DOWN, LEFT, RIGHT])

        # Advance walk animation
        if (self.x, self.y) != (old_x, old_y):
            self.animation_timer += 1
            if self.animation_timer >= ENEMY_ANIMATION_SPEED:
                self.animation_timer = 0
                self.step_frame = 1 - self.step_frame

        # Update shoot timer
        self.shoot_timer -= 1

        # Handle invisibility cadence for stealthy foes
        if self.invisibility_time > 0:
            self.invisibility_time -= 1
            self.visible = (
                self.invisibility_time % INVISIBILITY_FLICKER_PERIOD
                < INVISIBILITY_FLICKER_ON_FRAMES
            )
            if self.invisibility_time == 0:
                self.visible = True
                self.invisibility_cooldown = INVISIBILITY_INTERVAL
        elif self.enemy_type in {"garwor", "thorwor", "worluk"}:
            if self.invisibility_cooldown > 0:
                self.invisibility_cooldown -= 1
            else:
                self.invisibility_time = INVISIBILITY_DURATION
                self.visible = False
        else:
            self.visible = True

        if self.spawn_flash > 0:
            self.spawn_flash -= 1

    def try_shoot(self) -> Bullet | None:
        """Try to shoot a bullet."""
        if self.can_shoot and self.shoot_timer <= 0 and self.alive:
            self.shoot_timer = random.randint(90, 240)
            bullet_x = self.x + self.direction[0] * (ENEMY_SIZE // 2 + 5)
            bullet_y = self.y + self.direction[1] * (ENEMY_SIZE // 2 + 5)
            return Bullet(bullet_x, bullet_y, self.direction, RED, False)
        return None

    def take_damage(self) -> int:
        """Enemy takes damage."""
        self.alive = False
        return self.points

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the enemy."""
        if self.alive and self.visible:
            body_rect = pygame.Rect(self.rect)
            body_rect.inflate_ip(-ENEMY_OUTLINE, -ENEMY_OUTLINE)

            # Glowing aura
            aura_radius = ENEMY_GLOW
            aura_surface = pygame.Surface(
                (body_rect.width + aura_radius * 2, body_rect.height + aura_radius * 2),
                pygame.SRCALPHA,
            )
            flash = 180 if self.spawn_flash > 0 else 120
            aura_alpha = flash + 40 * math.sin(pygame.time.get_ticks() / 180)
            pygame.draw.ellipse(
                aura_surface,
                (self.color[0], self.color[1], self.color[2], int(aura_alpha)),
                aura_surface.get_rect(),
            )
            screen.blit(
                aura_surface,
                (
                    body_rect.centerx - aura_surface.get_width() // 2,
                    body_rect.centery - aura_surface.get_height() // 2,
                ),
            )

            pygame.draw.ellipse(screen, self.color, body_rect)

            # Feet positions to mimic stomping
            foot_offset = 3 if self.step_frame else -3
            left_foot = (self.x - 5, self.y + foot_offset)
            right_foot = (self.x + 5, self.y - foot_offset)
            pygame.draw.circle(screen, self.color, left_foot, 4)
            pygame.draw.circle(screen, self.color, right_foot, 4)

            # Eye slit to hint direction
            eye_width = 8
            eye_height = 4
            eye_rect = pygame.Rect(0, 0, eye_width, eye_height)
            eye_rect.center = (
                self.x + self.direction[0] * 5,
                self.y + self.direction[1] * 5,
            )
            pygame.draw.rect(screen, BLACK, eye_rect, border_radius=2)


class Burwor(Enemy):
    """Slowest and weakest enemy."""

    def __init__(self, x: float, y: float) -> None:
        """Initialize Burwor enemy at position"""
        super().__init__(x, y, BURWOR_SPEED, PURPLE, BURWOR_POINTS, "burwor")
        self.can_shoot = False  # Burwors don't shoot


class Garwor(Enemy):
    """Medium speed enemy that can shoot."""

    def __init__(self, x: float, y: float) -> None:
        """Initialize Garwor enemy at position"""
        super().__init__(x, y, GARWOR_SPEED, ORANGE, GARWOR_POINTS, "garwor")


class Thorwor(Enemy):
    """Fast enemy that can shoot."""

    def __init__(self, x: float, y: float) -> None:
        """Initialize Thorwor enemy at position"""
        super().__init__(x, y, THORWOR_SPEED, RED, THORWOR_POINTS, "thorwor")


class Worluk(Enemy):
    """Special invisible enemy that appears occasionally."""

    def __init__(self, x: float, y: float) -> None:
        """Initialize Worluk enemy at position"""
        super().__init__(x, y, WORLUK_SPEED, CYAN, WORLUK_POINTS, "worluk")
        self.visible = False
        self.can_shoot = False
        self.invisibility_cooldown = INVISIBILITY_INTERVAL // 2
        self.invisibility_time = INVISIBILITY_DURATION // 2

    def update(self, dungeon: Any, player_pos: tuple[float, float]) -> None:
        """Update Worluk with special visibility behavior."""
        super().update(dungeon, player_pos)


class Wizard(Enemy):
    """The titular Wizard of Wor - appears when few enemies remain."""

    def __init__(self, x: float, y: float) -> None:
        """Initialize Wizard enemy at position"""
        super().__init__(x, y, WIZARD_SPEED, YELLOW, WIZARD_POINTS, "wizard")
        self.appearance_timer = 300  # Frames before appearing

    def update(self, dungeon: Any, player_pos: tuple[float, float]) -> None:
        """Update Wizard with special appearance behavior."""
        if self.appearance_timer > 0:
            self.appearance_timer -= 1
            return

        super().update(dungeon, player_pos)

        # Wizard is more aggressive in chasing player
        if random.random() < 0.5:
            dx = player_pos[0] - self.x
            dy = player_pos[1] - self.y

            if abs(dx) > abs(dy):
                self.direction = RIGHT if dx > 0 else LEFT
            else:
                self.direction = DOWN if dy > 0 else UP

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the wizard (only after appearance timer)."""
        if self.appearance_timer <= 0:
            super().draw(screen)
