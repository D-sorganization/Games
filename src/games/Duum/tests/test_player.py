import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from src.player import Player


class TestPlayerExtra(unittest.TestCase):
    """Extra tests for the Player class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.player = Player(10.0, 10.0, 0.0)

    def test_move_zoomed(self) -> None:
        """Test move when zoomed returns early."""
        self.player.zoomed = True
        self.player.move(MagicMock(), [], forward=True)
        assert self.player.x == 10.0
        assert self.player.y == 10.0

    def test_move_shield_active(self) -> None:
        """Test move with shield active reduces speed."""
        self.player.shield_active = True

        def fake_move(entity, dx, dy, gm, b, radius=0.5) -> Any:
            entity.x += dx
            entity.y += dy

        with patch("games.shared.utils.try_move_entity", side_effect=fake_move):
            self.player.move(MagicMock(), [], forward=True)
        assert self.player.x != 10.0

    def test_move_not_moving(self) -> None:
        """Test move when blocked sets is_moving to False."""
        game_map = MagicMock()
        # Mock try_move_entity to not change x and y

        self.player.x = 10.0
        self.player.y = 10.0
        # If it moves 0, it should set is_moving = False
        # The built-in try_move_entity just moves if free.
        # We can just block visually or pass a solid map.
        # It's easier to mock the module function temporarily
        with patch("games.shared.utils.try_move_entity", return_value=None):
            self.player.move(game_map, [], forward=True)
            assert not self.player.is_moving

    def test_strafe_not_moving(self) -> None:
        """Test strafe when blocked sets is_moving to False."""
        game_map = MagicMock()
        self.player.x = 10.0
        self.player.y = 10.0
        with patch("games.shared.utils.try_move_entity", return_value=None):
            self.player.strafe(game_map, [], right=True)
            assert not self.player.is_moving

    def test_strafe_zoomed(self) -> None:
        """Test strafe zoomed returns."""
        self.player.zoomed = True
        self.player.strafe(MagicMock(), [], right=True)
        assert self.player.x == 10.0

    def test_strafe_shield_active_right(self) -> None:
        """Test strafe right with shield."""
        self.player.shield_active = True

        def fake_move(entity, dx, dy, gm, b, radius=0.5) -> Any:
            entity.x += dx
            entity.y += dy

        with patch("games.shared.utils.try_move_entity", side_effect=fake_move):
            self.player.strafe(MagicMock(), [], right=True)
        assert self.player.is_moving or (self.player.x != 10.0 or self.player.y != 10.0)

    def test_strafe_left(self) -> None:
        """Test strafe left."""

        def fake_move(entity, dx, dy, gm, b, radius=0.5) -> Any:
            entity.x += dx
            entity.y += dy

        with patch("games.shared.utils.try_move_entity", side_effect=fake_move):
            self.player.strafe(MagicMock(), [], right=False)
        assert self.player.is_moving

    def test_take_damage_invuln(self) -> None:
        """Test taking damage with shield or god_mode."""
        self.player.health = 100
        self.player.shield_active = True
        self.player.take_damage(50)
        assert self.player.health == 100

        self.player.shield_active = False
        self.player.god_mode = True
        self.player.take_damage(50)
        assert self.player.health == 100

    def test_take_damage_lethal(self) -> None:
        """Test taking damage leading to death."""
        self.player.health = 100
        self.player.take_damage(150)
        assert self.player.health == 0
        assert not self.player.alive

    def test_update_bobbing_is_moving(self) -> None:
        """Test bob phase when moving."""
        self.player.is_moving = True
        self.player.walk_distance = 5.0
        self.player.update()
        assert self.player.bob_phase == 5.0

        self.player.is_moving = False
        self.player.update()
        assert self.player.bob_phase == 4.5  # 5.0 * 0.9


if __name__ == "__main__":
    unittest.main()
