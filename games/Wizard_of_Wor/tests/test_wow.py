import sys
import unittest
from pathlib import Path

import pygame

# Initialize pygame for sprite classes
pygame.init()
pygame.display.set_mode((1, 1))  # Dummy display

# Add wizard_of_wor directory to path to support "from bullet import Bullet" style imports
sys.path.append(str((Path(__file__).parent / "../wizard_of_wor").resolve()))
sys.path.append(str((Path(__file__).parent / "..").resolve()))

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
