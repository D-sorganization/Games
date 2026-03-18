"""Original Tetris tests — kept for backward compatibility.

Uses pytest conventions (no sys.path hacking required).
"""

from __future__ import annotations

from games.Tetris.src.constants import BLACK, CYAN, GRID_HEIGHT, GRID_WIDTH, RED
from games.Tetris.src.game_logic import TetrisLogic
from games.Tetris.src.tetromino import Tetromino


class TestTetris:
    def test_tetromino_rotation(self) -> None:
        """Test tetromino rotation logic"""
        # T shape
        t = Tetromino(0, 0, "T")

        rotated = t.get_rotated_shape()
        # First rotation (0): default
        assert rotated == [[0, 1, 0], [1, 1, 1]]

        t.rotate()
        rotated = t.get_rotated_shape()
        assert rotated == [[1, 0], [1, 1], [1, 0]]

    def test_line_clearing(self) -> None:
        """Test line clearing mechanics and scoring"""
        logic = TetrisLogic()
        # Fill a line
        for x in range(GRID_WIDTH):
            logic.grid[GRID_HEIGHT - 1][x] = CYAN

        assert logic.grid[GRID_HEIGHT - 1][0] == CYAN
        logic.clear_lines()
        # Line should be cleared
        assert logic.grid[GRID_HEIGHT - 1][0] == BLACK
        assert logic.lines_cleared == 1
        # Score calculation: 100 * level (1) = 100.
        assert logic.score == 100

    def test_game_over(self) -> None:
        """Test game over condition detection"""
        logic = TetrisLogic()
        # Place a piece at spawn
        piece = logic.new_piece()
        # Fill the grid at spawn location to cause collision
        for y in range(4):
            for x in range(GRID_WIDTH):
                logic.grid[y][x] = RED

        # Check valid move for new piece
        assert not logic.valid_move(piece)
