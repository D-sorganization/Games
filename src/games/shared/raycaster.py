from __future__ import annotations

import math
import random
from collections import OrderedDict
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import numpy as np
import pygame

from .contracts import validate_positive
from .raycaster_math import (
    finalize_ray_data,
    get_ray_directions,
    init_dda_params,
    perform_dda_loop,
)
from .raycaster_rendering import (
    generate_background_surface as _generate_background_surface_fn,
)
from .raycaster_rendering import (
    generate_minimap_cache,
    prepare_wall_render_data,
    render_solid_wall_column,
    render_textured_wall_column,
)
from .raycaster_rendering import (
    render_floor_ceiling as _render_floor_ceiling_fn,
)
from .raycaster_rendering import (
    render_minimap as _render_minimap_fn,
)
from .raycaster_sprites import render_sprites as _render_sprites_fn
from .texture_generator import TextureGenerator
from .utils import cast_ray_dda

if TYPE_CHECKING:
    from .config import RaycasterConfig
    from .interfaces import (
        Bot,
        Map,
        Player,
        Portal,
        Projectile,
        WorldParticle,
    )


class Raycaster:
    """Raycasting engine for 3D rendering"""

    VISUAL_SCALE = 2.2
    STRIP_VISIBILITY_THRESHOLD = 0.3
    LARGE_SPRITE_THRESHOLD = 200

    def __init__(self, game_map: Map, config: RaycasterConfig):
        """Initialize raycaster"""
        self.game_map = game_map
        self.config = config

        self._init_map_data(game_map)
        self._init_textures()
        self._init_atmosphere()
        self._init_buffers()
        self._update_ray_angles()

    def _init_map_data(self, game_map: Map) -> None:
        """Initialize map-related members."""
        self.grid = game_map.grid
        self.np_grid = np.array(game_map.grid, dtype=np.int8)
        self.map_size = game_map.size
        self.map_width = game_map.width
        self.map_height = game_map.height

        # Cache for theme
        self._cached_level: int = -1
        self._cached_wall_colors: dict[int, tuple[int, int, int]] = {}

    def _init_textures(self) -> None:
        """Initialize texture mapping and caches."""
        self.use_textures = True
        self.textures = TextureGenerator.generate_textures()
        self.texture_map = {1: "stone", 2: "brick", 3: "metal", 4: "tech", 5: "hidden"}

        self.texture_strips: dict[str, list[pygame.Surface]] = {}
        for name, tex in self.textures.items():
            w = tex.get_width()
            h = tex.get_height()
            self.texture_strips[name] = [tex.subsurface((x, 0, 1, h)) for x in range(w)]

        # Bounded LRU cache -- eviction handled by update_cache() each frame.
        # 512 entries keeps memory bounded (see issue #583).
        self._strip_cache: OrderedDict[tuple[str, int, int], pygame.Surface] = (
            OrderedDict()
        )
        self._STRIP_CACHE_MAX: int = 512
        self._STRIP_CACHE_EVICT: int = 64

    def _init_atmosphere(self) -> None:
        """Initialize sky backgrounds and stars."""
        self._background_surface: pygame.Surface | None = None
        self._scaled_background_surface: pygame.Surface | None = None
        self._cached_background_theme_idx: int = -1

        self.stars = [
            (
                random.randint(0, self.config.SCREEN_WIDTH),
                random.randint(0, self.config.SCREEN_HEIGHT // 2),
                random.uniform(0.5, 2.5),
                random.choice([(255, 255, 255), (200, 200, 255), (255, 255, 200)]),
            )
            for _ in range(100)
        ]

    def _init_buffers(self) -> None:
        """Initialize rendering buffers and surfaces."""
        # Bounded LRU caches -- eviction handled by update_cache() each frame.
        # Limits chosen to bound peak VRAM (see issue #583).
        self.sprite_cache: OrderedDict[tuple, pygame.Surface] = OrderedDict()
        self._SPRITE_CACHE_MAX: int = 128
        self._SPRITE_CACHE_EVICT: int = 16
        self._scaled_sprite_cache: OrderedDict[tuple, pygame.Surface] = OrderedDict()
        self._SCALED_SPRITE_CACHE_MAX: int = 64
        self._SCALED_SPRITE_CACHE_EVICT: int = 8

        self.minimap_surface: pygame.Surface | None = None
        self.minimap_size = 200
        self.minimap_scale = self.minimap_size / self.map_size
        self._fog_surface: pygame.Surface | None = None
        self._fog_visited_count: int = 0

        self.render_scale = self.config.DEFAULT_RENDER_SCALE
        self.num_rays = self.config.SCREEN_WIDTH // self.render_scale

        size = (self.num_rays, self.config.SCREEN_HEIGHT)
        self.view_surface = pygame.Surface(size, pygame.SRCALPHA)

        self.shading_surfaces: list[pygame.Surface] = []
        self.fog_surfaces: list[pygame.Surface] = []
        self._generate_shading_caches()

        self.z_buffer: np.ndarray[Any, np.dtype[Any]] = np.full(
            self.num_rays, float("inf"), dtype=np.float64
        )

    @staticmethod
    def _make_alpha_surface(
        width: int, height: int, color: tuple[int, ...], alpha: int
    ) -> pygame.Surface:
        """Create a 1-pixel wide surface filled with *color* at *alpha*."""
        s = pygame.Surface((width, height), pygame.SRCALPHA)
        s.fill((*color, alpha) if len(color) == 3 else color[:3] + (alpha,))
        return s

    def _generate_shading_caches(self) -> None:
        """Pre-generate 1-pixel wide surfaces for shading and fog alpha levels."""
        # Height must cover max possible wall height
        cache_height = self.config.SCREEN_HEIGHT * 2

        # Generate shading surfaces (Black with varying alpha)
        self.shading_surfaces = [
            self._make_alpha_surface(1, cache_height, (0, 0, 0), alpha)
            for alpha in range(256)
        ]

        # Generate fog surfaces (Fog Color with varying alpha)
        fog_col = self.config.FOG_COLOR
        self.fog_surfaces = [
            self._make_alpha_surface(1, cache_height, fog_col, alpha)
            for alpha in range(256)
        ]

    def _update_ray_angles(self) -> None:
        """Pre-calculate relative ray angles."""
        # Normal FOV
        self.deltas = np.linspace(
            -self.config.HALF_FOV, self.config.HALF_FOV, self.num_rays
        )
        self.cos_deltas = np.cos(self.deltas)
        self.sin_deltas = np.sin(self.deltas)

        # Zoomed FOV
        zoomed_fov = self.config.FOV * self.config.ZOOM_FOV_MULT
        self.deltas_zoomed = np.linspace(-zoomed_fov / 2, zoomed_fov / 2, self.num_rays)
        self.cos_deltas_zoomed = np.cos(self.deltas_zoomed)
        self.sin_deltas_zoomed = np.sin(self.deltas_zoomed)

    def set_render_scale(self, scale: int) -> None:
        """Update render scale and related buffers."""
        validate_positive(scale, "scale")
        self.render_scale = scale
        self.num_rays = self.config.SCREEN_WIDTH // scale

        # Recreate buffers
        self.view_surface = pygame.Surface(
            (self.num_rays, self.config.SCREEN_HEIGHT), pygame.SRCALPHA
        )
        self.z_buffer = np.full(self.num_rays, float("inf"), dtype=np.float64)
        self._update_ray_angles()

    @staticmethod
    def _evict_lru(
        cache: OrderedDict[Any, Any],
        max_size: int,
        evict_count: int,
    ) -> None:
        """Evict LRU entries in batches until *cache* is within *max_size*.

        Each pass pops up to *evict_count* entries from the front (oldest).
        Using a batch size rather than evicting one-at-a-time amortises the
        cost of the length check across many insertions.

        Static helper keeps ``update_cache`` free of nested loops and makes
        the eviction policy independently testable.
        """
        while len(cache) > max_size:
            for _ in range(min(evict_count, len(cache))):
                cache.popitem(last=False)

    def update_cache(self) -> None:
        """Perform cache maintenance once per frame.

        Caches use OrderedDict with LRU eviction: on hit, entries are
        moved to the end via ``move_to_end``; on eviction, the *least*
        recently used entries are popped from the front.

        Hard limits are intentionally conservative to bound peak VRAM.
        See issue #583.
        """
        self._evict_lru(
            self._strip_cache, self._STRIP_CACHE_MAX, self._STRIP_CACHE_EVICT
        )
        self._evict_lru(
            self.sprite_cache, self._SPRITE_CACHE_MAX, self._SPRITE_CACHE_EVICT
        )
        self._evict_lru(
            self._scaled_sprite_cache,
            self._SCALED_SPRITE_CACHE_MAX,
            self._SCALED_SPRITE_CACHE_EVICT,
        )

    def _get_cached_strip(
        self, texture_name: str, strip_x: int, height: int
    ) -> pygame.Surface | None:
        """Get or create a scaled texture strip."""
        cache_key = (texture_name, strip_x, height)

        if cache_key in self._strip_cache:
            self._strip_cache.move_to_end(cache_key)
            return self._strip_cache[cache_key]

        strips = self.texture_strips.get(texture_name)
        if not strips:
            return None
        try:
            # Optimization: Check if height is reasonable to prevent memory errors
            if height > 16000:  # Arbitrary safe limit
                return None
            scaled_strip = pygame.transform.scale(strips[strip_x], (1, height))
            self._strip_cache[cache_key] = scaled_strip
            return scaled_strip
        except (pygame.error, ValueError, IndexError):
            return None

    def cast_ray(
        self,
        origin_x: float,
        origin_y: float,
        angle: float,
    ) -> tuple[float, int, float, int, int]:
        """Single ray cast for game logic (using utils DDA)."""
        dist, wall_type, hit_x, hit_y, side, map_x, map_y = cast_ray_dda(
            origin_x, origin_y, angle, self.game_map
        )

        # Calculate wall_x_hit for texture mapping (0.0 - 1.0)
        if side == 0:  # Vertical hit
            wall_x_hit = hit_y
        else:  # Horizontal hit
            wall_x_hit = hit_x

        wall_x_hit -= math.floor(wall_x_hit)

        return dist, wall_type, wall_x_hit, map_x, map_y

    def render_3d(
        self,
        screen: pygame.Surface,
        player: Player,
        bots: Sequence[Bot],
        level: int,
        view_offset_y: float = 0.0,
        projectiles: Sequence[Projectile] | None = None,
        particles: Sequence[WorldParticle] | None = None,
        flash_intensity: float = 0.0,
    ) -> None:
        """Render 3D view using vectorized raycasting."""
        self.update_cache()
        self._update_map_cache_if_needed()

        # Determine current FOV
        current_fov = self.config.FOV * (
            self.config.ZOOM_FOV_MULT if player.zoomed else 1.0
        )

        # Clear view surface
        self.view_surface.fill((0, 0, 0, 0))

        # Vectorized Raycasting
        (
            perp_wall_dist,
            wall_types,
            wall_x_hit,
            side,
            fisheye_factors,
        ) = self._calculate_rays(player)

        # Update Z Buffer
        self.z_buffer = perp_wall_dist

        # Render Walls
        self._render_walls_vectorized(
            perp_wall_dist,
            wall_types,
            wall_x_hit,
            side,
            player,
            fisheye_factors,
            level,
            view_offset_y,
            flash_intensity,
        )

        # Render Sprites
        projs = projectiles if projectiles is not None else []
        parts = particles if particles is not None else []
        self._render_sprites(
            player,
            bots,
            projs,
            parts,
            current_fov / 2,
            view_offset_y,
            flash_intensity,
        )

        # Blit to Screen
        self._blit_view_to_screen(screen)

    def _update_map_cache_if_needed(self) -> None:
        """Check if map changed and update cached grid."""
        if self.game_map.grid is not self.grid:
            self.grid = self.game_map.grid
            self.np_grid = np.array(self.game_map.grid, dtype=np.int8)

    def _calculate_rays(self, player: Player) -> tuple[
        np.ndarray[Any, np.dtype[Any]],
        np.ndarray[Any, np.dtype[Any]],
        np.ndarray[Any, np.dtype[Any]],
        np.ndarray[Any, np.dtype[Any]],
        np.ndarray[Any, np.dtype[Any]],
    ]:
        """Perform vectorized raycasting math."""
        # 1. Setup ray directions
        ray_dir_x, ray_dir_y = self._get_ray_directions(player)

        # 2. Setup DDA parameters
        (
            map_x,
            map_y,
            delta_dist_x,
            delta_dist_y,
            side_dist_x,
            side_dist_y,
            step_x,
            step_y,
        ) = self._init_dda_params(player, ray_dir_x, ray_dir_y)

        # 3. Perform DDA
        hits, wall_types, side = self._perform_dda_loop(
            map_x,
            map_y,
            side_dist_x,
            side_dist_y,
            delta_dist_x,
            delta_dist_y,
            step_x,
            step_y,
        )

        # 4. Calculate final distances and hit points
        return self._finalize_ray_data(
            player,
            hits,
            wall_types,
            side,
            side_dist_x,
            side_dist_y,
            delta_dist_x,
            delta_dist_y,
            ray_dir_x,
            ray_dir_y,
        )

    def _get_ray_directions(
        self, player: Player
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        """Calculate ray direction vectors (delegates to raycaster_math)."""
        return get_ray_directions(
            player,
            self.cos_deltas,
            self.sin_deltas,
            self.cos_deltas_zoomed,
            self.sin_deltas_zoomed,
        )

    def _init_dda_params(
        self,
        player: Player,
        ray_dir_x: np.ndarray[Any, Any],
        ray_dir_y: np.ndarray[Any, Any],
    ) -> tuple[Any, ...]:
        """Initialize DDA stepping parameters (delegates to raycaster_math)."""
        return init_dda_params(player, self.num_rays, ray_dir_x, ray_dir_y)

    def _perform_dda_loop(
        self,
        map_x: np.ndarray[Any, Any],
        map_y: np.ndarray[Any, Any],
        side_dist_x: np.ndarray[Any, Any],
        side_dist_y: np.ndarray[Any, Any],
        delta_dist_x: np.ndarray[Any, Any],
        delta_dist_y: np.ndarray[Any, Any],
        step_x: np.ndarray[Any, Any],
        step_y: np.ndarray[Any, Any],
    ) -> tuple[Any, ...]:
        """Perform the main DDA hit detection loop (delegates to raycaster_math)."""
        return perform_dda_loop(
            self.num_rays,
            self.map_width,
            self.map_height,
            self.np_grid,
            int(self.config.MAX_DEPTH * 1.5),
            map_x,
            map_y,
            side_dist_x,
            side_dist_y,
            delta_dist_x,
            delta_dist_y,
            step_x,
            step_y,
        )

    def _finalize_ray_data(
        self,
        player: Player,
        hits: np.ndarray[Any, Any],
        wall_types: np.ndarray[Any, Any],
        side: np.ndarray[Any, Any],
        side_dist_x: np.ndarray[Any, Any],
        side_dist_y: np.ndarray[Any, Any],
        delta_dist_x: np.ndarray[Any, Any],
        delta_dist_y: np.ndarray[Any, Any],
        ray_dir_x: np.ndarray[Any, Any],
        ray_dir_y: np.ndarray[Any, Any],
    ) -> tuple[Any, ...]:
        """Calculate final distances and wall-hit X coordinates.

        Delegates to raycaster_math.finalize_ray_data.
        """
        return finalize_ray_data(
            player,
            self.num_rays,
            hits,
            wall_types,
            side,
            side_dist_x,
            side_dist_y,
            delta_dist_x,
            delta_dist_y,
            ray_dir_x,
            ray_dir_y,
            self.cos_deltas,
            self.cos_deltas_zoomed,
        )

    def _blit_view_to_screen(self, screen: pygame.Surface) -> None:
        """Blit the rendered view to the main screen."""
        if self.render_scale == 1:
            screen.blit(self.view_surface, (0, 0))
        else:
            scaled_surface = pygame.transform.scale(
                self.view_surface, (self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT)
            )
            screen.blit(scaled_surface, (0, 0))

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

        # Pre-compute geometry and shading arrays
        (
            wall_heights_int_list,
            wall_tops_list,
            shades_list,
            fog_factors_list,
        ) = self._prepare_wall_render_data(
            distances, player, fisheye_factors, view_offset_y
        )

        use_textures = self.use_textures and len(self.textures) > 0

        # Pre-fetch texture strips
        wall_strips: dict[int, list[pygame.Surface]] = {}
        for wt in wall_colors.keys():
            tname = self.texture_map.get(wt, "brick")
            if tname in self.texture_strips:
                wall_strips[wt] = self.texture_strips[tname]

        view_surface = self.view_surface
        blits_sequence: list[
            tuple[pygame.Surface, tuple[int, int]]
            | tuple[pygame.Surface, tuple[int, int], tuple[int, int, int, int]]
        ] = []

        # Optimization: Convert numpy arrays to Python lists for faster per-element
        # access in the per-ray loop below.  Python list __getitem__ with an int
        # index is ~5-10x faster than numpy scalar indexing (arr[i]) because numpy
        # must box the result into a Python scalar on every access.  Since the loop
        # is pure-Python ``for i in range(num_rays)`` with individual element reads,
        # pre-converting via .tolist() is the optimal approach.  (See issue #477.)
        distances_list = distances.tolist()
        wall_types_list = wall_types.tolist()
        wall_x_hits_list = wall_x_hits.tolist()

        # Per-ray loop
        for i in range(self.num_rays):
            dist = distances_list[i]
            if dist >= self.config.MAX_DEPTH:
                continue

            wt = wall_types_list[i]
            if wt == 0:
                continue

            h = wall_heights_int_list[i]
            top = wall_tops_list[i]

            if use_textures and wt in wall_strips:
                self._render_textured_wall(
                    i,
                    wt,
                    h,
                    top,
                    wall_x_hits_list[i],
                    shades_list[i],
                    fog_factors_list[i],
                    wall_strips,
                    wall_colors,
                    view_surface,
                    blits_sequence,
                )
            else:
                self._render_solid_wall(
                    i,
                    wt,
                    h,
                    top,
                    shades_list[i],
                    fog_factors_list[i],
                    wall_colors,
                    view_surface,
                )

        # Perform batched blits
        if blits_sequence:
            view_surface.blits(blits_sequence, doreturn=False)

    def _resolve_wall_theme(self, level: int) -> dict[int, tuple[int, int, int]]:
        """Resolve wall colour theme for the current level."""
        if self._cached_level == level:
            return self._cached_wall_colors  # type: ignore[return-value]

        level_themes = self.config.LEVEL_THEMES or []
        theme_idx = (level - 1) % len(level_themes) if level_themes else 0
        theme = level_themes[theme_idx] if level_themes else None
        wall_colors: dict[int, tuple[int, int, int]] = (
            theme.get("walls", {}) if theme else {}
        )
        self._cached_level = level
        self._cached_wall_colors = wall_colors
        return wall_colors

    def _prepare_wall_render_data(
        self,
        distances: np.ndarray[Any, Any],
        player: Player,
        fisheye_factors: np.ndarray[Any, Any],
        view_offset_y: float,
    ) -> tuple[list[int], list[int], list[float], list[float]]:
        """Compute wall heights, tops, shading and fog from distances.

        Returns:
            (wall_heights_int_list, wall_tops_list, shades_list, fog_factors_list)
        """
        return prepare_wall_render_data(
            distances,
            fisheye_factors,
            self.config.SCREEN_HEIGHT,
            self.config.MAX_DEPTH,
            self.config.FOG_START,
            float(player.pitch),
            view_offset_y,
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

    def _render_sprites(
        self,
        player: Player,
        bots: Sequence[Bot],
        projectiles: Sequence[Projectile],
        particles: Sequence[WorldParticle],
        half_fov: float,
        view_offset_y: float = 0.0,
        flash_intensity: float = 0.0,
    ) -> None:
        """Render all sprites (bots, projectiles, particles) to the view surface.

        Delegates to raycaster_sprites module for the actual rendering logic.
        """
        _render_sprites_fn(
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

    def _generate_background_surface(self, level: int) -> None:
        """Pre-generate a high quality background surface for the level theme."""
        (
            self._background_surface,
            self._scaled_background_surface,
            self._cached_background_theme_idx,
        ) = _generate_background_surface_fn(
            level,
            self.config.LEVEL_THEMES or [],
            self.config.SCREEN_WIDTH,
            self.config.SCREEN_HEIGHT,
            self.config.GRAY,
            self.config.DARK_GRAY,
        )

    def render_floor_ceiling(
        self,
        screen: pygame.Surface,
        player: Player,
        level: int,
        view_offset_y: float = 0.0,
    ) -> None:
        """Render floor and sky with stars."""
        (
            self._background_surface,
            self._scaled_background_surface,
            self._cached_background_theme_idx,
        ) = _render_floor_ceiling_fn(
            screen,
            player,
            level,
            self.config.LEVEL_THEMES or [],
            self.config.SCREEN_WIDTH,
            self.config.SCREEN_HEIGHT,
            self.stars,
            self._cached_background_theme_idx,
            self._background_surface,
            self._scaled_background_surface,
            self.config.GRAY,
            self.config.DARK_GRAY,
            view_offset_y,
        )

    def _generate_minimap_cache(self) -> None:
        """Generate static minimap surface."""
        self.minimap_surface = generate_minimap_cache(
            self.minimap_size,
            self.minimap_scale,
            self.grid,
            self.map_width,
            self.map_height,
            self.config.WALL_COLORS or {},
            self.config.DARK_GRAY,
            self.config.GRAY,
        )

    def render_minimap(
        self,
        screen: pygame.Surface,
        player: Player,
        bots: Sequence[Bot],
        visited_cells: set[tuple[int, int]] | None = None,
        portal: Portal | None = None,
    ) -> None:
        """Render 2D minimap with fog of war support."""
        if self.minimap_surface is None:
            self._generate_minimap_cache()

        minimap_x = self.config.SCREEN_WIDTH - self.minimap_size - 20
        minimap_y = 20

        self._fog_surface, self._fog_visited_count = _render_minimap_fn(
            screen,
            player,
            bots,
            self.minimap_surface,
            self.minimap_size,
            self.minimap_scale,
            minimap_x,
            minimap_y,
            self._fog_surface,
            self._fog_visited_count,
            visited_cells,
            portal,
            self.config.ENEMY_TYPES,
            self.config.BLACK,
            self.config.RED,
            self.config.GREEN,
            self.config.CYAN,
        )
