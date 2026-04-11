"""Immutable parameter bundles for raycaster render helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import pygame

from .contracts import (
    ContractViolation,
    validate_non_negative,
    validate_not_none,
    validate_positive,
    validate_range,
)


@dataclass(frozen=True)
class SpriteRenderContext:
    """Inputs required to render all sprites for a raycasting frame."""

    player: Any
    bots: Sequence[Any]
    projectiles: Sequence[Any]
    particles: Sequence[Any]
    half_fov: float
    view_offset_y: float
    flash_intensity: float
    config: Any
    num_rays: int
    render_scale: int
    view_surface: pygame.Surface
    z_buffer: Any
    sprite_cache: Any
    sprite_cache_max: int
    sprite_cache_evict: int
    scaled_sprite_cache: Any
    scaled_cache_max: int
    scaled_cache_evict: int
    evict_fn: Callable[..., None]

    def __post_init__(self) -> None:
        validate_not_none(self.player, "player")
        validate_not_none(self.bots, "bots")
        validate_not_none(self.projectiles, "projectiles")
        validate_not_none(self.particles, "particles")
        validate_positive(self.half_fov, "half_fov")
        validate_non_negative(self.flash_intensity, "flash_intensity")
        validate_not_none(self.config, "config")
        validate_positive(self.num_rays, "num_rays")
        validate_positive(self.render_scale, "render_scale")
        validate_not_none(self.view_surface, "view_surface")
        validate_not_none(self.z_buffer, "z_buffer")
        validate_not_none(self.sprite_cache, "sprite_cache")
        validate_positive(self.sprite_cache_max, "sprite_cache_max")
        validate_non_negative(self.sprite_cache_evict, "sprite_cache_evict")
        validate_not_none(self.scaled_sprite_cache, "scaled_sprite_cache")
        validate_positive(self.scaled_cache_max, "scaled_cache_max")
        validate_non_negative(self.scaled_cache_evict, "scaled_cache_evict")
        if not callable(self.evict_fn):
            raise ContractViolation("evict_fn must be callable")


@dataclass(frozen=True)
class TexturedWallColumnContext:
    """Inputs required to render a single textured wall column."""

    i: int
    wt: int
    h: int
    top: int
    wall_x_hit: float
    shade: float
    fog: float
    wall_strips: dict[int, list[pygame.Surface]]
    wall_colors: dict[int, tuple[int, int, int]]
    view_surface: pygame.Surface
    blits_sequence: list[Any]
    gray: tuple[int, int, int]
    texture_map: dict[int, str]
    shading_surfaces: list[pygame.Surface]
    fog_surfaces: list[pygame.Surface]
    get_cached_strip_fn: Callable[[str, int, int], pygame.Surface | None]

    def __post_init__(self) -> None:
        validate_positive(self.h, "h")
        validate_range(self.wall_x_hit, 0.0, 1.0, "wall_x_hit")
        validate_range(self.shade, 0.0, 1.0, "shade")
        validate_range(self.fog, 0.0, 1.0, "fog")
        validate_not_none(self.wall_strips, "wall_strips")
        validate_not_none(self.wall_colors, "wall_colors")
        validate_not_none(self.view_surface, "view_surface")
        validate_not_none(self.blits_sequence, "blits_sequence")
        validate_not_none(self.gray, "gray")
        validate_not_none(self.texture_map, "texture_map")
        validate_not_none(self.shading_surfaces, "shading_surfaces")
        validate_not_none(self.fog_surfaces, "fog_surfaces")
        if not callable(self.get_cached_strip_fn):
            raise ContractViolation("get_cached_strip_fn must be callable")


@dataclass(frozen=True)
class MinimapRenderContext:
    """Inputs required to render a minimap frame."""

    screen: pygame.Surface
    player: Any
    bots: Sequence[Any]
    minimap_surface: pygame.Surface | None
    minimap_size: int
    minimap_scale: float
    minimap_x: int
    minimap_y: int
    fog_surface: pygame.Surface | None
    fog_visited_count: int
    visited_cells: set[tuple[int, int]] | None
    portal: Any
    enemy_types: dict[str, Any] | None
    black: tuple[int, int, int]
    red: tuple[int, int, int]
    green: tuple[int, int, int]
    cyan: tuple[int, int, int]

    def __post_init__(self) -> None:
        validate_not_none(self.screen, "screen")
        validate_not_none(self.player, "player")
        validate_not_none(self.bots, "bots")
        validate_positive(self.minimap_size, "minimap_size")
        validate_positive(self.minimap_scale, "minimap_scale")
        validate_non_negative(self.fog_visited_count, "fog_visited_count")
        validate_not_none(self.black, "black")
        validate_not_none(self.red, "red")
        validate_not_none(self.green, "green")
        validate_not_none(self.cyan, "cyan")
