from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Any, cast

import pygame

from . import constants as C  # noqa: N812
from .bot_renderer import BotRenderer

# Sprite Rendering thresholds
STRIP_VISIBILITY_THRESHOLD = 0.3
LARGE_SPRITE_THRESHOLD = 200

if TYPE_CHECKING:
    from .bot import Bot
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

        # Offscreen surface for low-res rendering (Optimization)
        self.view_surface = pygame.Surface(
            (C.NUM_RAYS, C.SCREEN_HEIGHT), pygame.SRCALPHA
        )

        # Z-Buffer for occlusion (Euclidean distance)
        self.z_buffer: list[float] = [float("inf")] * C.NUM_RAYS

    def cast_ray(
        self,
        origin_x: float,
        origin_y: float,
        angle: float,
    ) -> tuple[float, int]:
        """Cast a single ray using DDA
        Returns: (distance, wall_type)
        Distance is Euclidean distance along the ray.
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

            if grid[map_y][map_x] > 0:
                hit = True
                wall_type = grid[map_y][map_x]
                break

        if hit:
            if side == 0:
                distance = side_dist_x - delta_dist_x
            else:
                distance = side_dist_y - delta_dist_y
            return distance, wall_type

        return C.MAX_DEPTH, 0

    def render_3d(
        self,
        screen: pygame.Surface,
        player: Player,
        bots: list[Bot],
        level: int,
        view_offset_y: float = 0.0,
    ) -> None:
        """Render 3D view using raycasting"""
        # Clear view surface with transparent color
        self.view_surface.fill((0, 0, 0, 0))

        current_fov = C.FOV * (C.ZOOM_FOV_MULT if player.zoomed else 1.0)
        half_fov = current_fov / 2
        delta_angle = current_fov / C.NUM_RAYS

        ray_angle = player.angle - half_fov

        # Select theme
        theme_idx = (level - 1) % len(C.LEVEL_THEMES)
        theme = C.LEVEL_THEMES[theme_idx]
        wall_colors = cast("dict[int, tuple[int, int, int]]", theme["walls"])

        # Reset Z-Buffer
        self.z_buffer = [float("inf")] * C.NUM_RAYS

        # Raycast and draw walls
        for ray in range(C.NUM_RAYS):
            distance, wall_type = self.cast_ray(
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

                lit_r = base_color[0] * shade
                lit_g = base_color[1] * shade
                lit_b = base_color[2] * shade

                # Mix with Fog
                final_r = lit_r * (1 - fog_factor) + C.FOG_COLOR[0] * fog_factor
                final_g = lit_g * (1 - fog_factor) + C.FOG_COLOR[1] * fog_factor
                final_b = lit_b * (1 - fog_factor) + C.FOG_COLOR[2] * fog_factor

                color = (int(final_r), int(final_g), int(final_b))

                # Pitch Adjustment
                wall_top = (
                    (C.SCREEN_HEIGHT - wall_height) // 2 + player.pitch + view_offset_y
                )

                # Draw vertical line on view_surface (width=1)
                pygame.draw.line(
                    self.view_surface,
                    color,
                    (ray, int(wall_top)),
                    (ray, int(wall_top + wall_height)),
                )

            # Horizontal lines (Brick effect) - Removed for performance
            # The set_at loop was causing significant performance drops.
            # If needed, this should be implemented via a pre-generated texture pattern
            # or a faster line drawing method, but doing it per-ray per-line
            # in Python is too slow.

            ray_angle += delta_angle

        # Render Sprites
        self._render_sprites(player, bots, half_fov, view_offset_y)

        # Scale view surface to screen size and blit
        scaled_surface = pygame.transform.scale(
            self.view_surface, (C.SCREEN_WIDTH, C.SCREEN_HEIGHT)
        )
        screen.blit(scaled_surface, (0, 0))

    def _render_sprites(
        self,
        player: Player,
        bots: list[Bot],
        half_fov: float,
        view_offset_y: float = 0.0,
    ) -> None:
        """Render all sprites to the view surface"""
        bots_to_render = []
        for bot in bots:
            if bot.removed:
                continue

            dx = bot.x - player.x
            dy = bot.y - player.y
            bot_dist = math.sqrt(dx**2 + dy**2)

            if bot_dist > C.MAX_DEPTH:
                continue

            bot_angle = math.atan2(dy, dx)
            angle_to_bot = bot_angle - player.angle

            while angle_to_bot > math.pi:
                angle_to_bot -= 2 * math.pi
            while angle_to_bot < -math.pi:
                angle_to_bot += 2 * math.pi

            if abs(angle_to_bot) < half_fov + 0.5:
                bots_to_render.append((bot, bot_dist, angle_to_bot))

        bots_to_render.sort(key=lambda x: x[1], reverse=True)

        for bot, bot_dist, angle_to_bot in bots_to_render:
            self._draw_single_sprite(
                player, bot, bot_dist, angle_to_bot, half_fov, view_offset_y
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

        type_data: dict[str, Any] = bot.type_data
        sprite_size = base_sprite_size * float(type_data.get("scale", 1.0))

        center_ray = C.NUM_RAYS / 2
        ray_x = (
            center_ray
            + (angle / half_fov) * center_ray
            - (sprite_size / C.RENDER_SCALE) / 2
        )

        sprite_ray_width = sprite_size / C.RENDER_SCALE
        sprite_ray_x = ray_x

        sprite_y = C.SCREEN_HEIGHT / 2 - sprite_size / 2 + player.pitch + view_offset_y

        if sprite_ray_x + sprite_ray_width < 0 or sprite_ray_x >= C.NUM_RAYS:
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
                # Evict oldest
                keys_to_remove = list(self.sprite_cache.keys())[:40]
                for k in keys_to_remove:
                    del self.sprite_cache[k]
            self.sprite_cache[cache_key] = sprite_surface

        start_r = int(max(0, sprite_ray_x))
        end_r = int(min(C.NUM_RAYS, sprite_ray_x + sprite_ray_width))

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
                    self.view_surface.blit(
                        scaled_sprite, (run_start, int(sprite_y)), area
                    )
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

        ceiling_color = cast("tuple[int, int, int]", theme["ceiling"])
        pygame.draw.rect(screen, ceiling_color, (0, 0, C.SCREEN_WIDTH, horizon))

        star_offset = int(player_angle * 200) % C.SCREEN_WIDTH

        for sx, sy, size, color in self.stars:
            x = (sx + star_offset) % C.SCREEN_WIDTH
            y = sy + player.pitch + view_offset_y

            if 0 <= y < horizon:
                pygame.draw.circle(screen, color, (x, int(y)), int(size))

        moon_x = (C.SCREEN_WIDTH - 200 - int(player_angle * 100)) % (
            C.SCREEN_WIDTH * 2
        ) - C.SCREEN_WIDTH // 2
        moon_y = 100 + int(player.pitch + view_offset_y)

        if -100 < moon_x < C.SCREEN_WIDTH + 100:
            if 0 <= moon_y < horizon + 40:
                pygame.draw.circle(screen, (220, 220, 200), (int(moon_x), moon_y), 40)
                pygame.draw.circle(
                    screen, ceiling_color, (int(moon_x) - 10, moon_y), 40
                )

        floor_color = cast("tuple[int, int, int]", theme["floor"])
        pygame.draw.rect(
            screen,
            floor_color,
            (0, horizon, C.SCREEN_WIDTH, C.SCREEN_HEIGHT - horizon),
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
        minimap_size = 200
        map_size = self.game_map.size
        minimap_scale = minimap_size / map_size
        minimap_x = C.SCREEN_WIDTH - minimap_size - 20
        minimap_y = 20

        pygame.draw.rect(
            screen,
            C.BLACK,
            (minimap_x - 2, minimap_y - 2, minimap_size + 4, minimap_size + 4),
        )
        pygame.draw.rect(
            screen, C.DARK_GRAY, (minimap_x, minimap_y, minimap_size, minimap_size)
        )

        for i in range(map_size):
            for j in range(map_size):
                if self.grid[i][j] != 0:
                    if visited_cells is not None and (j, i) not in visited_cells:
                        continue

                    wall_type = self.grid[i][j]
                    color = C.WALL_COLORS.get(wall_type, C.GRAY)
                    pygame.draw.rect(
                        screen,
                        color,
                        (
                            minimap_x + j * minimap_scale,
                            minimap_y + i * minimap_scale,
                            minimap_scale,
                            minimap_scale,
                        ),
                    )

        if portal:
            portal_x = int(portal["x"])
            portal_y = int(portal["y"])
            if visited_cells is None or (portal_x, portal_y) in visited_cells:
                portal_map_x = minimap_x + portal_x * minimap_scale
                portal_map_y = minimap_y + portal_y * minimap_scale
                pygame.draw.circle(
                    screen,
                    C.CYAN,
                    (int(portal_map_x), int(portal_map_y)),
                    int(minimap_scale * 2),
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
                    bot_x = minimap_x + bot.x * minimap_scale
                    bot_y = minimap_y + bot.y * minimap_scale
                    pygame.draw.circle(screen, C.RED, (int(bot_x), int(bot_y)), 3)

        player_x = minimap_x + player.x * minimap_scale
        player_y = minimap_y + player.y * minimap_scale
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

        for projectile in projectiles:
            if not projectile.alive:
                continue

            dx = projectile.x - player.x
            dy = projectile.y - player.y
            proj_dist = math.sqrt(dx**2 + dy**2)

            if proj_dist > C.MAX_DEPTH:
                continue

            proj_angle = math.atan2(dy, dx)
            angle_to_proj = proj_angle - player.angle

            while angle_to_proj > math.pi:
                angle_to_proj -= 2 * math.pi
            while angle_to_proj < -math.pi:
                angle_to_proj += 2 * math.pi

            if abs(angle_to_proj) < half_fov:
                proj_size = max(2, 10 / proj_dist) if proj_dist > 0.1 else 100
                proj_x = (
                    C.SCREEN_WIDTH / 2 + (angle_to_proj / half_fov) * C.SCREEN_WIDTH / 2
                )
                proj_y = C.SCREEN_HEIGHT / 2 + player.pitch + view_offset_y

                # Simple Z-Check
                # Map angle to ray index
                center_ray = C.NUM_RAYS // 2
                ray_idx = int(center_ray + (angle_to_proj / half_fov) * center_ray)

                # Check bounds and Z-Buffer
                if 0 <= ray_idx < C.NUM_RAYS:
                    # Check if center is occluded
                    if proj_dist > self.z_buffer[ray_idx]:
                        # Occluded
                        continue

                pygame.draw.circle(
                    screen, C.RED, (int(proj_x), int(proj_y)), int(proj_size)
                )
                pygame.draw.circle(
                    screen,
                    C.ORANGE,
                    (int(proj_x), int(proj_y)),
                    int(proj_size * 0.6),
                )
