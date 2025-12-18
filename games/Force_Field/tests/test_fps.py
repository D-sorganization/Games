import os
import sys
import unittest

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # noqa: PTH100

from src.map import Map
from src.player import Player


class TestFPS(unittest.TestCase):
    def test_map_creation(self) -> None:
        """Test map initialization and bounds"""
        m = Map(30)
        assert m.size == 30
        # Check borders are walls
        assert m.grid[0][0] == 1
        assert m.grid[29][0] == 1

    def test_wall_collision(self) -> None:
        """Test wall collision detection"""
        m = Map(30)
        assert m.is_wall(0, 0)
        # Find a non-wall
        found = False
        for y in range(30):
            for x in range(30):
                if not m.is_wall(x, y):
                    found = True
                    break
            if found:
                break
        assert found

    def test_player_movement(self) -> None:
        """Test basic player movement"""
        # Mock map
        m = Map(30)
        # Clear a safe spot
        # We need to ensure surrounding walls don't block.
        # Player size logic is in move(): check wall at new_x, new_y.
        # radius check is for bots.

        start_x, start_y = 5.0, 5.0
        # Force clear path
        m.grid[int(start_y)][int(start_x)] = 0
        m.grid[int(start_y)][int(start_x) + 1] = 0  # Forward space
        m.grid[int(start_y)][int(start_x) - 1] = 0
        m.grid[int(start_y) + 1][int(start_x)] = 0
        m.grid[int(start_y) - 1][int(start_x)] = 0

        p = Player(start_x, start_y, 0)  # Facing East (0 rad)

        # Move forward
        # Speed 1.0
        p.move(m, [], forward=True, speed=1.0)
        assert abs(p.x - 6.0) < 1e-7
        assert abs(p.y - 5.0) < 1e-7


if __name__ == "__main__":
    unittest.main()
