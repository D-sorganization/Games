"""Tests for Force Field Shield functionality."""

import unittest

import games.Force_Field.src.constants as C
from games.Force_Field.src.input_manager import InputManager
from games.Force_Field.src.map import Map
from games.Force_Field.src.player import Player


class TestShieldFunctionality(unittest.TestCase):
    """Test the Force Field Shield mechanics."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.player = Player(10.0, 10.0, 0.0)
        self.player.invincible = False
        self.game_map = Map(20)
        self.input_manager = InputManager()

        # Clear center area for movement tests
        for y in range(5, 15):
            for x in range(5, 15):
                self.game_map.grid[y][x] = 0

    def test_shield_key_binding(self) -> None:
        """Test that shield is bound to SPACE key."""
        import pygame

        self.assertEqual(self.input_manager.bindings["shield"], pygame.K_SPACE)

    def test_shield_activation(self) -> None:
        """Test shield activation and deactivation."""
        # Initially shield should be inactive
        self.assertFalse(self.player.shield_active)
        self.assertEqual(self.player.shield_timer, C.SHIELD_MAX_DURATION)

        # Activate shield
        self.player.set_shield(True)
        self.assertTrue(self.player.shield_active)

        # Deactivate shield
        self.player.set_shield(False)
        self.assertFalse(self.player.shield_active)

    def test_shield_prevents_movement(self) -> None:
        """Test that shield prevents all movement."""
        initial_x = self.player.x
        initial_y = self.player.y

        # Activate shield
        self.player.set_shield(True)
        self.assertTrue(self.player.shield_active)

        # Try to move forward
        self.player.move(self.game_map, [])
        self.assertEqual(self.player.x, initial_x)
        self.assertEqual(self.player.y, initial_y)

        # Try to strafe
        self.player.strafe(self.game_map, [])
        self.assertEqual(self.player.x, initial_x)
        self.assertEqual(self.player.y, initial_y)

    def test_shield_blocks_damage(self) -> None:
        """Test that shield blocks all damage."""
        initial_health = self.player.health

        # Activate shield
        self.player.set_shield(True)

        # Take damage while shielded
        self.player.take_damage(50)
        self.assertEqual(self.player.health, initial_health)

        # Deactivate shield and take damage
        self.player.set_shield(False)
        self.player.take_damage(25)
        self.assertEqual(self.player.health, initial_health - 25)

    def test_shield_timer_depletion(self) -> None:
        """Test shield timer depletion and auto-deactivation."""
        # Activate shield
        self.player.set_shield(True)
        initial_timer = self.player.shield_timer

        # Update player (simulates frame updates)
        self.player.update()

        # Timer should decrease
        self.assertEqual(self.player.shield_timer, initial_timer - 1)

        # Set shield timer to 0 and update - should deactivate immediately
        self.player.shield_timer = 0
        self.player.update()

        # Shield should auto-deactivate
        self.assertFalse(self.player.shield_active)
        self.assertEqual(self.player.shield_recharge_delay, C.SHIELD_COOLDOWN_DEPLETED)

    def test_shield_cooldown_prevents_activation(self) -> None:
        """Test that shield cannot be activated during cooldown."""
        # Set cooldown
        self.player.shield_recharge_delay = 100

        # Try to activate shield
        self.player.set_shield(True)

        # Should not activate due to cooldown
        self.assertFalse(self.player.shield_active)

    def test_shield_recharge(self) -> None:
        """Test shield timer recharge after cooldown."""
        # Deplete shield
        self.player.shield_timer = 0
        self.player.shield_recharge_delay = 0

        # Update to trigger recharge
        self.player.update()

        # Timer should increase
        self.assertEqual(self.player.shield_timer, 2)  # +2 per frame recharge rate

    def test_bomb_auto_activates_shield(self) -> None:
        """Test that bomb activation auto-activates shield."""
        # Ensure bomb is available
        self.player.bombs = 1
        self.player.bomb_cooldown = 0

        # Activate bomb
        result = self.player.activate_bomb()

        self.assertTrue(result)
        self.assertTrue(self.player.shield_active)
        self.assertEqual(self.player.bombs, 0)
        self.assertEqual(self.player.bomb_cooldown, C.BOMB_COOLDOWN)

    def test_god_mode_blocks_damage(self) -> None:
        """Test that god mode also blocks damage."""
        initial_health = self.player.health

        # Enable god mode
        self.player.god_mode = True

        # Take damage
        self.player.take_damage(50)

        # Health should be unchanged
        self.assertEqual(self.player.health, initial_health)

    def test_shield_cooldown_types(self) -> None:
        """Test different cooldown durations."""
        # Normal cooldown (manual deactivation)
        self.player.set_shield(True)
        self.player.set_shield(False)
        self.assertEqual(self.player.shield_recharge_delay, C.SHIELD_COOLDOWN_NORMAL)

        # Reset for next test
        self.player.shield_recharge_delay = 0
        self.player.shield_timer = C.SHIELD_MAX_DURATION

        # Depleted cooldown (timer runs out)
        self.player.set_shield(True)
        self.player.shield_timer = 0
        self.player.update()
        self.assertEqual(self.player.shield_recharge_delay, C.SHIELD_COOLDOWN_DEPLETED)


if __name__ == "__main__":
    unittest.main()
