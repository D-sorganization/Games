"""Tests for games.Zombie_Survival.src.player."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from games.Zombie_Survival.src.player import Player


@pytest.fixture()
def player() -> Player:
    return Player(2.5, 2.5, 0.0)


@pytest.fixture()
def mock_map() -> MagicMock:
    m = MagicMock()
    m.grid = [[0] * 10 for _ in range(10)]
    m.width = 10
    m.height = 10
    return m


class TestZSPlayerInit:
    def test_init_sets_position(self, player: Player) -> None:
        assert player.x == 2.5
        assert player.y == 2.5
        assert player.angle == 0.0

    def test_init_alive(self, player: Player) -> None:
        assert player.alive is True


class TestZSPlayerMove:
    def test_move_forward(self, player: Player, mock_map: MagicMock) -> None:
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.move(mock_map, [])
            mock_move.assert_called_once()

    def test_move_backward(self, player: Player, mock_map: MagicMock) -> None:
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.move(mock_map, [], forward=False)
            mock_move.assert_called_once()

    def test_move_skips_when_zoomed(self, player: Player, mock_map: MagicMock) -> None:
        player.zoomed = True
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.move(mock_map, [])
            mock_move.assert_not_called()

    def test_move_skips_when_shield_active(self, player: Player, mock_map: MagicMock) -> None:
        player.shield_active = True
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.move(mock_map, [])
            mock_move.assert_not_called()


class TestZSPlayerStrafe:
    def test_strafe_right(self, player: Player, mock_map: MagicMock) -> None:
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.strafe(mock_map, [])
            mock_move.assert_called_once()

    def test_strafe_left(self, player: Player, mock_map: MagicMock) -> None:
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.strafe(mock_map, [], right=False)
            mock_move.assert_called_once()

    def test_strafe_skips_when_zoomed(self, player: Player, mock_map: MagicMock) -> None:
        player.zoomed = True
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.strafe(mock_map, [])
            mock_move.assert_not_called()

    def test_strafe_skips_when_shield_active(self, player: Player, mock_map: MagicMock) -> None:
        player.shield_active = True
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.strafe(mock_map, [])
            mock_move.assert_not_called()


class TestZSPlayerTakeDamage:
    def test_take_damage_reduces_health(self, player: Player) -> None:
        player.health = 100
        player.take_damage(30)
        assert player.health == 70

    def test_take_damage_kills_player(self, player: Player) -> None:
        player.health = 10
        player.take_damage(50)
        assert player.health == 0
        assert player.alive is False

    def test_take_damage_clamps_to_zero(self, player: Player) -> None:
        player.health = 5
        player.take_damage(100)
        assert player.health == 0

    def test_take_damage_shield_blocks(self, player: Player) -> None:
        player.shield_active = True
        player.health = 100
        player.take_damage(50)
        assert player.health == 100

    def test_take_damage_god_mode_blocks(self, player: Player) -> None:
        player.god_mode = True
        player.health = 100
        player.take_damage(50)
        assert player.health == 100


class TestZSPlayerUpdate:
    def test_update_calls_timers_and_weapon(self, player: Player) -> None:
        with (
            patch.object(player, "update_timers") as mock_timers,
            patch.object(player, "update_weapon_state") as mock_weapon,
        ):
            player.update()
            mock_timers.assert_called_once()
            mock_weapon.assert_called_once()
