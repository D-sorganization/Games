import unittest

from games.Force_Field.src.bot import Bot
from games.Force_Field.src.map import Map
from games.Force_Field.src.player import Player


class TestNinja(unittest.TestCase):
    def setUp(self) -> None:
        self.map = Map(30)
        # Clear area
        for y in range(10, 20):
            for x in range(10, 20):
                self.map.grid[y][x] = 0

    def test_ninja_attack(self) -> None:
        """Test that ninja attacks when close."""
        ninja = Bot(15.0, 15.0, 1, enemy_type="ninja")
        player = Player(15.5, 15.0, 0.0) # Very close (0.5 distance)

        initial_health = player.health

        # Ninja should attack immediately because distance < 1.2
        ninja.update(self.map, player, [])

        assert player.health < initial_health
        assert ninja.attack_timer > 0

    def test_ninja_move(self) -> None:
        """Test that ninja moves when far."""
        ninja = Bot(12.0, 12.0, 1, enemy_type="ninja")
        player = Player(18.0, 18.0, 0.0)

        initial_x = ninja.x
        initial_y = ninja.y

        ninja.update(self.map, player, [])

        # Should have moved towards player
        assert ninja.x != initial_x or ninja.y != initial_y

        # Should not have attacked (timer 0)
        assert ninja.attack_timer == 0

if __name__ == "__main__":
    unittest.main()
