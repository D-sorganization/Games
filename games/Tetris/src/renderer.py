import pygame

from .constants import *
from .game_logic import TetrisLogic
from .tetromino import Tetromino


class TetrisRenderer:
    def __init__(self, screen: pygame.Surface) -> None:
        """Initialize the renderer with target screen"""
        self.screen = screen
        self.font_large = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 18)

    def draw_grid(self, logic: TetrisLogic) -> None:
        """Draw the game grid"""
        # Draw the play area background
        pygame.draw.rect(
            self.screen,
            DARK_GRAY,
            (TOP_LEFT_X, TOP_LEFT_Y, PLAY_WIDTH, PLAY_HEIGHT),
        )

        # Draw the locked blocks
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                color = logic.grid[y][x]
                if color != BLACK:
                    # Draw block with 3D effect
                    rect = pygame.Rect(
                        TOP_LEFT_X + x * GRID_SIZE,
                        TOP_LEFT_Y + y * GRID_SIZE,
                        GRID_SIZE - 1,
                        GRID_SIZE - 1,
                    )
                    pygame.draw.rect(self.screen, color, rect)
                    # Highlight
                    lighter = tuple(min(255, c + 50) for c in color)
                    pygame.draw.rect(self.screen, lighter, rect, 2)

        # Draw grid lines
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(
                self.screen,
                GRAY,
                (TOP_LEFT_X, TOP_LEFT_Y + y * GRID_SIZE),
                (TOP_LEFT_X + PLAY_WIDTH, TOP_LEFT_Y + y * GRID_SIZE),
            )

        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(
                self.screen,
                GRAY,
                (TOP_LEFT_X + x * GRID_SIZE, TOP_LEFT_Y),
                (TOP_LEFT_X + x * GRID_SIZE, TOP_LEFT_Y + PLAY_HEIGHT),
            )

        # Draw border
        pygame.draw.rect(
            self.screen,
            WHITE,
            (TOP_LEFT_X - 2, TOP_LEFT_Y - 2, PLAY_WIDTH + 4, PLAY_HEIGHT + 4),
            3,
        )

    def draw_piece(
        self,
        piece: Tetromino,
        offset_x: int = 0,
        offset_y: int = 0,
        alpha: int = 255,
    ) -> None:
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
                    pygame.draw.rect(
                        self.screen,
                        lighter,
                        (px, py, GRID_SIZE - 1, GRID_SIZE - 1),
                        2,
                    )

    def draw_ghost_piece(self, logic: TetrisLogic) -> None:
        """Draw a ghost piece showing where the current piece will land"""
        ghost = Tetromino(
            logic.current_piece.x,
            logic.current_piece.y,
            logic.current_piece.shape_type,
        )
        ghost.rotation = logic.current_piece.rotation

        while logic.valid_move(ghost, y_offset=1):
            ghost.y += 1

        shape = ghost.get_rotated_shape()
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    px = TOP_LEFT_X + (ghost.x + x) * GRID_SIZE
                    py = TOP_LEFT_Y + (ghost.y + y) * GRID_SIZE
                    pygame.draw.rect(self.screen, GRAY, (px, py, GRID_SIZE - 1, GRID_SIZE - 1), 2)

    def draw_mini_piece(self, shape_type: str | None, x: int, y: int, size: int = 20) -> None:
        """Draw a small preview piece"""
        if shape_type is None:
            return

        piece = Tetromino(0, 0, shape_type)
        shape = piece.get_rotated_shape()

        for row_idx, row in enumerate(shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        self.screen,
                        piece.color,
                        (x + col_idx * size, y + row_idx * size, size - 1, size - 1),
                    )

    def draw_next_piece(self, logic: TetrisLogic) -> None:
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

        self.draw_mini_piece(logic.next_piece.shape_type, panel_x + 60, panel_y + 50, 25)

    def draw_held_piece(self, logic: TetrisLogic) -> None:
        """Draw the held piece preview"""
        panel_x = TOP_LEFT_X + PLAY_WIDTH + 20
        panel_y = TOP_LEFT_Y + 140
        panel_w = 200
        panel_h = 120

        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_w, panel_h), 2)

        text = self.font.render("Hold", True, WHITE)
        self.screen.blit(text, (panel_x + 10, panel_y + 10))

        if logic.held_piece:
            self.draw_mini_piece(logic.held_piece, panel_x + 60, panel_y + 50, 25)

        if not logic.can_hold:
            # Draw "locked" indicator
            lock_text = self.tiny_font.render("(used)", True, GRAY)
            self.screen.blit(lock_text, (panel_x + 70, panel_y + 100))

    def draw_stats(self, logic: TetrisLogic) -> None:
        """Draw game statistics"""
        panel_x = TOP_LEFT_X + PLAY_WIDTH + 20
        panel_y = TOP_LEFT_Y + 280

        stats = [
            ("Score", f"{logic.score}"),
            ("Lines", f"{logic.lines_cleared}"),
            ("Level", f"{logic.level}"),
            ("", ""),
            ("Singles", f"{logic.total_singles}"),
            ("Doubles", f"{logic.total_doubles}"),
            ("Triples", f"{logic.total_triples}"),
            ("Tetrises", f"{logic.total_tetrises}"),
        ]

        y_offset = panel_y
        for label, value in stats:
            if label:
                label_text = self.small_font.render(f"{label}:", True, LIGHT_GRAY)
                value_text = self.small_font.render(value, True, WHITE)
                self.screen.blit(label_text, (panel_x, y_offset))
                self.screen.blit(value_text, (panel_x + 100, y_offset))
            y_offset += 30

    def draw_button(self, rect: pygame.Rect, label: str, active: bool = True) -> None:
        """Draw a reusable UI button"""
        base_color = GREEN if active else GRAY
        pygame.draw.rect(self.screen, base_color, rect)
        pygame.draw.rect(self.screen, WHITE, rect, 2)
        text = self.small_font.render(label, True, BLACK)
        text_rect = text.get_rect(center=rect.center)
        self.screen.blit(text, text_rect)

    def draw_controls(self, show_controls_panel: bool) -> None:
        """Draw control instructions"""
        if not show_controls_panel:
            return

        controls = [
            ("←/→", "Move"),
            ("↑", "Rotate"),
            ("↓", "Soft Drop"),
            ("Space", "Hard Drop"),
            ("C", "Hold"),
            ("P", "Pause"),
            ("R", "Restart"),
            ("B", "Rewind"),
        ]

        panel_x = SCREEN_WIDTH - 220
        panel_y = TOP_LEFT_Y + 60

        pygame.draw.rect(
            self.screen,
            DARK_GRAY,
            (panel_x - 10, panel_y - 10, 200, len(controls) * 30 + 40),
        )
        pygame.draw.rect(
            self.screen,
            WHITE,
            (panel_x - 10, panel_y - 10, 200, len(controls) * 30 + 40),
            2,
        )

        title = self.font.render("Controls", True, WHITE)
        self.screen.blit(title, (panel_x, panel_y))

        y_offset = panel_y + 40
        for key, action in controls:
            key_text = self.small_font.render(key, True, GOLD)
            action_text = self.tiny_font.render(action, True, LIGHT_GRAY)
            self.screen.blit(key_text, (panel_x, y_offset))
            self.screen.blit(action_text, (panel_x + 80, y_offset + 5))
            y_offset += 30

    def draw_particles(self, logic: TetrisLogic) -> None:
        """Draw particle effects"""
        for particle in logic.particles:
            if particle.is_alive():
                # Draw particle with alpha
                surf = pygame.Surface((4, 4))
                surf.fill(particle.color)
                surf.set_alpha(particle.alpha)
                self.screen.blit(surf, (int(particle.x), int(particle.y)))

    def draw_score_popups(self, logic: TetrisLogic) -> None:
        """Draw score notification popups"""
        for popup in logic.score_popups:
            if popup.is_alive():
                # Render text with alpha
                text_surf = self.font_large.render(popup.text, True, popup.color)
                text_surf.set_alpha(popup.alpha)
                text_rect = text_surf.get_rect(
                    center=(int(popup.x), int(popup.y)),
                )
                self.screen.blit(text_surf, text_rect)

    def draw_menu(self, starting_level: int) -> None:
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
            color = GOLD if level == starting_level else WHITE
            level_text = self.font.render(f"Level {level}", True, color)
            text_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(level_text, text_rect)

            if level == starting_level:
                # Draw selection indicator
                pygame.draw.rect(
                    self.screen,
                    GOLD,
                    (
                        text_rect.x - 10,
                        text_rect.y - 5,
                        text_rect.width + 20,
                        text_rect.height + 10,
                    ),
                    2,
                )

            y_offset += 50

        # Start instruction
        start_text = self.small_font.render("Press ENTER to Start", True, GREEN)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, 550))
        self.screen.blit(start_text, start_rect)

        settings_text = self.small_font.render("Press S for Settings", True, LIGHT_GRAY)
        settings_rect = settings_text.get_rect(center=(SCREEN_WIDTH // 2, 590))
        self.screen.blit(settings_text, settings_rect)

        # Controls hint
        hint_text = self.tiny_font.render("Use UP/DOWN arrows to select level", True, GRAY)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 600))
        self.screen.blit(hint_text, hint_rect)

    def draw_game_over(self, logic: TetrisLogic) -> None:
        """Draw game over screen"""
        self.screen.fill(BLACK)

        # Game over screen
        game_over_text = self.font_large.render("GAME OVER", True, RED)
        score_text = self.font.render(f"Final Score: {logic.score}", True, WHITE)
        lines_text = self.font.render(
            f"Lines Cleared: {logic.lines_cleared}",
            True,
            WHITE,
        )
        level_text = self.font.render(f"Final Level: {logic.level}", True, WHITE)

        # Statistics
        stats_title = self.font.render("Line Clears:", True, GOLD)
        single_text = self.small_font.render(
            f"Singles: {logic.total_singles}",
            True,
            WHITE,
        )
        double_text = self.small_font.render(
            f"Doubles: {logic.total_doubles}",
            True,
            WHITE,
        )
        triple_text = self.small_font.render(
            f"Triples: {logic.total_triples}",
            True,
            WHITE,
        )
        tetris_text = self.small_font.render(
            f"Tetrises: {logic.total_tetrises}",
            True,
            CYAN,
        )

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
