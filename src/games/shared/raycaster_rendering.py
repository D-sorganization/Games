"""Pure rendering helpers for the raycasting engine.

Extracted from raycaster.py (issue #568) to reduce that module's size.
Contains column/wall rendering, sprite rendering/scaling, floor/ceiling
rendering, and minimap rendering.  All functions operate on pygame surfaces
and numpy arrays; they receive all required state via parameters so they can
be tested independently of the full Raycaster class.
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Any

import numpy as np
import pygame

from .raycaster_render_contexts import (
    MinimapRenderContext,
    TexturedWallColumnContext,
)

if TYPE_CHECKING:
    from collections import OrderedDict

    from .interfaces import Player, Projectile


# ---------------------------------------------------------------------------
# Wall rendering helpers
# ---------------------------------------------------------------------------


def prepare_wall_render_data(
    distances: np.ndarray[Any, Any],
    fisheye_factors: np.ndarray[Any, Any],
    screen_height: int,
    max_depth: float,
    fog_start: float,
    player_pitch: float,
    view_offset_y: float,
) -> tuple[list[int], list[int], list[float], list[float]]:
    """Compute wall heights, tops, shading and fog from distances.

    Returns:
        (wall_heights_int_list, wall_tops_list, shades_list, fog_factors_list)
    """
    corrected_dists = distances * fisheye_factors
    safe_dists = np.maximum(0.01, corrected_dists)

    wall_heights = np.minimum(screen_height * 4, (screen_height / safe_dists))
    wall_tops = (
        (screen_height - wall_heights) // 2 + player_pitch + view_offset_y
    ).astype(np.int32)
    wall_heights_int = wall_heights.astype(np.int32)

    shades = np.maximum(0.2, 1.0 - distances / 50.0)

    fog_factors = np.clip(
        (distances - max_depth * fog_start) / (max_depth * (1 - fog_start)),
        0.0,
        1.0,
    )

    # Convert to Python lists: these feed a per-ray Python loop where list
    # indexing outperforms numpy scalar indexing.  See issue #477 for details.
    return (
        wall_heights_int.tolist(),
        wall_tops.tolist(),
        shades.tolist(),
        fog_factors.tolist(),
    )


def render_textured_wall_column(
    context: TexturedWallColumnContext,
) -> None:
    """Render a single textured wall column with shading and fog."""
    strips = context.wall_strips[context.wt]
    tex_w = len(strips)
    tex_x = int(np.clip(int(context.wall_x_hit * tex_w), 0, tex_w - 1))

    if context.h >= 8000:
        # Solid colour fallback for extreme close-up
        col = context.wall_colors.get(context.wt, context.gray)
        col = (
            int(col[0] * context.shade),
            int(col[1] * context.shade),
            int(col[2] * context.shade),
        )
        pygame.draw.rect(
            context.view_surface,
            col,
            (context.i, context.top, 1, context.h),
        )
        return

    tname = context.texture_map.get(context.wt, "brick")
    scaled_strip = context.get_cached_strip_fn(tname, tex_x, int(context.h))

    if not scaled_strip:
        col = context.wall_colors.get(context.wt, context.gray)
        pygame.draw.rect(
            context.view_surface,
            col,
            (context.i, context.top, 1, context.h),
        )
        return

    context.blits_sequence.append((scaled_strip, (context.i, context.top)))

    # Shading overlay
    if context.shade < 1.0:
        alpha = max(0, min(255, int(255 * (1.0 - context.shade))))
        if alpha > 0:
            context.blits_sequence.append(
                (
                    context.shading_surfaces[alpha],
                    (context.i, context.top),
                    (0, 0, 1, context.h),
                )
            )

    # Fog overlay
    if context.fog > 0:
        fog_alpha = max(0, min(255, int(255 * context.fog)))
        if fog_alpha > 0:
            context.blits_sequence.append(
                (
                    context.fog_surfaces[fog_alpha],
                    (context.i, context.top),
                    (0, 0, 1, context.h),
                )
            )


def render_solid_wall_column(
    i: int,
    wt: int,
    h: int,
    top: int,
    shade: float,
    fog: float,
    wall_colors: dict[int, tuple[int, int, int]],
    view_surface: pygame.Surface,
    gray: tuple[int, int, int],
    fog_color: tuple[int, int, int],
) -> None:
    """Render a single wall column as a solid shaded/fogged colour."""
    col = wall_colors.get(wt, gray)

    r = col[0] * shade
    g = col[1] * shade
    b = col[2] * shade

    fr = r * (1 - fog) + fog_color[0] * fog
    fg_v = g * (1 - fog) + fog_color[1] * fog
    fb = b * (1 - fog) + fog_color[2] * fog

    final_col = (int(fr), int(fg_v), int(fb))
    pygame.draw.rect(view_surface, final_col, (i, top, 1, h))


# ---------------------------------------------------------------------------
# Sprite rendering helpers
# ---------------------------------------------------------------------------


def collect_visible_runs(
    start_r: int,
    end_r: int,
    dist: float,
    z_buffer: np.ndarray[Any, Any],
) -> tuple[list[tuple[int, int]], int]:
    """Scan z-buffer for visible column runs of a sprite.

    Returns:
        (visible_runs, total_visible_pixels)
    """
    visible_runs: list[tuple[int, int]] = []
    total_visible_pixels = 0
    r = start_r

    while r < end_r:
        if dist > z_buffer[r]:
            r += 1
            continue
        run_start = r
        r += 1
        while r < end_r and dist <= z_buffer[r]:
            r += 1
        visible_runs.append((run_start, r))
        total_visible_pixels += r - run_start

    return visible_runs, total_visible_pixels


def blit_whole_scaled(  # noqa: PLR0913
    sprite_surface: pygame.Surface,
    cache_key: tuple[Any, ...],
    visible_runs: list[tuple[int, int]],
    target_width: int,
    target_height: int,
    sprite_ray_x: float,
    sprite_y: float,
    visual_scale: float,
    scaled_sprite_cache: OrderedDict[tuple[Any, ...], pygame.Surface],
    scaled_cache_max: int,
    scaled_cache_evict: int,
    evict_lru_fn: Any,
    view_surface: pygame.Surface,
) -> None:
    """Blit visible runs using a whole-surface scale strategy."""
    bucket_step = 8
    raw_final_w = int(target_width * visual_scale)
    final_w = max(bucket_step, (raw_final_w // bucket_step) * bucket_step)

    aspect_ratio = sprite_surface.get_height() / sprite_surface.get_width()
    final_h = int(final_w * aspect_ratio)

    scaled_cache_key = (cache_key, final_w, final_h)
    if scaled_cache_key in scaled_sprite_cache:
        scaled_sprite_cache.move_to_end(scaled_cache_key)
        scaled_sprite = scaled_sprite_cache[scaled_cache_key]
    else:
        try:
            scaled_sprite = pygame.transform.scale(sprite_surface, (final_w, final_h))
            evict_lru_fn(scaled_sprite_cache, scaled_cache_max, scaled_cache_evict)
            scaled_sprite_cache[scaled_cache_key] = scaled_sprite
        except (ValueError, pygame.error):
            return

    for run_start, run_end in visible_runs:
        x_offset = int(run_start - sprite_ray_x)
        width = run_end - run_start

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
            view_surface.blit(scaled_sprite, (run_start, dst_y), area)


def blit_strip_scaled(  # noqa: PLR0913
    sprite_surface: pygame.Surface,
    visible_runs: list[tuple[int, int]],
    target_width: int,
    target_height: int,
    sprite_ray_x: float,
    sprite_ray_width: float,
    sprite_y: float,
    visual_scale: float,
    view_surface: pygame.Surface,
) -> None:
    """Blit visible runs using per-strip scaling (fallback for large sprites)."""
    tex_width = sprite_surface.get_width()
    tex_height = sprite_surface.get_height()
    logical_tex_width = tex_width / visual_scale
    tex_scale = logical_tex_width / sprite_ray_width
    tex_padding = (tex_width - logical_tex_width) / 2

    for run_start, run_end in visible_runs:
        run_width = run_end - run_start

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
            view_surface.blit(scaled_slice, (run_start, int(sprite_y)))
        except (ValueError, pygame.error):
            continue


def draw_projectile_effect(
    proj: Projectile,
    rect: pygame.Rect,
    surface: pygame.Surface,
) -> None:
    """Draw weapon-type-specific visual effects for a projectile."""
    weapon = proj.weapon_type

    if weapon == "plasma":
        pygame.draw.circle(surface, (255, 255, 255), rect.center, rect.width // 4)
    elif weapon == "rocket":
        pygame.draw.circle(surface, (255, 100, 0), rect.center, rect.width // 3)
    elif weapon == "bfg":
        pygame.draw.circle(surface, (200, 255, 200), rect.center, rect.width // 3)
    elif weapon == "bomb":
        pygame.draw.circle(surface, (255, 0, 0), (rect.centerx, rect.top), 2)
    elif weapon == "flamethrower":
        flame_color = (255, random.randint(100, 200), 0)
        pygame.draw.circle(surface, flame_color, rect.center, rect.width // 2)
        pygame.draw.circle(
            surface, (255, 50, 0), (rect.centerx, rect.centery), rect.width // 3
        )
    elif weapon == "pulse":
        pygame.draw.circle(surface, (200, 200, 255), rect.center, rect.width // 2)
        pygame.draw.circle(surface, (100, 100, 255), rect.center, rect.width // 3)
    elif weapon == "freezer":
        pygame.draw.circle(surface, (200, 255, 255), rect.center, rect.width // 2)
        pygame.draw.circle(surface, (150, 200, 255), rect.center, rect.width // 3)


# ---------------------------------------------------------------------------
# Floor / ceiling / sky rendering
# ---------------------------------------------------------------------------


def generate_background_surface(
    level: int,
    level_themes: list[dict[str, Any]],
    screen_width: int,
    screen_height: int,
    gray: tuple[int, int, int],
    dark_gray: tuple[int, int, int],
) -> tuple[pygame.Surface, pygame.Surface, int]:
    """Pre-generate a high-quality background surface for the level theme.

    Returns:
        (background_surface, scaled_background_surface, theme_idx)
    """
    theme_idx = (level - 1) % len(level_themes) if level_themes else 0
    theme = level_themes[theme_idx] if level_themes else None

    h = screen_height
    background_surface = pygame.Surface((1, h * 2))

    ceiling_color = theme["ceiling"] if theme else gray
    floor_color = theme["floor"] if theme else dark_gray

    # Sky gradient (top half)
    top_sky = (
        max(0, ceiling_color[0] - 30),
        max(0, ceiling_color[1] - 30),
        max(0, ceiling_color[2] - 30),
    )
    bottom_sky = ceiling_color

    # Floor gradient (bottom half)
    near_floor = floor_color
    far_floor = (
        max(0, floor_color[0] - 40),
        max(0, floor_color[1] - 40),
        max(0, floor_color[2] - 40),
    )

    for y in range(h):
        ratio = y / h
        r = top_sky[0] + (bottom_sky[0] - top_sky[0]) * ratio
        g = top_sky[1] + (bottom_sky[1] - top_sky[1]) * ratio
        b = top_sky[2] + (bottom_sky[2] - top_sky[2]) * ratio
        background_surface.set_at((0, y), (int(r), int(g), int(b)))

    for y in range(h):
        ratio = y / h
        r = far_floor[0] + (near_floor[0] - far_floor[0]) * ratio
        g = far_floor[1] + (near_floor[1] - far_floor[1]) * ratio
        b = far_floor[2] + (near_floor[2] - far_floor[2]) * ratio
        background_surface.set_at((0, h + y), (int(r), int(g), int(b)))

    scaled_background_surface = pygame.transform.scale(
        background_surface, (screen_width, h * 2)
    )
    return background_surface, scaled_background_surface, theme_idx


def render_floor_ceiling(  # noqa: PLR0913
    screen: pygame.Surface,
    player: Player,
    level: int,
    level_themes: list[dict[str, Any]],
    screen_width: int,
    screen_height: int,
    stars: list[tuple[int, int, float, tuple[int, int, int]]],
    cached_background_theme_idx: int,
    background_surface: pygame.Surface | None,
    scaled_background_surface: pygame.Surface | None,
    gray: tuple[int, int, int],
    dark_gray: tuple[int, int, int],
    view_offset_y: float = 0.0,
) -> tuple[pygame.Surface | None, pygame.Surface | None, int]:
    """Render floor and sky with stars and moon.

    Returns:
        (background_surface, scaled_background_surface, cached_background_theme_idx)
        so the caller can update its cached state.
    """
    level_themes_list = level_themes or []
    theme_idx = (level - 1) % len(level_themes_list) if level_themes_list else 0
    theme = level_themes_list[theme_idx] if level_themes_list else None

    background_surface, scaled_background_surface, cached_background_theme_idx = (
        _ensure_background_surface(
            level,
            level_themes_list,
            screen_width,
            screen_height,
            gray,
            dark_gray,
            cached_background_theme_idx,
            theme_idx,
            background_surface,
            scaled_background_surface,
        )
    )

    horizon = screen_height // 2 + int(player.pitch + view_offset_y)
    _blit_background(
        screen, scaled_background_surface, screen_width, screen_height, horizon
    )
    _draw_stars(screen, stars, player, screen_width, horizon, view_offset_y)
    _draw_moon(screen, player, screen_width, horizon, view_offset_y, theme, gray)
    return background_surface, scaled_background_surface, cached_background_theme_idx


def _ensure_background_surface(  # noqa: PLR0913
    level: int,
    level_themes_list: list[dict[str, Any]],
    screen_width: int,
    screen_height: int,
    gray: tuple[int, int, int],
    dark_gray: tuple[int, int, int],
    cached_background_theme_idx: int,
    theme_idx: int,
    background_surface: pygame.Surface | None,
    scaled_background_surface: pygame.Surface | None,
) -> tuple[pygame.Surface | None, pygame.Surface | None, int]:
    """Regenerate the background surface if the theme changed, else ensure scaling."""
    if cached_background_theme_idx != theme_idx or background_surface is None:
        background_surface, scaled_background_surface, theme_idx = (
            generate_background_surface(
                level, level_themes_list, screen_width, screen_height, gray, dark_gray
            )
        )
        cached_background_theme_idx = theme_idx
    elif scaled_background_surface is None:
        scaled_background_surface = pygame.transform.scale(
            background_surface, (screen_width, screen_height * 2)
        )
    return background_surface, scaled_background_surface, cached_background_theme_idx


def _blit_background(
    screen: pygame.Surface,
    bg: pygame.Surface | None,
    screen_width: int,
    screen_height: int,
    horizon: int,
) -> None:
    """Blit the sky (above horizon) and floor (below horizon) bands."""
    if bg is None:
        raise ValueError("DbC Blocked: background surface must not be None")
    if horizon > 0:
        screen.blit(
            bg, (0, horizon - screen_height), (0, 0, screen_width, screen_height)
        )
    if horizon < screen_height:
        screen.blit(bg, (0, horizon), (0, screen_height, screen_width, screen_height))


def _draw_stars(
    screen: pygame.Surface,
    stars: list[tuple[int, int, float, tuple[int, int, int]]],
    player: Player,
    screen_width: int,
    horizon: int,
    view_offset_y: float,
) -> None:
    """Draw scrolling star field in the sky portion."""
    star_offset = int(player.angle * 200) % screen_width
    for sx, sy, size, color in stars:
        x = (sx + star_offset) % screen_width
        y = int(sy + player.pitch + view_offset_y)
        if 0 <= y < horizon:
            pygame.draw.circle(screen, color, (x, int(y)), int(size))


def _draw_moon(
    screen: pygame.Surface,
    player: Player,
    screen_width: int,
    horizon: int,
    view_offset_y: float,
    theme: dict[str, Any] | None,
    gray: tuple[int, int, int],
) -> None:
    """Draw the moon disc with a shadow overlay."""
    moon_x = (screen_width - 200 - int(player.angle * 100)) % (
        screen_width * 2
    ) - screen_width // 2
    moon_y = 100 + int(player.pitch + view_offset_y)
    if not (-100 < moon_x < screen_width + 100):
        return
    if not (0 <= moon_y < horizon + 40):
        return
    pygame.draw.circle(screen, (220, 220, 200), (int(moon_x), moon_y), 40)
    moon_color = theme["ceiling"] if theme else gray
    pygame.draw.circle(screen, moon_color, (int(moon_x) - 10, moon_y), 40)


# ---------------------------------------------------------------------------
# Minimap rendering
# ---------------------------------------------------------------------------


def generate_minimap_cache(
    minimap_size: int,
    minimap_scale: float,
    grid: list[list[int]],
    map_width: int,
    map_height: int,
    wall_colors: dict[int, tuple[int, int, int]],
    dark_gray: tuple[int, int, int],
    gray: tuple[int, int, int],
) -> pygame.Surface:
    """Generate static minimap surface."""
    surface = pygame.Surface((minimap_size, minimap_size))
    surface.fill(dark_gray)

    for y in range(map_height):
        for x in range(map_width):
            w_type = grid[y][x]
            if w_type > 0:
                color = wall_colors.get(w_type, gray)
                pygame.draw.rect(
                    surface,
                    color,
                    (
                        x * minimap_scale,
                        y * minimap_scale,
                        minimap_scale,
                        minimap_scale,
                    ),
                )
    return surface


def render_minimap(
    context: MinimapRenderContext,
) -> tuple[pygame.Surface | None, int]:
    """Render 2D minimap with fog of war support.

    Returns:
        (fog_surface, fog_visited_count) -- caller should update its cached state.
    """
    _draw_minimap_border(context)
    fog_surface, fog_visited_count = _draw_minimap_tiles(
        context, context.fog_surface, context.fog_visited_count
    )
    _draw_minimap_portal(context)
    _draw_minimap_bots(context)
    _draw_minimap_player(context)
    return fog_surface, fog_visited_count


def _draw_minimap_border(context: MinimapRenderContext) -> None:
    """Draw the black border around the minimap."""
    pygame.draw.rect(
        context.screen,
        context.black,
        (
            context.minimap_x - 2,
            context.minimap_y - 2,
            context.minimap_size + 4,
            context.minimap_size + 4,
        ),
    )


def _draw_minimap_tiles(
    context: MinimapRenderContext,
    fog_surface: pygame.Surface | None,
    fog_visited_count: int,
) -> tuple[pygame.Surface | None, int]:
    """Blit the static minimap surface with optional fog of war."""
    if not context.minimap_surface:
        return fog_surface, fog_visited_count

    if context.visited_cells is not None:
        visited_count = len(context.visited_cells)
        if fog_surface is None or fog_visited_count != visited_count:
            fog_surface = pygame.Surface(
                (context.minimap_size, context.minimap_size), pygame.SRCALPHA
            )
            fog_surface.fill((0, 0, 0, 255))
            for vx, vy in context.visited_cells:
                fog_surface.fill(
                    (0, 0, 0, 0),
                    rect=(
                        vx * context.minimap_scale,
                        vy * context.minimap_scale,
                        context.minimap_scale,
                        context.minimap_scale,
                    ),
                )
            fog_visited_count = visited_count
        context.screen.blit(
            context.minimap_surface, (context.minimap_x, context.minimap_y)
        )
        context.screen.blit(fog_surface, (context.minimap_x, context.minimap_y))
    else:
        context.screen.blit(
            context.minimap_surface, (context.minimap_x, context.minimap_y)
        )
    return fog_surface, fog_visited_count


def _draw_minimap_portal(context: MinimapRenderContext) -> None:
    """Draw the portal indicator dot on the minimap."""
    if context.portal is None:
        return
    px, py = int(context.portal["x"]), int(context.portal["y"])
    if context.visited_cells is None or (px, py) in context.visited_cells:
        portal_map_x = context.minimap_x + px * context.minimap_scale
        portal_map_y = context.minimap_y + py * context.minimap_scale
        pygame.draw.circle(
            context.screen,
            context.cyan,
            (int(portal_map_x), int(portal_map_y)),
            int(context.minimap_scale * 2),
        )


def _draw_minimap_bots(context: MinimapRenderContext) -> None:
    """Draw red enemy dots on the minimap for visible bots."""
    for bot in context.bots:
        if not (
            bot.alive
            and bot.enemy_type != "health_pack"
            and context.enemy_types is not None
            and context.enemy_types[bot.enemy_type].get("visual_style") != "item"
        ):
            continue
        bot_cell = (int(bot.x), int(bot.y))
        if context.visited_cells is None or bot_cell in context.visited_cells:
            bot_x = context.minimap_x + bot.x * context.minimap_scale
            bot_y = context.minimap_y + bot.y * context.minimap_scale
            pygame.draw.circle(context.screen, context.red, (int(bot_x), int(bot_y)), 3)


def _draw_minimap_player(context: MinimapRenderContext) -> None:
    """Draw the player dot and direction arrow on the minimap."""
    player_x = context.minimap_x + context.player.x * context.minimap_scale
    player_y = context.minimap_y + context.player.y * context.minimap_scale
    pygame.draw.circle(context.screen, context.green, (int(player_x), int(player_y)), 3)
    dir_x = player_x + math.cos(context.player.angle) * 10
    dir_y = player_y + math.sin(context.player.angle) * 10
    pygame.draw.line(
        context.screen, context.green, (player_x, player_y), (dir_x, dir_y), 2
    )
