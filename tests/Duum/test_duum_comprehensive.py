"""Comprehensive tests for Duum game modules.

Expands coverage for projectile, map, input_manager, sound, spawn_manager,
and combat_manager — modules that previously had only 1-3 tests each.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pygame
import pytest

from games.Duum.src.input_manager import InputManager
from games.Duum.src.map import Map
from games.Duum.src.projectile import Projectile
from games.Duum.src.sound import SoundManager
from games.shared.contracts import ContractViolation

if TYPE_CHECKING:
    from games.Duum.src.spawn_manager import DuumSpawnManager

# ─── Projectile Tests ─────────────────────────────────────────


class TestDuumProjectileConstruction:
    """Test Duum Projectile construction and inheritance."""

    def test_inherits_from_projectile_base(self) -> None:
        from games.shared.projectile_base import ProjectileBase

        p = Projectile(0.0, 0.0, 0.0, 10, 5.0)
        assert isinstance(p, ProjectileBase)

    def test_default_attributes(self) -> None:
        p = Projectile(3.0, 4.0, math.pi / 2, 30, 4.0)
        assert p.x == 3.0
        assert p.y == 4.0
        assert p.angle == math.pi / 2
        assert p.damage == 30
        assert p.speed == 4.0
        assert p.alive is True

    def test_player_projectile(self) -> None:
        p = Projectile(0.0, 0.0, 0.0, 10, 5.0, is_player=True)
        assert p.is_player is True

    def test_weapon_type_freezer(self) -> None:
        p = Projectile(0.0, 0.0, 0.0, 10, 5.0, weapon_type="freezer")
        assert p.weapon_type == "freezer"

    def test_hit_hidden_pos_initially_none(self) -> None:
        p = Projectile(0.0, 0.0, 0.0, 10, 5.0)
        assert p.hit_hidden_pos is None


class TestDuumProjectileContracts:
    """DbC: validate preconditions on Duum projectile."""

    def test_negative_damage_raises(self) -> None:
        with pytest.raises(ContractViolation, match="damage"):
            Projectile(0.0, 0.0, 0.0, -5, 5.0)

    def test_zero_speed_raises(self) -> None:
        with pytest.raises(ContractViolation, match="speed"):
            Projectile(0.0, 0.0, 0.0, 10, 0.0)


class TestDuumProjectileMovement:
    """Test Duum projectile update/movement physics."""

    def _open_map(self) -> MagicMock:
        m = MagicMock()
        m.is_wall.return_value = False
        return m

    def test_moves_forward(self) -> None:
        p = Projectile(5.0, 5.0, 0.0, 10, 2.0)
        p.update(self._open_map())
        assert p.x > 5.0
        assert p.alive is True

    def test_wall_kills(self) -> None:
        m = MagicMock()
        m.is_wall.return_value = True
        m.get_wall_type.return_value = 1
        p = Projectile(5.0, 5.0, 0.0, 10, 1.0)
        p.update(m)
        assert p.alive is False

    def test_freezer_dies_on_ground(self) -> None:
        p = Projectile(5.0, 5.0, 0.0, 10, 1.0, weapon_type="freezer", z=0.05, vz=-0.1)
        p.update(self._open_map())
        assert p.alive is False

    def test_normal_projectile_survives_ground(self) -> None:
        """Normal projectiles don't die on ground, only bombs/freezers do."""
        p = Projectile(5.0, 5.0, 0.0, 10, 1.0, weapon_type="normal", z=0.05, vz=-0.1)
        p.update(self._open_map())
        assert p.alive is True


# ─── Map Tests ─────────────────────────────────────────────────


class TestDuumMapConstruction:
    """Test Duum Map construction and inheritance."""

    def test_inherits_from_map_base(self) -> None:
        from games.shared.map_base import MapBase

        game_map = Map(size=10)
        assert isinstance(game_map, MapBase)

    def test_default_size(self) -> None:
        from games.Duum.src.constants import DEFAULT_MAP_SIZE

        game_map = Map()
        assert game_map.size == DEFAULT_MAP_SIZE

    def test_custom_size(self) -> None:
        game_map = Map(size=18)
        assert game_map.size == 18

    def test_grid_is_square(self) -> None:
        game_map = Map(size=14)
        assert len(game_map.grid) == 14
        for row in game_map.grid:
            assert len(row) == 14


class TestDuumMapContracts:
    """DbC: validate map preconditions."""

    def test_zero_size_raises(self) -> None:
        with pytest.raises(ContractViolation, match="map_size"):
            Map(size=0)

    def test_negative_size_raises(self) -> None:
        with pytest.raises(ContractViolation, match="map_size"):
            Map(size=-3)


class TestDuumMapWalls:
    """Test Duum map wall queries."""

    def test_out_of_bounds_is_wall(self) -> None:
        game_map = Map(size=15)
        assert game_map.is_wall(100, 100) is True
        assert game_map.is_wall(-5, 5) is True

    def test_wall_type_out_of_bounds(self) -> None:
        game_map = Map(size=15)
        assert game_map.get_wall_type(-1, -1) == 1


# ─── SoundManager Tests ──────────────────────────────────────


