import math
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from games.shared.contracts import validate_not_none, validate_positive

if TYPE_CHECKING:
    from .interfaces import Map


def cast_ray_dda(
    start_x: float,
    start_y: float,
    angle: float,
    game_map: "Map",
    max_dist: float = 100.0,
) -> tuple[float, int, float, float, int, int, int]:
    """Cast a ray using DDA algorithm.

    Returns:
        (distance, wall_type, hit_x, hit_y, side, map_x, map_y)
        side: 0 for vertical wall (x-side), 1 for horizontal wall (y-side)
    """
    validate_not_none(game_map, "game_map")
    validate_positive(max_dist, "max_dist")
    ray_dir_x = math.cos(angle)
    ray_dir_y = math.sin(angle)
    dda_params = _init_dda_params(start_x, start_y, ray_dir_x, ray_dir_y)
    map_x, map_y, step_x, step_y, sdx, sdy, ddx, ddy = dda_params
    hit, wall_type, dist, side, map_x, map_y = _run_dda_loop(
        map_x, map_y, step_x, step_y, sdx, sdy, ddx, ddy, game_map, max_dist
    )
    hit_x = start_x + ray_dir_x * dist
    hit_y = start_y + ray_dir_y * dist
    if hit:
        return dist, wall_type, hit_x, hit_y, side, map_x, map_y
    return max_dist, 0, hit_x, hit_y, side, map_x, map_y


def _init_dda_params(
    start_x: float,
    start_y: float,
    ray_dir_x: float,
    ray_dir_y: float,
) -> tuple[int, int, int, int, float, float, float, float]:
    """Compute DDA grid cell, step directions, and initial side distances.

    Returns:
        (map_x, map_y, step_x, step_y, side_dist_x, side_dist_y,
         delta_dist_x, delta_dist_y)
    """
    map_x = int(start_x)
    map_y = int(start_y)
    delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
    delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30
    if ray_dir_x < 0:
        step_x = -1
        side_dist_x = (start_x - map_x) * delta_dist_x
    else:
        step_x = 1
        side_dist_x = (map_x + 1.0 - start_x) * delta_dist_x
    if ray_dir_y < 0:
        step_y = -1
        side_dist_y = (start_y - map_y) * delta_dist_y
    else:
        step_y = 1
        side_dist_y = (map_y + 1.0 - start_y) * delta_dist_y
    return (
        map_x,
        map_y,
        step_x,
        step_y,
        side_dist_x,
        side_dist_y,
        delta_dist_x,
        delta_dist_y,
    )


def _advance_dda(
    map_x: int,
    map_y: int,
    step_x: int,
    step_y: int,
    sdx: float,
    sdy: float,
    ddx: float,
    ddy: float,
) -> tuple[int, int, float, float, float, int]:
    """Advance one DDA grid step; return (mx, my, sdx, sdy, dist, side)."""
    if sdx < sdy:
        sdx += ddx
        return map_x + step_x, map_y, sdx, sdy, sdx - ddx, 0
    sdy += ddy
    return map_x, map_y + step_y, sdx, sdy, sdy - ddy, 1


def _run_dda_loop(
    map_x: int,
    map_y: int,
    step_x: int,
    step_y: int,
    side_dist_x: float,
    side_dist_y: float,
    delta_dist_x: float,
    delta_dist_y: float,
    game_map: "Map",
    max_dist: float,
) -> tuple[bool, int, float, int, int, int]:
    """Run the DDA march until a wall is hit or max_dist is exceeded.

    Returns: (hit, wall_type, dist, side, map_x, map_y)
    """
    grid, width, height = game_map.grid, game_map.width, game_map.height
    hit, wall_type, side, dist = False, 0, 0, 0.0
    for _ in range(int(max_dist * 1.5)):
        map_x, map_y, side_dist_x, side_dist_y, dist, side = _advance_dda(
            map_x, map_y, step_x, step_y, side_dist_x, side_dist_y, delta_dist_x, delta_dist_y
        )
        if dist > max_dist:
            break
        if not (0 <= map_x < width and 0 <= map_y < height):
            hit, wall_type = True, 1
            break
        if grid[map_y][map_x] > 0:
            hit, wall_type = True, grid[map_y][map_x]
            break
    return hit, wall_type, dist, side, map_x, map_y


def has_line_of_sight(
    x1: float, y1: float, x2: float, y2: float, game_map: "Map"
) -> bool:
    """Check if there is a clear line of sight between two points."""
    validate_not_none(game_map, "game_map")
    dx = x2 - x1
    dy = y2 - y1
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 0.001:
        return True

    angle = math.atan2(dy, dx)

    hit_dist, wall_type, _, _, _, _, _ = cast_ray_dda(
        x1, y1, angle, game_map, max_dist=dist
    )

    # Allow small epsilon error
    return hit_dist >= dist - 0.1


def try_move_entity(
    entity: Any,
    dx: float,
    dy: float,
    game_map: "Map",
    obstacles: Sequence[Any],
    radius: float = 0.5,
) -> None:
    """Try to move entity by dx, dy checking walls and obstacles."""
    validate_not_none(entity, "entity")
    validate_not_none(game_map, "game_map")
    validate_positive(radius, "radius")
    col_sq = radius * radius

    new_x = entity.x + dx
    if not game_map.is_wall(new_x, entity.y):
        if not _entity_collides_with_obstacles(
            new_x, entity.y, entity, obstacles, radius, col_sq
        ):
            entity.x = new_x

    new_y = entity.y + dy
    if not game_map.is_wall(entity.x, new_y):
        if not _entity_collides_with_obstacles(
            entity.x, new_y, entity, obstacles, radius, col_sq
        ):
            entity.y = new_y


def _entity_collides_with_obstacles(
    test_x: float,
    test_y: float,
    entity: Any,
    obstacles: Sequence[Any],
    radius: float,
    col_sq: float,
) -> bool:
    """Return True if the entity at (test_x, test_y) overlaps any live obstacle.

    Skips the entity itself and dead obstacles. Uses AABB pre-check before
    the more expensive squared-distance test.
    """
    for ob in obstacles:
        if ob is entity:
            continue
        if not getattr(ob, "alive", True):
            continue
        if abs(test_x - ob.x) > radius:
            continue
        if abs(test_y - ob.y) > radius:
            continue
        d_sq = (test_x - ob.x) ** 2 + (test_y - ob.y) ** 2
        if d_sq < col_sq:
            return True
    return False
