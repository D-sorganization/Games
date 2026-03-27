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

if TYPE_CHECKING:
    from collections import OrderedDict
    from collections.abc import Sequence

    from .interfaces import Bot, Player, Portal, Projectile


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


def render_textured_wall_column(  # noqa: PLR0913
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
    gray: tuple[int, int, int],
    texture_map: dict[int, str],
    shading_surfaces: list[pygame.Surface],
    fog_surfaces: list[pygame.Surface],
    get_cached_strip_fn: Any,
) -> None:
    """Render a single textured wall column with shading and fog."""
    strips = wall_strips[wt]
    tex_w = len(strips)
    tex_x = int(np.clip(int(wall_x_hit * tex_w), 0, tex_w - 1))

    if h >= 8000:
        # Solid colour fallback for extreme close-up
        col = wall_colors.get(wt, gray)
        col = (int(col[0] * shade), int(col[1] * shade), int(col[2] * shade))
        pygame.draw.rect(view_surface, col, (i, top, 1, h))
        return

    tname = texture_map.get(wt, "brick")
    scaled_strip = get_cached_strip_fn(tname, tex_x, int(h))

    if not scaled_strip:
        col = wall_colors.get(wt, gray)
        pygame.draw.rect(view_surface, col, (i, top, 1, h))
        return

    blits_sequence.append((scaled_strip, (i, top)))

    # Shading overlay
    if shade < 1.0:
        alpha = max(0, min(255, int(255 * (1.0 - shade))))
        if alpha > 0:
            blits_sequence.append((shading_surfaces[alpha], (i, top), (0, 0, 1, h)))

    # Fog overlay
    if fog > 0:
        fog_alpha = max(0, min(255, int(255 * fog)))
        if fog_alpha > 0:
            blits_sequence.append((fog_surfaces[fog_alpha], (i, top), (0, 0, 1, h)))


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
    player_angle = player.angle

    if cached_background_theme_idx != theme_idx or background_surface is None:
        background_surface, scaled_background_surface, theme_idx = (
            generate_background_surface(
                level,
                level_themes_list,
                screen_width,
                screen_height,
                gray,
                dark_gray,
            )
        )
        cached_background_theme_idx = theme_idx

    horizon = screen_height // 2 + int(player.pitch + view_offset_y)

    bg = scaled_background_surface
    if bg is None and background_surface is not None:
        scaled_background_surface = pygame.transform.scale(
            background_surface, (screen_width, screen_height * 2)
        )
        bg = scaled_background_surface

    if not (bg is not None):
        raise ValueError("DbC Blocked: Precondition failed.")

    if horizon > 0:
        screen.blit(
            bg,
            (0, horizon - screen_height),
            (0, 0, screen_width, screen_height),
        )

    if horizon < screen_height:
        screen.blit(
            bg,
            (0, horizon),
            (0, screen_height, screen_width, screen_height),
        )

    star_offset = int(player_angle * 200) % screen_width
    for sx, sy, size, color in stars:
        x = (sx + star_offset) % screen_width
        y = int(sy + player.pitch + view_offset_y)
        if 0 <= y < horizon:
            pygame.draw.circle(screen, color, (x, int(y)), int(size))

    moon_x = (screen_width - 200 - int(player_angle * 100)) % (
        screen_width * 2
    ) - screen_width // 2
    moon_y = 100 + int(player.pitch + view_offset_y)

    if -100 < moon_x < screen_width + 100:
        if 0 <= moon_y < horizon + 40:
            pygame.draw.circle(screen, (220, 220, 200), (int(moon_x), moon_y), 40)
            shadow_pos = (int(moon_x) - 10, moon_y)
            moon_color = theme["ceiling"] if theme else gray
            pygame.draw.circle(screen, moon_color, shadow_pos, 40)

    return background_surface, scaled_background_surface, cached_background_theme_idx


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


def render_minimap(  # noqa: PLR0913
    screen: pygame.Surface,
    player: Player,
    bots: Sequence[Bot],
    minimap_surface: pygame.Surface | None,
    minimap_size: int,
    minimap_scale: float,
    minimap_x: int,
    minimap_y: int,
    fog_surface: pygame.Surface | None,
    fog_visited_count: int,
    visited_cells: set[tuple[int, int]] | None,
    portal: Portal | None,
    enemy_types: dict[str, Any] | None,
    black: tuple[int, int, int],
    red: tuple[int, int, int],
    green: tuple[int, int, int],
    cyan: tuple[int, int, int],
) -> tuple[pygame.Surface | None, int]:
    """Render 2D minimap with fog of war support.

    Returns:
        (fog_surface, fog_visited_count) -- caller should update its cached state.
    """
    pygame.draw.rect(
        screen,
        black,
        (minimap_x - 2, minimap_y - 2, minimap_size + 4, minimap_size + 4),
    )

    if minimap_surface:
        if visited_cells is not None:
            visited_count = len(visited_cells)
            if fog_surface is None or fog_visited_count != visited_count:
                fog_surface = pygame.Surface(
                    (minimap_size, minimap_size), pygame.SRCALPHA
                )
                fog_surface.fill((0, 0, 0, 255))
                for vx, vy in visited_cells:
                    fog_surface.fill(
                        (0, 0, 0, 0),
                        rect=(
                            vx * minimap_scale,
                            vy * minimap_scale,
                            minimap_scale,
                            minimap_scale,
                        ),
                    )
                fog_visited_count = visited_count
            screen.blit(minimap_surface, (minimap_x, minimap_y))
            screen.blit(fog_surface, (minimap_x, minimap_y))
        else:
            screen.blit(minimap_surface, (minimap_x, minimap_y))

    if portal is not None:
        px, py = int(portal["x"]), int(portal["y"])
        if visited_cells is None or (px, py) in visited_cells:
            portal_map_x = minimap_x + px * minimap_scale
            portal_map_y = minimap_y + py * minimap_scale
            pygame.draw.circle(
                screen,
                cyan,
                (int(portal_map_x), int(portal_map_y)),
                int(minimap_scale * 2),
            )

    for bot in bots:
        if (
            bot.alive
            and bot.enemy_type != "health_pack"
            and enemy_types is not None
            and enemy_types[bot.enemy_type].get("visual_style") != "item"
        ):
            bot_cell_x = int(bot.x)
            bot_cell_y = int(bot.y)
            if visited_cells is None or (bot_cell_x, bot_cell_y) in visited_cells:
                bot_x = minimap_x + bot.x * minimap_scale
                bot_y = minimap_y + bot.y * minimap_scale
                pygame.draw.circle(screen, red, (int(bot_x), int(bot_y)), 3)

    player_x = minimap_x + player.x * minimap_scale
    player_y = minimap_y + player.y * minimap_scale
    pygame.draw.circle(screen, green, (int(player_x), int(player_y)), 3)

    dir_x = player_x + math.cos(player.angle) * 10
    dir_y = player_y + math.sin(player.angle) * 10
    pygame.draw.line(screen, green, (player_x, player_y), (dir_x, dir_y), 2)

    return fog_surface, fog_visited_count
