"""Sprite rendering functions for the raycasting engine.

Handles sorting, culling, and drawing of bots, projectiles, and world
particles onto the offscreen view surface.  Extracted from raycaster.py
to keep the main module under the 400-line guideline.
"""

from __future__ import annotations

import math
from collections import OrderedDict
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import pygame

from .bot_renderer import BotRenderer
from .raycaster_rendering import (
    blit_strip_scaled,
    blit_whole_scaled,
    collect_visible_runs,
    draw_projectile_effect,
)

if TYPE_CHECKING:
    from .config import RaycasterConfig
    from .interfaces import Bot, EnemyData, Player, Projectile, WorldParticle


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VISUAL_SCALE = 2.2
STRIP_VISIBILITY_THRESHOLD = 0.3
LARGE_SPRITE_THRESHOLD = 200


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_sprites(  # noqa: PLR0913
    player: Player,
    bots: Sequence[Bot],
    projectiles: Sequence[Projectile],
    particles: Sequence[WorldParticle],
    half_fov: float,
    view_offset_y: float,
    flash_intensity: float,
    config: RaycasterConfig,
    num_rays: int,
    render_scale: int,
    view_surface: pygame.Surface,
    z_buffer: np.ndarray[Any, np.dtype[Any]],
    sprite_cache: OrderedDict[tuple, pygame.Surface],
    sprite_cache_max: int,
    sprite_cache_evict: int,
    scaled_sprite_cache: OrderedDict[tuple, pygame.Surface],
    scaled_cache_max: int,
    scaled_cache_evict: int,
    evict_fn: Callable[..., None],
) -> None:
    """Render all sprites (bots, projectiles, particles) to the view surface."""
    sprites_to_render: list[tuple[Any, int]] = []

    p_cos = math.cos(player.angle)
    p_sin = math.sin(player.angle)
    max_dist_sq = config.MAX_DEPTH * config.MAX_DEPTH

    for bot in bots:
        if bot.removed:
            continue
        sprites_to_render.append((bot, 0))

    for proj in projectiles:
        if not proj.alive:
            continue
        sprites_to_render.append((proj, 1))

    for part in particles:
        if not part.alive:
            continue
        sprites_to_render.append((part, 2))

    final_sprites = _cull_and_sort_sprites(
        sprites_to_render, player, p_cos, p_sin, max_dist_sq, half_fov
    )

    for entity, dist, angle, type_id in final_sprites:
        if type_id == 1:
            proj = cast("Projectile", entity)
            _draw_single_projectile(
                player,
                proj,
                dist,
                angle,
                half_fov,
                view_offset_y,
                config,
                num_rays,
                render_scale,
                view_surface,
                z_buffer,
            )
        elif type_id == 2:
            part = cast("WorldParticle", entity)
            _draw_single_particle(
                player,
                part,
                dist,
                angle,
                half_fov,
                view_offset_y,
                config,
                num_rays,
                render_scale,
                view_surface,
                z_buffer,
            )
        else:
            bot = cast("Bot", entity)
            _draw_single_sprite(
                player,
                bot,
                dist,
                angle,
                half_fov,
                view_offset_y,
                flash_intensity,
                config,
                num_rays,
                render_scale,
                view_surface,
                z_buffer,
                sprite_cache,
                sprite_cache_max,
                sprite_cache_evict,
                scaled_sprite_cache,
                scaled_cache_max,
                scaled_cache_evict,
                evict_fn,
            )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _cull_and_sort_sprites(
    sprites: list[tuple[Any, int]],
    player: Player,
    p_cos: float,
    p_sin: float,
    max_dist_sq: float,
    half_fov: float,
) -> list[tuple[Any, float, float, int]]:
    """Cull off-screen sprites and sort back-to-front."""
    result: list[tuple[Any, float, float, int]] = []

    for entity, type_id in sprites:
        dx = entity.x - player.x
        dy = entity.y - player.y

        dist_sq = dx * dx + dy * dy
        if dist_sq > max_dist_sq:
            continue

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
            result.append((entity, dist, angle_to_sprite, type_id))

    result.sort(key=lambda x: x[1], reverse=True)
    return result


