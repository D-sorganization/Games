import unittest

import pygame
from wizard_of_wor.constants import (
    DOWN,
    GAME_AREA_X,
    GAME_AREA_Y,
    PLAYER_SPEED,
    RIGHT,
    UP,
)
from wizard_of_wor.enemy import Burwor, Garwor, Thorwor, Wizard, Worluk
from wizard_of_wor.player import Player
from wizard_of_wor.radar import Radar


class MockDungeon:
    def can_move_to(self, rect: pygame.Rect) -> bool:
        return True

    def get_random_spawn_position(self, prefer_player: bool = False) -> tuple[int, int]:
        return (100, 100)


class TestPlayer(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.player = Player(100, 100)
        self.dungeon = MockDungeon()

    def tearDown(self) -> None:
        pygame.quit()

    def test_initialization(self) -> None:
        self.assertEqual(self.player.x, 100)
        self.assertEqual(self.player.y, 100)
        self.assertTrue(self.player.alive)
        self.assertEqual(self.player.direction, RIGHT)

    def test_movement(self) -> None:
        # Simulate key presses
        keys = {
            pygame.K_w: True,
            pygame.K_s: False,
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False,
        }

        initial_y = self.player.y
        self.player.update(keys, self.dungeon)
        self.assertEqual(self.player.y, initial_y - PLAYER_SPEED)
        self.assertEqual(self.player.direction, UP)

        keys = {
            pygame.K_w: False,
            pygame.K_s: True,
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False,
        }
        initial_y = self.player.y
        self.player.update(keys, self.dungeon)
        self.assertEqual(self.player.y, initial_y + PLAYER_SPEED)
        self.assertEqual(self.player.direction, DOWN)

    def test_shooting(self) -> None:
        bullet, muzzle = self.player.shoot()
        self.assertIsNotNone(bullet)
        self.assertIsNotNone(muzzle)
        self.assertEqual(self.player.shoot_cooldown, self.player.shoot_delay)

        # Test cooldown
        bullet, muzzle = self.player.shoot()
        self.assertIsNone(bullet)
        self.assertIsNone(muzzle)

    def test_damage_and_shield(self) -> None:
        # Test shield
        self.player.grant_shield(100)
        self.assertTrue(self.player.invulnerable_timer > 0)
        took_damage = self.player.take_damage()
        self.assertFalse(took_damage)
        self.assertTrue(self.player.alive)

        # Remove shield
        self.player.invulnerable_timer = 0
        took_damage = self.player.take_damage()
        self.assertTrue(took_damage)
        self.assertFalse(self.player.alive)


class TestEnemy(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.dungeon = MockDungeon()

    def tearDown(self) -> None:
        pygame.quit()

    def test_enemy_types(self) -> None:
        burwor = Burwor(100, 100)
        self.assertEqual(burwor.enemy_type, "burwor")
        self.assertFalse(burwor.can_shoot)

        garwor = Garwor(100, 100)
        self.assertEqual(garwor.enemy_type, "garwor")
        self.assertTrue(garwor.can_shoot)

        thorwor = Thorwor(100, 100)
        self.assertEqual(thorwor.enemy_type, "thorwor")
        self.assertTrue(thorwor.can_shoot)

        worluk = Worluk(100, 100)
        self.assertEqual(worluk.enemy_type, "worluk")

        wizard = Wizard(100, 100)
        self.assertEqual(wizard.enemy_type, "wizard")

    def test_movement(self) -> None:
        enemy = Garwor(100, 100)
        initial_x, initial_y = enemy.x, enemy.y
        enemy.speed = 2  # Set a known speed

        # Force a direction
        enemy.direction = RIGHT
        enemy.move_timer = 0  # Reset timer to avoid random direction change
        enemy.direction_change_interval = 100

        player_pos = (200, 100)
        enemy.update(self.dungeon, player_pos)

        self.assertNotEqual((enemy.x, enemy.y), (initial_x, initial_y))

    def test_shooting(self) -> None:
        enemy = Garwor(100, 100)
        enemy.shoot_timer = 0
        bullet = enemy.try_shoot()
        self.assertIsNotNone(bullet)
        self.assertFalse(bullet.is_player_bullet)

    def test_wizard_appearance(self) -> None:
        wizard = Wizard(100, 100)
        self.assertTrue(wizard.appearance_timer > 0)
        wizard.update(self.dungeon, (200, 200))
        # Wizard shouldn't move while appearance timer > 0
        self.assertEqual(wizard.x, 100)
        self.assertEqual(wizard.y, 100)

        wizard.appearance_timer = 0
        wizard.update(self.dungeon, (200, 200))
        # Now it should move (unless random chance prevents it or it chooses to stay)
        # But we can verify appearance logic logic path was taken


class TestRadar(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.radar = Radar()
        self.screen = pygame.Surface((800, 600))

    def tearDown(self) -> None:
        pygame.quit()

    def test_update(self) -> None:
        initial_angle = self.radar.sweep_angle
        self.radar.update()
        self.assertNotEqual(self.radar.sweep_angle, initial_angle)

    def test_draw(self) -> None:
        player = Player(GAME_AREA_X + 10, GAME_AREA_Y + 10)
        enemies = [Burwor(GAME_AREA_X + 50, GAME_AREA_Y + 50)]

        # Just ensure it runs without error
        try:
            self.radar.draw(self.screen, enemies, player)
        except Exception as e:
            self.fail(f"Radar.draw raised exception: {e}")
