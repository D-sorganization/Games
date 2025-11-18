"""
Enemy characters for Wizard of Wor.
"""
import pygame
import random
from constants import *
from bullet import Bullet


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
        self.rect = pygame.Rect(x - ENEMY_SIZE // 2, y - ENEMY_SIZE // 2,
                               ENEMY_SIZE, ENEMY_SIZE)
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.move_timer = 0
        self.direction_change_interval = random.randint(30, 90)
        self.shoot_timer = random.randint(60, 180)
        self.can_shoot = True

    def update(self, dungeon, player_pos):
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

        # Update shoot timer
        self.shoot_timer -= 1

    def try_shoot(self):
        """Try to shoot a bullet."""
        if self.can_shoot and self.shoot_timer <= 0 and self.alive:
            self.shoot_timer = random.randint(90, 240)
            bullet_x = self.x + self.direction[0] * (ENEMY_SIZE // 2 + 5)
            bullet_y = self.y + self.direction[1] * (ENEMY_SIZE // 2 + 5)
            return Bullet(bullet_x, bullet_y, self.direction, RED, False)
        return None

    def take_damage(self):
        """Enemy takes damage."""
        self.alive = False
        return self.points

    def draw(self, screen):
        """Draw the enemy."""
        if self.alive and self.visible:
            pygame.draw.rect(screen, self.color, self.rect)
            # Add a darker border
            pygame.draw.rect(screen, (max(0, self.color[0] - 50),
                                     max(0, self.color[1] - 50),
                                     max(0, self.color[2] - 50)), self.rect, 2)


class Burwor(Enemy):
    """Slowest and weakest enemy."""

    def __init__(self, x, y):
        super().__init__(x, y, BURWOR_SPEED, PURPLE, BURWOR_POINTS, 'burwor')
        self.can_shoot = False  # Burwors don't shoot


class Garwor(Enemy):
    """Medium speed enemy that can shoot."""

    def __init__(self, x, y):
        super().__init__(x, y, GARWOR_SPEED, ORANGE, GARWOR_POINTS, 'garwor')


class Thorwor(Enemy):
    """Fast enemy that can shoot."""

    def __init__(self, x, y):
        super().__init__(x, y, THORWOR_SPEED, RED, THORWOR_POINTS, 'thorwor')


class Worluk(Enemy):
    """Special invisible enemy that appears occasionally."""

    def __init__(self, x, y):
        super().__init__(x, y, WORLUK_SPEED, CYAN, WORLUK_POINTS, 'worluk')
        self.visible = False
        self.blink_timer = 0
        self.can_shoot = False

    def update(self, dungeon, player_pos):
        """Update Worluk with special visibility behavior."""
        super().update(dungeon, player_pos)

        # Blink in and out of visibility
        self.blink_timer += 1
        if self.blink_timer >= 30:
            self.blink_timer = 0
            self.visible = not self.visible


class Wizard(Enemy):
    """The titular Wizard of Wor - appears when few enemies remain."""

    def __init__(self, x, y):
        super().__init__(x, y, WIZARD_SPEED, YELLOW, WIZARD_POINTS, 'wizard')
        self.appearance_timer = 300  # Frames before appearing

    def update(self, dungeon, player_pos):
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

    def draw(self, screen):
        """Draw the wizard (only after appearance timer)."""
        if self.appearance_timer <= 0:
            super().draw(screen)