class TestDuumSoundManager:
    """Test Duum SoundManager configuration."""

    def test_inherits_from_base(self) -> None:
        from games.shared.sound_manager_base import SoundManagerBase

        assert issubclass(SoundManager, SoundManagerBase)

    def test_has_sound_files(self) -> None:
        assert isinstance(SoundManager.SOUND_FILES, dict)
        assert len(SoundManager.SOUND_FILES) > 0

    def test_required_combat_sounds(self) -> None:
        required = ["shoot", "enemy_shoot", "bomb", "death", "player_hit"]
        for sound in required:
            assert sound in SoundManager.SOUND_FILES, f"Missing: {sound}"

    def test_required_music(self) -> None:
        required = ["music_intro", "music_loop", "ambient"]
        for track in required:
            assert track in SoundManager.SOUND_FILES, f"Missing: {track}"

    def test_weapon_sounds(self) -> None:
        weapons = ["shoot_pistol", "shoot_rifle", "shoot_shotgun", "shoot_plasma"]
        for ws in weapons:
            assert ws in SoundManager.SOUND_FILES, f"Missing: {ws}"

    def test_all_values_are_strings(self) -> None:
        for key, val in SoundManager.SOUND_FILES.items():
            assert isinstance(val, str), f"{key} has non-string value"

    def test_audio_file_extensions(self) -> None:
        valid = (".wav", ".mp3", ".ogg")
        for key, filename in SoundManager.SOUND_FILES.items():
            assert filename.endswith(valid), f"{key}: {filename} bad extension"

    def test_minimum_count(self) -> None:
        assert len(SoundManager.SOUND_FILES) > 20


# ─── InputManager Tests ──────────────────────────────────────


class TestDuumInputManager:
    """Test Duum InputManager bindings."""

    def test_inherits_from_base(self) -> None:
        from games.shared.input_manager_base import InputManagerBase

        assert issubclass(InputManager, InputManagerBase)

    def test_has_default_bindings(self) -> None:
        assert isinstance(InputManager.DEFAULT_BINDINGS, dict)

    def test_movement_keys(self) -> None:
        required = ["move_forward", "move_backward", "strafe_left", "strafe_right"]
        for key in required:
            assert key in InputManager.DEFAULT_BINDINGS, f"Missing: {key}"

    def test_combat_keys(self) -> None:
        required = ["shoot", "reload", "bomb"]
        for key in required:
            assert key in InputManager.DEFAULT_BINDINGS, f"Missing: {key}"

    def test_look_keys(self) -> None:
        required = ["turn_left", "turn_right", "look_up", "look_down"]
        for key in required:
            assert key in InputManager.DEFAULT_BINDINGS, f"Missing: {key}"

    def test_weapon_slots(self) -> None:
        for i in range(1, 7):
            assert f"weapon_{i}" in InputManager.DEFAULT_BINDINGS

    def test_duum_shoot_is_space(self) -> None:
        """Duum uses SPACE for shoot, unlike other games."""
        assert InputManager.DEFAULT_BINDINGS["shoot"] == pygame.K_SPACE

    def test_sprint_is_lshift(self) -> None:
        assert InputManager.DEFAULT_BINDINGS["sprint"] == pygame.K_LSHIFT

    def test_pause_is_escape(self) -> None:
        assert InputManager.DEFAULT_BINDINGS["pause"] == pygame.K_ESCAPE

    def test_all_bindings_are_ints(self) -> None:
        for key, val in InputManager.DEFAULT_BINDINGS.items():
            assert isinstance(val, int), f"{key} is not int"

    def test_movement_bindings_are_unique(self) -> None:
        movement = {
            InputManager.DEFAULT_BINDINGS[k]
            for k in ["move_forward", "move_backward", "strafe_left", "strafe_right"]
        }
        assert len(movement) == 4


# ─── SpawnManager Tests ──────────────────────────────────────


class TestDuumSpawnManagerExpanded:
    """Expanded tests for Duum SpawnManager."""

    @pytest.fixture()
    def manager(self) -> DuumSpawnManager:
        from games.Duum.src.spawn_manager import DuumSpawnManager

        return DuumSpawnManager(MagicMock())

    def test_boss_options_not_empty(self, manager: DuumSpawnManager) -> None:
        assert len(manager.BOSS_OPTIONS) > 0

    def test_weapon_pickups_not_empty(self, manager: DuumSpawnManager) -> None:
        assert len(manager.WEAPON_PICKUPS) > 0

    def test_make_bot_creates_bot(self, manager: DuumSpawnManager) -> None:
        from games.Duum.src.bot import Bot

        bot = manager._make_bot(5.0, 5.0, 1, "zombie")
        assert isinstance(bot, Bot)

    def test_make_bot_position(self, manager: DuumSpawnManager) -> None:
        bot = manager._make_bot(3.0, 7.0, 2, "zombie")
        assert bot.x == 3.0
        assert bot.y == 7.0

    def test_make_bot_level(self, manager: DuumSpawnManager) -> None:
        bot = manager._make_bot(1.0, 1.0, 4, "zombie")
        assert bot.level == 4
