#!/usr/bin/env python3
"""
Classic Tetris Game Clone
A fully playable Tetris implementation using Pygame
"""

import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
GRID_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
PLAY_WIDTH = GRID_WIDTH * GRID_SIZE
PLAY_HEIGHT = GRID_HEIGHT * GRID_SIZE
TOP_LEFT_X = (SCREEN_WIDTH - PLAY_WIDTH) // 2
TOP_LEFT_Y = SCREEN_HEIGHT - PLAY_HEIGHT - 50

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (40, 40, 40)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)

# Tetromino shapes
SHAPES = {
    'I': [[1, 1, 1, 1]],
    'O': [[1, 1],
          [1, 1]],
    'T': [[0, 1, 0],
          [1, 1, 1]],
    'S': [[0, 1, 1],
          [1, 1, 0]],
    'Z': [[1, 1, 0],
          [0, 1, 1]],
    'J': [[1, 0, 0],
          [1, 1, 1]],
    'L': [[0, 0, 1],
          [1, 1, 1]]
}

SHAPE_COLORS = {
    'I': CYAN,
    'O': YELLOW,
    'T': PURPLE,
    'S': GREEN,
    'Z': RED,
    'J': BLUE,
    'L': ORANGE
}


class Tetromino:
    """Represents a Tetris piece"""

    def __init__(self, x, y, shape_type):
        self.x = x
        self.y = y
        self.shape_type = shape_type
        self.shape = SHAPES[shape_type]
        self.color = SHAPE_COLORS[shape_type]
        self.rotation = 0

    def get_rotated_shape(self):
        """Get the current rotated shape"""
        shape = self.shape
        for _ in range(self.rotation % 4):
            shape = self._rotate_clockwise(shape)
        return shape

    def _rotate_clockwise(self, shape):
        """Rotate a shape 90 degrees clockwise"""
        return [[shape[y][x] for y in range(len(shape) - 1, -1, -1)]
                for x in range(len(shape[0]))]

    def rotate(self):
        """Rotate the tetromino"""
        self.rotation = (self.rotation + 1) % 4