def _draw_single_particle(  # noqa: PLR0913
    player: Player,
    particle: WorldParticle,
    dist: float,
    angle: float,
    half_fov: float,
    view_offset_y: float,
    config: RaycasterConfig,
    num_rays: int,
    render_scale: int,
    view_surface: pygame.Surface,
    z_buffer: np.ndarray[Any, np.dtype[Any]],
) -> None:
    """Draw a world particle."""
    safe_dist = max(0.01, dist)
    base_size = config.SCREEN_HEIGHT / safe_dist
    sprite_size = base_size * float(particle.size)

    center_ray = num_rays / 2
    sprite_scale = sprite_size / render_scale
    ray_x = center_ray + (angle / half_fov) * center_ray - sprite_scale / 2

    z_offset = (particle.z - 0.5) * (config.SCREEN_HEIGHT / safe_dist)
    sprite_y = (
        (config.SCREEN_HEIGHT / 2)
        - (sprite_size / 2)
        - z_offset
        + player.pitch
        + view_offset_y
    )

    if ray_x + sprite_scale < 0 or ray_x >= num_rays:
        return

    center_ray_idx = int(ray_x + sprite_scale / 2)
    if 0 <= center_ray_idx < num_rays:
        if dist > z_buffer[center_ray_idx]:
            return

    try:
        rect = pygame.Rect(
            int(ray_x), int(sprite_y), int(sprite_scale), int(sprite_scale)
        )
        if rect.width > 0 and rect.height > 0:
            pygame.draw.circle(
                view_surface, particle.color, rect.center, rect.width // 2
            )
    except (ValueError, pygame.error):
        pass


