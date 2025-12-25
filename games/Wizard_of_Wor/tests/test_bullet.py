import unittest

import pygame
from wizard_of_wor.bullet import Bullet
from wizard_of_wor.constants import (
    BULLET_SPEED,
    GAME_AREA_WIDTH,
    GAME_AREA_X,
    GAME_AREA_Y,
    RED,
    RIGHT,
    YELLOW,
)


class MockDungeon:
    def is_wall(self, x: float, y: float) -> bool:
        # Create a simple wall at (500, 100)
        if 490 <= x <= 510 and 90 <= y <= 110:
            return True
        return False


class TestBullet(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.dungeon = MockDungeon()

    def tearDown(self) -> None:
        pygame.quit()

    def test_initialization(self) -> None:
        bullet = Bullet(100, 100, RIGHT, YELLOW, True)
        self.assertEqual(bullet.x, 100)
        self.assertEqual(bullet.y, 100)
        self.assertEqual(bullet.direction, RIGHT)
        self.assertEqual(bullet.color, YELLOW)
        self.assertTrue(bullet.is_player_bullet)
        self.assertTrue(bullet.active)

    def test_movement(self) -> None:
        bullet = Bullet(100, 100, RIGHT, YELLOW, True)
        initial_x = bullet.x
        bullet.update(self.dungeon)
        self.assertEqual(bullet.x, initial_x + BULLET_SPEED)

    def test_collision_with_wall(self) -> None:
        # Spawn bullet right before the wall
        bullet = Bullet(485, 100, RIGHT, YELLOW, True)
        bullet.update(self.dungeon)
        # Should be inside wall now or past it, triggering inactive
        # Let's move it enough times to ensure it hits
        for _ in range(5):
            bullet.update(self.dungeon)
        self.assertFalse(bullet.active)

    def test_out_of_bounds(self) -> None:
        # Spawn bullet at edge, update moves it
        # Bullet moves at BULLET_SPEED (7)
        # If we spawn at GAME_AREA_X - 1 (39) and move RIGHT (+7), new x is 46,
        # which is > 40.
        # So we should spawn it such that even after update it is out of bounds

        # Moving LEFT from GAME_AREA_X
        bullet = Bullet(GAME_AREA_X - 1, GAME_AREA_Y, (-1, 0), YELLOW, True)
        bullet.update(self.dungeon)
        self.assertFalse(bullet.active)

        # Moving RIGHT from GAME_AREA_X + GAME_AREA_WIDTH
        bullet = Bullet(
            GAME_AREA_X + GAME_AREA_WIDTH + 1, GAME_AREA_Y, (1, 0), YELLOW, True
        )
        bullet.update(self.dungeon)
        self.assertFalse(bullet.active)

    def test_enemy_bullet(self) -> None:
        bullet = Bullet(100, 100, RIGHT, RED, False)
        self.assertFalse(bullet.is_player_bullet)
        self.assertEqual(bullet.color, RED)
