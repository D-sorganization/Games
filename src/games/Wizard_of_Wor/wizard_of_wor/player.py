"""
Player character for Wizard of Wor.
"""

import math
from typing import Any

import pygame
from bullet import Bullet
from constants import (
    BLACK,
    DOWN,
    FOOTSTEP_INTERVAL,
    GREEN,
    LEFT,
    PALE_YELLOW,
    PLAYER_ANIMATION_SPEED,
    PLAYER_SHIELD_FLASH,
    PLAYER_SIZE,
    PLAYER_SPEED,
    RIGHT,
    UP,
    WHITE,
    YELLOW,
)
from effects import Footstep, MuzzleFlash


class Player:
    """Player character that can move and shoot."""

    def __init__(self, x: float, y: float) -> None:
        """Initialize player at position."""
        self.x = x
        self.y = y
        self.direction = RIGHT
        self.speed = PLAYER_SPEED
        self.color = GREEN
        self.alive = True
        self.rect = pygame.Rect(
            x - PLAYER_SIZE // 2,
            y - PLAYER_SIZE // 2,
            PLAYER_SIZE,
            PLAYER_SIZE,
        )
        self.shoot_cooldown = 0
        self.shoot_delay = 15  # Frames between shots
        self.animation_timer = 0
        self.step_frame = 0
        self.invulnerable_timer = 0
        self.footstep_timer = 0

    def update(self, keys: Any, dungeon: Any, effects: list[Any] | None = None) -> None:
        """Update player movement, animation, and timers."""
        if not self.alive:
            return
        old_x, old_y = self.x, self.y
        moved = self._apply_movement(keys)
        self._sync_rect()
        if moved and not dungeon.can_move_to(self.rect):
            self.x, self.y = old_x, old_y
            self._sync_rect()
        self._update_walk_animation(moved, effects)
        self._tick_timers()

    def _apply_movement(self, keys: Any) -> bool:
        """Apply directional key presses, return True if the player moved."""
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
        return moved

    def _sync_rect(self) -> None:
        """Update the collision rect to match the current x/y position."""
        self.rect.x = self.x - PLAYER_SIZE // 2
        self.rect.y = self.y - PLAYER_SIZE // 2

    def _update_walk_animation(self, moved: bool, effects: list[Any] | None) -> None:
        """Advance the walk animation frame and emit footstep effects."""
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

    def _tick_timers(self) -> None:
        """Decrement footstep, shoot-cooldown, and invulnerability timers."""
        if self.footstep_timer > 0:
            self.footstep_timer -= 1
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
        """Draw the player body, shield, visor, legs, and direction indicator."""
        if not self.alive:
            return
        body_rect = pygame.Rect(self.rect)
        body_rect.inflate_ip(-4, -6)
        self._draw_shield_glow(screen, body_rect)
        pygame.draw.rect(screen, self.color, body_rect, border_radius=6)
        self._draw_visor(screen, body_rect)
        self._draw_legs(screen)
        self._draw_direction_indicator(screen)

    def _draw_shield_glow(self, screen: pygame.Surface, body_rect: pygame.Rect) -> None:
        """Draw the pulsing yellow shield glow when invulnerable."""
        if self.invulnerable_timer <= 0:
            return
        flash = 120 + 80 * math.sin(self.invulnerable_timer / PLAYER_SHIELD_FLASH)
        glow_surface = pygame.Surface(
            (body_rect.width + 10, body_rect.height + 10),
            pygame.SRCALPHA,
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

    def _draw_visor(self, screen: pygame.Surface, body_rect: pygame.Rect) -> None:
        """Draw the narrow black visor strip across the top of the body."""
        visor_width = body_rect.width // 2
        visor_rect = pygame.Rect(
            body_rect.centerx - visor_width // 2,
            body_rect.top + 2,
            visor_width,
            6,
        )
        pygame.draw.rect(screen, BLACK, visor_rect, border_radius=2)

    def _draw_legs(self, screen: pygame.Surface) -> None:
        """Draw the two animated walking legs."""
        leg_offset = 3 if self.step_frame else -3
        if self.direction in (UP, DOWN):
            left_leg = (self.x - 4, self.y + leg_offset)
            right_leg = (self.x + 4, self.y - leg_offset)
        else:
            left_leg = (self.x + leg_offset, self.y + 4)
            right_leg = (self.x - leg_offset, self.y - 4)
        pygame.draw.line(
            screen, self.color, left_leg, (left_leg[0], left_leg[1] + 6), 3
        )
        pygame.draw.line(
            screen, self.color, right_leg, (right_leg[0], right_leg[1] + 6), 3
        )

    def _draw_direction_indicator(self, screen: pygame.Surface) -> None:
        """Draw the small white dot indicating the player's facing direction."""
        indicator_offset = 9
        direction_map = {
            UP: (self.x, self.y - indicator_offset),
            DOWN: (self.x, self.y + indicator_offset),
            LEFT: (self.x - indicator_offset, self.y),
            RIGHT: (self.x + indicator_offset, self.y),
        }
        indicator_pos = direction_map.get(
            self.direction, (self.x + indicator_offset, self.y)
        )
        pygame.draw.circle(screen, WHITE, indicator_pos, 3)
