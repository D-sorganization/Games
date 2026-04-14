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
        """Draw the radar display including background, sweep, ping, and blips."""
        center = (self.x + self.size // 2, self.y + self.size // 2)
        scale_x = self.size / GAME_AREA_WIDTH
        scale_y = self.size / GAME_AREA_HEIGHT
        self._draw_background(screen)
        self._draw_sweep(screen, center)
        self._draw_ping_ring(screen, center)
        self._draw_label(screen)
        self._draw_player_blip(screen, player, scale_x, scale_y)
        self._draw_enemy_blips(screen, enemies, scale_x, scale_y)

    def _draw_background(self, screen: pygame.Surface) -> None:
        """Draw the radar background rect and crosshair lines."""
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

    def _draw_sweep(self, screen: pygame.Surface, center: tuple[int, int]) -> None:
        """Draw the rotating sweep line."""
        sweep_length = self.size // 2
        sweep_vector = pygame.math.Vector2(1, 0).rotate(self.sweep_angle)
        sweep_end = (
            int(center[0] + sweep_vector.x * sweep_length),
            int(center[1] + sweep_vector.y * sweep_length),
        )
        pygame.draw.line(screen, CYAN, center, sweep_end, 2)

    def _draw_ping_ring(self, screen: pygame.Surface, center: tuple[int, int]) -> None:
        """Draw the periodic expanding ping ring when active."""
        if self.ping_timer >= RADAR_PING_INTERVAL // 2:
            return
        half_interval = RADAR_PING_INTERVAL / 2
        ring_progress = 1 - (self.ping_timer / half_interval)
        ring_radius = int(ring_progress * (self.size // 2))
        ring_alpha = max(40, 150 - int(ring_progress * 150))
        if ring_radius <= 0:
            return
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

    def _draw_label(self, screen: pygame.Surface) -> None:
        """Draw the RADAR text label above the display."""
        font = pygame.font.Font(None, 20)
        label = font.render("RADAR", True, WHITE)
        screen.blit(label, (self.x + 5, self.y - 25))

    def _draw_player_blip(
        self,
        screen: pygame.Surface,
        player: Any,
        scale_x: float,
        scale_y: float,
    ) -> None:
        """Draw the green player position dot on the radar."""
        if player.alive:
            px = self.x + (player.x - GAME_AREA_X) * scale_x
            py = self.y + (player.y - GAME_AREA_Y) * scale_y
            pygame.draw.circle(screen, GREEN, (int(px), int(py)), 3)

    def _draw_enemy_blips(
        self,
        screen: pygame.Surface,
        enemies: list[Any],
        scale_x: float,
        scale_y: float,
    ) -> None:
        """Draw a colored dot for each visible, living enemy."""
        for enemy in enemies:
            if enemy.alive and enemy.visible:
                ex = self.x + (enemy.x - GAME_AREA_X) * scale_x
                ey = self.y + (enemy.y - GAME_AREA_Y) * scale_y
                pygame.draw.circle(screen, enemy.color, (int(ex), int(ey)), 2)
