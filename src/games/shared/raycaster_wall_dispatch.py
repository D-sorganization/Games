"""Wall-column rendering dispatch mixin for Raycaster.

Extracted from raycaster.py (issue #775) to reduce that module's size.
Contains the per-ray list building, wall column dispatch, visible-ray
iteration, vectorized wall rendering, and sprite/texture context helpers.

All methods are pure behaviour operating on ``self`` state -- they are
mixed into the ``Raycaster`` class so that the public API is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
import pygame

from .raycaster_render_contexts import SpriteRenderContext, TexturedWallColumnContext
from .raycaster_rendering import (
    prepare_wall_render_data,
    render_solid_wall_column,
    render_textured_wall_column,
)
from .raycaster_sprites import render_sprites as _render_sprites_fn

if TYPE_CHECKING:
    from collections import OrderedDict

    from .config import RaycasterConfig
    from .interfaces import Player


@dataclass(slots=True)
class _PerRayLists:
    """Bundle of per-ray Python lists produced by _build_per_ray_lists."""

    distances: list[float]
    wall_types: list[int]
    wall_x_hits: list[float]
    wall_heights: list[int]
    wall_tops: list[int]
    shades: list[float]
    fog_factors: list[float]


class _RaycasterWallDispatch:
    """Mixin providing wall-column dispatch and sprite context helpers."""

    # These attributes are provided by the owning Raycaster instance.
    config: RaycasterConfig
    num_rays: int
    use_textures: bool
    textures: Any
    texture_map: Any
    _texture_mgr: Any
    view_surface: pygame.Surface
    shading_surfaces: list[pygame.Surface]
    fog_surfaces: list[pygame.Surface]
    render_scale: int
    z_buffer: np.ndarray[Any, np.dtype[Any]]
    sprite_cache: OrderedDict[Any, Any]
    _SPRITE_CACHE_MAX: int
    _SPRITE_CACHE_EVICT: int
    _scaled_sprite_cache: OrderedDict[Any, Any]
    _SCALED_SPRITE_CACHE_MAX: int
    _SCALED_SPRITE_CACHE_EVICT: int
    _cached_level: int
    _cached_wall_colors: dict[int, tuple[int, int, int]]

    # Provided by Raycaster
    def _get_cached_strip(
        self, texture_name: str, strip_x: int, height: int
    ) -> pygame.Surface | None: ...  # type: ignore[empty-body]

    @staticmethod
    def _evict_lru(
        cache: OrderedDict[Any, Any],
        max_size: int,
        evict_count: int,
    ) -> None: ...  # type: ignore[empty-body]

    def _prepare_wall_render_data(
        self,
        distances: np.ndarray[Any, Any],
        player: Player,
        fisheye_factors: np.ndarray[Any, Any],
        view_offset_y: float,
    ) -> tuple[list[int], list[int], list[float], list[float]]:
        """Compute wall heights, tops, shading and fog from distances."""
        return prepare_wall_render_data(
            distances,
            fisheye_factors,
            self.config.SCREEN_HEIGHT,
            self.config.MAX_DEPTH,
            self.config.FOG_START,
            float(player.pitch),
            view_offset_y,
        )

    def _build_per_ray_lists(
        self,
        distances: np.ndarray[Any, Any],
        wall_types: np.ndarray[Any, Any],
        wall_x_hits: np.ndarray[Any, Any],
        player: Player,
        fisheye_factors: np.ndarray[Any, Any],
        view_offset_y: float,
    ) -> _PerRayLists:
        """Convert array inputs to Python lists for fast per-ray access.

        Python list indexing is ~5-10x faster than numpy scalar indexing
        for pure-Python per-ray loops.  (See issue #477.)
        """
        wall_heights, wall_tops, shades, fog_factors = self._prepare_wall_render_data(
            distances, player, fisheye_factors, view_offset_y
        )
        return _PerRayLists(
            distances=distances.tolist(),
            wall_types=wall_types.tolist(),
            wall_x_hits=wall_x_hits.tolist(),
            wall_heights=wall_heights,
            wall_tops=wall_tops,
            shades=shades,
            fog_factors=fog_factors,
        )

    def _draw_wall_column(  # noqa: PLR0913
        self,
        i: int,
        wt: int,
        h: int,
        top: int,
        wall_x_hit: float,
        shade: float,
        fog: float,
        use_textures: bool,
        wall_strips: dict[int, list[pygame.Surface]],
        wall_colors: dict[int, tuple[int, int, int]],
        view_surface: pygame.Surface,
        blits_sequence: list[Any],
    ) -> None:
        """Dispatch one ray column to the textured or solid wall renderer."""
        if use_textures and wt in wall_strips:
            self._render_textured_wall(
                i,
                wt,
                h,
                top,
                wall_x_hit,
                shade,
                fog,
                wall_strips,
                wall_colors,
                view_surface,
                blits_sequence,
            )
        else:
            self._render_solid_wall(
                i, wt, h, top, shade, fog, wall_colors, view_surface
            )

    def _iterate_visible_rays(
        self,
        prl: _PerRayLists,
        use_textures: bool,
        wall_strips: dict[int, list[pygame.Surface]],
        wall_colors: dict[int, tuple[int, int, int]],
        view_surface: pygame.Surface,
        blits_sequence: list[Any],
    ) -> None:
        """Loop over rays and dispatch each visible wall column to the renderer."""
        for i in range(self.num_rays):
            if prl.distances[i] >= self.config.MAX_DEPTH:
                continue
            wt = prl.wall_types[i]
            if wt == 0:
                continue
            self._draw_wall_column(
                i,
                wt,
                prl.wall_heights[i],
                prl.wall_tops[i],
                prl.wall_x_hits[i],
                prl.shades[i],
                prl.fog_factors[i],
                use_textures,
                wall_strips,
                wall_colors,
                view_surface,
                blits_sequence,
            )

    def _render_walls_vectorized(
        self,
        distances: np.ndarray[Any, Any],
        wall_types: np.ndarray[Any, Any],
        wall_x_hits: np.ndarray[Any, Any],
        sides: np.ndarray[Any, Any],
        player: Player,
        fisheye_factors: np.ndarray[Any, Any],
        level: int,
        view_offset_y: float,
        flash_intensity: float,
    ) -> None:
        """Render walls using computed arrays."""
        wall_colors = self._resolve_wall_theme(level)
        prl = self._build_per_ray_lists(
            distances, wall_types, wall_x_hits, player, fisheye_factors, view_offset_y
        )
        use_textures = self.use_textures and len(self.textures) > 0
        wall_strips = self._texture_mgr.build_wall_strips_for_render(wall_colors)
        view_surface = self.view_surface
        blits_sequence: list[Any] = []
        self._iterate_visible_rays(
            prl, use_textures, wall_strips, wall_colors, view_surface, blits_sequence
        )
        if blits_sequence:
            view_surface.blits(blits_sequence, doreturn=False)

    def _resolve_wall_theme(self, level: int) -> dict[int, tuple[int, int, int]]:
        """Resolve wall colour theme for the current level."""
        if self._cached_level == level:
            return self._cached_wall_colors

        level_themes = self.config.LEVEL_THEMES or []
        theme_idx = (level - 1) % len(level_themes) if level_themes else 0
        theme = level_themes[theme_idx] if level_themes else None
        wall_colors: dict[int, tuple[int, int, int]] = (
            theme.get("walls", {}) if theme else {}
        )
        self._cached_level = level
        self._cached_wall_colors = wall_colors
        return wall_colors

    def _build_textured_wall_context(  # noqa: PLR0913
        self,
        i: int,
        wt: int,
        h: int,
        top: int,
        wall_x_hit: float,
        shade: float,
        fog: float,
        wall_strips: dict[int, list[pygame.Surface]],
        wall_colors: dict[int, tuple[int, int, int]],
        view_surface: pygame.Surface,
        blits_sequence: list[Any],
    ) -> TexturedWallColumnContext:
        """Build a TexturedWallColumnContext from renderer state for one column."""
        return TexturedWallColumnContext(
            i,
            wt,
            h,
            top,
            wall_x_hit,
            shade,
            fog,
            wall_strips,
            wall_colors,
            view_surface,
            blits_sequence,
            self.config.GRAY,
            self.texture_map,
            self.shading_surfaces,
            self.fog_surfaces,
            self._get_cached_strip,
        )

    def _render_textured_wall(  # noqa: PLR0913
        self,
        i: int,
        wt: int,
        h: int,
        top: int,
        wall_x_hit: float,
        shade: float,
        fog: float,
        wall_strips: dict[int, list[pygame.Surface]],
        wall_colors: dict[int, tuple[int, int, int]],
        view_surface: pygame.Surface,
        blits_sequence: list[Any],
    ) -> None:
        """Render a single textured wall column with shading and fog."""
        render_textured_wall_column(
            self._build_textured_wall_context(
                i,
                wt,
                h,
                top,
                wall_x_hit,
                shade,
                fog,
                wall_strips,
                wall_colors,
                view_surface,
                blits_sequence,
            )
        )

    def _render_solid_wall(
        self,
        i: int,
        wt: int,
        h: int,
        top: int,
        shade: float,
        fog: float,
        wall_colors: dict[int, tuple[int, int, int]],
        view_surface: pygame.Surface,
    ) -> None:
        """Render a single wall column as a solid shaded/fogged colour."""
        render_solid_wall_column(
            i,
            wt,
            h,
            top,
            shade,
            fog,
            wall_colors,
            view_surface,
            self.config.GRAY,
            self.config.FOG_COLOR,
        )

    def _build_sprite_context(
        self,
        player: Player,
        bots: Any,
        projectiles: Any,
        particles: Any,
        half_fov: float,
        view_offset_y: float,
        flash_intensity: float,
    ) -> SpriteRenderContext:
        """Build a SpriteRenderContext from current renderer state."""
        return SpriteRenderContext(
            player,
            bots,
            projectiles,
            particles,
            half_fov,
            view_offset_y,
            flash_intensity,
            self.config,
            self.num_rays,
            self.render_scale,
            self.view_surface,
            self.z_buffer,
            self.sprite_cache,
            self._SPRITE_CACHE_MAX,
            self._SPRITE_CACHE_EVICT,
            self._scaled_sprite_cache,
            self._SCALED_SPRITE_CACHE_MAX,
            self._SCALED_SPRITE_CACHE_EVICT,
            self._evict_lru,
        )

    def _render_sprites(
        self,
        player: Player,
        bots: Any,
        projectiles: Any,
        particles: Any,
        half_fov: float,
        view_offset_y: float = 0.0,
        flash_intensity: float = 0.0,
    ) -> None:
        """Render all sprites (bots, projectiles, particles) to the view surface."""
        _render_sprites_fn(
            self._build_sprite_context(
                player,
                bots,
                projectiles,
                particles,
                half_fov,
                view_offset_y,
                flash_intensity,
            )
        )
