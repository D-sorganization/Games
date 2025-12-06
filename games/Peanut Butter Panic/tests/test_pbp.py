import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  # noqa: PTH100

from peanut_butter_panic.core import GameWorld, InputState, PowerUp


class TestPBP(unittest.TestCase):
    def test_initial_state(self) -> None:
        """Test the initial state of the game world"""
        world = GameWorld()
        assert len(world.sandwiches) == 2
        # Config defaults: player_health=3
        assert world.player.health == 3
        assert world.stats.score == 0

    def test_movement(self) -> None:
        """Test player movement mechanics"""
        world = GameWorld()
        initial_pos = world.player.position
        # Move right
        input_state = InputState(move=(1.0, 0.0))
        # Update for 0.1 seconds
        world.update(0.1, input_state)

        assert world.player.position[0] > initial_pos[0]
        assert abs(world.player.position[1] - initial_pos[1]) < 1e-7

    def test_golden_bread(self) -> None:
        """Test golden bread powerup effect"""
        world = GameWorld()
        # Damage a sandwich
        world.sandwiches[0].health = 1

        # Apply golden bread
        p = PowerUp(position=(0,0), kind="golden_bread", duration=0.0)
        world._apply_powerup(p)  # noqa: SLF001

        # Should heal by 2 (up to max 5)
        assert world.sandwiches[0].health == 3

if __name__ == "__main__":
    unittest.main()