class TetrisGame:
    """Main Tetris game class"""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.reset_game()

    def reset_game(self):
        """Reset the game state"""
        self.grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.game_over = False
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.fall_time = 0
        self.fall_speed = 500  # milliseconds

    def new_piece(self):
        """Create a new random tetromino"""
        shape_type = random.choice(list(SHAPES.keys()))
        return Tetromino(GRID_WIDTH // 2 - 1, 0, shape_type)

    def valid_move(self, piece, x_offset=0, y_offset=0, rotation_offset=0):
        """Check if a move is valid"""
        test_piece = Tetromino(piece.x + x_offset, piece.y + y_offset, piece.shape_type)
        test_piece.rotation = (piece.rotation + rotation_offset) % 4
        shape = test_piece.get_rotated_shape()

        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_x = test_piece.x + x
                    grid_y = test_piece.y + y

                    # Check boundaries
                    if grid_x < 0 or grid_x >= GRID_WIDTH or grid_y >= GRID_HEIGHT:
                        return False

                    # Check collision with existing blocks
                    if grid_y >= 0 and self.grid[grid_y][grid_x] != BLACK:
                        return False

        return True

    def lock_piece(self):
        """Lock the current piece into the grid"""
        shape = self.current_piece.get_rotated_shape()

        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_x = self.current_piece.x + x
                    grid_y = self.current_piece.y + y
                    if grid_y >= 0:
                        self.grid[grid_y][grid_x] = self.current_piece.color

        # Check for completed lines
        self.clear_lines()

        # Spawn new piece
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()

        # Check game over
        if not self.valid_move(self.current_piece):
            self.game_over = True

    def clear_lines(self):
        """Clear completed lines and update score"""
        lines_to_clear = []

        for y in range(GRID_HEIGHT):
            if all(cell != BLACK for cell in self.grid[y]):
                lines_to_clear.append(y)

        # Remove cleared lines
        for y in sorted(lines_to_clear, reverse=True):
            del self.grid[y]
            self.grid.insert(0, [BLACK for _ in range(GRID_WIDTH)])

        # Update score
        if lines_to_clear:
            self.lines_cleared += len(lines_to_clear)
            points = [0, 100, 300, 500, 800]
            self.score += points[len(lines_to_clear)] * self.level

            # Level up every 10 lines
            self.level = self.lines_cleared // 10 + 1
            self.fall_speed = max(100, 500 - (self.level - 1) * 50)

    def hard_drop(self):
        """Drop the piece instantly to the bottom"""
        drop_distance = 0
        while self.valid_move(self.current_piece, y_offset=1):
            self.current_piece.y += 1
            drop_distance += 1

        self.score += drop_distance * 2
        self.lock_piece()

    def draw_grid(self):
        """Draw the game grid"""
        # Draw the play area background
        pygame.draw.rect(self.screen, DARK_GRAY,
                        (TOP_LEFT_X, TOP_LEFT_Y, PLAY_WIDTH, PLAY_HEIGHT))

        # Draw the locked blocks
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                color = self.grid[y][x]
                if color != BLACK:
                    pygame.draw.rect(self.screen, color,
                                   (TOP_LEFT_X + x * GRID_SIZE,
                                    TOP_LEFT_Y + y * GRID_SIZE,
                                    GRID_SIZE - 1, GRID_SIZE - 1))

        # Draw grid lines
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(self.screen, GRAY,
                           (TOP_LEFT_X, TOP_LEFT_Y + y * GRID_SIZE),
                           (TOP_LEFT_X + PLAY_WIDTH, TOP_LEFT_Y + y * GRID_SIZE))

        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(self.screen, GRAY,
                           (TOP_LEFT_X + x * GRID_SIZE, TOP_LEFT_Y),
                           (TOP_LEFT_X + x * GRID_SIZE, TOP_LEFT_Y + PLAY_HEIGHT))

        # Draw border
        pygame.draw.rect(self.screen, WHITE,
                        (TOP_LEFT_X - 2, TOP_LEFT_Y - 2,
                         PLAY_WIDTH + 4, PLAY_HEIGHT + 4), 2)

    def draw_piece(self, piece, offset_x=0, offset_y=0):
        """Draw a tetromino piece"""
        shape = piece.get_rotated_shape()

        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    px = TOP_LEFT_X + (piece.x + x) * GRID_SIZE + offset_x
                    py = TOP_LEFT_Y + (piece.y + y) * GRID_SIZE + offset_y
                    pygame.draw.rect(self.screen, piece.color,
                                   (px, py, GRID_SIZE - 1, GRID_SIZE - 1))

    def draw_ghost_piece(self):
        """Draw a ghost piece showing where the current piece will land"""
        ghost = Tetromino(self.current_piece.x, self.current_piece.y,
                         self.current_piece.shape_type)
        ghost.rotation = self.current_piece.rotation

        while self.valid_move(ghost, y_offset=1):
            ghost.y += 1

        shape = ghost.get_rotated_shape()
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    px = TOP_LEFT_X + (ghost.x + x) * GRID_SIZE
                    py = TOP_LEFT_Y + (ghost.y + y) * GRID_SIZE
                    pygame.draw.rect(self.screen, GRAY,
                                   (px, py, GRID_SIZE - 1, GRID_SIZE - 1), 2)

    def draw_next_piece(self):
        """Draw the next piece preview"""
        text = self.font.render("Next:", True, WHITE)
        self.screen.blit(text, (TOP_LEFT_X + PLAY_WIDTH + 20, TOP_LEFT_Y + 20))

        shape = self.next_piece.get_rotated_shape()
        offset_x = TOP_LEFT_X + PLAY_WIDTH + 50
        offset_y = TOP_LEFT_Y + 70

        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.screen, self.next_piece.color,
                                   (offset_x + x * GRID_SIZE,
                                    offset_y + y * GRID_SIZE,
                                    GRID_SIZE - 1, GRID_SIZE - 1))

    def draw_stats(self):
        """Draw game statistics"""
        stats = [
            f"Score: {self.score}",
            f"Lines: {self.lines_cleared}",
            f"Level: {self.level}"
        ]

        y_offset = TOP_LEFT_Y + 200
        for stat in stats:
            text = self.small_font.render(stat, True, WHITE)
            self.screen.blit(text, (TOP_LEFT_X + PLAY_WIDTH + 20, y_offset))
            y_offset += 40

    def draw_controls(self):
        """Draw control instructions"""
        controls = [
            "Controls:",
            "← → : Move",
            "↑ : Rotate",
            "↓ : Soft Drop",
            "Space: Hard Drop",
            "P : Pause",
            "R : Restart"
        ]

        y_offset = TOP_LEFT_Y + 400
        for i, control in enumerate(controls):
            font = self.font if i == 0 else self.small_font
            text = font.render(control, True, WHITE)
            self.screen.blit(text, (TOP_LEFT_X + PLAY_WIDTH + 20, y_offset))
            y_offset += 30 if i == 0 else 25

    def draw(self):
        """Draw everything"""
        self.screen.fill(BLACK)

        if not self.game_over:
            self.draw_grid()
            self.draw_ghost_piece()
            self.draw_piece(self.current_piece)
            self.draw_next_piece()
            self.draw_stats()
            self.draw_controls()
        else:
            # Game over screen
            game_over_text = self.font.render("GAME OVER", True, RED)
            score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
            restart_text = self.small_font.render("Press R to Restart", True, WHITE)

            self.screen.blit(game_over_text,
                           (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
                            SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(score_text,
                           (SCREEN_WIDTH // 2 - score_text.get_width() // 2,
                            SCREEN_HEIGHT // 2 + 10))
            self.screen.blit(restart_text,
                           (SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                            SCREEN_HEIGHT // 2 + 60))

        pygame.display.flip()

    def handle_input(self):
        """Handle player input"""
        keys = pygame.key.get_pressed()

        if not self.game_over:
            if keys[pygame.K_LEFT] and self.valid_move(self.current_piece, x_offset=-1):
                self.current_piece.x -= 1
                pygame.time.wait(100)

            if keys[pygame.K_RIGHT] and self.valid_move(self.current_piece, x_offset=1):
                self.current_piece.x += 1
                pygame.time.wait(100)

            if keys[pygame.K_DOWN]:
                if self.valid_move(self.current_piece, y_offset=1):
                    self.current_piece.y += 1
                    self.score += 1
                pygame.time.wait(50)

    def run(self):
        """Main game loop"""
        paused = False

        while True:
            self.fall_time += self.clock.get_rawtime()
            self.clock.tick(60)

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                        paused = False

                    if event.key == pygame.K_p and not self.game_over:
                        paused = not paused

                    if not self.game_over and not paused:
                        if event.key == pygame.K_UP:
                            if self.valid_move(self.current_piece, rotation_offset=1):
                                self.current_piece.rotate()

                        if event.key == pygame.K_SPACE:
                            self.hard_drop()

            if not self.game_over and not paused:
                # Handle continuous input
                self.handle_input()

                # Automatic falling
                if self.fall_time >= self.fall_speed:
                    self.fall_time = 0

                    if self.valid_move(self.current_piece, y_offset=1):
                        self.current_piece.y += 1
                    else:
                        self.lock_piece()

            # Draw
            self.draw()

            # Show pause message
            if paused:
                pause_text = self.font.render("PAUSED", True, YELLOW)
                self.screen.blit(pause_text,
                               (SCREEN_WIDTH // 2 - pause_text.get_width() // 2,
                                SCREEN_HEIGHT // 2 - pause_text.get_height() // 2))
                pygame.display.flip()


if __name__ == "__main__":
    game = TetrisGame()
    game.run()
