import sys
import os
import unittest
import math
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.player import Player
from src.bot import Bot
from src.map import Map
from src.projectile import Projectile
import src.constants as C

class TestGameLogic(unittest.TestCase):
    def setUp(self):
        self.map = Map(30)
        # Clear center for testing
        for y in range(10, 20):
            for x in range(10, 20):
                self.map.grid[y][x] = 0

    def test_player_weapon_switching(self):
        player = Player(15.0, 15.0, 0.0)

        player.switch_weapon("rifle")
        self.assertEqual(player.current_weapon, "rifle")

        player.switch_weapon("pistol")
        self.assertEqual(player.current_weapon, "pistol")

        # Test non-existent weapon (should not switch)
        player.switch_weapon("bfg9000")
        self.assertEqual(player.current_weapon, "pistol")

    def test_player_shooting_ammo(self):
        player = Player(15.0, 15.0, 0.0)
        player.current_weapon = "pistol"
        initial_clip = player.weapon_state["pistol"]["clip"]

        # Shoot
        fired = player.shoot()
        self.assertTrue(fired)
        self.assertEqual(player.weapon_state["pistol"]["clip"], initial_clip - 1)
        self.assertTrue(player.shooting)
        self.assertGreater(player.shoot_timer, 0)

        # Try shoot immediately (should fail due to cooldown)
        fired_again = player.shoot()
        self.assertFalse(fired_again)

    def test_player_reload(self):
        player = Player(15.0, 15.0, 0.0)
        player.current_weapon = "pistol"
        player.weapon_state["pistol"]["clip"] = 0

        player.reload()
        self.assertTrue(player.weapon_state["pistol"]["reloading"])

        # Simulate update cycles
        reload_time = player.weapon_state["pistol"]["reload_timer"]
        for _ in range(reload_time + 1):
            player.update()

        self.assertFalse(player.weapon_state["pistol"]["reloading"])
        self.assertEqual(player.weapon_state["pistol"]["clip"], C.WEAPONS["pistol"]["clip_size"])

    def test_bot_movement_and_collision(self):
        # Bot at 12, 12, Player at 18, 18
        bot = Bot(12.0, 12.0, 1, enemy_type="zombie")
        player = Player(18.0, 18.0, 0.0)

        initial_dist = math.sqrt((player.x - bot.x)**2 + (player.y - bot.y)**2)

        # Update bot
        bot.update(self.map, player, [])

        new_dist = math.sqrt((player.x - bot.x)**2 + (player.y - bot.y)**2)

        # Bot should move closer
        self.assertLess(new_dist, initial_dist)

    def test_bot_takes_damage(self):
        bot = Bot(12.0, 12.0, 1, enemy_type="zombie")
        initial_health = bot.health

        bot.take_damage(10)
        self.assertEqual(bot.health, initial_health - 10)
        self.assertTrue(bot.alive)

        # Kill bot
        bot.take_damage(bot.health + 10)
        self.assertFalse(bot.alive)
        self.assertTrue(bot.dead)

    def test_projectile_update(self):
        # Fire east
        p = Projectile(15.0, 15.0, 0.0, 10, 1.0)

        p.update(self.map)
        self.assertAlmostEqual(p.x, 16.0)
        self.assertAlmostEqual(p.y, 15.0)
        self.assertTrue(p.alive)

        # Hit wall
        # Place wall at 17, 15
        self.map.grid[15][17] = 1
        p.update(self.map) # 17.0
        # It enters the wall cell, so it should die
        self.assertFalse(p.alive)

if __name__ == "__main__":
    unittest.main()
