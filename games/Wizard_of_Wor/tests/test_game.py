import unittest
from unittest.mock import patch

import pygame
from wizard_of_wor.constants import (
    CELL_SIZE,
    GAME_AREA_HEIGHT,
    GAME_AREA_WIDTH,
    GAME_AREA_X,
    GAME_AREA_Y,
    PLAYER_LIVES,
)
from wizard_of_wor.game import SoundBoard, WizardOfWorGame


class TestWizardOfWorGame(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        # Mocking pygame.mixer to avoid audio issues
        with patch("pygame.mixer.init"), patch("pygame.mixer.Sound"):
            self.game = WizardOfWorGame()

        # Override dungeon with a mock if needed, or rely on actual dungeon which is
        # deterministic enough for basic logic
        # For now, let's use the real game structure but disable the loop

    def tearDown(self) -> None:
        pygame.quit()

    def test_initialization(self) -> None:
        self.assertEqual(self.game.state, "playing")
        self.assertEqual(self.game.level, 1)
        self.assertEqual(self.game.lives, PLAYER_LIVES)
        self.assertIsNotNone(self.game.player)
        self.assertTrue(len(self.game.enemies) > 0)
        self.assertIsNotNone(self.game.radar)

    def test_start_level(self) -> None:
        self.game.level = 2
        self.game.start_level()
        self.assertEqual(self.game.state, "playing")
        # Level 2 has 4 burwor, 2 garwor, 0 thorwor
        # AND possibly a Worluk because level > 1
        # Check if enemy count is EITHER 6 OR 7
        self.assertIn(len(self.game.enemies), [6, 7])

    def test_spawn_enemy_fallback(self) -> None:
        # Fill the map with walls or something to force fallback?
        # It's hard to force the random loop to fail without mocking Random or Dungeon.
        # But we can call _spawn_enemy directly

        from wizard_of_wor.enemy import Burwor

        # Mock dungeon.get_random_spawn_position to always return a position near player
        with patch.object(
            self.game.dungeon,
            "get_random_spawn_position",
            return_value=(self.game.player.x, self.game.player.y),
        ):
            # This should force the fallback to corner
            self.game._spawn_enemy(Burwor)

        # Check if the last added enemy is at a corner
        last_enemy = self.game.enemies[-1]
        corners = [
            (GAME_AREA_X + CELL_SIZE * 2, GAME_AREA_Y + CELL_SIZE * 2),
            (
                GAME_AREA_X + GAME_AREA_WIDTH - CELL_SIZE * 2,
                GAME_AREA_Y + CELL_SIZE * 2,
            ),
            (
                GAME_AREA_X + CELL_SIZE * 2,
                GAME_AREA_Y + GAME_AREA_HEIGHT - CELL_SIZE * 2,
            ),
            (
                GAME_AREA_X + GAME_AREA_WIDTH - CELL_SIZE * 2,
                GAME_AREA_Y + GAME_AREA_HEIGHT - CELL_SIZE * 2,
            ),
        ]
        self.assertIn((last_enemy.x, last_enemy.y), corners)

    def test_check_collisions_player_bullet_hits_enemy(self) -> None:
        enemy = self.game.enemies[0]
        # Place bullet on enemy
        from wizard_of_wor.bullet import Bullet

        bullet = Bullet(enemy.x, enemy.y, (1, 0), is_player_bullet=True)
        self.game.bullets.append(bullet)

        initial_score = self.game.score

        self.game.check_collisions()

        self.assertFalse(bullet.active)
        self.assertNotIn(bullet, self.game.bullets)
        self.assertFalse(enemy.alive)
        self.assertGreater(self.game.score, initial_score)

    def test_check_collisions_enemy_bullet_hits_player(self) -> None:
        # Place bullet on player
        from wizard_of_wor.bullet import Bullet

        bullet = Bullet(
            self.game.player.x, self.game.player.y, (1, 0), is_player_bullet=False
        )
        self.game.bullets.append(bullet)

        # Ensure player is not invulnerable
        self.game.player.invulnerable_timer = 0

        self.game.check_collisions()

        self.assertFalse(bullet.active)
        self.assertFalse(self.game.player.alive)

    def test_check_collisions_player_hits_enemy(self) -> None:
        enemy = self.game.enemies[0]
        self.game.player.x = enemy.x
        self.game.player.y = enemy.y
        self.game.player.rect.x = enemy.x - 11
        self.game.player.rect.y = enemy.y - 11

        self.game.player.invulnerable_timer = 0

        self.game.check_collisions()

        self.assertFalse(self.game.player.alive)

    def test_wizard_spawn_logic(self) -> None:
        # Kill all enemies
        self.game.enemies = []
        self.game.update()

        # Should be level complete
        self.assertEqual(self.game.state, "level_complete")

        # Reset
        self.game.state = "playing"
        self.game.wizard_spawned = False
        from wizard_of_wor.enemy import Burwor

        self.game.enemies = [Burwor(100, 100)]  # 1 enemy left

        self.game.update()

        # Check if wizard spawned (last enemy should be Wizard)
        self.assertTrue(self.game.wizard_spawned)
        self.assertEqual(self.game.enemies[-1].enemy_type, "wizard")

    def test_game_over(self) -> None:
        self.game.lives = 1
        self.game.player.alive = False  # Dead

        self.game.update()

        self.assertEqual(self.game.lives, 0)
        self.assertEqual(self.game.state, "game_over")

    def test_soundboard(self) -> None:
        sb = SoundBoard()
        # It should try to init mixer, but might fail in headless or succeed if dummy
        # driver works
        # We just test that methods don't crash
        sb.play("shot")
        sb.play_intro()
