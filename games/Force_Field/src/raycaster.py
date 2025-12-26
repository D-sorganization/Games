from __future__ import annotations

import itertools
import math
import random
from typing import TYPE_CHECKING, Any, cast

import pygame

from . import constants as C  # noqa: N812
from .bot_renderer import BotRenderer
from .texture_generator import TextureGenerator

# Sprite Rendering thresholds
STRIP_VISIBILITY_THRESHOLD = 0.3
LARGE_SPRITE_THRESHOLD = 200

if TYPE_CHECKING:
    from .bot import Bot
    from .custom_types import EnemyData
    from .map import Map
    from .player import Player
    from .projectile import Projectile


class Raycaster:
    """Raycasting engine for 3D rendering"""

    def __init__(self, game_map: Map):
        """Initialize raycaster"""
        self.game_map = game_map
        # Optimization: Cache grid for faster access
        self.grid = game_map.grid
        self.map_size = game_map.size

        # Cache for theme
        self._cached_level: int = -1
        self._cached_wall_colors: dict[int, tuple[int, int, int]] = {}

        # Texture mapping
        self.use_textures = True
        self.textures = TextureGenerator.generate_textures()

        # Map wall types to texture names
        self.texture_map = {1: "stone", 2: "brick", 3: "metal", 4: "tech", 5: "secret"}

        # Pre-generate stars
        self.stars = []
        for _ in range(100):
            self.stars.append(
                (
                    random.randint(0, C.SCREEN_WIDTH),
                    random.randint(0, C.SCREEN_HEIGHT // 2),
                    random.uniform(0.5, 2.5),  # Size
                    random.choice([(255, 255, 255), (200, 200, 255), (255, 255, 200)]),
                )
            )

        # Sprite cache
        self.sprite_cache: dict[str, pygame.Surface] = {}

        # Minimap cache
        self.minimap_surface: pygame.Surface | None = None
        self.minimap_size = 200
        self.minimap_scale = self.minimap_size / self.map_size

        # Resolution settings
        self.render_scale = C.DEFAULT_RENDER_SCALE
        self.num_rays = C.SCREEN_WIDTH // self.render_scale

        # Offscreen surface for low-res rendering (Optimization)
        size = (self.num_rays, C.SCREEN_HEIGHT)
        self.view_surface = pygame.Surface(size, pygame.SRCALPHA)

        # Z-Buffer for occlusion (Euclidean distance)
        self.z_buffer: list[float] = [float("inf")] * self.num_rays

    def set_render_scale(self, scale: int) -> None:
        """Update render scale and related buffers."""
        self.render_scale = scale
        self.num_rays = C.SCREEN_WIDTH // scale

        # Recreate buffers
        self.view_surface = pygame.Surface(
            (self.num_rays, C.SCREEN_HEIGHT), pygame.SRCALPHA
        )
        self.z_buffer = [float("inf")] * self.num_rays

    def cast_ray(
        self,
        origin_x: float,
        origin_y: float,
        angle: float,
    ) -> tuple[float, int, float, int, int]:
        """Cast a single ray using DDA
        Returns: (distance, wall_type, wall_x, map_x, map_y)
        Distance is Euclidean distance along the ray.
        wall_x is the exact position of the hit on the wall (0.0 - 1.0)
        """
        ray_dir_x = math.cos(angle)
        ray_dir_y = math.sin(angle)

        map_x = int(origin_x)
        map_y = int(origin_y)

        # Calculate delta distance
        delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
        delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30

        # Calculate step and initial side distance
        if ray_dir_x < 0:
            step_x = -1
            side_dist_x = (origin_x - map_x) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (map_x + 1.0 - origin_x) * delta_dist_x

        if ray_dir_y < 0:
            step_y = -1
            side_dist_y = (origin_y - map_y) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (map_y + 1.0 - origin_y) * delta_dist_y

        hit = False
        side = 0  # 0 for NS, 1 for EW
        wall_type = 0

        # Max depth check to prevent infinite loop
        max_steps = int(C.MAX_DEPTH * 1.5)

        # Local variable access for speed
        grid = self.grid

        for _ in range(max_steps):
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1

            if 0 <= map_x < self.game_map.width and 0 <= map_y < self.game_map.height:
                if grid[map_y][map_x] > 0:
                    hit = True
                    wall_type = grid[map_y][map_x]
                    break
            else:
                # Treat out of bounds as a wall to stop the ray
                hit = True
                wall_type = 1
                break

        if hit:
            if side == 0:
                distance = side_dist_x - delta_dist_x
                wall_x_hit = origin_y + distance * ray_dir_y
            else:
                distance = side_dist_y - delta_dist_y
                wall_x_hit = origin_x + distance * ray_dir_x

            # Normalize wall_x_hit to 0-1
            wall_x_hit -= math.floor(wall_x_hit)
            return distance, wall_type, wall_x_hit, map_x, map_y

        return C.MAX_DEPTH, 0, 0.0, 0, 0

    def render_3d(
        self,
        screen: pygame.Surface,
        player: Player,
        bots: list[Bot],
        projectiles: list[Projectile],
        level: int,
        view_offset_y: float = 0.0,
    ) -> None:
        """Render 3D view using raycasting"""
        # Clear view surface with transparent color
        self.view_surface.fill((0, 0, 0, 0))

        current_fov = C.FOV * (C.ZOOM_FOV_MULT if player.zoomed else 1.0)
        half_fov = current_fov / 2
        delta_angle = current_fov / self.num_rays

        ray_angle = player.angle - half_fov

        # Select theme
        if hasattr(self, "_cached_level") and self._cached_level == level:
            wall_colors = self._cached_wall_colors
        else:
            theme_idx = (level - 1) % len(C.LEVEL_THEMES)
            theme = C.LEVEL_THEMES[theme_idx]
            wall_colors = theme["walls"]
            self._cached_level = level
            self._cached_wall_colors = wall_colors

        # Reset Z-Buffer
        # Re-using the existing list is faster than creating a new one
        if len(self.z_buffer) != self.num_rays:
            self.z_buffer = [float("inf")] * self.num_rays
        else:
            for i in range(self.num_rays):
                self.z_buffer[i] = float("inf")

        # Raycast and draw walls
        last_wall_type = 0
        last_color = (0, 0, 0)
        last_top = 0
        last_height = 0
        strip_width = 0
        start_ray = 0

        # Texture rendering settings
        use_textures = self.use_textures and len(self.textures) > 0

        for ray in range(self.num_rays):
            distance, wall_type, wall_x_hit, _, _ = self.cast_ray(
                player.x,
                player.y,
                ray_angle,
            )

            self.z_buffer[ray] = distance

            if wall_type > 0 and distance < C.MAX_DEPTH:
                # Fisheye correction
                corrected_dist = distance * math.cos(player.angle - ray_angle)

                # Prevent division by zero
                safe_dist = max(0.01, corrected_dist)
                wall_height = min(C.SCREEN_HEIGHT, (C.SCREEN_HEIGHT / safe_dist))

                base_color = wall_colors.get(wall_type, C.GRAY)

                # Fog Logic
                fog_factor = max(
                    0.0,
                    min(
                        1.0,
                        (distance - C.MAX_DEPTH * C.FOG_START)
                        / (C.MAX_DEPTH * (1 - C.FOG_START)),
                    ),
                )

                # Local lighting (Shade)
                # Adjusted to be a bit darker for atmosphere
                shade = max(0.2, 1.0 - distance / 50.0)

                # Pitch Adjustment
                pitch_off = player.pitch + view_offset_y
                wall_top = int((C.SCREEN_HEIGHT - wall_height) // 2 + pitch_off)
                wall_h_int = int(wall_height)

                # Texture Rendering
                tex_name = self.texture_map.get(wall_type, "brick")
                if use_textures and tex_name in self.textures:
                    # Flush any solid color strip being built
                    if strip_width > 0:
                        pygame.draw.rect(
                            self.view_surface,
                            last_color,
                            (start_ray, last_top, strip_width, last_height),
                        )
                        strip_width = 0

                    texture = self.textures[tex_name]
                    tex_w = texture.get_width()
                    tex_h = texture.get_height()

                    # Calculate texture X coordinate
                    tex_x = int(wall_x_hit * tex_w)
                    if tex_x >= tex_w:
                        tex_x = tex_w - 1
                    if tex_x < 0:
                        tex_x = 0

                    # Extract strip from texture
                    # Optimization: Don't create new surface if not needed?
                    # pygame.transform.scale is efficient.

                    # Calculate height to scale to
                    # If wall is bigger than screen, we need to handle clipping?
                    # Pygame handles blitting outside surface bounds, but performance
                    # might suffer if we scale to huge sizes.

                    # Optimization: If strip is very thin, skip detailed texture?
                    # For now, full render.

                    try:
                        # Get 1px wide strip
                        tex_strip = texture.subsurface((tex_x, 0, 1, tex_h))

                        # Scale it to wall height
                        # Note: we scale to wall_h_int, which might be > screen height.
                        # For very close walls, this can be slow.
                        # Limit max scaling size?
                        # Limit max scaling size?
                        # Arbitrary limit to prevent memory explosion
                        if wall_h_int < 8000:
                            scaled_strip = pygame.transform.scale(
                                tex_strip, (1, wall_h_int)
                            )

                            # Apply shading
                            if shade < 1.0:
                                shade_val = int(255 * shade)
                                shade_surf = pygame.Surface(
                                    (1, wall_h_int), pygame.SRCALPHA
                                )
                                # Alpha blending dark
                                shade_surf.fill((0, 0, 0, 255 - shade_val))
                                scaled_strip.blit(shade_surf, (0, 0))

                            # Blit to view surface
                            self.view_surface.blit(scaled_strip, (ray, wall_top))
                        else:
                            # Fallback to solid color for extreme closeups
                            pygame.draw.rect(
                                self.view_surface,
                                base_color,
                                (ray, wall_top, 1, wall_h_int),
                            )

                    except (pygame.error, ValueError):
                        pass

                else:
                    # Fallback to Solid Color Rendering (Strip Optimization)

                    lit_r = base_color[0] * shade
                    lit_g = base_color[1] * shade
                    lit_b = base_color[2] * shade

                    # Mix with Fog
                    final_r = lit_r * (1 - fog_factor) + C.FOG_COLOR[0] * fog_factor
                    final_g = lit_g * (1 - fog_factor) + C.FOG_COLOR[1] * fog_factor
                    final_b = lit_b * (1 - fog_factor) + C.FOG_COLOR[2] * fog_factor

                    color = (int(final_r), int(final_g), int(final_b))

                    # Strip Rendering Logic
                    can_group = False
                    if strip_width > 0:
                        # Check if we can group with previous strip
                        if (
                            wall_type == last_wall_type
                            and color == last_color
                            and abs(wall_top - last_top) <= 1
                            and abs(wall_h_int - last_height) <= 1
                        ):
                            can_group = True

                    if can_group:
                        strip_width += 1
                    else:
                        if strip_width > 0:
                            # Draw accumulated strip
                            pygame.draw.rect(
                                self.view_surface,
                                last_color,
                                (start_ray, last_top, strip_width, last_height),
                            )

                        # Start new strip
                        last_wall_type = wall_type
                        last_color = color
                        last_top = wall_top
                        last_height = wall_h_int
                        strip_width = 1
                        start_ray = ray
            else:
                # No wall hit (or too far)
                if strip_width > 0:
                    pygame.draw.rect(
                        self.view_surface,
                        last_color,
                        (start_ray, last_top, strip_width, last_height),
                    )
                strip_width = 0

            ray_angle += delta_angle

        # Draw final strip
        if strip_width > 0:
            pygame.draw.rect(
                self.view_surface,
                last_color,
                (start_ray, last_top, strip_width, last_height),
            )

        # Render Sprites
        self._render_sprites(player, bots, projectiles, half_fov, view_offset_y)

        # Scale view surface to screen size and blit
        if self.render_scale == 1:
            screen.blit(self.view_surface, (0, 0))
        else:
            scaled_surface = pygame.transform.scale(
                self.view_surface, (C.SCREEN_WIDTH, C.SCREEN_HEIGHT)
            )
            screen.blit(scaled_surface, (0, 0))

    def _render_sprites(
        self,
        player: Player,
        bots: list[Bot],
        projectiles: list[Projectile],
        half_fov: float,
        view_offset_y: float = 0.0,
    ) -> None:
        """Render all sprites (bots and projectiles) to the view surface"""
        sprites_to_render: list[tuple[Any, bool]] = []

        # Optimization: Pre-calculate player direction vector
        p_cos = math.cos(player.angle)
        p_sin = math.sin(player.angle)
        max_dist_sq = C.MAX_DEPTH * C.MAX_DEPTH

        max_dist_sq = C.MAX_DEPTH * C.MAX_DEPTH

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
        base_sprite_size = C.SCREEN_HEIGHT / safe_dist

        type_data: EnemyData = bot.type_data
        sprite_size = base_sprite_size * float(type_data.get("scale", 1.0))

        center_ray = self.num_rays / 2
        sprite_scale = sprite_size / self.render_scale
        ray_x = center_ray + (angle / half_fov) * center_ray - sprite_scale / 2

        sprite_ray_width = sprite_size / self.render_scale
        sprite_ray_x = ray_x

        sprite_y = C.SCREEN_HEIGHT / 2 - sprite_size / 2 + player.pitch + view_offset_y

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

        if cache_key in self.sprite_cache:
            sprite_surface = self.sprite_cache[cache_key]
        else:
            # Create base surface
            sprite_surface = pygame.Surface((cached_size, cached_size), pygame.SRCALPHA)
            BotRenderer.render_sprite(sprite_surface, bot, 0, 0, cached_size)

            # Apply shading cache
            shade_val = int(255 * distance_shade)
            shade_color = (shade_val, shade_val, shade_val)

            if shade_color != (255, 255, 255):
                sprite_surface.fill(shade_color, special_flags=pygame.BLEND_MULT)

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

        # Strategy:
        # If the sprite is mostly visible or small, scale the whole surface once.
        # This avoids calling pygame.transform.scale many times for small strips.
        scale_whole = True
        if (
            total_visible_pixels < target_width * STRIP_VISIBILITY_THRESHOLD
            and target_width > LARGE_SPRITE_THRESHOLD
        ):
            # If only a small fraction is visible and it's large, maybe strip
            # scaling is better? But strip scaling involves creating subsurfaces
            # which has overhead too. Modern Pygame/SDL is fast at scaling.
            # Let's default to scale_whole for simplicity.
            # actually, scaling a 1000x1000 image to just show 10 pixels is bad.
            scale_whole = False

        if scale_whole:
            try:
                scaled_sprite = pygame.transform.scale(
                    sprite_surface, (target_width, target_height)
                )
            except (ValueError, pygame.error):
                return

            for run_start, run_end in visible_runs:
                # Calculate x offset in the scaled sprite
                # sprite_ray_x corresponds to 0
                x_offset = int(run_start - sprite_ray_x)
                width = run_end - run_start

                # Clamp (just in case float math drifted)
                if x_offset < 0:
                    width += x_offset
                    x_offset = 0

                if x_offset + width > target_width:
                    width = target_width - x_offset

                if width > 0:
                    area = pygame.Rect(x_offset, 0, width, target_height)
                    pos = (run_start, int(sprite_y))
                    self.view_surface.blit(scaled_sprite, pos, area)
        else:
            # Fallback: Strip scaling (only for large occluded sprites)
            tex_width = sprite_surface.get_width()
            tex_height = sprite_surface.get_height()
            tex_scale = tex_width / sprite_ray_width

            for run_start, run_end in visible_runs:
                run_width = run_end - run_start

                tex_x_start = int((run_start - sprite_ray_x) * tex_scale)
                tex_x_end = int((run_end - sprite_ray_x) * tex_scale)

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
        base_size = C.SCREEN_HEIGHT / safe_dist
        sprite_size = base_size * float(proj.size)

        center_ray = self.num_rays / 2
        sprite_scale = sprite_size / self.render_scale
        ray_x = center_ray + (angle / half_fov) * center_ray - sprite_scale / 2

        # Height offset for arc (z-axis)
        # 0.5 is eye level (center screen).
        # Screen Y = center - (z - 0.5) * height_scale
        # height_scale is roughly C.SCREEN_HEIGHT / dist

        z_offset = (proj.z - 0.5) * (C.SCREEN_HEIGHT / safe_dist)
        sprite_y = (
            (C.SCREEN_HEIGHT / 2)
            - (sprite_size / 2)
            - z_offset
            + player.pitch
            + view_offset_y
        )

        # Draw checks
        if ray_x + sprite_scale < 0 or ray_x >= self.num_rays:
            return

        # Simple Circle Rendering for now (or specialized sprites)
        # We draw directly to view_surface

        # Correctly check z-buffer for center point visibility?
        # A simple center check is usually enough for small particles
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
                # Check if projectile has type_data fallback
                # If bomb, draw black circle. If plasma/rocket, use proj.color
                color = proj.color
                pygame.draw.circle(
                    self.view_surface, color, rect.center, rect.width // 2
                )

                # Glow
                if proj.weapon_type == "plasma":
                    pygame.draw.circle(
                        self.view_surface, (255, 255, 255), rect.center, rect.width // 4
                    )
                elif proj.weapon_type == "rocket":
                    pygame.draw.circle(
                        self.view_surface, (255, 100, 0), rect.center, rect.width // 3
                    )
                elif proj.weapon_type == "bomb":
                    # Draw fuse?
                    pygame.draw.circle(
                        self.view_surface, (255, 0, 0), (rect.centerx, rect.top), 2
                    )
        except (ValueError, pygame.error):
            pass

    def render_floor_ceiling(
        self,
        screen: pygame.Surface,
        player: Player,
        level: int,
        view_offset_y: float = 0.0,
    ) -> None:
        """Render floor and sky with stars"""
        theme_idx = (level - 1) % len(C.LEVEL_THEMES)
        theme = C.LEVEL_THEMES[theme_idx]
        player_angle = player.angle

        horizon = C.SCREEN_HEIGHT // 2 + int(player.pitch + view_offset_y)

        ceiling_color = theme["ceiling"]

        # Gradient Sky
        top_color = (
            max(0, ceiling_color[0] - 30),
            max(0, ceiling_color[1] - 30),
            max(0, ceiling_color[2] - 30),
        )
        bottom_color = ceiling_color

        # Draw sky in 10px bands
        for y in range(0, horizon, 10):
            ratio = y / max(1, horizon)
            r = top_color[0] + (bottom_color[0] - top_color[0]) * ratio
            g = top_color[1] + (bottom_color[1] - top_color[1]) * ratio
            b = top_color[2] + (bottom_color[2] - top_color[2]) * ratio
            height = int(min(10, horizon - y))
            pygame.draw.rect(
                screen,
                (int(r), int(g), int(b)),
                (0, y, C.SCREEN_WIDTH, height),
            )

        star_offset = int(player_angle * 200) % C.SCREEN_WIDTH

        for sx, sy, size, color in self.stars:
            x = (sx + star_offset) % C.SCREEN_WIDTH
            y = int(sy + player.pitch + view_offset_y)

            if 0 <= y < horizon:
                pygame.draw.circle(screen, color, (x, int(y)), int(size))

        moon_x = (C.SCREEN_WIDTH - 200 - int(player_angle * 100)) % (
            C.SCREEN_WIDTH * 2
        ) - C.SCREEN_WIDTH // 2
        moon_y = 100 + int(player.pitch + view_offset_y)

        if -100 < moon_x < C.SCREEN_WIDTH + 100:
            if 0 <= moon_y < horizon + 40:
                pygame.draw.circle(screen, (220, 220, 200), (int(moon_x), moon_y), 40)
                shadow_pos = (int(moon_x) - 10, moon_y)
                pygame.draw.circle(screen, ceiling_color, shadow_pos, 40)

        floor_color = theme["floor"]

        # Gradient Floor
        near_color = floor_color
        far_color = (
            max(0, floor_color[0] - 40),
            max(0, floor_color[1] - 40),
            max(0, floor_color[2] - 40),
        )

        floor_height = C.SCREEN_HEIGHT - horizon
        for y in range(0, floor_height, 10):
            ratio = y / max(1, floor_height)
            # Reverse ratio for floor (top is far, bottom is near)
            r = far_color[0] + (near_color[0] - far_color[0]) * ratio
            g = far_color[1] + (near_color[1] - far_color[1]) * ratio
            b = far_color[2] + (near_color[2] - far_color[2]) * ratio

            draw_y = horizon + y
            height = min(10, C.SCREEN_HEIGHT - draw_y)
            if height > 0:
                pygame.draw.rect(
                    screen,
                    (int(r), int(g), int(b)),
                    (0, draw_y, C.SCREEN_WIDTH, height),
                )

    def _generate_minimap_cache(self) -> None:
        """Generate static minimap surface."""
        self.minimap_surface = pygame.Surface((self.minimap_size, self.minimap_size))
        self.minimap_surface.fill(C.DARK_GRAY)

        for i in range(self.map_size):
            for j in range(self.map_size):
                if self.grid[i][j] != 0:
                    wall_type = self.grid[i][j]
                    color = C.WALL_COLORS.get(wall_type, C.GRAY)
                    pygame.draw.rect(
                        self.minimap_surface,
                        color,
                        (
                            j * self.minimap_scale,
                            i * self.minimap_scale,
                            self.minimap_scale,
                            self.minimap_scale,
                        ),
                    )

    def render_minimap(
        self,
        screen: pygame.Surface,
        player: Player,
        bots: list[Bot],
        visited_cells: set[tuple[int, int]] | None = None,
        portal: dict[str, Any] | None = None,
    ) -> None:
        """Render 2D minimap with fog of war support."""
        if self.minimap_surface is None:
            self._generate_minimap_cache()

        minimap_x = C.SCREEN_WIDTH - self.minimap_size - 20
        minimap_y = 20

        # Draw Border
        pygame.draw.rect(
            screen,
            C.BLACK,
            (
                minimap_x - 2,
                minimap_y - 2,
                self.minimap_size + 4,
                self.minimap_size + 4,
            ),
        )

        # Blit cached map
        if self.minimap_surface:
            # Create a mask surface for visited cells if needed
            if visited_cells is not None:
                # Optimized approach: Blit the full map, then cover unvisited areas
                # Or create a surface for visited areas.
                # Since fog of war is dynamic, we can't fully cache the visible result
                # but we can cache the base map.

                # Create fog mask
                fog_surface = pygame.Surface(
                    (self.minimap_size, self.minimap_size), pygame.SRCALPHA
                )
                fog_surface.fill((0, 0, 0, 255))  # Opaque black

                # Cut holes in fog
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

                # Apply fog to map (draw fog on top of the cached map on screen)
                screen.blit(self.minimap_surface, (minimap_x, minimap_y))
                screen.blit(fog_surface, (minimap_x, minimap_y))
            else:
                screen.blit(self.minimap_surface, (minimap_x, minimap_y))

        if portal:
            portal_x = int(portal["x"])
            portal_y = int(portal["y"])
            if visited_cells is None or (portal_x, portal_y) in visited_cells:
                portal_map_x = minimap_x + portal_x * self.minimap_scale
                portal_map_y = minimap_y + portal_y * self.minimap_scale
                pygame.draw.circle(
                    screen,
                    C.CYAN,
                    (int(portal_map_x), int(portal_map_y)),
                    int(self.minimap_scale * 2),  # Cast float to int
                )

        for bot in bots:
            if (
                bot.alive
                and bot.enemy_type != "health_pack"
                and C.ENEMY_TYPES[bot.enemy_type].get("visual_style") != "item"
            ):
                bot_cell_x = int(bot.x)
                bot_cell_y = int(bot.y)
                if visited_cells is None or (bot_cell_x, bot_cell_y) in visited_cells:
                    bot_x = minimap_x + bot.x * self.minimap_scale
                    bot_y = minimap_y + bot.y * self.minimap_scale
                    pygame.draw.circle(screen, C.RED, (int(bot_x), int(bot_y)), 3)

        player_x = minimap_x + player.x * self.minimap_scale
        player_y = minimap_y + player.y * self.minimap_scale
        pygame.draw.circle(screen, C.GREEN, (int(player_x), int(player_y)), 3)

        dir_x = player_x + math.cos(player.angle) * 10
        dir_y = player_y + math.sin(player.angle) * 10
        pygame.draw.line(screen, C.GREEN, (player_x, player_y), (dir_x, dir_y), 2)

    def render_projectiles(
        self,
        screen: pygame.Surface,
        player: Player,
        projectiles: list[Projectile],
        view_offset_y: float = 0.0,
    ) -> None:
        """Render bot projectiles"""
        current_fov = C.FOV * (C.ZOOM_FOV_MULT if player.zoomed else 1.0)
        half_fov = current_fov / 2

        # Optimization
        p_cos = math.cos(player.angle)
        p_sin = math.sin(player.angle)
        max_dist_sq = C.MAX_DEPTH * C.MAX_DEPTH

        for projectile in projectiles:
            if not projectile.alive:
                continue

            dx = projectile.x - player.x
            dy = projectile.y - player.y

            dist_sq = dx * dx + dy * dy
            if dist_sq > max_dist_sq:
                continue

            if dx * p_cos + dy * p_sin < 0:
                continue

            proj_dist = math.sqrt(dist_sq)

            proj_angle = math.atan2(dy, dx)
            angle_to_proj = proj_angle - player.angle

            while angle_to_proj > math.pi:
                angle_to_proj -= 2 * math.pi
            while angle_to_proj < -math.pi:
                angle_to_proj += 2 * math.pi

            if abs(angle_to_proj) < half_fov:
                proj_size = max(2, 10 / proj_dist) if proj_dist > 0.1 else 100
                offset_x = (angle_to_proj / half_fov) * C.SCREEN_WIDTH / 2
                proj_x = C.SCREEN_WIDTH / 2 + offset_x
                proj_y = C.SCREEN_HEIGHT / 2 + player.pitch + view_offset_y

                # Simple Z-Check
                # Map angle to ray index
                center_ray = self.num_rays // 2
                ray_idx = int(center_ray + (angle_to_proj / half_fov) * center_ray)

                # Check bounds and Z-Buffer
                if 0 <= ray_idx < self.num_rays:
                    # Check if center is occluded
                    if proj_dist > self.z_buffer[ray_idx]:
                        # Occluded
                        continue

                center = (int(proj_x), int(proj_y))
                pygame.draw.circle(screen, C.RED, center, int(proj_size))
                pygame.draw.circle(
                    screen,
                    C.ORANGE,
                    (int(proj_x), int(proj_y)),
                    int(proj_size * 0.6),
                )
