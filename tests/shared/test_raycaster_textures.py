"""Tests for games.shared.raycaster_textures module.

Covers TextureCache, build_texture_strips, and TextureManager
using mock surfaces to avoid full pygame rendering.

TextureGenerator.generate_textures is patched to avoid the
pygame.surfarray dependency (not available in all environments).
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

pygame = pytest.importorskip("pygame")

import pygame as pg  # noqa: E402

from games.shared.raycaster_textures import (  # noqa: E402
    DEFAULT_TEXTURE_MAP,
    TextureCache,
    TextureManager,
    build_texture_strips,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


class DummySurface:
    """Lightweight stand-in for pygame.Surface that supports subsurface slicing."""

    def __init__(self, size: tuple[int, int] = (4, 4)) -> None:
        self._w, self._h = size

    def get_width(self) -> int:
        return self._w

    def get_height(self) -> int:
        return self._h

    def subsurface(self, rect: tuple[int, int, int, int]) -> DummySurface:
        return DummySurface((rect[2], rect[3]))

    def fill(self, *args: object, **kwargs: object) -> None:
        pass

    def __bool__(self) -> bool:
        return True


def _make_dummy_textures() -> dict[str, DummySurface]:
    """Return minimal dummy textures for all default names."""
    names = ["stone", "brick", "metal", "tech", "hidden"]
    return {name: DummySurface((8, 8)) for name in names}


@pytest.fixture(autouse=True)
def _init_pygame() -> None:
    pg.init()
    try:
        pg.display.set_mode((64, 64), pg.HIDDEN)
    except (pg.error, OSError):
        pass


def _make_strips(width: int = 4, height: int = 4) -> dict[str, list[DummySurface]]:
    """Return a minimal strip mapping backed by DummySurface objects."""
    surf = DummySurface((width, height))
    return {"brick": [surf.subsurface((x, 0, 1, height)) for x in range(width)]}


_SCALE_PATCH = "games.shared.raycaster_textures.pygame.transform.scale"
_GEN_PATCH = "games.shared.raycaster_textures.TextureGenerator.generate_textures"


# ---------------------------------------------------------------------------
# build_texture_strips
# ---------------------------------------------------------------------------


class TestBuildTextureStrips:
    """Tests for the build_texture_strips helper."""

    def test_strips_per_column(self) -> None:
        """Each texture should produce width-many strip surfaces."""
        tex = DummySurface((8, 16))
        result = build_texture_strips({"stone": tex})
        assert "stone" in result
        assert len(result["stone"]) == 8

    def test_strip_dimensions(self) -> None:
        """Each strip should be 1 pixel wide and full texture height."""
        tex = DummySurface((4, 32))
        strips = build_texture_strips({"metal": tex})["metal"]
        for strip in strips:
            assert strip.get_width() == 1
            assert strip.get_height() == 32

    def test_multiple_textures(self) -> None:
        """All textures should be present in the result."""
        textures = {"a": DummySurface((2, 2)), "b": DummySurface((3, 3))}
        result = build_texture_strips(textures)
        assert set(result) == {"a", "b"}
        assert len(result["a"]) == 2
        assert len(result["b"]) == 3

    def test_empty_dict_raises(self) -> None:
        """Passing an empty dict should raise AssertionError (DbC)."""
        with pytest.raises(AssertionError):
            build_texture_strips({})


# ---------------------------------------------------------------------------
# TextureCache
# ---------------------------------------------------------------------------


def _scaled_dummy(surface: object, size: tuple[int, int]) -> DummySurface:
    """Stand-in for pygame.transform.scale that returns a DummySurface."""
    return DummySurface(size)


class TestTextureCache:
    """Tests for the bounded LRU TextureCache."""

    def test_cache_miss_returns_scaled_strip(self) -> None:
        """First access should scale the strip and cache it."""
        strips = _make_strips(4, 16)
        cache = TextureCache(strips, max_entries=10)
        with patch(_SCALE_PATCH, side_effect=_scaled_dummy):
            result = cache.get("brick", 0, 32)
        assert result is not None
        assert result.get_height() == 32
        assert result.get_width() == 1

    def test_cache_hit_returns_same_surface(self) -> None:
        """Second access to the same key should return the cached surface."""
        strips = _make_strips(4, 16)
        cache = TextureCache(strips, max_entries=10)
        with patch(_SCALE_PATCH, side_effect=_scaled_dummy):
            first = cache.get("brick", 0, 32)
            second = cache.get("brick", 0, 32)
        assert first is second

    def test_unknown_texture_returns_none(self) -> None:
        """Requesting a texture not in strips should return None."""
        cache = TextureCache(_make_strips(), max_entries=10)
        assert cache.get("nonexistent", 0, 32) is None

    def test_excessive_height_returns_none(self) -> None:
        """Heights > 16000 should be rejected (memory guard)."""
        cache = TextureCache(_make_strips(), max_entries=10)
        assert cache.get("brick", 0, 20000) is None

    def test_evict_lru_removes_oldest(self) -> None:
        """evict_lru should purge oldest entries when cache exceeds max_entries."""
        strips = _make_strips(4, 16)
        cache = TextureCache(strips, max_entries=2, evict_count=1)
        with patch(_SCALE_PATCH, side_effect=_scaled_dummy):
            cache.get("brick", 0, 10)
            cache.get("brick", 1, 10)
            cache.get("brick", 2, 10)  # Over limit; triggers eviction next call
        cache.evict_lru()
        assert cache.size <= 2

    def test_size_property(self) -> None:
        """size should reflect the number of entries in the cache."""
        strips = _make_strips(4, 16)
        cache = TextureCache(strips, max_entries=10)
        assert cache.size == 0
        with patch(_SCALE_PATCH, side_effect=_scaled_dummy):
            cache.get("brick", 0, 10)
        assert cache.size == 1

    def test_invalid_max_entries_raises(self) -> None:
        """max_entries <= 0 should raise AssertionError (DbC)."""
        with pytest.raises(AssertionError):
            TextureCache(_make_strips(), max_entries=0)

    def test_invalid_evict_count_raises(self) -> None:
        """evict_count <= 0 should raise AssertionError (DbC)."""
        with pytest.raises(AssertionError):
            TextureCache(_make_strips(), max_entries=10, evict_count=0)


# ---------------------------------------------------------------------------
# TextureManager
# ---------------------------------------------------------------------------


@pytest.fixture()
def mgr() -> TextureManager:
    """Return a TextureManager backed by dummy textures."""
    dummy_textures = _make_dummy_textures()
    with (
        patch(
            _GEN_PATCH,
            return_value=dummy_textures,
        ),
        patch(_SCALE_PATCH, side_effect=_scaled_dummy),
    ):
        return TextureManager()


class TestTextureManager:
    """Integration-level tests for TextureManager."""

    def test_default_texture_map(self, mgr: TextureManager) -> None:
        """TextureManager should use DEFAULT_TEXTURE_MAP if none given."""
        assert mgr.texture_map == DEFAULT_TEXTURE_MAP

    def test_custom_texture_map(self) -> None:
        """Custom texture_map should be stored verbatim."""
        dummy_textures = _make_dummy_textures()
        with patch(
            _GEN_PATCH,
            return_value=dummy_textures,
        ):
            custom = {1: "custom_tex"}
            mgr2 = TextureManager(texture_map=custom)
            assert mgr2.texture_map == custom

    def test_use_textures_is_true(self, mgr: TextureManager) -> None:
        """use_textures should default to True."""
        assert mgr.use_textures is True

    def test_texture_strips_populated(self, mgr: TextureManager) -> None:
        """texture_strips should contain strips for all generated textures."""
        assert len(mgr.texture_strips) > 0
        for name, strips in mgr.texture_strips.items():
            assert len(strips) > 0, f"No strips for texture '{name}'"

    def test_get_cached_strip_returns_surface(self, mgr: TextureManager) -> None:
        """get_cached_strip should return a Surface for valid requests."""
        with patch(
            _SCALE_PATCH,
            side_effect=_scaled_dummy,
        ):
            name = next(iter(mgr.texture_strips))
            result = mgr.get_cached_strip(name, 0, 64)
        assert result is not None
        assert result.get_height() == 64

    def test_get_cached_strip_unknown_returns_none(self, mgr: TextureManager) -> None:
        """get_cached_strip for an unknown texture should return None."""
        assert mgr.get_cached_strip("does_not_exist", 0, 64) is None

    def test_evict_cache_does_not_raise(self, mgr: TextureManager) -> None:
        """evict_cache() should be callable without error."""
        mgr.evict_cache()  # Should not raise

    def test_get_wall_strips_filters_by_texture_map(self, mgr: TextureManager) -> None:
        """get_wall_strips should only include wall types with a known texture."""
        wall_strips = mgr.get_wall_strips()
        for wt, strips in wall_strips.items():
            assert isinstance(wt, int)
            assert len(strips) > 0

    def test_build_wall_strips_for_render(self, mgr: TextureManager) -> None:
        """build_wall_strips_for_render should return strips for known types."""
        # wall_colors with a known type (type 1 → stone) and an unknown type
        wall_colors = {1: (100, 100, 100), 99: (0, 0, 0)}
        result = mgr.build_wall_strips_for_render(wall_colors)
        assert 1 in result
        for _wt, strips in result.items():
            assert len(strips) > 0

    def test_cache_size_property(self, mgr: TextureManager) -> None:
        """cache_size should reflect current strip cache size."""
        assert mgr.cache_size == 0
        with patch(
            _SCALE_PATCH,
            side_effect=_scaled_dummy,
        ):
            name = next(iter(mgr.texture_strips))
            mgr.get_cached_strip(name, 0, 32)
        assert mgr.cache_size == 1
