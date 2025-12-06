import math
import pygame
from typing import TYPE_CHECKING, Tuple, Optional, List, Dict, Any
from . import constants as C

if TYPE_CHECKING:
    from .map import Map
    from .player import Player
    from .bot import Bot
    from .projectile import Projectile

class Raycaster:
    """Raycasting engine for 3D rendering"""

    def __init__(self, game_map: "Map"):
        """Initialize raycaster"""
        self.game_map = game_map

    def cast_ray(
        self,
        origin_x: float,
        origin_y: float,
        angle: float,
    ) -> Tuple[float, int, Optional["Bot"]]:
        """Cast a single ray and return distance, wall type, and hit bot"""
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        closest_bot = None

        # Cast ray
        for depth in range(1, int(C.MAX_DEPTH * 100)):
            target_x = origin_x + depth * 0.01 * cos_a
            target_y = origin_y + depth * 0.01 * sin_a
            distance = depth * 0.01

            if self.game_map.is_wall(target_x, target_y):
                wall_type = self.game_map.get_wall_type(target_x, target_y)
                return distance, wall_type, closest_bot

        return C.MAX_DEPTH, 0, None

    def cast_ray_with_bots(
        self,
        origin_x: float,
        origin_y: float,
        angle: float,
        player_angle: float,
        bots: List["Bot"],
    ) -> Tuple[float, int, Optional["Bot"]]:
        """Cast ray and detect bots"""
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        closest_bot = None
        closest_bot_dist = float("inf")

        # Check bots first
        for bot in bots:
            if not bot.alive:
                continue

            # Calculate bot relative position
            dx = bot.x - origin_x
            dy = bot.y - origin_y
            bot_dist = math.sqrt(dx**2 + dy**2)

            # Check if bot is in ray direction
            bot_angle = math.atan2(dy, dx)
            # Normalize angles to [0, 2π) range for comparison
            bot_angle_norm = bot_angle if bot_angle >= 0 else bot_angle + 2 * math.pi
            angle_norm = angle % (2 * math.pi)
            angle_diff = abs(bot_angle_norm - angle_norm)
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff

            # Bot hitbox
            if angle_diff < 0.1 and bot_dist < closest_bot_dist:
                closest_bot = bot
                closest_bot_dist = bot_dist

        # Cast ray for walls
        for depth in range(1, int(C.MAX_DEPTH * 100)):
            target_x = origin_x + depth * 0.01 * cos_a
            target_y = origin_y + depth * 0.01 * sin_a
            distance = depth * 0.01

            # Check if we hit a bot before the wall
            if closest_bot and distance > closest_bot_dist:
                # Fix fish-eye effect
                corrected_dist = closest_bot_dist * math.cos(player_angle - angle)
                return corrected_dist, -1, closest_bot

            if self.game_map.is_wall(target_x, target_y):
                wall_type = self.game_map.get_wall_type(target_x, target_y)
                corrected_dist = distance * math.cos(player_angle - angle)
                return corrected_dist, wall_type, None

        return C.MAX_DEPTH, 0, None

    def render_enemy_sprite(
        self,
        screen: pygame.Surface,
        bot: "Bot",
        sprite_x: int,
        sprite_y: int,
        sprite_size: float,
    ) -> None:
        """Render a detailed enemy sprite with head, body, legs, and arms"""
        center_x = sprite_x + sprite_size / 2
        body_width = sprite_size * 0.5
        body_height = sprite_size * 0.6
        head_size = sprite_size * 0.35
        leg_width = sprite_size * 0.12
        leg_height = sprite_size * 0.4
        arm_width = sprite_size * 0.1
        arm_height = sprite_size * 0.35

        type_data: Dict[str, Any] = bot.type_data
        base_color: Tuple[int, int, int] = type_data["color"]
        dark_color = tuple(max(0, c - 40) for c in base_color)
        leg_color = (30, 30, 30)

        # Walk animation
        leg_phase = math.sin(bot.walk_animation) * 0.3
        arm_swing = math.sin(bot.walk_animation + math.pi) * 0.2

        # Shoot animation
        shoot_offset = bot.shoot_animation * sprite_size * 0.15

        # Head
        head_y = sprite_y + sprite_size * 0.05
        pygame.draw.ellipse(
            screen,
            base_color,
            (center_x - head_size / 2, head_y, head_size, head_size),
        )

        # Eyes
        eye_size = head_size * 0.15
        eye_y = head_y + head_size * 0.3
        eye_spacing = head_size * 0.25
        pygame.draw.circle(screen, C.WHITE, (int(center_x - eye_spacing), int(eye_y)), int(eye_size))
        pygame.draw.circle(screen, C.WHITE, (int(center_x + eye_spacing), int(eye_y)), int(eye_size))
        pygame.draw.circle(
            screen,
            C.BLACK,
            (int(center_x - eye_spacing), int(eye_y)),
            int(eye_size * 0.6),
        )
        pygame.draw.circle(
            screen,
            C.BLACK,
            (int(center_x + eye_spacing), int(eye_y)),
            int(eye_size * 0.6),
        )

        # Body
        body_x = center_x - body_width / 2
        body_y = head_y + head_size * 0.7
        pygame.draw.rect(screen, base_color, (body_x, body_y, body_width, body_height))

        # Arms
        arm_y = body_y + body_height * 0.1
        # Left arm
        left_arm_x = body_x - arm_width + arm_swing * sprite_size
        pygame.draw.rect(screen, dark_color, (left_arm_x, arm_y, arm_width, arm_height))
        # Right arm (with shoot animation)
        right_arm_x = body_x + body_width - shoot_offset
        right_arm_y = arm_y + shoot_offset * 0.3
        pygame.draw.rect(screen, dark_color, (right_arm_x, right_arm_y, arm_width, arm_height))

        # Legs
        leg_y = body_y + body_height * 0.7
        # Left leg
        left_leg_x = center_x - body_width * 0.3 + leg_phase * sprite_size
        pygame.draw.rect(screen, leg_color, (left_leg_x, leg_y, leg_width, leg_height))
        # Right leg
        right_leg_x = center_x + body_width * 0.1 - leg_phase * sprite_size
        pygame.draw.rect(screen, leg_color, (right_leg_x, leg_y, leg_width, leg_height))

        # Muzzle flash when shooting
        if bot.shoot_animation > 0.5:
            flash_size = sprite_size * 0.2
            flash_x = right_arm_x + arm_width
            flash_y = right_arm_y + arm_height * 0.3
            pygame.draw.circle(screen, C.YELLOW, (int(flash_x), int(flash_y)), int(flash_size))
            pygame.draw.circle(screen, C.ORANGE, (int(flash_x), int(flash_y)), int(flash_size * 0.6))

    def render_3d(self, screen: pygame.Surface, player: "Player", bots: List["Bot"]) -> None:
        """Render 3D view using raycasting"""
        ray_angle = player.angle - C.HALF_FOV

        # Collect all bots to render as sprites
        bots_to_render = []
        for bot in bots:
            if not bot.alive:
                continue

            # Calculate bot position relative to player
            dx = bot.x - player.x
            dy = bot.y - player.y
            bot_dist = math.sqrt(dx**2 + dy**2)

            if bot_dist > C.MAX_DEPTH:
                continue

            # Calculate angle to bot
            bot_angle = math.atan2(dy, dx)
            angle_to_bot = bot_angle - player.angle

            # Normalize angle
            while angle_to_bot > math.pi:
                angle_to_bot -= 2 * math.pi
            while angle_to_bot < -math.pi:
                angle_to_bot += 2 * math.pi

            # Check if bot is in FOV
            if abs(angle_to_bot) < C.HALF_FOV + 0.2:
                # Check line of sight
                has_los = True
                steps = int(bot_dist * 10)
                for i in range(1, steps):
                    check_x = player.x + (dx * i / steps)
                    check_y = player.y + (dy * i / steps)
                    if self.game_map.is_wall(check_x, check_y):
                        has_los = False
                        break

                if has_los:
                    bots_to_render.append((bot, bot_dist, angle_to_bot))

        # Sort bots by distance (far to near)
        bots_to_render.sort(key=lambda x: x[1], reverse=True)

        for ray in range(C.NUM_RAYS):
            distance, wall_type, hit_bot = self.cast_ray_with_bots(
                player.x,
                player.y,
                ray_angle,
                player.angle,
                bots,
            )

            if hit_bot:
                # Skip bot rendering here - we'll render sprites separately
                continue

            if wall_type > 0:
                # Render wall with texture
                if distance > 0:
                    wall_height = min(C.SCREEN_HEIGHT, (C.SCREEN_HEIGHT / distance))
                else:
                    wall_height = C.SCREEN_HEIGHT

                base_color = C.WALL_COLORS.get(wall_type, C.GRAY)
                shade = max(0, 255 - int(distance * 25))
                color = tuple(min(255, max(0, c * shade // 255)) for c in base_color)

                wall_top = (C.SCREEN_HEIGHT - wall_height) // 2

                # Draw base wall color
                pygame.draw.rect(screen, color, (ray * 2, wall_top, 2, wall_height))

                # Add texture pattern based on wall type and position
                texture_pattern = (ray + int(distance * 10)) % 8
                if texture_pattern < 4:  # Add texture stripes
                    darker_color = tuple(max(0, c - 20) for c in color)
                    # Vertical stripes for texture
                    for stripe_y in range(int(wall_top), int(wall_top + wall_height), 4):
                        pygame.draw.line(
                            screen,
                            darker_color,
                            (ray * 2, stripe_y),
                            (ray * 2, min(stripe_y + 2, int(wall_top + wall_height))),
                            1,
                        )

                # Add horizontal texture lines
                if wall_type == 2 or wall_type == 3:  # Building walls get brick pattern
                    for brick_y in range(int(wall_top), int(wall_top + wall_height), 8):
                        darker_color = tuple(max(0, c - 15) for c in color)
                        pygame.draw.line(
                            screen,
                            darker_color,
                            (ray * 2, brick_y),
                            (ray * 2 + 2, brick_y),
                            1,
                        )

            ray_angle += C.DELTA_ANGLE

        # Render enemy sprites (after walls, far to near)
        for bot, bot_dist, angle_to_bot in bots_to_render:
            # Calculate sprite size based on distance and enemy scale
            base_sprite_size = C.SCREEN_HEIGHT / bot_dist if bot_dist > 0 else C.SCREEN_HEIGHT
            type_data: Dict[str, Any] = bot.type_data
            sprite_size = base_sprite_size * float(type_data.get("scale", 1.0))

            # Calculate sprite position on screen
            sprite_x = (
                C.SCREEN_WIDTH / 2 + (angle_to_bot / C.HALF_FOV) * C.SCREEN_WIDTH / 2 - sprite_size / 2
            )
            sprite_y = C.SCREEN_HEIGHT / 2 - sprite_size / 2

            # Apply distance shading
            distance_shade: float = max(0.4, 1.0 - bot_dist / C.MAX_DEPTH)

            # Create a temporary surface for the sprite
            sprite_surface = pygame.Surface(
                (int(sprite_size), int(sprite_size)),
                pygame.SRCALPHA,
            )
            self.render_enemy_sprite(sprite_surface, bot, 0, 0, sprite_size)

            # Apply shading by creating a dark overlay
            shade_surface = pygame.Surface((int(sprite_size), int(sprite_size)))
            shade_surface.fill(
                (
                    int(255 * distance_shade),
                    int(255 * distance_shade),
                    int(255 * distance_shade),
                ),
            )
            sprite_surface.blit(shade_surface, (0, 0), special_flags=pygame.BLEND_MULT)

            # Blit sprite to screen
            screen.blit(sprite_surface, (int(sprite_x), int(sprite_y)))

    def render_floor_ceiling(self, screen: pygame.Surface) -> None:
        """Render floor and ceiling"""
        pygame.draw.rect(
            screen,
            C.DARK_GRAY,
            (0, C.SCREEN_HEIGHT // 2, C.SCREEN_WIDTH, C.SCREEN_HEIGHT // 2),
        )
        pygame.draw.rect(screen, C.BLACK, (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT // 2))

    def render_minimap(
        self,
        screen: pygame.Surface,
        player: "Player",
        bots: List["Bot"],
    ) -> None:
        """Render 2D minimap"""
        minimap_size = 200
        map_size = self.game_map.size
        minimap_scale = minimap_size / map_size
        minimap_x = C.SCREEN_WIDTH - minimap_size - 20
        minimap_y = 20

        # Draw minimap background
        pygame.draw.rect(
            screen,
            C.BLACK,
            (minimap_x - 2, minimap_y - 2, minimap_size + 4, minimap_size + 4),
        )
        pygame.draw.rect(screen, C.DARK_GRAY, (minimap_x, minimap_y, minimap_size, minimap_size))

        # Draw walls
        for i in range(map_size):
            for j in range(map_size):
                if self.game_map.grid[i][j] != 0:
                    wall_type = self.game_map.grid[i][j]
                    color = C.WALL_COLORS.get(wall_type, C.WHITE)
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

        # Draw bots
        for bot in bots:
            if bot.alive:
                bot_x = minimap_x + bot.x * minimap_scale
                bot_y = minimap_y + bot.y * minimap_scale
                pygame.draw.circle(screen, C.RED, (int(bot_x), int(bot_y)), 3)

        # Draw player
        player_x = minimap_x + player.x * minimap_scale
        player_y = minimap_y + player.y * minimap_scale
        pygame.draw.circle(screen, C.GREEN, (int(player_x), int(player_y)), 3)

        # Draw direction
        dir_x = player_x + math.cos(player.angle) * 10
        dir_y = player_y + math.sin(player.angle) * 10
        pygame.draw.line(screen, C.GREEN, (player_x, player_y), (dir_x, dir_y), 2)

    def render_projectiles(self, screen: pygame.Surface, player: "Player", projectiles: List["Projectile"]) -> None:
        """Render bot projectiles"""
        for projectile in projectiles:
            if not projectile.alive:
                continue

            # Calculate projectile position relative to player
            dx = projectile.x - player.x
            dy = projectile.y - player.y
            proj_dist = math.sqrt(dx**2 + dy**2)

            if proj_dist > C.MAX_DEPTH:
                continue

            # Calculate angle to projectile
            proj_angle = math.atan2(dy, dx)
            angle_to_proj = proj_angle - player.angle

            # Normalize angle
            while angle_to_proj > math.pi:
                angle_to_proj -= 2 * math.pi
            while angle_to_proj < -math.pi:
                angle_to_proj += 2 * math.pi

            # Check if projectile is in FOV
            if abs(angle_to_proj) < C.HALF_FOV:
                # Calculate screen position
                proj_size = max(2, 10 / proj_dist) if proj_dist > 0 else 10
                proj_x = C.SCREEN_WIDTH / 2 + (angle_to_proj / C.HALF_FOV) * C.SCREEN_WIDTH / 2
                proj_y = C.SCREEN_HEIGHT / 2

                # Draw projectile as a glowing circle
                pygame.draw.circle(screen, C.RED, (int(proj_x), int(proj_y)), int(proj_size))
                pygame.draw.circle(
                    screen,
                    C.ORANGE,
                    (int(proj_x), int(proj_y)),
                    int(proj_size * 0.6),
                )
