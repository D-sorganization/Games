"""
Pure math/DDA helpers for the raycasting engine.

Extracted from raycaster.py (issue #583) to reduce that module's size.
No pygame imports -- these functions operate solely on numpy arrays and
plain Python floats so they can be tested without a display.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .interfaces import Player


def get_ray_directions(
    player: Player,
    cos_deltas: np.ndarray[Any, Any],
    sin_deltas: np.ndarray[Any, Any],
    cos_deltas_zoomed: np.ndarray[Any, Any],
    sin_deltas_zoomed: np.ndarray[Any, Any],
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """Calculate ray direction vectors for all rays.

    Returns:
        (ray_dir_x, ray_dir_y) -- zeros replaced with 1e-30 to avoid
        division-by-zero in downstream DDA steps.
    """
    if player.zoomed:
        _cos_deltas, _sin_deltas = cos_deltas_zoomed, sin_deltas_zoomed
    else:
        _cos_deltas, _sin_deltas = cos_deltas, sin_deltas

    p_cos, p_sin = math.cos(player.angle), math.sin(player.angle)
    ray_dir_x = p_cos * _cos_deltas - p_sin * _sin_deltas
    ray_dir_y = p_sin * _cos_deltas + p_cos * _sin_deltas

    # Avoid division by zero in delta_dist calculation
    ray_dir_x[ray_dir_x == 0] = 1e-30
    ray_dir_y[ray_dir_y == 0] = 1e-30
    return ray_dir_x, ray_dir_y


def init_dda_params(
    player: Player,
    num_rays: int,
    ray_dir_x: np.ndarray[Any, Any],
    ray_dir_y: np.ndarray[Any, Any],
) -> tuple[Any, ...]:
    """Initialize per-ray DDA stepping parameters.

    Returns:
        (map_x, map_y, delta_dist_x, delta_dist_y,
         side_dist_x, side_dist_y, step_x, step_y)
    """
    map_x = np.full(num_rays, int(player.x), dtype=np.int32)
    map_y = np.full(num_rays, int(player.y), dtype=np.int32)

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
    return (
        map_x,
        map_y,
        delta_dist_x,
        delta_dist_y,
        side_dist_x,
        side_dist_y,
        step_x,
        step_y,
    )


def perform_dda_loop(
    num_rays: int,
    map_width: int,
    map_height: int,
    np_grid: np.ndarray[Any, Any],
    max_steps: int,
    map_x: np.ndarray[Any, Any],
    map_y: np.ndarray[Any, Any],
    side_dist_x: np.ndarray[Any, Any],
    side_dist_y: np.ndarray[Any, Any],
    delta_dist_x: np.ndarray[Any, Any],
    delta_dist_y: np.ndarray[Any, Any],
    step_x: np.ndarray[Any, Any],
    step_y: np.ndarray[Any, Any],
) -> tuple[Any, ...]:
    """Perform the main DDA hit-detection loop.

    Returns:
        (hits, wall_types, side)
    """
    hits = np.zeros(num_rays, dtype=bool)
    side = np.zeros(num_rays, dtype=np.int32)
    wall_types = np.zeros(num_rays, dtype=np.int32)
    active = np.ones(num_rays, dtype=bool)

    for _ in range(max_steps):
        mask_x = (side_dist_x < side_dist_y) & active
        mask_y = (~mask_x) & active

        side_dist_x[mask_x] += delta_dist_x[mask_x]
        map_x[mask_x] += step_x[mask_x]
        side[mask_x] = 0

        side_dist_y[mask_y] += delta_dist_y[mask_y]
        map_y[mask_y] += step_y[mask_y]
        side[mask_y] = 1

        in_bounds = (map_x >= 0) & (map_x < map_width) & (map_y >= 0) & (map_y < map_height)
        out_of_bounds = (~in_bounds) & active
        if np.any(out_of_bounds):
            hits[out_of_bounds] = True
            wall_types[out_of_bounds] = 1
            active[out_of_bounds] = False

        check_mask = in_bounds & active
        if np.any(check_mask):
            grid_vals = np_grid[map_y[check_mask], map_x[check_mask]]
            wall_hit_mask = grid_vals > 0

            indices = np.nonzero(check_mask)[0][wall_hit_mask]
            if len(indices) > 0:
                hits[indices] = True
                wall_types[indices] = grid_vals[wall_hit_mask]
                active[indices] = False

        if not np.any(active):
            break

    return hits, wall_types, side


def finalize_ray_data(
    player: Player,
    num_rays: int,
    hits: np.ndarray[Any, Any],
    wall_types: np.ndarray[Any, Any],
    side: np.ndarray[Any, Any],
    side_dist_x: np.ndarray[Any, Any],
    side_dist_y: np.ndarray[Any, Any],
    delta_dist_x: np.ndarray[Any, Any],
    delta_dist_y: np.ndarray[Any, Any],
    ray_dir_x: np.ndarray[Any, Any],
    ray_dir_y: np.ndarray[Any, Any],
    cos_deltas: np.ndarray[Any, Any],
    cos_deltas_zoomed: np.ndarray[Any, Any],
) -> tuple[Any, ...]:
    """Calculate final perpendicular distances and wall-hit X coordinates.

    The *hits* parameter is accepted for API symmetry with ``perform_dda_loop``
    but is not used in distance computation.

    Returns:
        (perp_wall_dist, wall_types, wall_x_hit, side, fisheye_factors)
    """
    del hits  # unused; retained in signature for call-site symmetry
    perp_wall_dist = np.zeros(num_rays, dtype=np.float64)
    mask_0, mask_1 = side == 0, side == 1
    perp_wall_dist[mask_0] = side_dist_x[mask_0] - delta_dist_x[mask_0]
    perp_wall_dist[mask_1] = side_dist_y[mask_1] - delta_dist_y[mask_1]

    wall_x_hit = np.zeros(num_rays, dtype=np.float64)
    wall_x_hit[mask_0] = player.y + perp_wall_dist[mask_0] * ray_dir_y[mask_0]
    wall_x_hit[mask_1] = player.x + perp_wall_dist[mask_1] * ray_dir_x[mask_1]
    wall_x_hit -= np.floor(wall_x_hit)

    fisheye_factors = cos_deltas_zoomed if player.zoomed else cos_deltas
    return perp_wall_dist, wall_types, wall_x_hit, side, fisheye_factors
