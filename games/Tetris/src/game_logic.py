import random
from typing import Optional, List, Dict, Any
from .constants import *
from .tetromino import Tetromino
from .particles import Particle, ScorePopup

class TetrisLogic:
    """Handles the game logic, state, and rules"""

    def __init__(self):
        self.starting_level = 1
        self.allow_rewind = False
        self.reset_game()

    def reset_game(self) -> None:
        """Reset the game state"""
        self.grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.held_piece: Optional[str] = None
        self.can_hold = True
        self.game_over = False
        self.score = 0
        self.lines_cleared = 0
        self.level = self.starting_level
        self.fall_time = 0
        self.fall_speed = max(50, 500 - (self.level - 1) * 40)
        self.combo = 0
        self.particles: List[Particle] = []
        self.score_popups: List[ScorePopup] = []
        self.lines_cleared_this_drop = 0
        self.total_singles = 0
        self.total_doubles = 0
        self.total_triples = 0
        self.total_tetrises = 0
        self.rewind_history: List[Dict[str, Any]] = []

    def new_piece(self) -> Tetromino:
        """Create a new random tetromino"""
        shape_type = random.choice(list(SHAPES.keys()))
        return Tetromino(GRID_WIDTH // 2 - 1, 0, shape_type)

    def copy_piece(self, piece: Tetromino) -> Tetromino:
        """Create a shallow copy of a tetromino"""
        clone = Tetromino(piece.x, piece.y, piece.shape_type)
        clone.rotation = piece.rotation
        return clone

    def create_snapshot(self) -> Dict[str, Any]:
        """Capture the current game state for rewinding"""
        return {
            "grid": [row[:] for row in self.grid],
            "current_piece": self.copy_piece(self.current_piece),
            "next_piece": self.copy_piece(self.next_piece),
            "held_piece": self.held_piece,
            "can_hold": self.can_hold,
            "score": self.score,
            "lines_cleared": self.lines_cleared,
            "level": self.level,
            "fall_time": self.fall_time,
            "fall_speed": self.fall_speed,
            "combo": self.combo,
            "lines_cleared_this_drop": self.lines_cleared_this_drop,
            "total_singles": self.total_singles,
            "total_doubles": self.total_doubles,
            "total_triples": self.total_triples,
            "total_tetrises": self.total_tetrises,
        }

    def restore_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Restore a saved game state"""
        self.grid = snapshot["grid"]
        self.current_piece = snapshot["current_piece"]
        self.next_piece = snapshot["next_piece"]
        self.held_piece = snapshot["held_piece"]
        self.can_hold = bool(snapshot["can_hold"])
        self.score = int(snapshot["score"])
        self.lines_cleared = int(snapshot["lines_cleared"])
        self.level = int(snapshot["level"])
        self.fall_time = int(snapshot["fall_time"])
        self.fall_speed = int(snapshot["fall_speed"])
        self.combo = int(snapshot["combo"])
        self.lines_cleared_this_drop = int(snapshot["lines_cleared_this_drop"])
        self.total_singles = int(snapshot["total_singles"])
        self.total_doubles = int(snapshot["total_doubles"])
        self.total_triples = int(snapshot["total_triples"])
        self.total_tetrises = int(snapshot["total_tetrises"])

    def update_rewind_history(self) -> None:
        """Append the current state to the rewind history"""
        if not self.allow_rewind:
            self.rewind_history.clear()
            return

        self.rewind_history.append(self.create_snapshot())
        if len(self.rewind_history) > REWIND_HISTORY_LIMIT:
            self.rewind_history.pop(0)

    def rewind(self) -> None:
        """Rewind the game to a previous point"""
        if not self.allow_rewind:
            return
        if len(self.rewind_history) <= REWIND_STEP:
            return

        snapshot = self.rewind_history[-REWIND_STEP]
        self.rewind_history = self.rewind_history[:-REWIND_STEP]
        self.restore_snapshot(snapshot)
        self.game_over = False
        # State change should be handled by the controller/main loop, logic just updates internal state

    def valid_move(
        self,
        piece: Tetromino,
        x_offset: int = 0,
        y_offset: int = 0,
        rotation_offset: int = 0,
    ) -> bool:
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
            temp = self.held_piece
            self.held_piece = self.current_piece.shape_type
            new_piece = Tetromino(GRID_WIDTH // 2 - 1, 0, temp)
            if not self.valid_move(new_piece):
                self.game_over = True
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
                1: 100,  # Single
                2: 300,  # Double
                3: 500,  # Triple
                4: 800,  # Tetris
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

            # Create score popup
            popup_text = self.get_line_clear_text(num_lines)
            if combo_for_bonus > 1:
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
                level_popup = ScorePopup(
                    f"LEVEL {self.level}!",
                    popup_x,
                    popup_y - 40,
                    SILVER,
                )
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

    def update_particles(self) -> None:
        for particle in self.particles[:]:
            if particle.is_alive():
                particle.update()
            else:
                self.particles.remove(particle)

    def update_popups(self) -> None:
        for popup in self.score_popups[:]:
            if popup.is_alive():
                popup.update()
            else:
                self.score_popups.remove(popup)

    def update(self, delta_time_ms: int) -> None:
        """Main update loop for game logic"""
        self.update_rewind_history()
        self.fall_time += delta_time_ms

        if self.fall_time >= self.fall_speed:
            self.fall_time = 0
            if self.valid_move(self.current_piece, y_offset=1):
                self.current_piece.y += 1
            else:
                self.lock_piece()

        self.update_particles()
        self.update_popups()
