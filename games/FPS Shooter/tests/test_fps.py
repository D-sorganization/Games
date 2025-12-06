import unittest
import math
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.map import Map
# Raycaster needs pygame to init? No, it just takes map.
# But it imports pygame. So we rely on system pygame.
from src.raycaster import Raycaster
from src.player import Player

class TestFPS(unittest.TestCase):
    def test_map_creation(self):
        m = Map(30)
        self.assertEqual(m.size, 30)
        # Check borders are walls
        self.assertEqual(m.grid[0][0], 1)
        self.assertEqual(m.grid[29][0], 1)

    def test_wall_collision(self):
        m = Map(30)
        self.assertTrue(m.is_wall(0, 0))
        # Find a non-wall
        found = False
        for y in range(30):
            for x in range(30):
                if not m.is_wall(x, y):
                    found = True
                    break
            if found: break
        self.assertTrue(found)

    def test_player_movement(self):
        # Mock map
        m = Map(30)
        # Clear a safe spot
        # We need to ensure surrounding walls don't block.
        # Player size logic is in move(): check wall at new_x, new_y.
        # radius check is for bots.

        start_x, start_y = 5.0, 5.0
        # Force clear path
        m.grid[int(start_y)][int(start_x)] = 0
        m.grid[int(start_y)][int(start_x)+1] = 0 # Forward space
        m.grid[int(start_y)][int(start_x)-1] = 0
        m.grid[int(start_y)+1][int(start_x)] = 0
        m.grid[int(start_y)-1][int(start_x)] = 0

        p = Player(start_x, start_y, 0) # Facing East (0 rad)

        # Move forward
        # Speed 1.0
        p.move(m, [], forward=True, speed=1.0)
        self.assertAlmostEqual(p.x, 6.0)
        self.assertAlmostEqual(p.y, 5.0)

if __name__ == '__main__':
    unittest.main()
