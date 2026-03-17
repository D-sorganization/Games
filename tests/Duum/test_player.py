"""Tests for games.Duum.src.player and games.Duum.src.combat_manager."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from games.Duum.src.player import Player


@pytest.fixture()
def player() -> Player:
    return Player(2.5, 2.5, 0.0)


@pytest.fixture()
def mock_map() -> MagicMock:
    m = MagicMock()
    m.grid = [[0] * 15 for _ in range(15)]
    m.width = 15
    m.height = 15
    return m


class TestDuumPlayerInit:
    def test_init_sets_position(self, player: Player) -> None:
        assert player.x == 2.5
        assert player.y == 2.5
        assert player.angle == 0.0

    def test_init_bobbing_attributes(self, player: Player) -> None:
        assert player.bob_phase == 0.0
        assert player.walk_distance == 0.0


class TestDuumPlayerMove:
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

    def test_move_reduces_speed_when_shield_active(
        self, player: Player, mock_map: MagicMock
    ) -> None:
        player.shield_active = True
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.move(mock_map, [])
            mock_move.assert_called_once()
            # Speed should be reduced by 0.8 when shield active

    def test_move_updates_is_moving_when_entity_moves(
        self, player: Player, mock_map: MagicMock
    ) -> None:
        def move_entity(
            entity: object, dx: float, dy: float, *args: object, **kw: object
        ) -> None:
            player.x += 0.1  # Simulate actual movement

        with patch("games.shared.utils.try_move_entity", side_effect=move_entity):
            player.move(mock_map, [])
        assert player.is_moving is True
        assert player.walk_distance > 0.0

    def test_move_sets_is_moving_false_when_blocked(
        self, player: Player, mock_map: MagicMock
    ) -> None:
        # When try_move_entity doesn't actually move (e.g. blocked by wall)
        with patch("games.shared.utils.try_move_entity"):
            player.move(mock_map, [])
        assert player.is_moving is False


class TestDuumPlayerStrafe:
    def test_strafe_right(self, player: Player, mock_map: MagicMock) -> None:
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.strafe(mock_map, [])
            mock_move.assert_called_once()

    def test_strafe_left(self, player: Player, mock_map: MagicMock) -> None:
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.strafe(mock_map, [], right=False)
            mock_move.assert_called_once()

    def test_strafe_skips_when_zoomed(
        self, player: Player, mock_map: MagicMock
    ) -> None:
        player.zoomed = True
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.strafe(mock_map, [])
            mock_move.assert_not_called()

    def test_strafe_allows_shield_active(
        self, player: Player, mock_map: MagicMock
    ) -> None:
        player.shield_active = True
        with patch("games.shared.utils.try_move_entity") as mock_move:
            player.strafe(mock_map, [])
            mock_move.assert_called_once()

    def test_strafe_updates_walk_distance(
        self, player: Player, mock_map: MagicMock
    ) -> None:
        def move_entity(
            entity: object, dx: float, dy: float, *args: object, **kw: object
        ) -> None:
            player.x += 0.1

        with patch("games.shared.utils.try_move_entity", side_effect=move_entity):
            player.strafe(mock_map, [])
        assert player.walk_distance > 0.0


class TestDuumPlayerTakeDamage:
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


class TestDuumPlayerUpdate:
    def test_update_moving_updates_bob_phase(self, player: Player) -> None:
        player.is_moving = True
        player.walk_distance = 5.0
        player.update()
        assert player.bob_phase == 5.0

    def test_update_idle_decays_bob_phase(self, player: Player) -> None:
        player.is_moving = False
        player.bob_phase = 10.0
        player.update()
        assert player.bob_phase == pytest.approx(9.0)  # 10 * 0.9

    def test_update_calls_timers_and_weapon(self, player: Player) -> None:
        with (
            patch.object(player, "update_timers") as mock_t,
            patch.object(player, "update_weapon_state") as mock_w,
        ):
            player.update()
            mock_t.assert_called_once()
            mock_w.assert_called_once()


class TestDuumCombatManager:
    def test_init_creates_instance(self) -> None:
        from games.Duum.src.combat_manager import DuumCombatManager

        cm = DuumCombatManager(MagicMock(), MagicMock(), MagicMock())
        assert cm is not None

    def test_inherits_from_base(self) -> None:
        from games.Duum.src.combat_manager import DuumCombatManager
        from games.shared.combat_manager import CombatManagerBase

        cm = DuumCombatManager(MagicMock(), MagicMock(), MagicMock())
        assert isinstance(cm, CombatManagerBase)

    def test_init_with_on_kill(self) -> None:
        from games.Duum.src.combat_manager import DuumCombatManager

        callback = MagicMock()
        cm = DuumCombatManager(MagicMock(), MagicMock(), MagicMock(), on_kill=callback)
        assert cm is not None
