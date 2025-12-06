import os
import sys
import unittest

import pygame

# Initialize pygame for sprite classes
pygame.init()
pygame.display.set_mode((1, 1)) # Dummy display

# Add wizard_of_wor directory to path to support "from bullet import Bullet" style imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../wizard_of_wor")))  # noqa: PTH100
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  # noqa: PTH100

# Now we can import
from constants import *  # noqa: E402
from player import Player  # noqa: E402


class TestWoW(unittest.TestCase):
    def test_player_init(self) -> None:
        """Test player initialization"""
        # Player init signature: (x, y)
        p = Player(100, 100)
        assert p.x == 100
        assert p.y == 100
        assert p.alive

if __name__ == "__main__":
    unittest.main()
