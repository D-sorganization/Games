"""Texture loading, caching, and strip management for the raycasting engine.

Extracted from raycaster.py to separate texture management (a single
responsibility) from the core ray-casting and rendering logic.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Any

import pygame

from .texture_generator import TextureGenerator

if TYPE_CHECKING:
    pass


# Default mapping of wall-type integers to texture names
DEFAULT_TEXTURE_MAP: dict[int, str] = {
    1: "stone",
    2: "brick",
    3: "metal",
    4: "tech",
    5: "hidden",
}


def build_texture_strips(
    textures: dict[str, pygame.Surface],
) -> dict[str, list[pygame.Surface]]:
    """Pre-slice each texture surface into 1-pixel-wide column strips.

    Args:
        textures: Mapping of texture name to full texture surface.

    Returns:
        Mapping of texture name to list of 1-pixel-wide sub-surfaces (one per column).

    Preconditions:
        ``textures`` must be non-empty and all surfaces must have positive dimensions.
    """
    msg = "textures must not be empty"
    assert textures, msg
    strips: dict[str, list[pygame.Surface]] = {}
    for name, tex in textures.items():
        w = tex.get_width()
        h = tex.get_height()
        strips[name] = [tex.subsurface((x, 0, 1, h)) for x in range(w)]
    return strips


class TextureCache:
    """Bounded LRU cache for scaled texture-strip surfaces.

    Manages a single OrderedDict that maps ``(texture_name, strip_x, height)``
    keys to pre-scaled 1×height ``pygame.Surface`` objects.  Eviction happens
    in batches to amortise the cost of the length check (see issue #583).

    Args:
        strips: Pre-built texture-strip mapping from :func:`build_texture_strips`.
        max_entries: Maximum number of cache entries before eviction is triggered.
        evict_count: Number of LRU entries to drop per eviction pass.
    """

    def __init__(
        self,
        strips: dict[str, list[pygame.Surface]],
        max_entries: int = 512,
        evict_count: int = 64,
    ) -> None:
        msg = "max_entries must be positive"
        assert max_entries > 0, msg
        msg = "evict_count must be positive"
        assert evict_count > 0, msg
        self._strips = strips
        self._max_entries = max_entries
        self._evict_count = evict_count
        self._cache: OrderedDict[tuple[str, int, int], pygame.Surface] = OrderedDict()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(
        self, texture_name: str, strip_x: int, height: int
    ) -> pygame.Surface | None:
        """Return a cached scaled strip, creating it on first access.

        Args:
            texture_name: Key into the texture strips dictionary.
            strip_x: Column index within the texture.
            height: Target render height in pixels.

        Returns:
            Scaled 1×height surface, or ``None`` if the texture is unknown
            or if the height exceeds the safe limit.
        """
        key = (texture_name, strip_x, height)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]

        strips = self._strips.get(texture_name)
        if not strips:
            return None
        try:
            if height > 16000:
                return None
            scaled = pygame.transform.scale(strips[strip_x], (1, height))
            self._cache[key] = scaled
            return scaled
        except (pygame.error, ValueError, IndexError):
            return None

    def evict_lru(self) -> None:
        """Evict the oldest entries when the cache exceeds its size limit."""
        while len(self._cache) > self._max_entries:
            for _ in range(min(self._evict_count, len(self._cache))):
                self._cache.popitem(last=False)

    # ------------------------------------------------------------------
    # Internal helpers (exposed for testing)
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Current number of entries in the cache."""
        return len(self._cache)


class TextureManager:
    """Aggregates texture generation, strip management, and strip caching.

    This class is the single entry-point for all texture concerns; the
    :class:`~games.shared.raycaster.Raycaster` delegates to it instead of
    managing individual texture dicts directly.

    Args:
        texture_map: Optional override for the wall-type → texture-name mapping.
            Defaults to :data:`DEFAULT_TEXTURE_MAP`.
        strip_cache_max: Maximum number of cached scaled strips.
        strip_cache_evict: Number of LRU entries to drop on each eviction pass.
    """

    def __init__(
        self,
        texture_map: dict[int, str] | None = None,
        strip_cache_max: int = 512,
        strip_cache_evict: int = 64,
    ) -> None:
        self.texture_map: dict[int, str] = (
            dict(DEFAULT_TEXTURE_MAP) if texture_map is None else texture_map
        )
        self.use_textures: bool = True
        self.textures: dict[str, pygame.Surface] = TextureGenerator.generate_textures()
        self.texture_strips: dict[str, list[pygame.Surface]] = build_texture_strips(
            self.textures
        )
        self._cache: TextureCache = TextureCache(
            self.texture_strips, strip_cache_max, strip_cache_evict
        )

    # ------------------------------------------------------------------
    # Delegated helpers
    # ------------------------------------------------------------------

    def get_cached_strip(
        self, texture_name: str, strip_x: int, height: int
    ) -> pygame.Surface | None:
        """Fetch (and cache) a scaled strip.  See :meth:`TextureCache.get`."""
        return self._cache.get(texture_name, strip_x, height)

    def evict_cache(self) -> None:
        """Perform a cache-maintenance pass.  Call once per frame."""
        self._cache.evict_lru()

    def get_wall_strips(self) -> dict[int, list[pygame.Surface]]:
        """Return a mapping of wall-type → texture strip list.

        Only wall types present in :attr:`texture_map` that also have a
        loaded texture are included.
        """
        result: dict[int, list[pygame.Surface]] = {}
        for wt, tname in self.texture_map.items():
            if tname in self.texture_strips:
                result[wt] = self.texture_strips[tname]
        return result

    # Keep raw access for legacy callers that read these directly
    @property
    def cache_size(self) -> int:
        """Current number of entries in the strip cache."""
        return self._cache.size

    def build_wall_strips_for_render(
        self, wall_colors: dict[int, Any]
    ) -> dict[int, list[pygame.Surface]]:
        """Pre-fetch texture strips for wall types present in *wall_colors*.

        Args:
            wall_colors: Mapping of wall-type int to colour.

        Returns:
            Mapping of wall-type int to list of texture strips.
        """
        wall_strips: dict[int, list[pygame.Surface]] = {}
        for wt in wall_colors:
            tname = self.texture_map.get(wt, "brick")
            if tname in self.texture_strips:
                wall_strips[wt] = self.texture_strips[tname]
        return wall_strips
