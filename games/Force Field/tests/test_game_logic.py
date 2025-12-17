import math
import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.resolve()))

import src.constants as C  # noqa: N812
from src.bot import Bot
from src.map import Map
from src.player import Player
from src.projectile import Projectile


class TestGameLogic(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.map = Map(30)
        # Clear center for testing
        for y in range(10, 20):
            for x in range(10, 20):
                self.map.grid[y][x] = 0

    def test_player_weapon_switching(self) -> None:
        """Test player weapon switching functionality."""
        player = Player(15.0, 15.0, 0.0)

        player.switch_weapon("rifle")
        assert player.current_weapon == "rifle"

        player.switch_weapon("pistol")
        assert player.current_weapon == "pistol"

        # Test non-existent weapon (should not switch)
        player.switch_weapon("bfg9000")
        assert player.current_weapon == "pistol"

    def test_player_shooting_ammo(self) -> None:
        """Test player shooting mechanics and ammo consumption."""
        player = Player(15.0, 15.0, 0.0)
        player.current_weapon = "pistol"
        initial_clip = player.weapon_state["pistol"]["clip"]

        # Shoot
        fired = player.shoot()
        assert fired
        assert player.weapon_state["pistol"]["clip"] == initial_clip - 1
        assert player.shooting
        assert player.shoot_timer > 0

        # Try shoot immediately (should fail due to cooldown)
        fired_again = player.shoot()
        assert not fired_again

    def test_player_reload(self) -> None:
        """Test player weapon reload functionality."""
        player = Player(15.0, 15.0, 0.0)
        player.current_weapon = "pistol"
        player.weapon_state["pistol"]["clip"] = 0

        player.reload()
        assert player.weapon_state["pistol"]["reloading"]

        # Simulate update cycles
        reload_time = player.weapon_state["pistol"]["reload_timer"]
        for _ in range(reload_time + 1):
            player.update()

        assert not player.weapon_state["pistol"]["reloading"]
        assert player.weapon_state["pistol"]["clip"] == C.WEAPONS["pistol"]["clip_size"]

    def test_bot_movement_and_collision(self) -> None:
        """Test bot movement towards player and collision detection."""
        # Bot at 12, 12, Player at 18, 18
        bot = Bot(12.0, 12.0, 1, enemy_type="zombie")
        player = Player(18.0, 18.0, 0.0)

        initial_dist = math.sqrt((player.x - bot.x) ** 2 + (player.y - bot.y) ** 2)

        # Update bot
        bot.update(self.map, player, [])

        new_dist = math.sqrt((player.x - bot.x) ** 2 + (player.y - bot.y) ** 2)

        # Bot should move closer
        assert new_dist < initial_dist

    def test_bot_takes_damage(self) -> None:
        """Test bot damage handling and death state."""
        bot = Bot(12.0, 12.0, 1, enemy_type="zombie")
        initial_health = bot.health

        bot.take_damage(10)
        assert bot.health == initial_health - 10
        assert bot.alive

        # Kill bot
        bot.take_damage(bot.health + 10)
        assert not bot.alive
        assert bot.dead

    def test_projectile_update(self) -> None:
        """Test projectile movement and collision with walls."""
        # Fire east
        p = Projectile(15.0, 15.0, 0.0, 10, 1.0)

        p.update(self.map)
        assert abs(p.x - 16.0) < 0.01
        assert abs(p.y - 15.0) < 0.01
        assert p.alive

        # Hit wall
        # Place wall at 17, 15
        self.map.grid[15][17] = 1
        p.update(self.map)  # 17.0
        # It enters the wall cell, so it should die
        assert not p.alive

    def test_player_rocket_launcher(self) -> None:
        """Test rocket launcher."""
        player = Player(15.0, 15.0, 0.0)
        # Unlock rocket (assuming we might need to, but switch_weapon checks availability elsewhere.
        # Player class logic doesn't strictly check unlocks, Game class does.
        # But wait, Player.switch_weapon validates against WEAPONS keys.)

        player.switch_weapon("rocket")
        assert player.current_weapon == "rocket"

        initial_clip = player.weapon_state["rocket"]["clip"]
        assert initial_clip == 1

        fired = player.shoot()
        assert fired
        assert player.weapon_state["rocket"]["clip"] == 0


if __name__ == "__main__":
    unittest.main()
