from __future__ import annotations

import itertools
import math
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import pygame

from .bot_renderer import BotRenderer
from .texture_generator import TextureGenerator
from .utils import cast_ray_dda

if TYPE_CHECKING:
    from .config import RaycasterConfig
    from .interfaces import Bot, EnemyData, Map, Player, Projectile


class Raycaster:
    """Raycasting engine for 3D rendering"""

    VISUAL_SCALE = 2.2
    STRIP_VISIBILITY_THRESHOLD = 0.3
    LARGE_SPRITE_THRESHOLD = 200

    def __init__(self, game_map: Map, config: RaycasterConfig):
        """Initialize raycaster"""
        self.game_map = game_map
        self.config = config

        # Create numpy grid for faster access in vectorized calculations
        self.grid = game_map.grid
        self.np_grid = np.array(game_map.grid, dtype=np.int8)
        self.map_size = game_map.size
        self.map_width = game_map.width
        self.map_height = game_map.height

        # Cache for theme
        self._cached_level: int = -1
        self._cached_wall_colors: dict[int, tuple[int, int, int]] = {}

        # Pre-rendered background surface (Sky/Floor)
        self._background_surface: pygame.Surface | None = None
        self._scaled_background_surface: pygame.Surface | None = None
        self._cached_background_theme_idx: int = -1

        # Texture mapping
        self.use_textures = True
        self.textures = TextureGenerator.generate_textures()

        # Map wall types to texture names
        self.texture_map = {1: "stone", 2: "brick", 3: "metal", 4: "tech", 5: "secret"}

        # Pre-cache texture strips for performance
        self.texture_strips: dict[str, list[pygame.Surface]] = {}
        for name, tex in self.textures.items():
            w = tex.get_width()
            h = tex.get_height()
            strips = []
            for x in range(w):
                strips.append(tex.subsurface((x, 0, 1, h)))
            self.texture_strips[name] = strips

        # Initialize strip cache
        self._strip_cache: dict[tuple[str, int, int], pygame.Surface] = {}

        # Pre-generate stars
        self.stars = []

        for _ in range(100):
            self.stars.append(
                (
                    random.randint(0, self.config.SCREEN_WIDTH),
                    random.randint(0, self.config.SCREEN_HEIGHT // 2),
                    random.uniform(0.5, 2.5),  # Size
                    random.choice([(255, 255, 255), (200, 200, 255), (255, 255, 200)]),
                )
            )

        # Sprite cache
        self.sprite_cache: dict[str, pygame.Surface] = {}
        # Scaled Sprite cache (key: (base_cache_key, width, height))
        self._scaled_sprite_cache: dict[tuple[str, int, int], pygame.Surface] = {}

        # Minimap cache
        self.minimap_surface: pygame.Surface | None = None
        self.minimap_size = 200
        self.minimap_scale = self.minimap_size / self.map_size

        # Resolution settings
        self.render_scale = self.config.DEFAULT_RENDER_SCALE
        self.num_rays = self.config.SCREEN_WIDTH // self.render_scale

        # Offscreen surface for low-res rendering (Optimization)
        size = (self.num_rays, self.config.SCREEN_HEIGHT)
        self.view_surface = pygame.Surface(size, pygame.SRCALPHA)

        # Optimization: Caches for shading/fog overlays
        self.shading_surfaces: list[pygame.Surface] = []
        self.fog_surfaces: list[pygame.Surface] = []
        self._generate_shading_caches()

        # Z-Buffer for occlusion (Euclidean distance)
        self.z_buffer: np.ndarray[Any, np.dtype[Any]] = np.full(
            self.num_rays, float("inf"), dtype=np.float64
        )

        # Precalculate ray angles relative to player angle
        self._update_ray_angles()

    def _generate_shading_caches(self) -> None:
        """Pre-generate 1-pixel wide surfaces for shading and fog alpha levels."""
        # Height must cover max possible wall height
        cache_height = self.config.SCREEN_HEIGHT * 2
        self.shading_surfaces = []
        self.fog_surfaces = []

        # Generate shading surfaces (Black with varying alpha)
        for alpha in range(256):
            s = pygame.Surface((1, cache_height), pygame.SRCALPHA)
            s.fill((0, 0, 0, alpha))
            self.shading_surfaces.append(s)

        # Generate fog surfaces (Fog Color with varying alpha)
        # Assuming FOG_COLOR is constant during runtime
        fog_col = self.config.FOG_COLOR
        for alpha in range(256):
            s = pygame.Surface((1, cache_height), pygame.SRCALPHA)
            s.fill((*fog_col, alpha))
            self.fog_surfaces.append(s)

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
        self.render_scale = scale
        self.num_rays = self.config.SCREEN_WIDTH // scale

        # Recreate buffers
        self.view_surface = pygame.Surface(
            (self.num_rays, self.config.SCREEN_HEIGHT), pygame.SRCALPHA
        )
        self.z_buffer = np.full(self.num_rays, float("inf"), dtype=np.float64)
        self._update_ray_angles()

    def update_cache(self) -> None:
        """Perform cache maintenance once per frame."""
        # Limit cache size to prevent memory issues
        if len(self._strip_cache) > 10000:
            # Remove oldest entries
            keys_to_remove = list(itertools.islice(self._strip_cache, 1000))
            for key in keys_to_remove:
                del self._strip_cache[key]

        if len(self.sprite_cache) > 400:
            sprite_keys_to_remove = list(itertools.islice(self.sprite_cache, 40))
            for k in sprite_keys_to_remove:
                del self.sprite_cache[k]

        if len(self._scaled_sprite_cache) > 200:
            scaled_keys_to_remove = list(
                itertools.islice(self._scaled_sprite_cache, 20)
            )
            for scaled_k in scaled_keys_to_remove:
                del self._scaled_sprite_cache[scaled_k]

    def _get_cached_strip(
        self, texture_name: str, strip_x: int, height: int
    ) -> pygame.Surface | None:
        """Get or create a scaled texture strip."""
        cache_key = (texture_name, strip_x, height)

        if cache_key in self._strip_cache:
            return self._strip_cache[cache_key]

        strips = self.texture_strips.get(texture_name)
        if not strips:
            return None
        try:
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
        )

        # Render Sprites
        projs = projectiles if projectiles is not None else []
        self._render_sprites(player, bots, projs, current_fov / 2, view_offset_y)

        # Blit to Screen
        self._blit_view_to_screen(screen)

    def _update_map_cache_if_needed(self) -> None:
        """Check if map changed and update cached grid."""
        if self.game_map.grid is not self.grid:
            self.grid = self.game_map.grid
            self.np_grid = np.array(self.game_map.grid, dtype=np.int8)
        elif self.game_map.grid != self.grid:
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
        # Select pre-calculated tables
        if player.zoomed:
            cos_deltas = self.cos_deltas_zoomed
            sin_deltas = self.sin_deltas_zoomed
        else:
            cos_deltas = self.cos_deltas
            sin_deltas = self.sin_deltas

        # Angle sum identity optimization:
        # cos(a + b) = cos(a)cos(b) - sin(a)sin(b)
        # sin(a + b) = sin(a)cos(b) + cos(a)sin(b)
        p_cos = math.cos(player.angle)
        p_sin = math.sin(player.angle)

        ray_dir_x = p_cos * cos_deltas - p_sin * sin_deltas
        ray_dir_y = p_sin * cos_deltas + p_cos * sin_deltas

        # Avoid division by zero
        ray_dir_x[ray_dir_x == 0] = 1e-30
        ray_dir_y[ray_dir_y == 0] = 1e-30

        map_x = np.full(self.num_rays, int(player.x), dtype=np.int32)
        map_y = np.full(self.num_rays, int(player.y), dtype=np.int32)

        delta_dist_x = np.abs(1.0 / ray_dir_x)
        delta_dist_y = np.abs(1.0 / ray_dir_y)

        step_x = np.where(ray_dir_x < 0, -1, 1).astype(np.int32)
        step_y = np.where(ray_dir_y < 0, -1, 1).astype(np.int32)

        side_dist_x = np.where(
            ray_dir_x < 0,
            (player.x - map_x) * delta_dist_x,
            (map_x + 1.0 - player.x) * delta_dist_x,
        )
        side_dist_y = np.where(
            ray_dir_y < 0,
            (player.y - map_y) * delta_dist_y,
            (map_y + 1.0 - player.y) * delta_dist_y,
        )

        hits = np.zeros(self.num_rays, dtype=bool)
        side = np.zeros(self.num_rays, dtype=np.int32)
        wall_types = np.zeros(self.num_rays, dtype=np.int32)

        max_steps = int(self.config.MAX_DEPTH * 1.5)
        active = np.ones(self.num_rays, dtype=bool)

        map_width = self.map_width
        map_height = self.map_height
        np_grid = self.np_grid

        # Vectorized DDA Loop
        for _ in range(max_steps):
            mask_x = (side_dist_x < side_dist_y) & active
            mask_y = (~mask_x) & active

            side_dist_x[mask_x] += delta_dist_x[mask_x]
            map_x[mask_x] += step_x[mask_x]
            side[mask_x] = 0

            side_dist_y[mask_y] += delta_dist_y[mask_y]
            map_y[mask_y] += step_y[mask_y]
            side[mask_y] = 1

            in_bounds = (
                (map_x >= 0) & (map_x < map_width) & (map_y >= 0) & (map_y < map_height)
            )

            out_of_bounds = (~in_bounds) & active
            if np.any(out_of_bounds):
                hits[out_of_bounds] = True
                wall_types[out_of_bounds] = 1
                active[out_of_bounds] = False

            check_mask = in_bounds & active
            if np.any(check_mask):
                current_map_y = map_y[check_mask]
                current_map_x = map_x[check_mask]
                grid_vals = np_grid[current_map_y, current_map_x]
                wall_hit_mask = grid_vals > 0

                active_indices = np.nonzero(check_mask)[0]
                hit_local_indices = np.nonzero(wall_hit_mask)[0]
                hit_global_indices = active_indices[hit_local_indices]

                if len(hit_global_indices) > 0:
                    hits[hit_global_indices] = True
                    wall_types[hit_global_indices] = grid_vals[wall_hit_mask]
                    active[hit_global_indices] = False

            if not np.any(active):
                break

        # Calculate Distances
        perp_wall_dist = np.zeros(self.num_rays, dtype=np.float64)
        mask_side_0 = side == 0
        perp_wall_dist[mask_side_0] = (
            side_dist_x[mask_side_0] - delta_dist_x[mask_side_0]
        )
        mask_side_1 = side == 1
        perp_wall_dist[mask_side_1] = (
            side_dist_y[mask_side_1] - delta_dist_y[mask_side_1]
        )

        # Wall X Hit
        wall_x_hit = np.zeros(self.num_rays, dtype=np.float64)
        wall_x_hit[mask_side_0] = (
            player.y + perp_wall_dist[mask_side_0] * ray_dir_y[mask_side_0]
        )
        wall_x_hit[mask_side_1] = (
            player.x + perp_wall_dist[mask_side_1] * ray_dir_x[mask_side_1]
        )
        wall_x_hit -= np.floor(wall_x_hit)

        # Return cos_deltas instead of ray_angles for fisheye correction
        return perp_wall_dist, wall_types, wall_x_hit, side, cos_deltas

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
    ) -> None:
        """Render walls using computed arrays."""
        # Theme Setup
        if hasattr(self, "_cached_level") and self._cached_level == level:
            wall_colors = self._cached_wall_colors
        else:
            # 0. Setup themes
            level_themes = self.config.LEVEL_THEMES or []
            theme_idx = (level - 1) % len(level_themes) if level_themes else 0
            theme = level_themes[theme_idx] if level_themes else None
            wall_colors = (
                theme["walls"] if theme else {}
            )  # Ensure wall_colors is a dict
            self._cached_level = level
            self._cached_wall_colors = wall_colors

        # Fisheye correction
        # corrected_dists = distances * np.cos(player.angle - ray_angles)
        # fisheye_factors already contains cos(deltas) which equals
        # cos(player.angle - ray_angles)
        corrected_dists = distances * fisheye_factors
        safe_dists = np.maximum(0.01, corrected_dists)

        # Calculate heights
        wall_heights = np.minimum(
            self.config.SCREEN_HEIGHT * 4, (self.config.SCREEN_HEIGHT / safe_dists)
        )
        wall_tops = (
            (self.config.SCREEN_HEIGHT - wall_heights) // 2
            + player.pitch
            + view_offset_y
        ).astype(np.int32)
        wall_heights_int = wall_heights.astype(np.int32)

        # Shading
        shades = np.maximum(0.2, 1.0 - distances / 50.0)

        # Fog
        fog_factors = np.clip(
            (distances - self.config.MAX_DEPTH * self.config.FOG_START)
            / (self.config.MAX_DEPTH * (1 - self.config.FOG_START)),
            0.0,
            1.0,
        )

        use_textures = self.use_textures and len(self.textures) > 0

        # Pre-fetch texture strips
        # Map integer wall types to texture strip lists
        wall_strips = {}
        for wt in wall_colors.keys():
            tname = self.texture_map.get(wt, "brick")
            if tname in self.texture_strips:
                wall_strips[wt] = self.texture_strips[tname]

        view_surface = self.view_surface
        shading_surfaces = self.shading_surfaces
        fog_surfaces = self.fog_surfaces

        # Batched Blit List
        # Batched Blit List
        blits_sequence: list[
            tuple[pygame.Surface, tuple[int, int]]
            | tuple[pygame.Surface, tuple[int, int], tuple[int, int, int, int]]
        ] = []

        # Optimization: Convert numpy arrays to lists for faster iteration
        # Accessing numpy elements in a loop is significantly slower than list access
        distances_list = distances.tolist()
        wall_types_list = wall_types.tolist()
        wall_x_hits_list = wall_x_hits.tolist()
        wall_heights_int_list = wall_heights_int.tolist()
        wall_tops_list = wall_tops.tolist()
        shades_list = shades.tolist()
        fog_factors_list = fog_factors.tolist()

        # Loop
        for i in range(self.num_rays):
            dist = distances_list[i]
            if dist >= self.config.MAX_DEPTH:
                continue

            wt = wall_types_list[i]
            if wt == 0:
                continue

            h = wall_heights_int_list[i]
            top = wall_tops_list[i]

            # Texture rendering
            if use_textures and wt in wall_strips:
                strips = wall_strips[wt]
                tex_w = len(strips)

                # Calculate texture X
                tex_x = int(wall_x_hits_list[i] * tex_w)
                tex_x = int(np.clip(tex_x, 0, tex_w - 1))

                # Only render if height is reasonable
                if h < 8000:
                    tname = self.texture_map.get(wt, "brick")
                    # Ensure height is int for cache hit
                    scaled_strip = self._get_cached_strip(tname, tex_x, int(h))

                    if scaled_strip:
                        blits_sequence.append((scaled_strip, (i, top)))

                        # Shading (Darken)
                        shade = shades_list[i]
                        if shade < 1.0:
                            alpha = int(255 * (1.0 - shade))
                            if alpha > 0:
                                try:
                                    blits_sequence.append(
                                        (
                                            shading_surfaces[alpha],
                                            (i, top),
                                            (0, 0, 1, h),
                                        )
                                    )
                                except IndexError:
                                    pass

                        # Fog
                        fog = fog_factors_list[i]
                        if fog > 0:
                            fog_alpha = int(255 * fog)
                            if fog_alpha > 0:
                                try:
                                    blits_sequence.append(
                                        (
                                            fog_surfaces[fog_alpha],
                                            (i, top),
                                            (0, 0, 1, h),
                                        )
                                    )
                                except IndexError:
                                    pass
                    else:
                        # Fallback if cache failed
                        col = wall_colors.get(wt, self.config.GRAY)
                        pygame.draw.rect(view_surface, col, (i, top, 1, h))
                else:
                    # Solid color fallback for massive closeness
                    col = wall_colors.get(wt, self.config.GRAY)
                    shade = shades_list[i]
                    col = (
                        int(col[0] * shade),
                        int(col[1] * shade),
                        int(col[2] * shade),
                    )
                    pygame.draw.rect(view_surface, col, (i, top, 1, h))
            else:
                # Solid Color Fallback
                col = wall_colors.get(wt, self.config.GRAY)
                shade = shades_list[i]
                fog = fog_factors_list[i]

                # Mix color
                r = col[0] * shade
                g = col[1] * shade
                b = col[2] * shade

                fr = r * (1 - fog) + self.config.FOG_COLOR[0] * fog
                fg = g * (1 - fog) + self.config.FOG_COLOR[1] * fog
                fb = b * (1 - fog) + self.config.FOG_COLOR[2] * fog

                final_col = (int(fr), int(fg), int(fb))

                pygame.draw.rect(view_surface, final_col, (i, top, 1, h))

        # Perform batched blits
        if blits_sequence:
            view_surface.blits(blits_sequence, doreturn=False)

    def _render_sprites(
        self,
        player: Player,
        bots: Sequence[Bot],
        projectiles: Sequence[Projectile],
        half_fov: float,
        view_offset_y: float = 0.0,
    ) -> None:
        """Render all sprites (bots and projectiles) to the view surface"""
        sprites_to_render: list[tuple[Any, bool]] = []

        # Optimization: Pre-calculate player direction vector
        p_cos = math.cos(player.angle)
        p_sin = math.sin(player.angle)
        max_dist_sq = self.config.MAX_DEPTH * self.config.MAX_DEPTH

        # Merge bots and projectiles
        for bot in bots:
            if bot.removed:
                continue
            sprites_to_render.append((bot, False))

        for proj in projectiles:
            if not proj.alive:
                continue
            sprites_to_render.append((proj, True))

        final_sprites = []

        for entity, is_projectile in sprites_to_render:
            dx = entity.x - player.x
            dy = entity.y - player.y

            # Distance culling
            dist_sq = dx * dx + dy * dy
            if dist_sq > max_dist_sq:
                continue

            # Dot product check
            if dx * p_cos + dy * p_sin < 0:
                continue

            dist = math.sqrt(dist_sq)
            angle = math.atan2(dy, dx)
            angle_to_sprite = angle - player.angle

            while angle_to_sprite > math.pi:
                angle_to_sprite -= 2 * math.pi
            while angle_to_sprite < -math.pi:
                angle_to_sprite += 2 * math.pi

            if abs(angle_to_sprite) < half_fov + 0.5:
                final_sprites.append((entity, dist, angle_to_sprite, is_projectile))

        # Sort by distance (far to near)
        final_sprites.sort(key=lambda x: x[1], reverse=True)

        for entity, dist, angle, is_proj in final_sprites:
            if is_proj:
                proj = cast("Projectile", entity)
                self._draw_single_projectile(
                    player, proj, dist, angle, half_fov, view_offset_y
                )
            else:
                bot = cast("Bot", entity)
                self._draw_single_sprite(
                    player, bot, dist, angle, half_fov, view_offset_y
                )

    def _draw_single_sprite(
        self,
        player: Player,
        bot: Bot,
        dist: float,
        angle: float,
        half_fov: float,
        view_offset_y: float = 0.0,
    ) -> None:
        """Draw a single sprite to the view surface.

        Calculates sprite position, scaling, and occlusion, then blits z-buffered
        vertical strips to the offscreen view surface.
        """
        safe_dist = max(0.01, dist)
        base_sprite_size = self.config.SCREEN_HEIGHT / safe_dist

        type_data: EnemyData = bot.type_data
        sprite_size = base_sprite_size * float(type_data.get("scale", 1.0))

        center_ray = self.num_rays / 2
        sprite_scale = sprite_size / self.render_scale
        ray_x = center_ray + (angle / half_fov) * center_ray - sprite_scale / 2

        sprite_ray_width = sprite_size / self.render_scale
        sprite_ray_x = ray_x

        sprite_y = (
            self.config.SCREEN_HEIGHT / 2
            - sprite_size / 2
            + player.pitch
            + view_offset_y
        )

        visual_scale = self.VISUAL_SCALE

        if sprite_ray_x + sprite_ray_width < 0:
            return
        if sprite_ray_x >= self.num_rays:
            return

        cache_display_size = min(sprite_size, 800)
        cached_size = int(round(cache_display_size / 10.0) * 10.0)
        cached_size = max(cached_size, 10)

        # Calculate shade level (0-20)
        distance_shade = max(0.2, 1.0 - dist / 50.0)  # Match wall shading intensity
        shade_level = int(distance_shade * 20)

        cache_key = (
            f"{bot.enemy_type}_{bot.type_data.get('visual_style')}_"
            f"{int(bot.walk_animation * 5)}_{int(bot.shoot_animation * 5)}_"
            f"{bot.dead}_{int(bot.death_timer // 5)}_{cached_size}_{shade_level}"
        )

        if bot.frozen:
            cache_key += "_frozen"

        if cache_key in self.sprite_cache:
            sprite_surface = self.sprite_cache[cache_key]
        else:
            # Create base surface with visual padding
            # Size is visually scaled to allow glows/effects outside logical bounds
            surf_size = int(cached_size * visual_scale)
            padding = (surf_size - cached_size) // 2

            sprite_surface = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            BotRenderer.render_sprite(
                sprite_surface, bot, padding, padding, cached_size, self.config
            )

            # Apply shading cache
            shade_val = int(255 * distance_shade)
            shade_color = (shade_val, shade_val, shade_val)

            if shade_color != (255, 255, 255):
                sprite_surface.fill(shade_color, special_flags=pygame.BLEND_MULT)

            if bot.frozen:
                # Apply blue tint for frozen effect
                sprite_surface.fill((150, 200, 255), special_flags=pygame.BLEND_MULT)

            if len(self.sprite_cache) > 400:
                # Evict oldest efficiently
                keys_to_remove = list(itertools.islice(self.sprite_cache, 40))
                for k in keys_to_remove:
                    del self.sprite_cache[k]
            self.sprite_cache[cache_key] = sprite_surface

        start_r = int(max(0, sprite_ray_x))
        end_r = int(min(self.num_rays, sprite_ray_x + sprite_ray_width))

        if start_r >= end_r:
            return

        # Optimization: Pre-calculate target size
        target_width = int(sprite_ray_width)
        target_height = int(sprite_size)

        if target_width <= 0 or target_height <= 0:
            return

        # Collect visible runs first to decide on scaling strategy
        visible_runs = []
        r = start_r
        total_visible_pixels = 0

        # Local lookup for speed
        z_buffer = self.z_buffer

        while r < end_r:
            # Skip occluded rays
            if dist > z_buffer[r]:
                r += 1
                continue

            # Found start of visible run
            run_start = r
            r += 1
            while r < end_r and dist <= z_buffer[r]:
                r += 1

            visible_runs.append((run_start, r))
            total_visible_pixels += r - run_start

        if not visible_runs:
            return

        # Scale whole strategy (most common)
        scale_whole = True
        if (
            total_visible_pixels < target_width * self.STRIP_VISIBILITY_THRESHOLD
            and target_width > self.LARGE_SPRITE_THRESHOLD
        ):
            scale_whole = False

        if scale_whole:
            # Scale to visual size (includes padding)
            # Bucketing logic to reduce unique scale calls:
            # Snap to nearest 8 pixels for width
            bucket_step = 8
            raw_final_w = int(target_width * visual_scale)
            final_w = max(bucket_step, (raw_final_w // bucket_step) * bucket_step)

            # Maintain aspect ratio for height
            aspect_ratio = sprite_surface.get_height() / sprite_surface.get_width()
            final_h = int(final_w * aspect_ratio)

            scaled_cache_key = (cache_key, final_w, final_h)
            if scaled_cache_key in self._scaled_sprite_cache:
                scaled_sprite = self._scaled_sprite_cache[scaled_cache_key]
            else:
                try:
                    scaled_sprite = pygame.transform.scale(
                        sprite_surface, (final_w, final_h)
                    )

                    # Cache management
                    if len(self._scaled_sprite_cache) > 200:
                        # Evict oldest (simple dict iteration is insertion order)
                        # We remove a chunk to avoid frequent maintenance
                        scaled_keys_to_remove = list(
                            itertools.islice(self._scaled_sprite_cache, 20)
                        )
                        for scaled_k in scaled_keys_to_remove:
                            del self._scaled_sprite_cache[scaled_k]

                    self._scaled_sprite_cache[scaled_cache_key] = scaled_sprite
                except (ValueError, pygame.error):
                    return

            for run_start, run_end in visible_runs:
                # Calculate x offset in the scaled sprite
                x_offset = int(run_start - sprite_ray_x)
                width = run_end - run_start

                # Clamp
                if x_offset < 0:
                    width += x_offset
                    x_offset = 0

                if x_offset + width > target_width:
                    width = target_width - x_offset

                if width > 0:
                    padding_x = (final_w - target_width) // 2
                    src_x = int(padding_x + (run_start - sprite_ray_x))

                    area = pygame.Rect(src_x, 0, width, final_h)
                    logical_top_edge_y = (final_h - target_height) // 2
                    dst_y = int(sprite_y - logical_top_edge_y)

                    pos = (run_start, dst_y)
                    self.view_surface.blit(scaled_sprite, pos, area)
        else:
            # Fallback: Strip scaling
            for run_start, run_end in visible_runs:
                run_width = run_end - run_start

                tex_width = sprite_surface.get_width()
                tex_height = sprite_surface.get_height()

                logical_tex_width = tex_width / visual_scale
                tex_scale = logical_tex_width / sprite_ray_width

                tex_padding = (tex_width - logical_tex_width) / 2

                tex_x_start = int(tex_padding + (run_start - sprite_ray_x) * tex_scale)
                tex_x_end = int(tex_padding + (run_end - sprite_ray_x) * tex_scale)

                tex_x_start = max(0, min(tex_width, tex_x_start))
                tex_x_end = max(0, min(tex_width, tex_x_end))

                w = tex_x_end - tex_x_start
                if w <= 0:
                    continue

                area = pygame.Rect(tex_x_start, 0, w, tex_height)
                try:
                    slice_surf = sprite_surface.subsurface(area)
                    scaled_slice = pygame.transform.scale(
                        slice_surf, (run_width, target_height)
                    )
                    self.view_surface.blit(scaled_slice, (run_start, int(sprite_y)))
                except (ValueError, pygame.error):
                    continue

    def _draw_single_projectile(
        self,
        player: Player,
        proj: Projectile,
        dist: float,
        angle: float,
        half_fov: float,
        view_offset_y: float = 0.0,
    ) -> None:
        """Draw a projectile sprite."""
        safe_dist = max(0.01, dist)

        # Calculate screen position
        base_size = self.config.SCREEN_HEIGHT / safe_dist
        sprite_size = base_size * float(proj.size)

        center_ray = self.num_rays / 2
        sprite_scale = sprite_size / self.render_scale
        ray_x = center_ray + (angle / half_fov) * center_ray - sprite_scale / 2

        z_offset = (proj.z - 0.5) * (self.config.SCREEN_HEIGHT / safe_dist)
        sprite_y = (
            (self.config.SCREEN_HEIGHT / 2)
            - (sprite_size / 2)
            - z_offset
            + player.pitch
            + view_offset_y
        )

        if ray_x + sprite_scale < 0 or ray_x >= self.num_rays:
            return

        # Simple Center occlusion check
        center_ray_idx = int(ray_x + sprite_scale / 2)
        if 0 <= center_ray_idx < self.num_rays:
            if dist > self.z_buffer[center_ray_idx]:
                return  # Occluded

        # Draw
        try:
            rect = pygame.Rect(
                int(ray_x), int(sprite_y), int(sprite_scale), int(sprite_scale)
            )
            if rect.width > 0 and rect.height > 0:
                color = proj.color
                pygame.draw.circle(
                    self.view_surface, color, rect.center, rect.width // 2
                )

                if proj.weapon_type == "plasma":
                    pygame.draw.circle(
                        self.view_surface,
                        (255, 255, 255),
                        rect.center,
                        rect.width // 4,
                    )
                elif proj.weapon_type == "rocket":
                    pygame.draw.circle(
                        self.view_surface,
                        (255, 100, 0),
                        rect.center,
                        rect.width // 3,
                    )
                elif proj.weapon_type == "bfg":
                    pygame.draw.circle(
                        self.view_surface,
                        (200, 255, 200),
                        rect.center,
                        rect.width // 3,
                    )
                elif proj.weapon_type == "bomb":
                    pygame.draw.circle(
                        self.view_surface,
                        (255, 0, 0),
                        (rect.centerx, rect.top),
                        2,
                    )
                elif proj.weapon_type == "flamethrower":
                    # Dynamic flame effect
                    flame_color = (
                        255,
                        random.randint(100, 200),
                        0,
                    )
                    # Draw multiple circles for fluffy fire
                    pygame.draw.circle(
                        self.view_surface,
                        flame_color,
                        rect.center,
                        rect.width // 2,
                    )
                    pygame.draw.circle(
                        self.view_surface,
                        (255, 50, 0),
                        (rect.centerx, rect.centery),
                        rect.width // 3,
                    )
                elif proj.weapon_type == "pulse":
                    # Pulse Rifle projectile: Blue/White energy ball
                    pygame.draw.circle(
                        self.view_surface,
                        (200, 200, 255),
                        rect.center,
                        rect.width // 2,
                    )
                    pygame.draw.circle(
                        self.view_surface,
                        (100, 100, 255),
                        rect.center,
                        rect.width // 3,
                    )
                elif proj.weapon_type == "freezer":
                    # Freezer projectile: Cyan energy ball
                    pygame.draw.circle(
                        self.view_surface,
                        (200, 255, 255),
                        rect.center,
                        rect.width // 2,
                    )
                    pygame.draw.circle(
                        self.view_surface,
                        (150, 200, 255),
                        rect.center,
                        rect.width // 3,
                    )

        except (ValueError, pygame.error):
            pass

    def _generate_background_surface(self, level: int) -> None:
        """Pre-generate a high quality background surface for the level theme."""
        level_themes = self.config.LEVEL_THEMES or []
        theme_idx = (level - 1) % len(level_themes) if level_themes else 0
        theme = level_themes[theme_idx] if level_themes else None

        h = self.config.SCREEN_HEIGHT
        self._background_surface = pygame.Surface((1, h * 2))

        ceiling_color = theme["ceiling"] if theme else self.config.GRAY
        floor_color = theme["floor"] if theme else self.config.DARK_GRAY

        # Sky Gradient (Top half)
        # Top of surface is Zenith (darker?), Middle is Horizon (lighter/ceiling_color)
        top_sky = (
            max(0, ceiling_color[0] - 30),
            max(0, ceiling_color[1] - 30),
            max(0, ceiling_color[2] - 30),
        )
        bottom_sky = ceiling_color

        # Floor Gradient (Bottom half)
        near_floor = floor_color
        far_floor = (
            max(0, floor_color[0] - 40),
            max(0, floor_color[1] - 40),
            max(0, floor_color[2] - 40),
        )

        # Draw gradients
        for y in range(h):
            ratio = y / h
            r = top_sky[0] + (bottom_sky[0] - top_sky[0]) * ratio
            g = top_sky[1] + (bottom_sky[1] - top_sky[1]) * ratio
            b = top_sky[2] + (bottom_sky[2] - top_sky[2]) * ratio
            self._background_surface.set_at((0, y), (int(r), int(g), int(b)))

        for y in range(h):
            ratio = y / h
            r = far_floor[0] + (near_floor[0] - far_floor[0]) * ratio
            g = far_floor[1] + (near_floor[1] - far_floor[1]) * ratio
            b = far_floor[2] + (near_floor[2] - far_floor[2]) * ratio

            self._background_surface.set_at((0, h + y), (int(r), int(g), int(b)))

        # Cache scaled version
        # (Optimization: Do this once per level load, not per frame)
        self._scaled_background_surface = pygame.transform.scale(
            self._background_surface, (self.config.SCREEN_WIDTH, h * 2)
        )

        self._cached_background_theme_idx = theme_idx

    def render_floor_ceiling(
        self,
        screen: pygame.Surface,
        player: Player,
        level: int,
        view_offset_y: float = 0.0,
    ) -> None:
        """Render floor and sky with stars"""
        level_themes = self.config.LEVEL_THEMES or []
        theme_idx = (level - 1) % len(level_themes) if level_themes else 0
        theme = level_themes[theme_idx] if level_themes else None
        player_angle = player.angle

        if (
            self._cached_background_theme_idx != theme_idx
            or self._background_surface is None
        ):
            self._generate_background_surface(level)

        horizon = self.config.SCREEN_HEIGHT // 2 + int(player.pitch + view_offset_y)

        bg = self._scaled_background_surface
        # Fallback if scaling failed or wasn't generated
        if bg is None and self._background_surface is not None:
            self._scaled_background_surface = pygame.transform.scale(
                self._background_surface,
                (self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT * 2),
            )
            bg = self._scaled_background_surface

        assert bg is not None

        # Fill screen with appropriate sections
        # Sky
        if horizon > 0:
            # Optimized: Use pre-scaled surface
            # We want the top half (Sky)
            # Source area is entire top half: (0, 0, W, H)
            # Dest Y is horizon - H.
            screen.blit(
                bg,
                (0, horizon - self.config.SCREEN_HEIGHT),
                (0, 0, self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT),
            )

        # Floor
        if horizon < self.config.SCREEN_HEIGHT:
            # Optimized: Use pre-scaled surface
            # We want the bottom half (Floor)
            # Source area starts at Y=H
            screen.blit(
                bg,
                (0, horizon),
                (
                    0,
                    self.config.SCREEN_HEIGHT,
                    self.config.SCREEN_WIDTH,
                    self.config.SCREEN_HEIGHT,
                ),
            )

        # Stars
        star_offset = int(player_angle * 200) % self.config.SCREEN_WIDTH

        for sx, sy, size, color in self.stars:
            x = (sx + star_offset) % self.config.SCREEN_WIDTH
            y = int(sy + player.pitch + view_offset_y)

            if 0 <= y < horizon:
                pygame.draw.circle(screen, color, (x, int(y)), int(size))

        # Moon
        moon_x = (self.config.SCREEN_WIDTH - 200 - int(player_angle * 100)) % (
            self.config.SCREEN_WIDTH * 2
        ) - self.config.SCREEN_WIDTH // 2
        moon_y = 100 + int(player.pitch + view_offset_y)

        if -100 < moon_x < self.config.SCREEN_WIDTH + 100:
            if 0 <= moon_y < horizon + 40:
                pygame.draw.circle(screen, (220, 220, 200), (int(moon_x), moon_y), 40)
                shadow_pos = (int(moon_x) - 10, moon_y)
                moon_color = theme["ceiling"] if theme else self.config.GRAY
                pygame.draw.circle(screen, moon_color, shadow_pos, 40)

    def _generate_minimap_cache(self) -> None:
        """Generate static minimap surface."""
        self.minimap_surface = pygame.Surface((self.minimap_size, self.minimap_size))
        self.minimap_surface.fill(self.config.DARK_GRAY)

        wall_colors = self.config.WALL_COLORS or {}
        for y in range(self.map_height):
            for x in range(self.map_width):
                w_type = self.grid[y][x]
                if w_type > 0:
                    color = wall_colors.get(w_type, self.config.GRAY)
                    pygame.draw.rect(
                        self.minimap_surface,
                        color,
                        (
                            x * self.minimap_scale,
                            y * self.minimap_scale,
                            self.minimap_scale,
                            self.minimap_scale,
                        ),
                    )

    def render_minimap(
        self,
        screen: pygame.Surface,
        player: Player,
        bots: Sequence[Bot],
        visited_cells: set[tuple[int, int]] | None = None,
        portal: dict[str, Any] | None = None,
    ) -> None:
        """Render 2D minimap with fog of war support."""
        if self.minimap_surface is None:
            self._generate_minimap_cache()

        minimap_x = self.config.SCREEN_WIDTH - self.minimap_size - 20
        minimap_y = 20

        # Draw Border
        pygame.draw.rect(
            screen,
            self.config.BLACK,
            (
                minimap_x - 2,
                minimap_y - 2,
                self.minimap_size + 4,
                self.minimap_size + 4,
            ),
        )

        if self.minimap_surface:
            if visited_cells is not None:
                fog_surface = pygame.Surface(
                    (self.minimap_size, self.minimap_size), pygame.SRCALPHA
                )
                fog_surface.fill((0, 0, 0, 255))

                for vx, vy in visited_cells:
                    fog_surface.fill(
                        (0, 0, 0, 0),
                        rect=(
                            vx * self.minimap_scale,
                            vy * self.minimap_scale,
                            self.minimap_scale,
                            self.minimap_scale,
                        ),
                    )
                screen.blit(self.minimap_surface, (minimap_x, minimap_y))
                screen.blit(fog_surface, (minimap_x, minimap_y))
            else:
                screen.blit(self.minimap_surface, (minimap_x, minimap_y))

        if portal is not None:
            px, py = int(portal["x"]), int(portal["y"])
            if visited_cells is None or (px, py) in visited_cells:
                portal_map_x = minimap_x + px * self.minimap_scale
                portal_map_y = minimap_y + py * self.minimap_scale
                pygame.draw.circle(
                    screen,
                    self.config.CYAN,
                    (int(portal_map_x), int(portal_map_y)),
                    int(self.minimap_scale * 2),
                )

        for bot in bots:
            if (
                bot.alive
                and bot.enemy_type != "health_pack"
                and self.config.ENEMY_TYPES is not None
                and self.config.ENEMY_TYPES[bot.enemy_type].get("visual_style")
                != "item"
            ):
                bot_cell_x = int(bot.x)
                bot_cell_y = int(bot.y)
                if visited_cells is None or (bot_cell_x, bot_cell_y) in visited_cells:
                    bot_x = minimap_x + bot.x * self.minimap_scale
                    bot_y = minimap_y + bot.y * self.minimap_scale
                    pygame.draw.circle(
                        screen, self.config.RED, (int(bot_x), int(bot_y)), 3
                    )

        player_x = minimap_x + player.x * self.minimap_scale
        player_y = minimap_y + player.y * self.minimap_scale
        pygame.draw.circle(screen, self.config.GREEN, (int(player_x), int(player_y)), 3)

        dir_x = player_x + math.cos(player.angle) * 10
        dir_y = player_y + math.sin(player.angle) * 10
        pygame.draw.line(
            screen, self.config.GREEN, (player_x, player_y), (dir_x, dir_y), 2
        )