def _draw_single_projectile(  # noqa: PLR0913
    player: Player,
    proj: Projectile,
    dist: float,
    angle: float,
    half_fov: float,
    view_offset_y: float,
    config: RaycasterConfig,
    num_rays: int,
    render_scale: int,
    view_surface: pygame.Surface,
    z_buffer: np.ndarray[Any, np.dtype[Any]],
) -> None:
    """Draw a projectile sprite."""
    safe_dist = max(0.01, dist)
    base_size = config.SCREEN_HEIGHT / safe_dist
    sprite_size = base_size * float(proj.size)

    center_ray = num_rays / 2
    sprite_scale = sprite_size / render_scale
    ray_x = center_ray + (angle / half_fov) * center_ray - sprite_scale / 2

    z_offset = (proj.z - 0.5) * (config.SCREEN_HEIGHT / safe_dist)
    sprite_y = (
        (config.SCREEN_HEIGHT / 2)
        - (sprite_size / 2)
        - z_offset
        + player.pitch
        + view_offset_y
    )

    if ray_x + sprite_scale < 0 or ray_x >= num_rays:
        return

    center_ray_idx = int(ray_x + sprite_scale / 2)
    if 0 <= center_ray_idx < num_rays:
        if dist > z_buffer[center_ray_idx]:
            return

    try:
        rect = pygame.Rect(
            int(ray_x), int(sprite_y), int(sprite_scale), int(sprite_scale)
        )
        if rect.width > 0 and rect.height > 0:
            pygame.draw.circle(view_surface, proj.color, rect.center, rect.width // 2)
            draw_projectile_effect(proj, rect, view_surface)
    except (ValueError, pygame.error):
        pass


def _draw_single_sprite(  # noqa: PLR0913
    player: Player,
    bot: Bot,
    dist: float,
    angle: float,
    half_fov: float,
    view_offset_y: float,
    flash_intensity: float,
    config: RaycasterConfig,
    num_rays: int,
    render_scale: int,
    view_surface: pygame.Surface,
    z_buffer: np.ndarray[Any, np.dtype[Any]],
    sprite_cache: OrderedDict[tuple, pygame.Surface],
    sprite_cache_max: int,
    sprite_cache_evict: int,
    scaled_sprite_cache: OrderedDict[tuple, pygame.Surface],
    scaled_cache_max: int,
    scaled_cache_evict: int,
    evict_fn: Callable[..., None],
) -> None:
    """Draw a single bot sprite with caching and z-buffered strips."""
    safe_dist = max(0.01, dist)
    base_sprite_size = config.SCREEN_HEIGHT / safe_dist

    type_data: EnemyData = bot.type_data
    sprite_size = base_sprite_size * float(type_data.get("scale", 1.0))

    center_ray = num_rays / 2
    sprite_scale = sprite_size / render_scale
    ray_x = center_ray + (angle / half_fov) * center_ray - sprite_scale / 2

    sprite_ray_width = sprite_size / render_scale
    sprite_ray_x = ray_x

    sprite_y = config.SCREEN_HEIGHT / 2 - sprite_size / 2 + player.pitch + view_offset_y

    if sprite_ray_x + sprite_ray_width < 0 or sprite_ray_x >= num_rays:
        return

    sprite_surface, cache_key, _distance_shade = _get_or_create_sprite_surface(
        bot,
        sprite_size,
        dist,
        flash_intensity,
        config,
        sprite_cache,
        sprite_cache_max,
        sprite_cache_evict,
        evict_fn,
    )

    start_r = int(max(0, sprite_ray_x))
    end_r = int(min(num_rays, sprite_ray_x + sprite_ray_width))
    if start_r >= end_r:
        return

    target_width = int(sprite_ray_width)
    target_height = int(sprite_size)
    if target_width <= 0 or target_height <= 0:
        return

    visible_runs, total_visible_pixels = collect_visible_runs(
        start_r, end_r, dist, z_buffer
    )
    if not visible_runs:
        return

    _blit_sprite_runs(
        sprite_surface,
        cache_key,
        visible_runs,
        total_visible_pixels,
        target_width,
        target_height,
        sprite_ray_x,
        sprite_ray_width,
        sprite_y,
        sprite_size,
        view_surface,
        scaled_sprite_cache,
        scaled_cache_max,
        scaled_cache_evict,
        evict_fn,
    )


def _get_or_create_sprite_surface(  # noqa: PLR0913
    bot: Bot,
    sprite_size: float,
    dist: float,
    flash_intensity: float,
    config: RaycasterConfig,
    sprite_cache: OrderedDict[tuple, pygame.Surface],
    sprite_cache_max: int,
    sprite_cache_evict: int,
    evict_fn: Callable[..., None],
) -> tuple[pygame.Surface, tuple[Any, ...], float]:
    """Get or create a cached sprite surface for the given bot."""
    cache_display_size = min(sprite_size, 800)
    cached_size = max(int(round(cache_display_size / 10.0) * 10.0), 10)

    distance_shade = max(0.2, 1.0 - dist / 50.0)
    if flash_intensity > 0:
        flash_factor = flash_intensity * max(0.0, 1.0 - dist / 15.0)
        distance_shade = min(1.0, distance_shade + flash_factor)

    shade_level = int(distance_shade * 20)

    cache_key = (
        bot.enemy_type,
        bot.type_data.get("visual_style"),
        int(bot.walk_animation * 5),
        int(bot.shoot_animation * 5),
        bot.dead,
        int(bot.death_timer // 5),
        cached_size,
        shade_level,
        bot.frozen,
    )

    if cache_key in sprite_cache:
        sprite_cache.move_to_end(cache_key)
        return sprite_cache[cache_key], cache_key, distance_shade

    surf_size = int(cached_size * VISUAL_SCALE)
    padding = (surf_size - cached_size) // 2

    sprite_surface = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    BotRenderer.render_sprite(
        sprite_surface, bot, padding, padding, cached_size, config
    )

    shade_val = int(255 * distance_shade)
    shade_color = (shade_val, shade_val, shade_val)
    if shade_color != (255, 255, 255):
        sprite_surface.fill(shade_color, special_flags=pygame.BLEND_MULT)

    if bot.frozen:
        sprite_surface.fill((150, 200, 255), special_flags=pygame.BLEND_MULT)

    evict_fn(sprite_cache, sprite_cache_max, sprite_cache_evict)
    sprite_cache[cache_key] = sprite_surface
    return sprite_surface, cache_key, distance_shade


def _blit_sprite_runs(  # noqa: PLR0913
    sprite_surface: pygame.Surface,
    cache_key: tuple[Any, ...],
    visible_runs: list[tuple[int, int]],
    total_visible_pixels: int,
    target_width: int,
    target_height: int,
    sprite_ray_x: float,
    sprite_ray_width: float,
    sprite_y: float,
    sprite_size: float,
    view_surface: pygame.Surface,
    scaled_sprite_cache: OrderedDict[tuple, pygame.Surface],
    scaled_cache_max: int,
    scaled_cache_evict: int,
    evict_fn: Callable[..., None],
) -> None:
    """Blit visible sprite runs using whole-scale or strip-scale strategy."""
    scale_whole = True
    if (
        total_visible_pixels < target_width * STRIP_VISIBILITY_THRESHOLD
        and target_width > LARGE_SPRITE_THRESHOLD
    ):
        scale_whole = False

    if scale_whole:
        blit_whole_scaled(
            sprite_surface,
            cache_key,
            visible_runs,
            target_width,
            target_height,
            sprite_ray_x,
            sprite_y,
            VISUAL_SCALE,
            scaled_sprite_cache,
            scaled_cache_max,
            scaled_cache_evict,
            evict_fn,
            view_surface,
        )
    else:
        blit_strip_scaled(
            sprite_surface,
            visible_runs,
            target_width,
            target_height,
            sprite_ray_x,
            sprite_ray_width,
            sprite_y,
            VISUAL_SCALE,
            view_surface,
        )
