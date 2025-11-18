"""
Dungeon/Maze generation and management for Wizard of Wor.
"""

import pygame
from constants import *


class Dungeon:
    """Manages the dungeon maze layout."""

    def __init__(self):
        """Initialize the dungeon with walls."""
        self.cols = GAME_AREA_WIDTH // CELL_SIZE
        self.rows = GAME_AREA_HEIGHT // CELL_SIZE

        # Create grid (0 = empty, 1 = wall)
        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

        # Build classic Wizard of Wor style maze
        self._build_classic_maze()

    def _build_classic_maze(self):
        """Build a maze similar to classic Wizard of Wor."""
        # Border walls
        for i in range(self.rows):
            self.grid[i][0] = 1  # Left wall
            self.grid[i][self.cols - 1] = 1  # Right wall

        for j in range(self.cols):
            self.grid[0][j] = 1  # Top wall
            self.grid[self.rows - 1][j] = 1  # Bottom wall

        # Create horizontal corridors with vertical barriers
        # Top section
        for j in range(4, self.cols - 4):
            self.grid[3][j] = 1

        # Middle sections - create chambers
        for i in range(5, 8):
            self.grid[i][5] = 1
            self.grid[i][self.cols - 6] = 1

        # Bottom section
        for j in range(4, self.cols - 4):
            self.grid[self.rows - 4][j] = 1

        # Add some internal walls for interesting gameplay
        # Left chamber
        self.grid[7][3] = 1
        self.grid[8][3] = 1

        # Right chamber
        self.grid[7][self.cols - 4] = 1
        self.grid[8][self.cols - 4] = 1

        # Center obstacles
        mid_row = self.rows // 2
        mid_col = self.cols // 2

        self.grid[mid_row][mid_col - 2] = 1
        self.grid[mid_row][mid_col + 2] = 1
        self.grid[mid_row - 2][mid_col] = 1
        self.grid[mid_row + 2][mid_col] = 1

    def is_wall(self, x, y):
        """Check if a position contains a wall."""
        # Convert pixel coordinates to grid coordinates
        grid_x = int((x - GAME_AREA_X) // CELL_SIZE)
        grid_y = int((y - GAME_AREA_Y) // CELL_SIZE)

        if 0 <= grid_x < self.cols and 0 <= grid_y < self.rows:
            return self.grid[grid_y][grid_x] == 1
        return True  # Out of bounds counts as wall

    def can_move_to(self, rect):
        """Check if a rectangle can move to a position without hitting walls."""
        # Check corners of the rectangle
        corners = [
            (rect.left, rect.top),
            (rect.right, rect.top),
            (rect.left, rect.bottom),
            (rect.right, rect.bottom),
        ]

        for x, y in corners:
            if self.is_wall(x, y):
                return False
        return True

    def get_random_spawn_position(self):
        """Get a random valid spawn position in the dungeon."""
        import random

        while True:
            grid_x = random.randint(2, self.cols - 3)
            grid_y = random.randint(2, self.rows - 3)

            if self.grid[grid_y][grid_x] == 0:
                x = GAME_AREA_X + grid_x * CELL_SIZE + CELL_SIZE // 2
                y = GAME_AREA_Y + grid_y * CELL_SIZE + CELL_SIZE // 2
                return (x, y)

    def draw(self, screen):
        """Draw the dungeon walls."""
        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i][j] == 1:
                    x = GAME_AREA_X + j * CELL_SIZE
                    y = GAME_AREA_Y + i * CELL_SIZE
                    pygame.draw.rect(screen, BLUE, (x, y, CELL_SIZE, CELL_SIZE))
                    pygame.draw.rect(screen, CYAN, (x, y, CELL_SIZE, CELL_SIZE), 1)
