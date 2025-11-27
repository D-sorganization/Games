#!/usr/bin/env python3
"""
Enhanced Tetris Game Clone
A fully featured Tetris implementation with levels, scoring, and modern features
"""

import random
import sys
from enum import Enum
from typing import TYPE_CHECKING, cast

import pygame

if TYPE_CHECKING:
    from pygame import event as pygame_event

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
GRID_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
PLAY_WIDTH = GRID_WIDTH * GRID_SIZE
PLAY_HEIGHT = GRID_HEIGHT * GRID_SIZE
TOP_LEFT_X = 50
TOP_LEFT_Y = SCREEN_HEIGHT - PLAY_HEIGHT - 50

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (200, 200, 200)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)

# Tetromino shapes
SHAPES = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1],
          [1, 1]],
    "T": [[0, 1, 0],
          [1, 1, 1]],
    "S": [[0, 1, 1],
          [1, 1, 0]],
    "Z": [[1, 1, 0],
          [0, 1, 1]],
    "J": [[1, 0, 0],
          [1, 1, 1]],
    "L": [[0, 0, 1],
          [1, 1, 1]]
}

SHAPE_COLORS = {
    "I": CYAN,
    "O": YELLOW,
    "T": PURPLE,
    "S": GREEN,
    "Z": RED,
    "J": BLUE,
    "L": ORANGE
}


class GameState(Enum):
    """Game states"""
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4


class Particle:
    """Visual particle effect"""
    def __init__(self, x: float, y: float, color: tuple[int, int, int],
                 velocity_x: float, velocity_y: float) -> None:
        """Initialize particle with position, color, and velocity"""
        self.x = x
        self.y = y
        self.color = color
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.lifetime = 60
        self.alpha = 255

    def update(self) -> None:
        """Update particle position and lifetime"""
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y += 0.2  # Gravity
        self.lifetime -= 1
        self.alpha = int((self.lifetime / 60) * 255)

    def is_alive(self) -> bool:
        """Check if particle is still alive"""
        return self.lifetime > 0


class ScorePopup:
    """Score notification popup"""
    def __init__(self, text: str, x: int, y: int,
                 color: tuple[int, int, int] = GOLD) -> None:
        """Initialize score popup with text, position, and color"""
        self.text = text
        self.x = x
        self.y = y
        self.start_y = y
        self.color = color
        self.lifetime = 90
        self.alpha = 255

    def update(self) -> None:
        """Update popup position and lifetime"""
        self.y -= 1
        self.lifetime -= 1
        self.alpha = int((self.lifetime / 90) * 255)

    def is_alive(self) -> bool:
        """Check if popup is still alive"""
        return self.lifetime > 0


class Tetromino:
    """Represents a Tetris piece"""

    def __init__(self, x: int, y: int, shape_type: str) -> None:
        """Initialize tetromino with position and shape type"""
        self.x = x
        self.y = y
        self.shape_type = shape_type
        self.shape = SHAPES[shape_type]
        self.color = SHAPE_COLORS[shape_type]
        self.rotation = 0

    def get_rotated_shape(self) -> list[list[int]]:
        """Get the current rotated shape"""
        shape = self.shape
        for _ in range(self.rotation % 4):
            shape = self._rotate_clockwise(shape)
        return shape

    def _rotate_clockwise(self, shape: list[list[int]]) -> list[list[int]]:
        """Rotate a shape 90 degrees clockwise"""
        return [[shape[y][x] for y in range(len(shape) - 1, -1, -1)]
                for x in range(len(shape[0]))]

    def rotate(self) -> None:
        """Rotate the tetromino"""
        self.rotation = (self.rotation + 1) % 4


