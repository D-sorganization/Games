import os
import sys
import unittest

# Add games/Tetris to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  # noqa: PTH100

from src.constants import *
from src.game_logic import TetrisLogic
from src.tetromino import Tetromino


class TestTetris(unittest.TestCase):
    def test_tetromino_rotation(self) -> None:
        """Test tetromino rotation logic"""
        # T shape
        t = Tetromino(0, 0, "T")


        rotated = t.get_rotated_shape()
        # First rotation (0): default
        assert rotated == [[0, 1, 0], [1, 1, 1]]

        t.rotate()
        rotated = t.get_rotated_shape()
        # Rotated 90 deg clockwise
        # shape is [[0, 1, 0], [1, 1, 1]] (2 rows, 3 cols)
        # New rows = old cols = 3. New cols = old rows = 2.
        # x=0: y=1 -> 1, y=0 -> 0 => [1, 0]
        # x=1: y=1 -> 1, y=0 -> 1 => [1, 1]
        # x=2: y=1 -> 1, y=0 -> 0 => [1, 0]
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
        # Spawn is at y=0 usually.
        for y in range(4):
            for x in range(GRID_WIDTH):
                logic.grid[y][x] = RED

        # Check valid move for new piece
        # logic.new_piece() spawns at y=0.
        assert not logic.valid_move(piece)

if __name__ == "__main__":
    unittest.main()
