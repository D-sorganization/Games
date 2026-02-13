"""Tests for the games.shared.config module."""

from __future__ import annotations

import pytest

from games.shared.config import RaycasterConfig


class TestRaycasterConfig:
    """Tests for the RaycasterConfig dataclass."""

    def test_required_fields(self) -> None:
        """RaycasterConfig should require screen size and FOV."""
        cfg = RaycasterConfig(
            SCREEN_WIDTH=1200,
            SCREEN_HEIGHT=800,
            FOV=1.047,
            HALF_FOV=0.524,
        )
        assert cfg.SCREEN_WIDTH == 1200
        assert cfg.SCREEN_HEIGHT == 800
        assert cfg.FOV == pytest.approx(1.047)
        assert cfg.HALF_FOV == pytest.approx(0.524)

    def test_default_values(self) -> None:
        """Default optional values should be sensible."""
        cfg = RaycasterConfig(
            SCREEN_WIDTH=800,
            SCREEN_HEIGHT=600,
            FOV=1.0,
            HALF_FOV=0.5,
        )
        assert cfg.ZOOM_FOV_MULT == pytest.approx(0.5)
        assert cfg.DEFAULT_RENDER_SCALE == 1
        assert cfg.MAX_DEPTH == pytest.approx(20.0)
        assert cfg.FOG_START == pytest.approx(0.6)
        assert cfg.FOG_COLOR == (0, 0, 0)
        assert cfg.LEVEL_THEMES is None
        assert cfg.WALL_COLORS is None

    def test_color_defaults(self) -> None:
        """Default colors should be standard values."""
        cfg = RaycasterConfig(
            SCREEN_WIDTH=800,
            SCREEN_HEIGHT=600,
            FOV=1.0,
            HALF_FOV=0.5,
        )
        assert cfg.BLACK == (0, 0, 0)
        assert cfg.WHITE == (255, 255, 255)
        assert cfg.RED == (255, 0, 0)
        assert cfg.GREEN == (0, 255, 0)
        assert cfg.CYAN == (0, 255, 255)
        assert cfg.YELLOW == (255, 255, 0)

    def test_custom_fog_color(self) -> None:
        """Should accept custom fog color."""
        cfg = RaycasterConfig(
            SCREEN_WIDTH=800,
            SCREEN_HEIGHT=600,
            FOV=1.0,
            HALF_FOV=0.5,
            FOG_COLOR=(20, 0, 0),
        )
        assert cfg.FOG_COLOR == (20, 0, 0)

    def test_custom_wall_colors(self) -> None:
        """Should accept custom wall colors mapping."""
        walls = {1: (100, 100, 100), 2: (200, 200, 200)}
        cfg = RaycasterConfig(
            SCREEN_WIDTH=800,
            SCREEN_HEIGHT=600,
            FOV=1.0,
            HALF_FOV=0.5,
            WALL_COLORS=walls,
        )
        assert cfg.WALL_COLORS == walls

    def test_custom_render_scale(self) -> None:
        """Should accept custom render scale."""
        cfg = RaycasterConfig(
            SCREEN_WIDTH=1200,
            SCREEN_HEIGHT=800,
            FOV=1.0,
            HALF_FOV=0.5,
            DEFAULT_RENDER_SCALE=4,
        )
        assert cfg.DEFAULT_RENDER_SCALE == 4
