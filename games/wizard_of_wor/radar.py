"""
Radar system for Wizard of Wor.
"""
import pygame
from constants import *


class Radar:
    """Displays enemy positions on a mini-map."""

    def __init__(self):
        """Initialize radar."""
        self.x = RADAR_X
        self.y = RADAR_Y
        self.size = RADAR_SIZE

    def draw(self, screen, enemies, player):
        """Draw the radar with enemy positions."""
        # Draw radar background
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.size, self.size))
        pygame.draw.rect(screen, CYAN, (self.x, self.y, self.size, self.size), 2)

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
            pygame.draw.circle(screen, GREEN, (int(player_radar_x), int(player_radar_y)), 3)

        # Draw enemy positions
        for enemy in enemies:
            if enemy.alive:
                enemy_radar_x = self.x + (enemy.x - GAME_AREA_X) * scale_x
                enemy_radar_y = self.y + (enemy.y - GAME_AREA_Y) * scale_y

                # Use different colors for different enemy types
                color = enemy.color if enemy.visible else GRAY
                pygame.draw.circle(screen, color, (int(enemy_radar_x), int(enemy_radar_y)), 2)
