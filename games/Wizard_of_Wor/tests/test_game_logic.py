import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pygame

# Set dummy video driver before initializing pygame
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1, 1))

# Add wizard_of_wor directory to path
sys.path.append(str((Path(__file__).parent / "../wizard_of_wor").resolve()))

from dungeon import Dungeon
from game import WizardOfWorGame
from player import Player
from enemy import Enemy
from constants import GAME_AREA_X, CELL_SIZE, GAME_AREA_WIDTH

class TestGameLogic(unittest.TestCase):
    def setUp(self):
        # Patch pygame.mixer to avoid audio issues
        self.mixer_patch = patch('pygame.mixer')
        self.mixer_mock = self.mixer_patch.start()

        self.game = WizardOfWorGame()
        # Stop the intro sound to prevent errors if sound is somehow enabled
        if hasattr(self.game, 'soundboard'):
             self.game.soundboard.enabled = False

    def tearDown(self):
        self.mixer_patch.stop()
        pygame.quit()

    def test_dungeon_spawn_points(self):
        dungeon = Dungeon()

        # Check enemy spawn points (default)
        pos_enemy = dungeon.get_random_spawn_position(prefer_player=False)
        self.assertTrue(pos_enemy[0] >= GAME_AREA_X)

        # Check player spawn points
        pos_player = dungeon.get_random_spawn_position(prefer_player=True)
        self.assertTrue(pos_player[0] >= GAME_AREA_X)

        self.assertNotEqual(dungeon.player_spawn_cells, dungeon.enemy_spawn_cells)

    def test_respawn_player_uses_correct_pool(self):
        """
        Verify respawn_player uses prefer_player=True.
        """
        # Mock dungeon to have distinct pools
        self.game.dungeon = MagicMock()
        self.game.dungeon.get_random_spawn_position.return_value = (100, 100)

        # Call respawn_player
        self.game.respawn_player()

        # Verify get_random_spawn_position was called with prefer_player=True
        self.game.dungeon.get_random_spawn_position.assert_called_with(prefer_player=True)

        # Check player initialized correctly
        self.assertIsNotNone(self.game.player)
        self.assertEqual(self.game.player.x, 100)
        self.assertEqual(self.game.player.y, 100)

    def test_respawn_clears_enemy_bullets(self):
        """
        Verify respawn_player handles bullets correctly.
        (Actually the code keeps player bullets, filters out everything else?
        The code is: self.bullets = [b for b in self.bullets if b.is_player_bullet]
        This means enemy bullets are removed.)
        """
        from bullet import Bullet

        p_bullet = Bullet(0, 0, (0,0), is_player_bullet=True)
        e_bullet = Bullet(0, 0, (0,0), is_player_bullet=False)

        self.game.bullets = [p_bullet, e_bullet]

        # Mock dungeon to avoid errors
        self.game.dungeon = MagicMock()
        self.game.dungeon.get_random_spawn_position.return_value = (100, 100)

        self.game.respawn_player()

        self.assertIn(p_bullet, self.game.bullets)
        self.assertNotIn(e_bullet, self.game.bullets)

if __name__ == "__main__":
    unittest.main()
