"""Comprehensive tests for Force Field game modules.

Expands coverage for projectile, input_manager, and sound — modules that
previously had only 1 test each.
"""

from __future__ import annotations

import math
from unittest.mock import MagicMock

import pygame
import pytest

from games.Force_Field.src.input_manager import InputManager
from games.Force_Field.src.projectile import Projectile
from games.Force_Field.src.sound import SoundManager
from games.shared.contracts import ContractViolation

# ─── Projectile Tests ─────────────────────────────────────────


class TestFFProjectileConstruction:
    """Test Force Field Projectile construction and inheritance."""

    def test_inherits_from_projectile_base(self) -> None:
        from games.shared.projectile_base import ProjectileBase

        p = Projectile(0.0, 0.0, 0.0, 10, 5.0)
        assert isinstance(p, ProjectileBase)

    def test_default_attributes(self) -> None:
        p = Projectile(2.0, 3.0, 0.0, 15, 6.0)
        assert p.x == 2.0
        assert p.y == 3.0
        assert p.damage == 15
        assert p.speed == 6.0
        assert p.alive is True

    def test_player_projectile(self) -> None:
        p = Projectile(0.0, 0.0, 0.0, 10, 5.0, is_player=True)
        assert p.is_player is True

    def test_default_weapon_type(self) -> None:
        p = Projectile(0.0, 0.0, 0.0, 10, 5.0)
        assert p.weapon_type == "normal"


class TestFFProjectileContracts:
    """DbC: validate Force Field projectile preconditions."""

    def test_negative_damage_raises(self) -> None:
        with pytest.raises(ContractViolation, match="damage"):
            Projectile(0.0, 0.0, 0.0, -1, 5.0)

    def test_zero_speed_raises(self) -> None:
        with pytest.raises(ContractViolation, match="speed"):
            Projectile(0.0, 0.0, 0.0, 10, 0.0)


class TestFFProjectileMovement:
    """Test Force Field projectile physics."""

    def _open_map(self) -> MagicMock:
        m = MagicMock()
        m.is_wall.return_value = False
        return m

    def test_moves_at_angle(self) -> None:
        angle = math.pi / 6  # 30°
        p = Projectile(5.0, 5.0, angle, 10, 2.0)
        p.update(self._open_map())
        expected_x = 5.0 + math.cos(angle) * 2.0
        expected_y = 5.0 + math.sin(angle) * 2.0
        assert abs(p.x - expected_x) < 1e-9
        assert abs(p.y - expected_y) < 1e-9

    def test_dead_no_update(self) -> None:
        p = Projectile(5.0, 5.0, 0.0, 10, 1.0)
        p.alive = False
        p.update(self._open_map())
        assert p.x == 5.0


# ─── SoundManager Tests ──────────────────────────────────────


class TestFFSoundManager:
    """Test Force Field SoundManager configuration."""

    def test_inherits_from_base(self) -> None:
        from games.shared.sound_manager_base import SoundManagerBase

        assert issubclass(SoundManager, SoundManagerBase)

    def test_has_sound_files(self) -> None:
        assert isinstance(SoundManager.SOUND_FILES, dict)
        assert len(SoundManager.SOUND_FILES) > 0

    def test_combat_sounds(self) -> None:
        required = ["shoot", "enemy_shoot", "death", "player_hit"]
        for sound in required:
            assert sound in SoundManager.SOUND_FILES, f"Missing: {sound}"

    def test_music_tracks(self) -> None:
        required = ["music_intro", "music_loop"]
        for track in required:
            assert track in SoundManager.SOUND_FILES, f"Missing: {track}"

    def test_all_values_strings(self) -> None:
        for key, val in SoundManager.SOUND_FILES.items():
            assert isinstance(val, str), f"{key} not a string"

    def test_audio_extensions(self) -> None:
        valid = (".wav", ".mp3", ".ogg")
        for key, filename in SoundManager.SOUND_FILES.items():
            assert filename.endswith(valid), f"{key}: {filename}"


# ─── InputManager Tests ──────────────────────────────────────


class TestFFInputManager:
    """Test Force Field InputManager bindings."""

    def test_inherits_from_base(self) -> None:
        from games.shared.input_manager_base import InputManagerBase

        assert issubclass(InputManager, InputManagerBase)

    def test_has_default_bindings(self) -> None:
        assert isinstance(InputManager.DEFAULT_BINDINGS, dict)

    def test_movement_keys(self) -> None:
        required = ["move_forward", "move_backward", "strafe_left", "strafe_right"]
        for key in required:
            assert key in InputManager.DEFAULT_BINDINGS

    def test_combat_keys(self) -> None:
        required = ["shoot", "reload", "bomb", "shield"]
        for key in required:
            assert key in InputManager.DEFAULT_BINDINGS

    def test_force_field_has_dash(self) -> None:
        """Force Field has a unique dash mechanic."""
        assert "dash" in InputManager.DEFAULT_BINDINGS
        assert InputManager.DEFAULT_BINDINGS["dash"] == pygame.K_LSHIFT

    def test_sprint_is_tab(self) -> None:
        """Force Field uses TAB for sprint (dash took LSHIFT)."""
        assert InputManager.DEFAULT_BINDINGS["sprint"] == pygame.K_TAB

    def test_shield_is_space(self) -> None:
        assert InputManager.DEFAULT_BINDINGS["shield"] == pygame.K_SPACE

    def test_weapon_slots(self) -> None:
        for i in range(1, 7):
            assert f"weapon_{i}" in InputManager.DEFAULT_BINDINGS

    def test_has_minigun(self) -> None:
        assert "weapon_minigun" in InputManager.DEFAULT_BINDINGS

    def test_all_bindings_are_ints(self) -> None:
        for key, val in InputManager.DEFAULT_BINDINGS.items():
            assert isinstance(val, int), f"{key} not int"

    def test_movement_bindings_unique(self) -> None:
        movement = {
            InputManager.DEFAULT_BINDINGS[k]
            for k in ["move_forward", "move_backward", "strafe_left", "strafe_right"]
        }
        assert len(movement) == 4

    def test_pause_is_escape(self) -> None:
        assert InputManager.DEFAULT_BINDINGS["pause"] == pygame.K_ESCAPE
