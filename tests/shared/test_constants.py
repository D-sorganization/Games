"""Tests for the games.shared.constants module.

Validates that shared constants have sensible values and correct types,
acting as a safety net against accidental mutations.
"""

from __future__ import annotations

import math

import pytest

from games.shared import constants as C


class TestScreenConstants:
    """Tests for screen and display constants."""

    def test_screen_dimensions_positive(self) -> None:
        """Screen dimensions must be positive integers."""
        assert C.SCREEN_WIDTH > 0
        assert C.SCREEN_HEIGHT > 0
        assert isinstance(C.SCREEN_WIDTH, int)
        assert isinstance(C.SCREEN_HEIGHT, int)

    def test_fps_positive(self) -> None:
        """FPS must be a positive integer."""
        assert C.FPS > 0
        assert isinstance(C.FPS, int)


class TestRenderConstants:
    """Tests for rendering quality constants."""

    def test_default_render_scale_valid(self) -> None:
        """Default render scale must be in the options list."""
        assert C.DEFAULT_RENDER_SCALE in C.RENDER_SCALE_OPTIONS

    def test_render_scale_names_match_options(self) -> None:
        """Every render scale option should have a name."""
        for scale in C.RENDER_SCALE_OPTIONS:
            assert scale in C.RENDER_SCALE_NAMES


class TestPlayerConstants:
    """Tests for player-related constants."""

    def test_speeds_positive(self) -> None:
        """Player speeds must be positive."""
        assert C.PLAYER_SPEED > 0
        assert C.PLAYER_SPRINT_SPEED > 0

    def test_sprint_faster_than_walk(self) -> None:
        """Sprint speed should be greater than normal speed."""
        assert C.PLAYER_SPRINT_SPEED > C.PLAYER_SPEED

    def test_fov_valid_range(self) -> None:
        """FOV must be between 0 and pi."""
        assert 0 < C.FOV < math.pi

    def test_half_fov_consistency(self) -> None:
        """HALF_FOV should be exactly half of FOV."""
        assert C.HALF_FOV == pytest.approx(C.FOV / 2)


class TestMapConstants:
    """Tests for map constants."""

    def test_map_sizes_sorted(self) -> None:
        """Map sizes should be in ascending order."""
        assert C.MAP_SIZES == sorted(C.MAP_SIZES)

    def test_default_map_size_in_list(self) -> None:
        """Default map size should be one of the available sizes."""
        assert C.DEFAULT_MAP_SIZE in C.MAP_SIZES


class TestDifficultyConstants:
    """Tests for difficulty settings."""

    def test_all_difficulties_have_required_keys(self) -> None:
        """Each difficulty must have damage_mult, health_mult, score_mult."""
        required_keys = {"damage_mult", "health_mult", "score_mult"}
        for name, settings in C.DIFFICULTIES.items():
            assert required_keys.issubset(
                set(settings.keys())
            ), f"Difficulty '{name}' missing keys"

    def test_normal_difficulty_is_baseline(self) -> None:
        """NORMAL difficulty should have all multipliers at 1.0."""
        normal = C.DIFFICULTIES["NORMAL"]
        assert normal["damage_mult"] == 1.0
        assert normal["health_mult"] == 1.0
        assert normal["score_mult"] == 1.0

    def test_easy_is_easier_than_normal(self) -> None:
        """EASY should have lower damage multiplier than NORMAL."""
        easy = C.DIFFICULTIES["EASY"]["damage_mult"]
        normal = C.DIFFICULTIES["NORMAL"]["damage_mult"]
        assert easy < normal


class TestColorConstants:
    """Tests for color tuple constants."""

    @pytest.mark.parametrize(
        "color_name",
        ["BLACK", "WHITE", "RED", "GREEN", "BLUE", "YELLOW", "CYAN"],
    )
    def test_colors_are_rgb_tuples(self, color_name: str) -> None:
        """Standard colors should be 3-element tuples of ints 0-255."""
        color = getattr(C, color_name)
        assert isinstance(color, tuple)
        assert len(color) == 3
        for component in color:
            assert 0 <= component <= 255


class TestCombatConstants:
    """Tests for health and combat constants."""

    def test_initial_health_equals_max(self) -> None:
        """Initial health should equal max health."""
        assert C.INITIAL_HEALTH == C.MAX_HEALTH

    def test_headshot_multiplier_greater_than_one(self) -> None:
        """Headshot multiplier should be greater than 1."""
        assert C.HEADSHOT_MULTIPLIER > 1.0
