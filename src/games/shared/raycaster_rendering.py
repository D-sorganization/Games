"""Pure rendering helpers for the raycasting engine.

Extracted from raycaster.py (issue #568) to reduce that module's size.
Contains column/wall rendering and sprite rendering/scaling.

Floor/ceiling/sky and minimap rendering live in raycaster_environment.py
(extracted in issue #775).  The names below are re-exported for backward
compatibility with any code that imports them from this module.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

import numpy as np
import pygame

from .raycaster_environment import (  # noqa: F401  re-exported for compat
    generate_background_surface,
    generate_minimap_cache,
    render_floor_ceiling,
    render_minimap,
)
from .raycaster_render_contexts import (
    TexturedWallColumnContext,
)

if TYPE_CHECKING:
    from collections import OrderedDict

    from .interfaces import Projectile


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

    # Floor/ceiling, sky, and minimap rendering functions are re-exported above
    # from raycaster_environment.py (see the imports at the top of this module).
