import unittest
import sys
import os

# Add games/Tetris to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tetromino import Tetromino
from src.game_logic import TetrisLogic
from src.constants import *

class TestTetris(unittest.TestCase):
    def test_tetromino_rotation(self):
        # T shape
        t = Tetromino(0, 0, "T")
        # Default: [[0, 1, 0], [1, 1, 1]]

        rotated = t.get_rotated_shape()
        # First rotation (0): default
        self.assertEqual(rotated, [[0, 1, 0], [1, 1, 1]])

        t.rotate()
        rotated = t.get_rotated_shape()
        # Rotated 90 deg clockwise
        # shape is [[0, 1, 0], [1, 1, 1]] (2 rows, 3 cols)
        # New rows = old cols = 3. New cols = old rows = 2.
        # x=0: y=1 -> 1, y=0 -> 0 => [1, 0]
        # x=1: y=1 -> 1, y=0 -> 1 => [1, 1]
        # x=2: y=1 -> 1, y=0 -> 0 => [1, 0]
        self.assertEqual(rotated, [[1, 0], [1, 1], [1, 0]])

    def test_line_clearing(self):
        logic = TetrisLogic()
        # Fill a line
        for x in range(GRID_WIDTH):
            logic.grid[GRID_HEIGHT - 1][x] = CYAN

        self.assertEqual(logic.grid[GRID_HEIGHT - 1][0], CYAN)
        logic.clear_lines()
        # Line should be cleared (BLACK is (0,0,0) which is truthy? No, it's tuple)
        self.assertEqual(logic.grid[GRID_HEIGHT - 1][0], BLACK)
        self.assertEqual(logic.lines_cleared, 1)
        # Score calculation: 100 * level (1) = 100.
        self.assertEqual(logic.score, 100)

    def test_game_over(self):
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
        self.assertFalse(logic.valid_move(piece))

if __name__ == '__main__':
    unittest.main()
