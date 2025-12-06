import unittest
import sys
import os
import pygame

# Initialize pygame for sprite classes
pygame.init()
pygame.display.set_mode((1, 1)) # Dummy display

# Add wizard_of_wor directory to path to support "from bullet import Bullet" style imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../wizard_of_wor')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import
from player import Player
from constants import *

class TestWoW(unittest.TestCase):
    def test_player_init(self):
        # Player init signature: (x, y)
        p = Player(100, 100)
        self.assertEqual(p.x, 100)
        self.assertEqual(p.y, 100)
        self.assertEqual(p.alive, True)

if __name__ == '__main__':
    unittest.main()
