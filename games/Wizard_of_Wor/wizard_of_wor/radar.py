"""
Radar system for Wizard of Wor.
"""

from typing import Any

import pygame
from constants import (
    BLACK,
    CYAN,
    GAME_AREA_HEIGHT,
    GAME_AREA_WIDTH,
    GAME_AREA_X,
    GAME_AREA_Y,
    GRAY,
    GREEN,
    RADAR_PING_INTERVAL,
    RADAR_SIZE,
    RADAR_SWEEP_SPEED,
    RADAR_X,
    RADAR_Y,
    SLATE,
    WHITE,
)


class Radar:
    """Displays enemy positions on a mini-map."""

    def __init__(self) -> None:
        """Initialize radar."""
        self.x = RADAR_X
        self.y = RADAR_Y
        self.size = RADAR_SIZE
        self.sweep_angle = 0
        self.ping_timer = RADAR_PING_INTERVAL

    def update(self) -> None:
        """Advance radar sweep angle."""
        self.sweep_angle = (self.sweep_angle + RADAR_SWEEP_SPEED) % 360
        self.ping_timer -= 1
        if self.ping_timer <= 0:
            self.ping_timer = RADAR_PING_INTERVAL

    def draw(self, screen: pygame.Surface, enemies: list[Any], player: Any) -> None:
        """Draw the radar with enemy positions."""
        # Draw radar background with cross hairs
        background = pygame.Rect(self.x, self.y, self.size, self.size)
        pygame.draw.rect(screen, BLACK, background)
        pygame.draw.rect(screen, CYAN, background, 2)
        pygame.draw.line(
            screen,
            SLATE,
            (self.x, self.y + self.size // 2),
            (self.x + self.size, self.y + self.size // 2),
        )
        pygame.draw.line(
            screen,
            SLATE,
            (self.x + self.size // 2, self.y),
            (self.x + self.size // 2, self.y + self.size),
        )

        # Sweep line for arcade-style radar
        center = (self.x + self.size // 2, self.y + self.size // 2)
        sweep_length = self.size // 2
        sweep_vector = pygame.math.Vector2(1, 0).rotate(self.sweep_angle)
        sweep_end = (
            int(center[0] + sweep_vector.x * sweep_length),
            int(center[1] + sweep_vector.y * sweep_length),
        )
        pygame.draw.line(screen, CYAN, center, sweep_end, 2)

        # Periodic ping ring
        if self.ping_timer < RADAR_PING_INTERVAL // 2:
            half_interval = RADAR_PING_INTERVAL / 2
            ring_progress = 1 - (self.ping_timer / half_interval)
            ring_radius = int(ring_progress * (self.size // 2))
            ring_alpha = max(40, 150 - int(ring_progress * 150))
            if ring_radius > 0:
                ring_surface = pygame.Surface(
                    (ring_radius * 2 + 4, ring_radius * 2 + 4),
                    pygame.SRCALPHA,
                )
                ring_center = (
                    ring_surface.get_width() // 2,
                    ring_surface.get_height() // 2,
                )
                pygame.draw.circle(
                    ring_surface,
                    (*CYAN, ring_alpha),
                    ring_center,
                    ring_radius,
                    width=2,
                )
                screen.blit(
                    ring_surface,
                    (center[0] - ring_center[0], center[1] - ring_center[1]),
                )

        # Draw label
        font = pygame.font.Font(None, 20)
        label = font.render("RADAR", True, WHITE)
        screen.blit(label, (self.x + 5, self.y - 25))

        # Calculate scale factor
        scale_x = self.size / GAME_AREA_WIDTH
        scale_y = self.size / GAME_AREA_HEIGHT

        # Draw player position
        if player.alive:
            player_radar_x = self.x + (player.x - GAME_AREA_X) * scale_x
            player_radar_y = self.y + (player.y - GAME_AREA_Y) * scale_y
            pygame.draw.circle(
                screen,
                GREEN,
                (int(player_radar_x), int(player_radar_y)),
                3,
            )

        # Draw enemy positions
        for enemy in enemies:
            if enemy.alive and enemy.visible:  # Only show visible enemies
                enemy_radar_x = self.x + (enemy.x - GAME_AREA_X) * scale_x
                enemy_radar_y = self.y + (enemy.y - GAME_AREA_Y) * scale_y

                # Use enemy color
                pygame.draw.circle(
                    screen,
                    enemy.color,
                    (int(enemy_radar_x), int(enemy_radar_y)),
                    2,
                )
