"""Tests for games.Force_Field.src.player."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from games.Force_Field.src.player import Player


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


class TestPlayerInit:
    def test_init_sets_position(self, player: Player) -> None:
        assert player.x == 2.5
        assert player.y == 2.5
        assert player.angle == 0.0

    def test_init_dash_attrs(self, player: Player) -> None:
        assert player.DASH_SPEED_MULT == 2.5
        assert player.DASH_STAMINA_COST == 20
        assert player.DASH_DURATION == 10
        assert player.DASH_COOLDOWN == 60

    def test_init_melee_attrs(self, player: Player) -> None:
        assert player.melee_cooldown == 0
        assert not player.melee_active
        assert player.melee_timer == 0

    def test_init_invincibility(self, player: Player) -> None:
        assert player.invincible is True
        assert player.invincibility_timer == 300

    def test_init_respawn(self, player: Player) -> None:
        assert player.respawn_delay == 0
        assert not player.respawning


class TestPlayerMove:
    def test_move_forward(self, player: Player, mock_map: MagicMock) -> None:
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.move(mock_map, [])
            mock_move.assert_called_once()

    def test_move_backward(self, player: Player, mock_map: MagicMock) -> None:
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.move(mock_map, [], forward=False)
            args = mock_move.call_args
            # dx should be negative (backward)
            assert args is not None

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

    def test_move_speed_boosted_when_dashing(self, player: Player, mock_map: MagicMock) -> None:
        player.dash_active = True
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.move(mock_map, [])
            mock_move.assert_called_once()


class TestPlayerStrafe:
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

    def test_strafe_boosted_when_dashing(self, player: Player, mock_map: MagicMock) -> None:
        player.dash_active = True
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.strafe(mock_map, [])
            mock_move.assert_called_once()


class TestPlayerDash:
    def test_dash_activates_when_stamina_ok(self, player: Player) -> None:
        player.stamina = 100
        player.dash_cooldown = 0
        player.dash()
        assert player.dash_active is True
        assert player.stamina < 100

    def test_dash_fails_on_cooldown(self, player: Player) -> None:
        player.stamina = 100
        player.dash_cooldown = 30
        player.dash()
        assert player.dash_active is False

    def test_dash_fails_insufficient_stamina(self, player: Player) -> None:
        player.stamina = 5
        player.dash_cooldown = 0
        player.dash()
        assert player.dash_active is False


class TestPlayerMelee:
    def test_melee_attack_sets_active(self, player: Player) -> None:
        result = player.melee_attack()
        assert result is True
        assert player.melee_active is True
        assert player.melee_cooldown == 30

    def test_melee_attack_fails_on_cooldown(self, player: Player) -> None:
        player.melee_cooldown = 10
        result = player.melee_attack()
        assert result is False


class TestPlayerTakeDamage:
    def test_take_damage_reduces_health(self, player: Player) -> None:
        player.invincible = False
        player.health = 100
        died = player.take_damage(30)
        assert player.health == 70
        assert died is False

    def test_take_damage_kills_player(self, player: Player) -> None:
        player.invincible = False
        player.health = 10
        died = player.take_damage(50)
        assert player.health == 0
        assert player.alive is False
        assert player.respawning is True
        assert died is True

    def test_take_damage_invincible_blocks(self, player: Player) -> None:
        player.invincible = True
        player.health = 100
        died = player.take_damage(50)
        assert player.health == 100
        assert died is False

    def test_take_damage_god_mode_blocks(self, player: Player) -> None:
        player.invincible = False
        player.god_mode = True
        player.health = 100
        died = player.take_damage(50)
        assert player.health == 100
        assert died is False

    def test_take_damage_shield_blocks(self, player: Player) -> None:
        player.invincible = False
        player.shield_active = True
        player.health = 100
        died = player.take_damage(50)
        assert player.health == 100
        assert died is False

    def test_take_damage_dead_player_no_effect(self, player: Player) -> None:
        player.invincible = False
        player.alive = False
        player.health = 0
        died = player.take_damage(50)
        assert died is False


class TestPlayerUpdate:
    def test_update_moving_advances_bob(self, player: Player) -> None:
        player.is_moving = True
        initial_bob = player.bob_phase
        player.update()
        assert player.bob_phase != initial_bob

    def test_update_idle_applies_sway(self, player: Player) -> None:
        player.is_moving = False
        player.update()  # Should not raise

    def test_update_dash_timer_counts_down(self, player: Player) -> None:
        player.dash_active = True
        player.dash_timer = 1
        player.update()
        assert player.dash_active is False

    def test_update_dash_cooldown_counts_down(self, player: Player) -> None:
        player.dash_cooldown = 5
        player.update()
        assert player.dash_cooldown == 4

    def test_update_melee_cooldown_counts_down(self, player: Player) -> None:
        player.melee_cooldown = 5
        player.update()
        assert player.melee_cooldown == 4

    def test_update_melee_timer_expires(self, player: Player) -> None:
        player.melee_timer = 1
        player.melee_active = True
        player.update()
        assert player.melee_active is False

    def test_update_invincibility_expires(self, player: Player) -> None:
        player.invincibility_timer = 1
        player.invincible = True
        player.update()
        assert player.invincible is False

    def test_update_respawn_delay_expires(self, player: Player) -> None:
        player.respawn_delay = 1
        player.respawning = True
        player.alive = False
        player.update()
        assert player.alive is True
        assert player.respawning is False
        assert player.health == player.max_health

    def test_update_damage_flash_counts_down(self, player: Player) -> None:
        player.damage_flash_timer = 3
        player.update()
        assert player.damage_flash_timer == 2

    def test_update_pitch_constrained(self, player: Player) -> None:
        player.pitch = 10000.0
        player.update()
        from games.Force_Field.src import constants as C

        assert player.pitch <= C.PITCH_LIMIT

    def test_update_dash_active_faster_bob(self, player: Player) -> None:
        player.is_moving = True
        player.dash_active = True
        player.dash_timer = 100  # Keep dash active
        initial_bob = player.bob_phase
        player.update()
        # With dash active, bob advances by 0.15 instead of 0.1
        assert abs((player.bob_phase - initial_bob) - 0.15) < 1e-9