class TetrisGame:
    """Main Tetris game class"""

    def __init__(self) -> None:
        """Initialize the Tetris game with display and initial state"""
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Enhanced Tetris")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 18)

        self.state = GameState.MENU
        self.starting_level = 1
        self.held_piece: str | None = None
        self.particles: list[Particle] = []
        self.score_popups: list[ScorePopup] = []
        self.reset_game()

    def reset_game(self) -> None:
        """Reset the game state"""
        self.grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.held_piece = None
        self.can_hold = True
        self.game_over = False
        self.score = 0
        self.lines_cleared = 0
        self.level = self.starting_level
        self.fall_time = 0
        self.fall_speed = max(50, 500 - (self.level - 1) * 40)
        self.combo = 0
        self.particles.clear()
        self.score_popups.clear()
        self.lines_cleared_this_drop = 0
        self.total_singles = 0
        self.total_doubles = 0
        self.total_triples = 0
        self.total_tetrises = 0

    def new_piece(self) -> Tetromino:
        """Create a new random tetromino"""
        shape_type = random.choice(list(SHAPES.keys()))
        return Tetromino(GRID_WIDTH // 2 - 1, 0, shape_type)

    def valid_move(self, piece: Tetromino, x_offset: int = 0,
                   y_offset: int = 0, rotation_offset: int = 0) -> bool:
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
                    if grid_x < 0:
                        return False
                    if grid_x >= GRID_WIDTH:
                        return False
                    if grid_y >= GRID_HEIGHT:
                        return False

                    # Check collision with existing blocks
                    if grid_y >= 0 and self.grid[grid_y][grid_x] != BLACK:
                        return False

        return True

    def hold_piece(self) -> None:
        """Hold the current piece"""
        if not self.can_hold:
            return

        if self.held_piece is None:
            self.held_piece = self.current_piece.shape_type
            self.current_piece = self.next_piece
            self.next_piece = self.new_piece()
        else:
            # Swap current and held piece
            # In this branch, held_piece is guaranteed to be str (not None)
            # MyPy understands the type narrowing from the if/else check above
            if self.held_piece is None:
                return  # This should never happen, but helps type checking
            temp = self.held_piece
            self.held_piece = self.current_piece.shape_type
            new_piece = Tetromino(GRID_WIDTH // 2 - 1, 0, temp)
            # Validate that the swapped piece can spawn
            if not self.valid_move(new_piece):
                # Cannot spawn, game over
                self.game_over = True
                self.state = GameState.GAME_OVER
                return
            self.current_piece = new_piece

        self.can_hold = False

    def lock_piece(self) -> None:
        """Lock the current piece into the grid"""
        shape = self.current_piece.get_rotated_shape()

        # Lock the piece
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_x = self.current_piece.x + x
                    grid_y = self.current_piece.y + y
                    if grid_y >= 0:
                        self.grid[grid_y][grid_x] = self.current_piece.color

        # Check for completed lines
        self.clear_lines()

        # Reset hold ability
        self.can_hold = True

        # Spawn new piece
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()

        # Check game over
        if not self.valid_move(self.current_piece):
            self.game_over = True
            self.state = GameState.GAME_OVER

    def create_particles(self, row: int) -> None:
        """Create particle effects for cleared line"""
        for x in range(GRID_WIDTH):
            color = self.grid[row][x]
            if color != BLACK:
                px = TOP_LEFT_X + x * GRID_SIZE + GRID_SIZE // 2
                py = TOP_LEFT_Y + row * GRID_SIZE + GRID_SIZE // 2
                for _ in range(3):
                    vx = random.uniform(-3, 3)
                    vy = random.uniform(-5, -2)
                    self.particles.append(Particle(px, py, color, vx, vy))

    def clear_lines(self) -> None:
        """Clear completed lines and update score"""
        lines_to_clear = []

        for y in range(GRID_HEIGHT):
            if all(cell != BLACK for cell in self.grid[y]):
                lines_to_clear.append(y)

        # Create particles for cleared lines
        for y in lines_to_clear:
            self.create_particles(y)

        # Remove cleared lines
        for y in sorted(lines_to_clear, reverse=True):
            del self.grid[y]
            self.grid.insert(0, [BLACK for _ in range(GRID_WIDTH)])

        # Update score and statistics
        if lines_to_clear:
            num_lines = len(lines_to_clear)
            self.lines_cleared += num_lines
            self.lines_cleared_this_drop = num_lines

            # Base score values (classic Tetris scoring)
            score_values = {
                1: 100,   # Single
                2: 300,   # Double
                3: 500,   # Triple
                4: 800    # Tetris
            }

            # Calculate score with level multiplier
            base_score = score_values.get(num_lines, 0)
            earned_score = base_score * self.level

            # Add combo bonus (calculate before incrementing combo)
            combo_for_bonus = self.combo
            if combo_for_bonus > 0:
                combo_bonus = 50 * combo_for_bonus * self.level
                earned_score += combo_bonus

            self.score += earned_score
            self.combo += 1

            # Track statistics
            if num_lines == 1:
                self.total_singles += 1
            elif num_lines == 2:
                self.total_doubles += 1
            elif num_lines == 3:
                self.total_triples += 1
            elif num_lines == 4:
                self.total_tetrises += 1

            # Create score popup (use combo value before increment for display)
            popup_text = self.get_line_clear_text(num_lines)
            # Match original condition: only show combo for 3rd consecutive clear and beyond
            if combo_for_bonus > 1:
                # Display combo number that matches the bonus calculation
                # combo_for_bonus=2 means 3rd consecutive (show "x3"),
                # combo_for_bonus=3 means 4th (show "x4"), etc.
                popup_text += f" x{combo_for_bonus + 1} COMBO!"
            popup_x = TOP_LEFT_X + PLAY_WIDTH // 2
            popup_y = TOP_LEFT_Y + PLAY_HEIGHT // 2
            self.score_popups.append(ScorePopup(popup_text, popup_x, popup_y))

            # Level up every 10 lines
            new_level = self.starting_level + (self.lines_cleared // 10)
            if new_level > self.level:
                self.level = new_level
                self.fall_speed = max(50, 500 - (self.level - 1) * 40)
                # Level up popup
                level_popup = ScorePopup(f"LEVEL {self.level}!", popup_x, popup_y - 40, SILVER)
                self.score_popups.append(level_popup)
        else:
            # Reset combo if no lines cleared
            self.combo = 0

    def get_line_clear_text(self, num_lines: int) -> str:
        """Get text description for line clear"""
        if num_lines == 1:
            return "SINGLE!"
        if num_lines == 2:
            return "DOUBLE!"
        if num_lines == 3:
            return "TRIPLE!"
        if num_lines == 4:
            return "TETRIS!"
        return ""

    def hard_drop(self) -> None:
        """Drop the piece instantly to the bottom"""
        drop_distance = 0
        while self.valid_move(self.current_piece, y_offset=1):
            self.current_piece.y += 1
            drop_distance += 1

        self.score += drop_distance * 2
        self.lock_piece()

    def draw_grid(self) -> None:
        """Draw the game grid"""
        # Draw the play area background
        pygame.draw.rect(self.screen, DARK_GRAY,
                        (TOP_LEFT_X, TOP_LEFT_Y, PLAY_WIDTH, PLAY_HEIGHT))

        # Draw the locked blocks
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                color = self.grid[y][x]
                if color != BLACK:
                    # Draw block with 3D effect
                    rect = pygame.Rect(TOP_LEFT_X + x * GRID_SIZE,
                                      TOP_LEFT_Y + y * GRID_SIZE,
                                      GRID_SIZE - 1, GRID_SIZE - 1)
                    pygame.draw.rect(self.screen, color, rect)
                    # Highlight
                    lighter = tuple(min(255, c + 50) for c in color)
                    pygame.draw.rect(self.screen, lighter, rect, 2)

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
                         PLAY_WIDTH + 4, PLAY_HEIGHT + 4), 3)

    def draw_piece(self, piece: Tetromino, offset_x: int = 0,
                   offset_y: int = 0, alpha: int = 255) -> None:
        """Draw a tetromino piece"""
        shape = piece.get_rotated_shape()

        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    px = TOP_LEFT_X + (piece.x + x) * GRID_SIZE + offset_x
                    py = TOP_LEFT_Y + (piece.y + y) * GRID_SIZE + offset_y

                    # Create surface for transparency
                    surf = pygame.Surface((GRID_SIZE - 1, GRID_SIZE - 1))
                    surf.fill(piece.color)
                    surf.set_alpha(alpha)
                    self.screen.blit(surf, (px, py))

                    # Draw highlight
                    lighter = tuple(min(255, c + 50) for c in piece.color)
                    pygame.draw.rect(self.screen, lighter,
                                   (px, py, GRID_SIZE - 1, GRID_SIZE - 1), 2)

    def draw_ghost_piece(self) -> None:
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

    def draw_mini_piece(self, shape_type: str | None,
                        x: int, y: int, size: int = 20) -> None:
        """Draw a small preview piece"""
        if shape_type is None:
            return

        piece = Tetromino(0, 0, shape_type)
        shape = piece.get_rotated_shape()

        for row_idx, row in enumerate(shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.screen, piece.color,
                                   (x + col_idx * size,
                                    y + row_idx * size,
                                    size - 1, size - 1))

    def draw_next_piece(self) -> None:
        """Draw the next piece preview"""
        # Panel background
        panel_x = TOP_LEFT_X + PLAY_WIDTH + 20
        panel_y = TOP_LEFT_Y
        panel_w = 200
        panel_h = 120

        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_w, panel_h), 2)

        text = self.font.render("Next", True, WHITE)
        self.screen.blit(text, (panel_x + 10, panel_y + 10))

        self.draw_mini_piece(self.next_piece.shape_type, panel_x + 60, panel_y + 50, 25)

    def draw_held_piece(self) -> None:
        """Draw the held piece preview"""
        panel_x = TOP_LEFT_X + PLAY_WIDTH + 20
        panel_y = TOP_LEFT_Y + 140
        panel_w = 200
        panel_h = 120

        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_w, panel_h), 2)

        text = self.font.render("Hold", True, WHITE)
        self.screen.blit(text, (panel_x + 10, panel_y + 10))

        if self.held_piece:
            self.draw_mini_piece(self.held_piece, panel_x + 60, panel_y + 50, 25)

        if not self.can_hold:
            # Draw "locked" indicator
            lock_text = self.tiny_font.render("(used)", True, GRAY)
            self.screen.blit(lock_text, (panel_x + 70, panel_y + 100))

    def draw_stats(self) -> None:
        """Draw game statistics"""
        panel_x = TOP_LEFT_X + PLAY_WIDTH + 20
        panel_y = TOP_LEFT_Y + 280

        stats = [
            ("Score", f"{self.score}"),
            ("Lines", f"{self.lines_cleared}"),
            ("Level", f"{self.level}"),
            ("", ""),
            ("Singles", f"{self.total_singles}"),
            ("Doubles", f"{self.total_doubles}"),
            ("Triples", f"{self.total_triples}"),
            ("Tetrises", f"{self.total_tetrises}"),
        ]

        y_offset = panel_y
        for label, value in stats:
            if label:
                label_text = self.small_font.render(f"{label}:", True, LIGHT_GRAY)
                value_text = self.small_font.render(value, True, WHITE)
                self.screen.blit(label_text, (panel_x, y_offset))
                self.screen.blit(value_text, (panel_x + 100, y_offset))
            y_offset += 30

    def draw_controls(self) -> None:
        """Draw control instructions"""
        controls = [
            ("←/→", "Move"),
            ("↑", "Rotate"),
            ("↓", "Soft Drop"),
            ("Space", "Hard Drop"),
            ("C", "Hold"),
            ("P", "Pause"),
            ("R", "Restart"),
        ]

        panel_x = 10
        panel_y = TOP_LEFT_Y

        title = self.font.render("Controls", True, WHITE)
        self.screen.blit(title, (panel_x, panel_y))

        y_offset = panel_y + 40
        for key, action in controls:
            key_text = self.small_font.render(key, True, GOLD)
            action_text = self.tiny_font.render(action, True, LIGHT_GRAY)
            self.screen.blit(key_text, (panel_x, y_offset))
            self.screen.blit(action_text, (panel_x + 80, y_offset + 5))
            y_offset += 30

    def draw_particles(self) -> None:
        """Draw particle effects"""
        for particle in self.particles[:]:
            if particle.is_alive():
                particle.update()
                # Draw particle with alpha
                surf = pygame.Surface((4, 4))
                surf.fill(particle.color)
                surf.set_alpha(particle.alpha)
                self.screen.blit(surf, (int(particle.x), int(particle.y)))
            else:
                self.particles.remove(particle)

    def draw_score_popups(self) -> None:
        """Draw score notification popups"""
        for popup in self.score_popups[:]:
            if popup.is_alive():
                popup.update()
                # Render text with alpha
                text_surf = self.font_large.render(popup.text, True, popup.color)
                text_surf.set_alpha(popup.alpha)
                text_rect = text_surf.get_rect(center=(int(popup.x), int(popup.y)))
                self.screen.blit(text_surf, text_rect)
            else:
                self.score_popups.remove(popup)

    def draw_menu(self) -> None:
        """Draw the level selection menu"""
        self.screen.fill(BLACK)

        # Title
        title = self.font_large.render("TETRIS", True, CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        # Instructions
        instruction = self.font.render("Select Starting Level", True, WHITE)
        inst_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(instruction, inst_rect)

        # Level options
        levels = [1, 5, 10, 15, 20]
        y_offset = 280
        for level in levels:
            color = GOLD if level == self.starting_level else WHITE
            level_text = self.font.render(f"Level {level}", True, color)
            text_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(level_text, text_rect)

            if level == self.starting_level:
                # Draw selection indicator
                pygame.draw.rect(self.screen, GOLD,
                               (text_rect.x - 10, text_rect.y - 5,
                                text_rect.width + 20, text_rect.height + 10), 2)

            y_offset += 50

        # Start instruction
        start_text = self.small_font.render("Press ENTER to Start", True, GREEN)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, 550))
        self.screen.blit(start_text, start_rect)

        # Controls hint
        hint_text = self.tiny_font.render("Use UP/DOWN arrows to select level", True, GRAY)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 600))
        self.screen.blit(hint_text, hint_rect)

    def draw(self) -> None:
        """Draw everything"""
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state in [GameState.PLAYING, GameState.PAUSED]:
            self.screen.fill(BLACK)
            self.draw_grid()
            self.draw_ghost_piece()
            self.draw_piece(self.current_piece)
            self.draw_next_piece()
            self.draw_held_piece()
            self.draw_stats()
            self.draw_controls()
            # Only animate particles and popups when playing (not paused)
            if self.state == GameState.PLAYING:
                self.draw_particles()
                self.draw_score_popups()
            else:
                # Draw particles and popups without updating them when paused
                for particle in self.particles:
                    if particle.is_alive():
                        surf = pygame.Surface((4, 4))
                        surf.fill(particle.color)
                        surf.set_alpha(particle.alpha)
                        self.screen.blit(surf, (int(particle.x), int(particle.y)))
                for popup in self.score_popups:
                    if popup.is_alive():
                        text_surf = self.font_large.render(popup.text, True, popup.color)
                        text_surf.set_alpha(popup.alpha)
                        text_rect = text_surf.get_rect(center=(int(popup.x), int(popup.y)))
                        self.screen.blit(text_surf, text_rect)

            if self.state == GameState.PAUSED:
                # Pause overlay
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.fill(BLACK)
                overlay.set_alpha(128)
                self.screen.blit(overlay, (0, 0))

                pause_text = self.font_large.render("PAUSED", True, YELLOW)
                pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                self.screen.blit(pause_text, pause_rect)

        elif self.state == GameState.GAME_OVER:
            self.screen.fill(BLACK)

            # Game over screen
            game_over_text = self.font_large.render("GAME OVER", True, RED)
            score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
            lines_text = self.font.render(f"Lines Cleared: {self.lines_cleared}", True, WHITE)
            level_text = self.font.render(f"Final Level: {self.level}", True, WHITE)

            # Statistics
            stats_title = self.font.render("Line Clears:", True, GOLD)
            single_text = self.small_font.render(f"Singles: {self.total_singles}", True, WHITE)
            double_text = self.small_font.render(f"Doubles: {self.total_doubles}", True, WHITE)
            triple_text = self.small_font.render(f"Triples: {self.total_triples}", True, WHITE)
            tetris_text = self.small_font.render(f"Tetrises: {self.total_tetrises}", True, CYAN)

            restart_text = self.small_font.render("Press R to Restart", True, GREEN)

            y_pos = 150
            for text in [game_over_text, score_text, lines_text, level_text]:
                rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                self.screen.blit(text, rect)
                y_pos += 60

            y_pos += 20
            stats_rect = stats_title.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
            self.screen.blit(stats_title, stats_rect)
            y_pos += 40

            for text in [single_text, double_text, triple_text, tetris_text]:
                rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                self.screen.blit(text, rect)
                y_pos += 35

            y_pos += 20
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
            self.screen.blit(restart_text, restart_rect)

        pygame.display.flip()

    def handle_menu_input(self, event: "pygame_event.Event") -> None:
        """Handle menu input"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                levels = [1, 5, 10, 15, 20]
                current_idx = levels.index(self.starting_level)
                self.starting_level = levels[max(0, current_idx - 1)]
            elif event.key == pygame.K_DOWN:
                levels = [1, 5, 10, 15, 20]
                current_idx = levels.index(self.starting_level)
                self.starting_level = levels[min(len(levels) - 1, current_idx + 1)]
            elif event.key == pygame.K_RETURN:
                self.reset_game()
                self.state = GameState.PLAYING

    def handle_input(self) -> None:
        """Handle player input"""
        keys = pygame.key.get_pressed()

        if self.state == GameState.PLAYING:
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

    def run(self) -> None:
        """Main game loop"""
        while True:
            if self.state == GameState.PLAYING:
                self.fall_time += self.clock.get_rawtime()

            self.clock.tick(60)

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.state == GameState.MENU:
                    self.handle_menu_input(event)  # type: ignore[arg-type]

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.state = GameState.MENU
                        self.starting_level = 1

                    if event.key == pygame.K_p:
                        if self.state in [GameState.PLAYING, GameState.PAUSED]:
                            if self.state == GameState.PLAYING:
                                self.state = GameState.PAUSED
                            else:
                                self.state = GameState.PLAYING

                    if self.state == GameState.PLAYING:
                        if event.key == pygame.K_UP:
                            if self.valid_move(self.current_piece, rotation_offset=1):
                                self.current_piece.rotate()

                        if event.key == pygame.K_SPACE:
                            self.hard_drop()

                        if event.key == pygame.K_c:
                            self.hold_piece()

            if self.state == GameState.PLAYING:
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


if __name__ == "__main__":
    game = TetrisGame()
    game.run()
