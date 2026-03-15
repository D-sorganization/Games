"""Tests for games.shared.spawn_manager module.

Uses mock dependencies to test spawn logic without pygame.
"""

from __future__ import annotations

import random
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from games.shared.spawn_manager import SpawnManagerBase

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_constants(**overrides: Any) -> SimpleNamespace:
    """Create minimal constants for SpawnManagerBase."""
    defaults = dict(
        ENEMY_TYPES={
            "grunt": {"health_mult": 1.0, "damage_mult": 1.0, "speed_mult": 1.0},
            "gunner": {"health_mult": 1.5, "damage_mult": 1.2, "speed_mult": 0.8},
            "boss": {"health_mult": 5.0, "damage_mult": 3.0, "speed_mult": 0.5},
            "health_pack": {"health_mult": 0.0, "damage_mult": 0.0, "speed_mult": 0.0},
            "ammo_box": {"health_mult": 0.0, "damage_mult": 0.0, "speed_mult": 0.0},
            "bomb_item": {"health_mult": 0.0, "damage_mult": 0.0, "speed_mult": 0.0},
        },
        DIFFICULTIES={
            "EASY": {"score_mult": 0.5, "health_mult": 0.8, "damage_mult": 0.7},
            "NORMAL": {"score_mult": 1.0, "health_mult": 1.0, "damage_mult": 1.0},
            "HARD": {"score_mult": 1.5, "health_mult": 1.5, "damage_mult": 1.5},
        },
        SPAWN_SAFE_ZONE_RADIUS=15.0,
        MIN_BOSS_DISTANCE=15.0,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_game_map(size: int = 30) -> SimpleNamespace:
    """Create a mock game map where no cell is a wall."""
    return SimpleNamespace(
        size=size,
        is_wall=MagicMock(return_value=False),
    )


class ConcreteSpawnManager(SpawnManagerBase):
    """Concrete implementation for testing."""

    def __init__(self, entity_manager: Any, constants: Any) -> None:
        super().__init__(entity_manager, constants)
        self.bots_created: list[SimpleNamespace] = []

    def _make_bot(
        self,
        x: float,
        y: float,
        level: int,
        enemy_type: str,
        difficulty: str = "NORMAL",
    ) -> SimpleNamespace:
        bot = SimpleNamespace(
            x=x,
            y=y,
            level=level,
            enemy_type=enemy_type,
            difficulty=difficulty,
        )
        self.bots_created.append(bot)
        return bot


@pytest.fixture()
def sm() -> ConcreteSpawnManager:
    """Create a spawn manager with mocked entity manager."""
    em = MagicMock()
    return ConcreteSpawnManager(em, _make_constants())


# ---------------------------------------------------------------------------
# Exclusion logic
# ---------------------------------------------------------------------------


class TestIsExcluded:
    """Tests for _is_excluded filtering."""

    def test_boss_is_excluded(self, sm: ConcreteSpawnManager) -> None:
        assert sm._is_excluded("boss") is True

    def test_health_pack_is_excluded(self, sm: ConcreteSpawnManager) -> None:
        assert sm._is_excluded("health_pack") is True

    def test_pickup_prefix_is_excluded(self, sm: ConcreteSpawnManager) -> None:
        assert sm._is_excluded("pickup_rifle") is True

    def test_grunt_not_excluded(self, sm: ConcreteSpawnManager) -> None:
        assert sm._is_excluded("grunt") is False

    def test_gunner_not_excluded(self, sm: ConcreteSpawnManager) -> None:
        assert sm._is_excluded("gunner") is False


# ---------------------------------------------------------------------------
# Enemy count calculation
# ---------------------------------------------------------------------------


class TestGetNumEnemies:
    """Tests for _get_num_enemies level scaling."""

    def test_level_1_normal(self, sm: ConcreteSpawnManager) -> None:
        count = sm._get_num_enemies(1, "NORMAL")
        assert count == 7  # min(50, 5 + 1 * 2 * 1.0) = 7

    def test_level_10_normal(self, sm: ConcreteSpawnManager) -> None:
        count = sm._get_num_enemies(10, "NORMAL")
        assert count == 25  # min(50, 5 + 10 * 2 * 1.0) = 25

    def test_caps_at_50(self, sm: ConcreteSpawnManager) -> None:
        count = sm._get_num_enemies(100, "NORMAL")
        assert count == 50

    def test_hard_scales_higher(self, sm: ConcreteSpawnManager) -> None:
        normal = sm._get_num_enemies(5, "NORMAL")
        hard = sm._get_num_enemies(5, "HARD")
        assert hard > normal


# ---------------------------------------------------------------------------
# Spawn enemies
# ---------------------------------------------------------------------------


class TestSpawnEnemies:
    """Tests for spawn_enemies."""

    def test_spawns_expected_count(self) -> None:
        """Should spawn the calculated number of enemies."""
        em = MagicMock()
        sm = ConcreteSpawnManager(em, _make_constants())
        game_map = _make_game_map()
        random.seed(42)

        sm.spawn_enemies(
            player_pos=(15.0, 15.0, 0.0),
            game_map=game_map,
            level=1,
            difficulty="NORMAL",
        )
        expected = sm._get_num_enemies(1, "NORMAL")
        assert em.add_bot.call_count == expected

    def test_no_boss_types_in_regular_spawn(self) -> None:
        """Regular enemies should not include excluded types."""
        em = MagicMock()
        sm = ConcreteSpawnManager(em, _make_constants())
        game_map = _make_game_map()
        random.seed(42)

        sm.spawn_enemies(
            player_pos=(15.0, 15.0, 0.0),
            game_map=game_map,
            level=1,
            difficulty="NORMAL",
        )
        for bot in sm.bots_created:
            if bot.enemy_type not in ("grunt", "gunner"):
                # Could be any non-excluded type
                assert not sm._is_excluded(bot.enemy_type)


# ---------------------------------------------------------------------------
# Spawn boss
# ---------------------------------------------------------------------------


class TestSpawnBoss:
    """Tests for spawn_boss."""

    def test_boss_is_spawned(self) -> None:
        """At least one boss should be added."""
        em = MagicMock()
        sm = ConcreteSpawnManager(em, _make_constants())
        game_map = _make_game_map()
        random.seed(42)

        sm.spawn_boss(
            player_pos=(15.0, 15.0, 0.0),
            game_map=game_map,
            level=1,
            difficulty="NORMAL",
        )
        assert em.add_bot.call_count >= 1


# ---------------------------------------------------------------------------
# Spawn pickups
# ---------------------------------------------------------------------------


class TestSpawnPickups:
    """Tests for spawn_pickups."""

    def test_pickups_are_from_weapon_list(self) -> None:
        """Spawned pickups should be from the WEAPON_PICKUPS list."""
        em = MagicMock()
        sm = ConcreteSpawnManager(em, _make_constants())
        game_map = _make_game_map()
        random.seed(42)

        sm.spawn_pickups(game_map, level=1)
        for bot in sm.bots_created:
            assert bot.enemy_type in sm.WEAPON_PICKUPS


# ---------------------------------------------------------------------------
# Spawn items
# ---------------------------------------------------------------------------


class TestSpawnItems:
    """Tests for spawn_items."""

    def test_items_are_health_ammo_or_bomb(self) -> None:
        """Spawned items should be health_pack, ammo_box, or bomb_item."""
        em = MagicMock()
        sm = ConcreteSpawnManager(em, _make_constants())
        game_map = _make_game_map()
        random.seed(42)

        sm.spawn_items(game_map, level=1)
        valid_types = {"health_pack", "ammo_box", "bomb_item"}
        for bot in sm.bots_created:
            assert bot.enemy_type in valid_types

    def test_item_count_matches_constant(self) -> None:
        """Should spawn exactly ITEM_COUNT items (assuming no walls)."""
        em = MagicMock()
        sm = ConcreteSpawnManager(em, _make_constants())
        game_map = _make_game_map()
        random.seed(42)

        sm.spawn_items(game_map, level=1)
        assert em.add_bot.call_count == sm.ITEM_COUNT


# ---------------------------------------------------------------------------
# Spawn all
# ---------------------------------------------------------------------------


class TestSpawnAll:
    """Tests for spawn_all orchestrator."""

    def test_spawn_all_calls_sub_methods(self) -> None:
        """spawn_all should invoke all sub-spawn methods."""
        em = MagicMock()
        sm = ConcreteSpawnManager(em, _make_constants())
        game_map = _make_game_map()
        random.seed(42)

        sm.spawn_all(
            player_pos=(15.0, 15.0, 0.0),
            game_map=game_map,
            level=1,
            difficulty="NORMAL",
        )
        # Should have called add_bot multiple times
        assert em.add_bot.call_count > 0
