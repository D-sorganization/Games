import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .map import Map


def cast_ray_dda(
    start_x: float,
    start_y: float,
    angle: float,
    game_map: "Map",
    max_dist: float = 100.0,
) -> tuple[float, int, float, float]:
    """Cast a ray using DDA algorithm.

    Returns:
        (distance, wall_type, hit_x, hit_y)
    """
    ray_dir_x = math.cos(angle)
    ray_dir_y = math.sin(angle)

    map_x = int(start_x)
    map_y = int(start_y)

    # Calculate delta distance
    delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
    delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30

    # Calculate step and initial side distance
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

    hit = False
    wall_type = 0

    # Max depth check to prevent infinite loop (approximate)
    # We can limit by distance or steps. DDA steps approx = distance.
    max_steps = int(max_dist * 1.5)

    # Local variable access for speed (if this was in a class)
    # But here we access game_map.grid
    grid = game_map.grid
    width = game_map.width
    height = game_map.height

    dist = 0.0

    for _ in range(max_steps):
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            map_x += step_x
            dist = side_dist_x - delta_dist_x
        else:
            side_dist_y += delta_dist_y
            map_y += step_y
            dist = side_dist_y - delta_dist_y

        if dist > max_dist:
            break

        # Check bounds first
        if not (0 <= map_x < width and 0 <= map_y < height):
            # Out of bounds - treat as wall
            hit = True
            wall_type = 1
            break

        # Within bounds - check for wall
        if grid[map_y][map_x] > 0:
            hit = True
            wall_type = grid[map_y][map_x]
            break

    if hit:
        return dist, wall_type, start_x + ray_dir_x * dist, start_y + ray_dir_y * dist

    return max_dist, 0, start_x + ray_dir_x * max_dist, start_y + ray_dir_y * max_dist


def has_line_of_sight(
    x1: float, y1: float, x2: float, y2: float, game_map: "Map"
) -> bool:
    """Check if there is a clear line of sight between two points."""
    dx = x2 - x1
    dy = y2 - y1
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 0.001:
        return True

    angle = math.atan2(dy, dx)

    hit_dist, wall_type, _, _ = cast_ray_dda(x1, y1, angle, game_map, max_dist=dist)

    # Allow small epsilon error
    return hit_dist >= dist - 0.1


def try_move_entity(
    entity: Any,
    dx: float,
    dy: float,
    game_map: "Map",
    obstacles: list[Any],
    radius: float = 0.5,
) -> None:
    """Try to move entity by dx, dy checking walls and obstacles."""
    col_sq = radius * radius

    # Try X movement
    new_x = entity.x + dx
    if not game_map.is_wall(new_x, entity.y):
        collision = False
        for ob in obstacles:
            if ob is entity:
                continue
            if hasattr(ob, "alive") and not ob.alive:
                continue

            # Quick check
            if abs(new_x - ob.x) > radius:
                continue
            if abs(entity.y - ob.y) > radius:
                continue

            # Squared distance check
            d_sq = (new_x - ob.x) ** 2 + (entity.y - ob.y) ** 2
            if d_sq < col_sq:
                collision = True
                break

        if not collision:
            entity.x = new_x

    # Try Y movement
    new_y = entity.y + dy
    if not game_map.is_wall(entity.x, new_y):
        collision = False
        for ob in obstacles:
            if ob is entity:
                continue
            if hasattr(ob, "alive") and not ob.alive:
                continue

            d_sq = (entity.x - ob.x) ** 2 + (new_y - ob.y) ** 2
            if d_sq < col_sq:
                collision = True
                break

        if not collision:
            entity.y = new_y
