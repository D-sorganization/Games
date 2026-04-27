"""Raycasting engine for 3D rendering.

Wall-column rendering dispatch helpers live in raycaster_wall_dispatch.py
(_RaycasterWallDispatch mixin, issue #775).
"""

from __future__ import annotations

import math
import random
from collections import OrderedDict
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import numpy as np
import pygame

from .contracts import validate_positive
from .raycaster_environment import (
    generate_background_surface as _generate_background_surface_fn,
)
from .raycaster_environment import (
    generate_minimap_cache,
)
from .raycaster_environment import (
    render_floor_ceiling as _render_floor_ceiling_fn,
)
from .raycaster_environment import (
    render_minimap as _render_minimap_fn,
)
from .raycaster_math import (
    finalize_ray_data,
    get_ray_directions,
    init_dda_params,
    perform_dda_loop,
)
from .raycaster_render_contexts import (
    MinimapRenderContext,
)
from .raycaster_textures import TextureManager
from .raycaster_wall_dispatch import (
    _PerRayLists,  # noqa: F401  re-exported for tests that import it from here
    _RaycasterWallDispatch,
)
from .texture_generator import (
    TextureGenerator,  # noqa: F401  (re-exported for test patching)
)
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


# Type alias for the 5-array tuple returned by _calculate_rays.
# Placed after imports to avoid E402; uses string literals since numpy
# is available at runtime but the alias is only used for annotations.
_RayArrays = tuple[
    np.ndarray[Any, np.dtype[Any]],
    np.ndarray[Any, np.dtype[Any]],
    np.ndarray[Any, np.dtype[Any]],
    np.ndarray[Any, np.dtype[Any]],
    np.ndarray[Any, np.dtype[Any]],
]


class Raycaster(_RaycasterWallDispatch):
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
        """Initialize texture management via TextureManager (see raycaster_textures)."""
        self._texture_mgr = TextureManager(
            strip_cache_max=512,
            strip_cache_evict=64,
        )
        # Expose frequently-accessed attributes at the Raycaster level for
        # backward compatibility with callers that read these directly.
        self.use_textures: bool = self._texture_mgr.use_textures
        self.textures = self._texture_mgr.textures
        self.texture_map = self._texture_mgr.texture_map
        self.texture_strips = self._texture_mgr.texture_strips

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

        Delegates strip-cache eviction to :class:`TextureManager` and handles
        sprite caches locally (they remain in the Raycaster for now).

        Caches use OrderedDict with LRU eviction: on hit, entries are
        moved to the end via ``move_to_end``; on eviction, the *least*
        recently used entries are popped from the front.

        Hard limits are intentionally conservative to bound peak VRAM.
        See issue #583.
        """
        self._texture_mgr.evict_cache()
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
        """Get or create a scaled texture strip (delegates to TextureManager)."""
        return self._texture_mgr.get_cached_strip(texture_name, strip_x, height)

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

    def _render_walls_and_sprites(
        self,
        player: Player,
        bots: Sequence[Bot],
        level: int,
        view_offset_y: float,
        projectiles: Sequence[Projectile],
        particles: Sequence[WorldParticle],
        flash_intensity: float,
        current_fov: float,
    ) -> None:
        """Raycast walls and render sprites to the view surface."""
        rays = self._calculate_rays(player)
        perp_wall_dist, wall_types, wall_x_hit, side, fisheye_factors = rays
        self.z_buffer = perp_wall_dist
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
        self._render_sprites(
            player,
            bots,
            projectiles,
            particles,
            current_fov / 2,
            view_offset_y,
            flash_intensity,
        )

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
        current_fov = self.config.FOV * (
            self.config.ZOOM_FOV_MULT if player.zoomed else 1.0
        )
        self.view_surface.fill((0, 0, 0, 0))
        self._render_walls_and_sprites(
            player,
            bots,
            level,
            view_offset_y,
            projectiles if projectiles is not None else [],
            particles if particles is not None else [],
            flash_intensity,
            current_fov,
        )
        self._blit_view_to_screen(screen)

    def _update_map_cache_if_needed(self) -> None:
        """Check if map changed and update cached grid."""
        if self.game_map.grid is not self.grid:
            self.grid = self.game_map.grid
            self.np_grid = np.array(self.game_map.grid, dtype=np.int8)

    def _run_dda(
        self,
        player: Player,
        ray_dir_x: np.ndarray[Any, Any],
        ray_dir_y: np.ndarray[Any, Any],
    ) -> tuple[Any, Any, Any, Any, Any, Any, Any, Any, Any, Any]:
        """Run DDA setup + loop.

        Returns (hits, wall_types, side, side_dists, deltas, steps).
        """
        map_x, map_y, ddx, ddy, sdx, sdy, sx, sy = self._init_dda_params(
            player, ray_dir_x, ray_dir_y
        )
        hits, wall_types, side = self._perform_dda_loop(
            map_x, map_y, sdx, sdy, ddx, ddy, sx, sy
        )
        return hits, wall_types, side, sdx, sdy, ddx, ddy, ray_dir_x, ray_dir_y, map_x

    def _calculate_rays(self, player: Player) -> _RayArrays:
        """Perform vectorized raycasting math."""
        ray_dir_x, ray_dir_y = self._get_ray_directions(player)
        hits, wall_types, side, sdx, sdy, ddx, ddy, rdx, rdy, _mx = self._run_dda(
            player, ray_dir_x, ray_dir_y
        )
        return self._finalize_ray_data(
            player, hits, wall_types, side, sdx, sdy, ddx, ddy, rdx, rdy
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
        sdx: np.ndarray[Any, Any],
        sdy: np.ndarray[Any, Any],
        ddx: np.ndarray[Any, Any],
        ddy: np.ndarray[Any, Any],
        rdx: np.ndarray[Any, Any],
        rdy: np.ndarray[Any, Any],
    ) -> tuple[Any, ...]:
        """Calculate final distances and wall-hit X; delegates to raycaster_math."""
        return finalize_ray_data(
            player,
            self.num_rays,
            hits,
            wall_types,
            side,
            sdx,
            sdy,
            ddx,
            ddy,
            rdx,
            rdy,
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

    # Wall-column dispatch and sprite context methods are inherited from
    # _RaycasterWallDispatch (see raycaster_wall_dispatch.py).

    def _generate_background_surface(self, level: int) -> None:
        """Pre-generate a high quality background surface for the level theme."""
        (
            self._background_surface,
            self._scaled_background_surface,
            self._cached_background_theme_idx,
        ) = _generate_background_surface_fn(
            level,
            self.config.LEVEL_THEMES or [],  # type: ignore[arg-type]
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
            self.config.LEVEL_THEMES or [],  # type: ignore[arg-type]
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

    def _build_minimap_context(
        self,
        screen: pygame.Surface,
        player: Player,
        bots: Sequence[Bot],
        minimap_x: int,
        minimap_y: int,
        visited_cells: set[tuple[int, int]] | None,
        portal: Portal | None,
    ) -> MinimapRenderContext:
        """Construct a MinimapRenderContext from current renderer state."""
        assert self.minimap_surface is not None, "call _generate_minimap_cache first"
        return MinimapRenderContext(
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
        ctx = self._build_minimap_context(
            screen, player, bots, minimap_x, 20, visited_cells, portal
        )
        self._fog_surface, self._fog_visited_count = _render_minimap_fn(ctx)
