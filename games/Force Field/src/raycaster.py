from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

import pygame

from . import constants as C  # noqa: N812

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

    def cast_ray(
        self,
        origin_x: float,
        origin_y: float,
        angle: float,
    ) -> Tuple[float, int, Bot | None]:
        """Cast a single ray using DDA"""
        ray_dir_x = math.cos(angle)
        ray_dir_y = math.sin(angle)

        map_x = int(origin_x)
        map_y = int(origin_y)

        delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
        delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30

        step_x = 1 if ray_dir_x >= 0 else -1
        side_dist_x = (
            (map_x + 1.0 - origin_x) * delta_dist_x
            if ray_dir_x >= 0
            else (origin_x - map_x) * delta_dist_x
        )

        step_y = 1 if ray_dir_y >= 0 else -1
        side_dist_y = (
            (map_y + 1.0 - origin_y) * delta_dist_y
            if ray_dir_y >= 0
            else (origin_y - map_y) * delta_dist_y
        )

        hit = False
        side = 0  # 0 for NS, 1 for EW
        wall_type = 0

        # Max depth check to prevent infinite loop
        # We can approximate max steps by MAX_DEPTH magnitude
        max_steps = int(C.MAX_DEPTH * 1.5)
        for _ in range(max_steps):
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1

            # Check if wall hit
            if self.game_map.is_wall(map_x, map_y):
                hit = True
                wall_type = self.game_map.get_wall_type(map_x, map_y)
                break

        if hit:
            distance = side_dist_x - delta_dist_x if side == 0 else side_dist_y - delta_dist_y
            return distance, wall_type, None

        return C.MAX_DEPTH, 0, None

    def cast_ray_with_bots(
        self,
        origin_x: float,
        origin_y: float,
        angle: float,
        player_angle: float,
        bots: List[Bot],
    ) -> Tuple[float, int, Bot | None]:
        """Cast ray using DDA and detect bots"""
        # Bot detection (keep existing logic or improve? Existing is simple geometric check)
        closest_bot = None
        closest_bot_dist = float("inf")

        # Check bots first (geometric check independent of grid)
        # This allows seeing bots even if they are not exactly on a grid line being stepped
        for bot in bots:
            if not bot.alive:
                continue

            dx = bot.x - origin_x
            dy = bot.y - origin_y
            bot_dist = math.sqrt(dx**2 + dy**2)

            bot_angle = math.atan2(dy, dx)
            bot_angle_norm = bot_angle if bot_angle >= 0 else bot_angle + 2 * math.pi
            angle_norm = angle % (2 * math.pi)
            angle_diff = abs(bot_angle_norm - angle_norm)
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff

            # Bot hitbox - slightly generous for ray detection
            if angle_diff < 0.05 and bot_dist < closest_bot_dist:
                closest_bot = bot
                closest_bot_dist = bot_dist

        # Now cast ray for walls using DDA
        ray_dir_x = math.cos(angle)
        ray_dir_y = math.sin(angle)

        map_x = int(origin_x)
        map_y = int(origin_y)

        delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
        delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30

        step_x = 1 if ray_dir_x >= 0 else -1
        side_dist_x = (
            (map_x + 1.0 - origin_x) * delta_dist_x
            if ray_dir_x >= 0
            else (origin_x - map_x) * delta_dist_x
        )

        step_y = 1 if ray_dir_y >= 0 else -1
        side_dist_y = (
            (map_y + 1.0 - origin_y) * delta_dist_y
            if ray_dir_y >= 0
            else (origin_y - map_y) * delta_dist_y
        )

        hit = False
        side = 0
        wall_type = 0

        max_steps = int(C.MAX_DEPTH * 1.5)

        wall_dist = C.MAX_DEPTH

        for _ in range(max_steps):
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1

            if self.game_map.is_wall(map_x, map_y):
                hit = True
                wall_type = self.game_map.get_wall_type(map_x, map_y)
                break

        if hit:
            wall_dist = side_dist_x - delta_dist_x if side == 0 else side_dist_y - delta_dist_y

            # Fisheye correction for wall
            corrected_wall_dist = wall_dist * math.cos(player_angle - angle)

            # Check if bot is closer than wall
            if closest_bot and closest_bot_dist < wall_dist:
                corrected_bot_dist = closest_bot_dist * math.cos(player_angle - angle)
                return corrected_bot_dist, -1, closest_bot

            return corrected_wall_dist, wall_type, None

        # No wall hit, but maybe bot?
        if closest_bot and closest_bot_dist < C.MAX_DEPTH:
            corrected_bot_dist = closest_bot_dist * math.cos(player_angle - angle)
            return corrected_bot_dist, -1, closest_bot

        return C.MAX_DEPTH, 0, None

    def render_enemy_sprite(
        self,
        screen: pygame.Surface,
        bot: Bot,
        sprite_x: int,
        sprite_y: int,
        sprite_size: float,
    ) -> None:
        """Render a detailed enemy sprite with shape relative to type (Doom Style)"""
        center_x = sprite_x + sprite_size / 2

        type_data: Dict[str, Any] = bot.type_data
        base_color: Tuple[int, int, int] = type_data["color"]

        if bot.enemy_type == "health_pack":
            # Draw Green Cross
            rect_w = sprite_size * 0.2
            rect_h = sprite_size * 0.6
            pygame.draw.rect(
                screen,
                base_color,
                (center_x - rect_w / 2, sprite_y + sprite_size * 0.2, rect_w, rect_h),
            )
            pygame.draw.rect(
                screen,
                base_color,
                (center_x - rect_h / 2, sprite_y + sprite_size * 0.4, rect_h, rect_w),
            )
            return

        # Doom-style Procedural Drawing parameters
        body_width = sprite_size * 0.6
        body_height = sprite_size
        head_size = sprite_size * 0.4

        body_x = center_x - body_width / 2
        body_y = sprite_y + sprite_size * 0.05

        # 1. Body
        # Main torso
        pygame.draw.rect(
            screen, base_color, (body_x, body_y + head_size * 0.8, body_width, body_height * 0.6)
        )

        # Pants/Belt (Dark Brown/Black)
        pygame.draw.rect(
            screen,
            (42, 28, 28),
            (body_x, body_y + body_height * 0.65, body_width, body_height * 0.1),
        )

        # 2. Head (Gray Box)
        pygame.draw.rect(
            screen, (217, 217, 217), (center_x - head_size / 2, body_y, head_size, head_size)
        )

        # 3. Eyes with spinning pupils
        eye_radius = head_size * 0.12
        pupil_radius = eye_radius * 0.6
        eye_y_offset = head_size * 0.25
        eye_spacing = head_size * 0.18

        # White parts of the eye
        pygame.draw.circle(
            screen,
            (255, 255, 255),
            (int(center_x - eye_spacing), int(body_y + eye_y_offset)),
            int(eye_radius),
        )
        pygame.draw.circle(
            screen,
            (255, 255, 255),
            (int(center_x + eye_spacing), int(body_y + eye_y_offset)),
            int(eye_radius),
        )

        # Spinning black pupils
        pupil_angle = bot.eye_rotation
        pupil_offset = eye_radius * 0.4
        pupil_x_off = math.cos(pupil_angle) * pupil_offset
        pupil_y_off = math.sin(pupil_angle) * pupil_offset

        pygame.draw.circle(
            screen,
            (34, 34, 34),
            (int(center_x - eye_spacing + pupil_x_off), int(body_y + eye_y_offset + pupil_y_off)),
            int(pupil_radius),
        )
        pygame.draw.circle(
            screen,
            (34, 34, 34),
            (int(center_x + eye_spacing + pupil_x_off), int(body_y + eye_y_offset + pupil_y_off)),
            int(pupil_radius),
        )

        # 4. Mouth Animation
        mouth_width = head_size * 0.7
        mouth_height = head_size * 0.3 if bot.mouth_open else head_size * 0.12
        mouth_x = center_x - mouth_width / 2
        mouth_y = body_y + head_size * 0.65

        # Mouth Interior (Red)
        pygame.draw.rect(screen, (180, 42, 42), (mouth_x, mouth_y, mouth_width, mouth_height))

        # White teeth details
        tooth_width = mouth_width / 6
        tooth_height = mouth_height * 0.6
        for i in range(6):
            pygame.draw.rect(
                screen,
                (238, 238, 238),
                (mouth_x + i * tooth_width, mouth_y, tooth_width * 0.6, tooth_height),
            )

        # 5. Drool (Blue Lines)
        drool_color = (126, 214, 255)
        drool_len = mouth_height * 1.2 + (bot.drool_offset % 10)

        # Left Drool
        pygame.draw.line(
            screen,
            drool_color,
            (mouth_x + mouth_width * 0.1, mouth_y + mouth_height),
            (mouth_x + mouth_width * 0.1, mouth_y + mouth_height + drool_len),
            max(2, int(sprite_size * 0.01)),
        )
        # Right Drool
        pygame.draw.line(
            screen,
            drool_color,
            (mouth_x + mouth_width * 0.9, mouth_y + mouth_height),
            (mouth_x + mouth_width * 0.9, mouth_y + mouth_height + drool_len * 0.8),
            max(2, int(sprite_size * 0.01)),
        )

        # Weapon / Arm (Preserved from original logic but adjusted)
        arm_y = body_y + body_height * 0.2
        shoot_offset = bot.shoot_animation * 10
        pygame.draw.rect(
            screen,
            (20, 20, 20),
            (center_x + body_width / 2, arm_y, sprite_size * 0.4 - shoot_offset, sprite_size * 0.1),
        )

        # Muzzle flash
        if bot.shoot_animation > 0.5:
            pygame.draw.circle(
                screen,
                C.YELLOW,
                (int(center_x + body_width / 2 + sprite_size * 0.4), int(arm_y)),
                int(sprite_size * 0.2),
            )

    def render_3d(
        self, screen: pygame.Surface, player: Player, bots: List[Bot], level: int
    ) -> None:
        """Render 3D view using raycasting"""
        current_fov = C.FOV * (C.ZOOM_FOV_MULT if player.zoomed else 1.0)
        half_fov = current_fov / 2
        delta_angle = current_fov / C.NUM_RAYS

        ray_angle = player.angle - half_fov

        # Select theme
        theme_idx = (level - 1) % len(C.LEVEL_THEMES)
        theme = C.LEVEL_THEMES[theme_idx]
        wall_colors = theme["walls"]

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
            if abs(angle_to_bot) < half_fov + 0.2:
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

                base_color = wall_colors.get(wall_type, C.GRAY)
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

            ray_angle += delta_angle

        # Render enemy sprites (after walls, far to near)
        for bot, bot_dist, angle_to_bot in bots_to_render:
            # Calculate sprite size based on distance and enemy scale
            base_sprite_size = C.SCREEN_HEIGHT / bot_dist if bot_dist > 0 else C.SCREEN_HEIGHT
            type_data: Dict[str, Any] = bot.type_data
            sprite_size = base_sprite_size * float(type_data.get("scale", 1.0))

            # Calculate sprite position on screen
            sprite_x = (
                C.SCREEN_WIDTH / 2
                + (angle_to_bot / half_fov) * C.SCREEN_WIDTH / 2
                - sprite_size / 2
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

    def render_floor_ceiling(self, screen: pygame.Surface, player_angle: float, level: int) -> None:
        """Render floor and sky with stars"""
        theme_idx = (level - 1) % len(C.LEVEL_THEMES)
        theme = C.LEVEL_THEMES[theme_idx]

        # Sky/Ceiling
        ceiling_color = theme["ceiling"]
        pygame.draw.rect(screen, ceiling_color, (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT // 2))

        # Draw stars (randomized but consistent)
        # Use player angle to offset stars for parallax effect
        star_offset = int(player_angle * 200) % C.SCREEN_WIDTH

        for sx, sy, size, color in self.stars:
            # Parallax x
            x = (sx + star_offset) % C.SCREEN_WIDTH
            pygame.draw.circle(screen, color, (x, sy), int(size))

        # Draw Moon
        moon_x = (C.SCREEN_WIDTH - 200 - int(player_angle * 100)) % (
            C.SCREEN_WIDTH * 2
        ) - C.SCREEN_WIDTH // 2
        if -100 < moon_x < C.SCREEN_WIDTH + 100:
            pygame.draw.circle(screen, (220, 220, 200), (int(moon_x), 100), 40)
            pygame.draw.circle(
                screen, ceiling_color, (int(moon_x) - 10, 100), 40
            )  # Crescent, match sky color

        # Floor
        floor_color = theme["floor"]
        pygame.draw.rect(
            screen,
            floor_color,
            (0, C.SCREEN_HEIGHT // 2, C.SCREEN_WIDTH, C.SCREEN_HEIGHT // 2),
        )

    def render_minimap(
        self,
        screen: pygame.Surface,
        player: Player,
        bots: List[Bot],
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

    def render_projectiles(
        self, screen: pygame.Surface, player: Player, projectiles: List[Projectile]
    ) -> None:
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
