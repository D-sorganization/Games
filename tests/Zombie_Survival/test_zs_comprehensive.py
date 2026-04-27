"""Comprehensive tests for Zombie Survival game modules.

Expands coverage for projectile, map, input_manager, sound, spawn_manager,
and combat_manager — modules that previously had only 1-3 tests each.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pygame
import pytest

from games.shared.contracts import ContractViolation
from games.Zombie_Survival.src.input_manager import InputManager
from games.Zombie_Survival.src.map import Map
from games.Zombie_Survival.src.projectile import Projectile
from games.Zombie_Survival.src.sound import SoundManager

if TYPE_CHECKING:
    from games.Zombie_Survival.src.combat_manager import ZSCombatManager
    from games.Zombie_Survival.src.spawn_manager import ZSSpawnManager

# ─── Projectile Tests ─────────────────────────────────────────


class TestProjectileConstruction:
    """Test Zombie Survival Projectile construction and inheritance."""

    def test_inherits_from_projectile_base(self) -> None:
        from games.shared.projectile_base import ProjectileBase

        p = Projectile(0.0, 0.0, 0.0, 10, 5.0)
        assert isinstance(p, ProjectileBase)

    def test_default_attributes(self) -> None:
        p = Projectile(1.5, 2.5, math.pi, 25, 3.0)
        assert p.x == 1.5
        assert p.y == 2.5
        assert p.angle == math.pi
        assert p.damage == 25
        assert p.speed == 3.0
        assert p.alive is True
        assert p.is_player is False

    def test_player_projectile(self) -> None:
        p = Projectile(0.0, 0.0, 0.0, 10, 5.0, is_player=True)
        assert p.is_player is True

    def test_custom_color_and_size(self) -> None:
        p = Projectile(0.0, 0.0, 0.0, 10, 5.0, color=(0, 255, 0), size=0.5)
        assert p.color == (0, 255, 0)
        assert p.size == 0.5

    def test_weapon_type_default(self) -> None:
        p = Projectile(0.0, 0.0, 0.0, 10, 5.0)
        assert p.weapon_type == "normal"

    def test_weapon_type_bomb(self) -> None:
        p = Projectile(0.0, 0.0, 0.0, 50, 2.0, weapon_type="bomb")
        assert p.weapon_type == "bomb"

    def test_3d_physics_defaults(self) -> None:
        p = Projectile(0.0, 0.0, 0.0, 10, 5.0)
        assert p.z == 0.5
        assert p.vz == 0.0
        assert p.gravity == 0.0

    def test_3d_physics_custom(self) -> None:
        p = Projectile(0.0, 0.0, 0.0, 10, 5.0, z=1.0, vz=0.5, gravity=0.1)
        assert p.z == 1.0
        assert p.vz == 0.5
        assert p.gravity == 0.1


class TestProjectileContracts:
    """DbC: validate preconditions on projectile construction."""

    def test_negative_damage_raises(self) -> None:
        """Negative damage violates contract."""
        with pytest.raises(ContractViolation, match="damage"):
            Projectile(0.0, 0.0, 0.0, -1, 5.0)

    def test_zero_speed_raises(self) -> None:
        with pytest.raises(ContractViolation, match="speed"):
            Projectile(0.0, 0.0, 0.0, 10, 0.0)

    def test_negative_speed_raises(self) -> None:
        with pytest.raises(ContractViolation, match="speed"):
            Projectile(0.0, 0.0, 0.0, 10, -1.0)

    def test_zero_damage_allowed(self) -> None:
        """Zero damage is valid (e.g., a tracer round)."""
        p = Projectile(0.0, 0.0, 0.0, 0, 5.0)
        assert p.damage == 0


class TestProjectileMovement:
    """Test projectile update/movement physics."""

    def _make_open_map(self) -> MagicMock:
        """Create a mock map with no walls."""
        m = MagicMock()
        m.is_wall.return_value = False
        return m

    def _make_wall_map(self) -> MagicMock:
        """Create a mock map where everything is a wall."""
        m = MagicMock()
        m.is_wall.return_value = True
        m.get_wall_type.return_value = 1
        return m

    def test_moves_in_direction(self) -> None:
        p = Projectile(5.0, 5.0, 0.0, 10, 1.0)  # angle=0 → +x
        p.update(self._make_open_map())
        assert p.x > 5.0
        assert abs(p.y - 5.0) < 1e-9

    def test_dead_projectile_does_not_move(self) -> None:
        p = Projectile(5.0, 5.0, 0.0, 10, 1.0)
        p.alive = False
        p.update(self._make_open_map())
        assert p.x == 5.0

    def test_wall_collision_kills_projectile(self) -> None:
        p = Projectile(5.0, 5.0, 0.0, 10, 1.0)
        p.update(self._make_wall_map())
        assert p.alive is False

    def test_hidden_wall_records_position(self) -> None:
        m = MagicMock()
        m.is_wall.return_value = True
        m.get_wall_type.return_value = 5  # hidden wall
        p = Projectile(5.0, 5.0, 0.0, 10, 1.0)
        p.update(m)
        assert p.alive is False
        assert p.hit_hidden_pos is not None

    def test_bomb_dies_on_ground(self) -> None:
        p = Projectile(5.0, 5.0, 0.0, 50, 1.0, weapon_type="bomb", z=0.05, vz=-0.1)
        p.update(self._make_open_map())
        assert p.alive is False

    def test_gravity_reduces_vz(self) -> None:
        p = Projectile(5.0, 5.0, 0.0, 10, 1.0, vz=1.0, gravity=0.1)
        initial_vz = p.vz
        p.update(self._make_open_map())
        assert p.vz < initial_vz

    def test_diagonal_movement(self) -> None:
        angle = math.pi / 4  # 45°
        p = Projectile(5.0, 5.0, angle, 10, 1.0)
        p.update(self._make_open_map())
        assert p.x > 5.0
        assert p.y > 5.0


# ─── Map Tests ─────────────────────────────────────────────────


class TestMapConstruction:
    """Test Zombie Survival Map construction and inheritance."""

    def test_inherits_from_map_base(self) -> None:
        from games.shared.map_base import MapBase

        game_map = Map(size=10)
        assert isinstance(game_map, MapBase)

    def test_default_size(self) -> None:
        from games.Zombie_Survival.src.constants import DEFAULT_MAP_SIZE

        game_map = Map()
        assert game_map.size == DEFAULT_MAP_SIZE

    def test_custom_size(self) -> None:
        game_map = Map(size=15)
        assert game_map.size == 15

    def test_grid_dimensions_match_size(self) -> None:
        game_map = Map(size=12)
        assert len(game_map.grid) == 12
        assert all(len(row) == 12 for row in game_map.grid)

    def test_width_height_properties(self) -> None:
        game_map = Map(size=20)
        assert game_map.width == 20
        assert game_map.height == 20


class TestMapContracts:
    """DbC: validate map preconditions."""

    def test_zero_size_raises(self) -> None:
        with pytest.raises(ContractViolation, match="map_size"):
            Map(size=0)

    def test_negative_size_raises(self) -> None:
        with pytest.raises(ContractViolation, match="map_size"):
            Map(size=-5)


class TestMapWallChecks:
    """Test wall query methods."""

    def test_border_is_wall(self) -> None:
        game_map = Map(size=15)
        # Out-of-bounds should be wall
        assert game_map.is_wall(-1, 5) is True
        assert game_map.is_wall(5, -1) is True
        assert game_map.is_wall(15, 5) is True

    def test_out_of_bounds_wall_type(self) -> None:
        game_map = Map(size=15)
        assert game_map.get_wall_type(-1, 5) == 1

    def test_center_is_open(self) -> None:
        """Center should generally be open (connectivity enforced)."""
        game_map = Map(size=20)
        cx, cy = 10, 10
        # The center region should have at least some open cells
        has_open = any(
            game_map.grid[cy + dy][cx + dx] == 0
            for dx in range(-2, 3)
            for dy in range(-2, 3)
            if 0 <= cx + dx < 20 and 0 <= cy + dy < 20
        )
        assert has_open


# ─── SoundManager Tests ──────────────────────────────────────


class TestSoundManager:
    """Test Zombie Survival SoundManager configuration."""

    def test_inherits_from_base(self) -> None:
        from games.shared.sound_manager_base import SoundManagerBase

        assert issubclass(SoundManager, SoundManagerBase)

    def test_has_sound_files_dict(self) -> None:
        assert isinstance(SoundManager.SOUND_FILES, dict)

    def test_required_combat_sounds(self) -> None:
        required = ["shoot", "enemy_shoot", "bomb", "death", "player_hit"]
        for sound in required:
            assert sound in SoundManager.SOUND_FILES, f"Missing combat sound: {sound}"

    def test_required_music_tracks(self) -> None:
        required = ["music_intro", "music_loop", "ambient"]
        for track in required:
            assert track in SoundManager.SOUND_FILES, f"Missing music track: {track}"

    def test_weapon_specific_sounds(self) -> None:
        weapon_sounds = [
            "shoot_pistol",
            "shoot_rifle",
            "shoot_shotgun",
            "shoot_plasma",
        ]
        for ws in weapon_sounds:
            assert ws in SoundManager.SOUND_FILES, f"Missing weapon sound: {ws}"

    def test_reload_sounds(self) -> None:
        reload_sounds = ["reload_pistol", "reload_rifle", "reload_shotgun"]
        for rs in reload_sounds:
            assert rs in SoundManager.SOUND_FILES, f"Missing reload sound: {rs}"

    def test_all_files_are_strings(self) -> None:
        for key, filename in SoundManager.SOUND_FILES.items():
            assert isinstance(filename, str), f"{key} filename is not a string"

    def test_all_files_have_audio_extension(self) -> None:
        valid_extensions = (".wav", ".mp3", ".ogg")
        for key, filename in SoundManager.SOUND_FILES.items():
            msg = f"{key}: {filename} has invalid audio extension"
            assert filename.endswith(valid_extensions), msg

    def test_minimum_sound_count(self) -> None:
        assert len(SoundManager.SOUND_FILES) > 20


# ─── InputManager Tests ──────────────────────────────────────


class TestInputManager:
    """Test Zombie Survival InputManager bindings."""

    def test_inherits_from_base(self) -> None:
        from games.shared.input_manager_base import InputManagerBase

        assert issubclass(InputManager, InputManagerBase)

    def test_has_default_bindings(self) -> None:
        assert isinstance(InputManager.DEFAULT_BINDINGS, dict)

    def test_required_movement_keys(self) -> None:
        required = ["move_forward", "move_backward", "strafe_left", "strafe_right"]
        for key in required:
            assert key in InputManager.DEFAULT_BINDINGS, f"Missing binding: {key}"

    def test_required_combat_keys(self) -> None:
        required = ["shoot", "reload", "bomb", "shield"]
        for key in required:
            assert key in InputManager.DEFAULT_BINDINGS, f"Missing binding: {key}"

    def test_required_navigation_keys(self) -> None:
        required = ["turn_left", "turn_right", "look_up", "look_down"]
        for key in required:
            assert key in InputManager.DEFAULT_BINDINGS, f"Missing binding: {key}"

    def test_weapon_selection_keys(self) -> None:
        for i in range(1, 7):
            key = f"weapon_{i}"
            assert key in InputManager.DEFAULT_BINDINGS, f"Missing binding: {key}"

    def test_sprint_binding(self) -> None:
        assert InputManager.DEFAULT_BINDINGS["sprint"] == pygame.K_LSHIFT

    def test_pause_binding(self) -> None:
        assert InputManager.DEFAULT_BINDINGS["pause"] == pygame.K_ESCAPE

    def test_all_bindings_are_integers(self) -> None:
        for key, value in InputManager.DEFAULT_BINDINGS.items():
            assert isinstance(value, int), f"{key} binding is not an int"

    def test_no_duplicate_bindings(self) -> None:
        """Each key should have a unique binding (no accidental double-binds)."""
        # Note: Some games may intentionally reuse keys, so we just check
        # the most critical ones don't overlap
        movement_keys = {
            InputManager.DEFAULT_BINDINGS[k]
            for k in ["move_forward", "move_backward", "strafe_left", "strafe_right"]
        }
        assert len(movement_keys) == 4, "Movement WASD bindings must be unique"

    def test_has_minigun_binding(self) -> None:
        assert "weapon_minigun" in InputManager.DEFAULT_BINDINGS


# ─── SpawnManager Tests ──────────────────────────────────────


class TestZSSpawnManagerExpanded:
    """Expanded tests for ZSSpawnManager."""

    @pytest.fixture()
    def manager(self) -> ZSSpawnManager:
        from games.Zombie_Survival.src.spawn_manager import ZSSpawnManager

        return ZSSpawnManager(MagicMock())

    def test_boss_options_not_empty(self, manager: ZSSpawnManager) -> None:
        assert len(manager.BOSS_OPTIONS) > 0

    def test_weapon_pickups_not_empty(self, manager: ZSSpawnManager) -> None:
        assert len(manager.WEAPON_PICKUPS) > 0

    def test_boss_options_are_strings(self, manager: ZSSpawnManager) -> None:
        for opt in manager.BOSS_OPTIONS:
            assert isinstance(opt, str)

    def test_make_bot_returns_bot(self, manager: ZSSpawnManager) -> None:
        from games.Zombie_Survival.src.bot import Bot

        bot = manager._make_bot(5.0, 5.0, 1, "zombie")
        assert isinstance(bot, Bot)

    def test_make_bot_position(self, manager: ZSSpawnManager) -> None:
        bot = manager._make_bot(3.0, 7.0, 2, "zombie")
        assert bot.x == 3.0
        assert bot.y == 7.0

    def test_make_bot_level(self, manager: ZSSpawnManager) -> None:
        bot = manager._make_bot(1.0, 1.0, 5, "zombie")
        assert bot.level == 5


# ─── CombatManager Tests ─────────────────────────────────────


class TestZSCombatManagerExpanded:
    """Expanded tests for ZSCombatManager."""

    @pytest.fixture()
    def cm(self) -> ZSCombatManager:
        from games.Zombie_Survival.src.combat_manager import ZSCombatManager

        return ZSCombatManager(MagicMock(), MagicMock(), MagicMock())

    def test_instance_creation(self, cm: ZSCombatManager) -> None:
        assert cm is not None

    def test_inherits_from_base(self, cm: ZSCombatManager) -> None:
        from games.shared.combat_manager import CombatManagerBase

        assert isinstance(cm, CombatManagerBase)

    def test_has_entity_manager(self, cm: ZSCombatManager) -> None:
        assert hasattr(cm, "entity_manager")

    def test_has_particle_system(self, cm: ZSCombatManager) -> None:
        assert hasattr(cm, "particle_system")

    def test_has_sound_manager(self, cm: ZSCombatManager) -> None:
        assert hasattr(cm, "sound_manager")

    def test_with_on_kill_callback(self) -> None:
        from games.Zombie_Survival.src.combat_manager import ZSCombatManager

        callback = MagicMock()
        cm = ZSCombatManager(MagicMock(), MagicMock(), MagicMock(), on_kill=callback)
        assert cm is not None
