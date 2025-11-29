"""
Dungeon/Maze generation and management for Wizard of Wor.
"""

import random

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

        # Pre-rendered surfaces for speed and extra texture
        self.surface = pygame.Surface((GAME_AREA_WIDTH, GAME_AREA_HEIGHT))
        self.grid_overlay = pygame.Surface((GAME_AREA_WIDTH, GAME_AREA_HEIGHT), pygame.SRCALPHA)
        self._render_background()

        # Pre-compute curated spawn cells reminiscent of arcade entryways
        self.player_spawn_cells = self._build_spawn_cells(center_bias=True)
        self.enemy_spawn_cells = self._build_spawn_cells(center_bias=False)

    def _build_classic_maze(self) -> None:
        """Build a maze similar to classic Wizard of Wor with more roomy layout."""
        # Border walls
        for i in range(self.rows):
            self.grid[i][0] = 1  # Left wall
            self.grid[i][self.cols - 1] = 1  # Right wall

        for j in range(self.cols):
            self.grid[0][j] = 1  # Top wall
            self.grid[self.rows - 1][j] = 1  # Bottom wall

        mid_row = self.rows // 2
        mid_col = self.cols // 2

        # Horizontal corridors framing the map
        for j in range(3, self.cols - 3):
            self.grid[4][j] = 1
            self.grid[mid_row][j] = 1
            self.grid[self.rows - 5][j] = 1

        # Vertical pillars creating mirrored chambers
        for i in range(6, self.rows - 6):
            if i % 2 == 0:
                self.grid[i][4] = 1
                self.grid[i][self.cols - 5] = 1

        # Side alcoves
        for j in range(8, self.cols - 8, 6):
            self.grid[mid_row - 3][j] = 1
            self.grid[mid_row + 3][j] = 1

        # Center cruciform and corner nooks
        for offset in range(-3, 4):
            self.grid[mid_row + offset][mid_col] = 1
            self.grid[mid_row][mid_col + offset] = 1

        for offset in (-6, 6):
            self.grid[mid_row - 2][mid_col + offset] = 1
            self.grid[mid_row + 2][mid_col + offset] = 1

        # Entry tunnels on each side (leave gaps for doors)
        for j in range(2, 6):
            self.grid[mid_row - 1][j] = 0
            self.grid[mid_row][j] = 0
            self.grid[mid_row + 1][j] = 0
            self.grid[mid_row - 1][self.cols - j - 1] = 0
            self.grid[mid_row][self.cols - j - 1] = 0
            self.grid[mid_row + 1][self.cols - j - 1] = 0

    def _render_background(self) -> None:
        """Paint walls and subtle floor texture to a cached surface."""
        self.surface.fill(DEEP_BLUE)
        self.grid_overlay.fill((0, 0, 0, 0))

        # Floor grid to evoke arcade cabinet scanlines
        grid_color = (*SLATE, FLOOR_GRID_ALPHA)
        for i in range(0, GAME_AREA_HEIGHT, CELL_SIZE // 2):
            pygame.draw.line(self.grid_overlay, grid_color, (0, i), (GAME_AREA_WIDTH, i))
        for j in range(0, GAME_AREA_WIDTH, CELL_SIZE // 2):
            pygame.draw.line(self.grid_overlay, grid_color, (j, 0), (j, GAME_AREA_HEIGHT))

        # Walls with inner highlight
        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i][j] == 1:
                    x = j * CELL_SIZE
                    y = i * CELL_SIZE
                    wall_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(self.surface, BLUE, wall_rect)
                    pygame.draw.rect(self.surface, CYAN, wall_rect, 2)
                    inner_rect = wall_rect.inflate(-8, -8)
                    pygame.draw.rect(self.surface, SLATE, inner_rect, 1)

    def _build_spawn_cells(self, center_bias: bool) -> list[tuple[int, int]]:
        """Create a curated list of viable spawn cells similar to arcade doorways."""
        viable_cells = []
        for y in range(2, self.rows - 2):
            for x in range(2, self.cols - 2):
                if self.grid[y][x] == 0:
                    at_side_door = x in (2, self.cols - 3) and abs(y - self.rows // 2) <= 2
                    near_center = abs(x - self.cols // 2) <= 2 and abs(y - self.rows // 2) <= 4
                    corner_pad = (x, y) in {
                        (3, 3),
                        (3, self.rows - 4),
                        (self.cols - 4, 3),
                        (self.cols - 4, self.rows - 4),
                    }

                    if center_bias and (near_center or at_side_door):
                        viable_cells.append((x, y))
                    elif not center_bias and (at_side_door or corner_pad):
                        viable_cells.append((x, y))
        if not viable_cells:
            viable_cells = [(self.cols // 2, self.rows // 2)]
        return viable_cells

    def is_wall(self, x: float, y: float) -> bool:
        """Check if a position contains a wall."""
        # Convert pixel coordinates to grid coordinates
        grid_x = int((x - GAME_AREA_X) // CELL_SIZE)
        grid_y = int((y - GAME_AREA_Y) // CELL_SIZE)

        if 0 <= grid_x < self.cols and 0 <= grid_y < self.rows:
            return self.grid[grid_y][grid_x] == 1
        return True  # Out of bounds counts as wall

    def can_move_to(self, rect: pygame.Rect) -> bool:
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

    def _cell_to_world(self, cell_x: int, cell_y: int) -> tuple[int, int]:
        """Convert a grid cell into pixel coordinates at the center of that cell."""
        x = GAME_AREA_X + cell_x * CELL_SIZE + CELL_SIZE // 2
        y = GAME_AREA_Y + cell_y * CELL_SIZE + CELL_SIZE // 2
        return (x, y)

    def get_random_spawn_position(self, prefer_player: bool = False) -> tuple[int, int]:
        """Get a random valid spawn position in the dungeon."""
        source = self.player_spawn_cells if prefer_player else self.enemy_spawn_cells
        if not source:
            empty_cells = [
                (x, y)
                for y in range(1, self.rows - 1)
                for x in range(1, self.cols - 1)
                if self.grid[y][x] == 0
            ]
            if empty_cells:
                center = (self.cols // 2, self.rows // 2)
                grid_x, grid_y = min(
                    empty_cells,
                    key=lambda cell: abs(cell[0] - center[0]) + abs(cell[1] - center[1]),
                )
            else:
                grid_x, grid_y = self.cols // 2, self.rows // 2
            return self._cell_to_world(grid_x, grid_y)

        grid_x, grid_y = random.choice(source)
        return self._cell_to_world(grid_x, grid_y)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the dungeon walls."""
        screen.blit(self.surface, (GAME_AREA_X, GAME_AREA_Y))
        screen.blit(self.grid_overlay, (GAME_AREA_X, GAME_AREA_Y))
