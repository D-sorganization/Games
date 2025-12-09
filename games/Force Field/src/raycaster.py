from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, cast

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

        wall_dist: float = float(C.MAX_DEPTH)

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
        """Render sprite based on visual style"""
        center_x = sprite_x + sprite_size / 2
        type_data: Dict[str, Any] = bot.type_data
        base_color = type_data["color"]
        visual_style = type_data.get("visual_style", "monster")

        # Health Pack
        if bot.enemy_type == "health_pack":
            rect_w = sprite_size * 0.4
            rect_h = sprite_size * 0.3
            kit_y = sprite_y + sprite_size * 0.7
            pygame.draw.rect(
                screen,
                (220, 220, 220),
                (center_x - rect_w / 2, kit_y, rect_w, rect_h),
                border_radius=4,
            )
            cross_thick = rect_w * 0.2
            pygame.draw.rect(
                screen,
                (200, 0, 0),
                (center_x - cross_thick / 2, kit_y + 5, cross_thick, rect_h - 10),
            )
            pygame.draw.rect(
                screen,
                (200, 0, 0),
                (
                    center_x - rect_w / 2 + 5,
                    kit_y + rect_h / 2 - cross_thick / 2,
                    rect_w - 10,
                    cross_thick,
                ),
            )
            return

        render_height = sprite_size
        render_width = sprite_size * 0.55 if visual_style == "monster" else sprite_size * 0.7
        render_y = sprite_y

        if bot.dead:
            # Melting animation
            melt_pct = min(1.0, bot.death_timer / 60.0)

            # Interpolate Color to Goo
            goo_color = (50, 150, 50)
            base_color = tuple(
                int(c * (1 - melt_pct) + g * melt_pct) for c, g in zip(base_color, goo_color)
            )

            # Squish
            scale_y = 1.0 - (melt_pct * 0.85)
            scale_x = 1.0 + (melt_pct * 0.8)

            current_h = render_height * scale_y
            current_w = render_width * scale_x

            render_y = int(sprite_y + (render_height - current_h) + (render_height * 0.05))
            render_height = int(current_h)
            render_width = int(current_w)

            if bot.disintegrate_timer > 0:
                dis_pct = bot.disintegrate_timer / 100.0
                radius_mult = 1.0 - dis_pct
                if radius_mult <= 0:
                    return
                pygame.draw.ellipse(
                    screen,
                    base_color,
                    (
                        center_x - render_width / 2 * radius_mult,
                        render_y + render_height - 10,
                        render_width * radius_mult,
                        20 * radius_mult,
                    ),
                )
                return

        if visual_style == "baby":
            # Render Baby Style (Round, Big Head, Cute/Creepy)
            # Body
            body_rect = pygame.Rect(
                int(center_x - render_width / 2),
                int(render_y + render_height * 0.4),
                int(render_width),
                int(render_height * 0.6),
            )
            pygame.draw.rect(screen, base_color, body_rect, border_radius=int(render_width * 0.4))

            # Head (Floating slightly above)
            head_size = render_width
            head_y = render_y
            pygame.draw.circle(
                screen, base_color, (center_x, head_y + head_size / 2), head_size / 2
            )

            # Face
            eye_r = head_size * 0.15
            pygame.draw.circle(
                screen,
                C.WHITE,
                (center_x - head_size * 0.2, head_y + head_size * 0.4),
                eye_r,
            )
            pygame.draw.circle(
                screen,
                C.WHITE,
                (center_x + head_size * 0.2, head_y + head_size * 0.4),
                eye_r,
            )

            # Pupils - dilated
            pygame.draw.circle(
                screen,
                C.BLACK,
                (center_x - head_size * 0.2, head_y + head_size * 0.4),
                eye_r * 0.6,
            )
            pygame.draw.circle(
                screen,
                C.BLACK,
                (center_x + head_size * 0.2, head_y + head_size * 0.4),
                eye_r * 0.6,
            )

            # Mouth
            if bot.mouth_open:
                pygame.draw.circle(
                    screen,
                    (50, 0, 0),
                    (center_x, head_y + head_size * 0.75),
                    head_size * 0.1,
                )
            else:
                # Small flat mouth
                pygame.draw.line(
                    screen,
                    (50, 0, 0),
                    (center_x - 5, head_y + head_size * 0.75),
                    (center_x + 5, head_y + head_size * 0.75),
                    2,
                )
            return

        # Monster Style (Detailed, Textured)
        body_x = center_x - render_width / 2

        # 1. Body (Rounded Torso)
        # Use ellipse for more organic look
        torso_rect = pygame.Rect(
            int(body_x),
            int(render_y + render_height * 0.25),
            int(render_width),
            int(render_height * 0.5),
        )
        # Draw torso
        pygame.draw.ellipse(screen, base_color, torso_rect)

        # Muscle definition (Shadows)
        dark_color = tuple(max(0, c - 40) for c in base_color)
        light_color = tuple(min(255, c + 30) for c in base_color)

        # Highlight top
        pygame.draw.ellipse(
            screen,
            light_color,
            (
                body_x + render_width * 0.2,
                render_y + render_height * 0.25,
                render_width * 0.6,
                render_height * 0.2,
            ),
        )

        # Ribs/Abs
        dark_color = tuple(max(0, c - 50) for c in base_color)
        for i in range(3):
            y_off = render_y + render_height * (0.35 + i * 0.1)
            pygame.draw.line(
                screen,
                dark_color,
                (body_x + 5, y_off),
                (body_x + render_width - 5, y_off),
                2,
            )

        # 2. Head
        if not bot.dead or bot.death_timer < 30:
            head_size = int(render_width * 0.6)
            head_y = int(render_y + render_height * 0.05)
            head_rect = pygame.Rect(center_x - head_size // 2, head_y, head_size, head_size)
            pygame.draw.rect(screen, base_color, head_rect)

            # Glowing Eyes
            eye_color = (255, 50, 0)
            if bot.enemy_type == "boss":
                eye_color = (255, 255, 0)

            # Angry Eyes
            pygame.draw.polygon(
                screen,
                eye_color,
                [
                    (center_x - head_size * 0.3, head_y + head_size * 0.3),
                    (center_x - head_size * 0.1, head_y + head_size * 0.3),
                    (center_x - head_size * 0.2, head_y + head_size * 0.45),
                ],
            )
            pygame.draw.polygon(
                screen,
                eye_color,
                [
                    (center_x + head_size * 0.3, head_y + head_size * 0.3),
                    (center_x + head_size * 0.1, head_y + head_size * 0.3),
                    (center_x + head_size * 0.2, head_y + head_size * 0.45),
                ],
            )

            # Mouth
            mouth_y = head_y + head_size * 0.65
            mouth_w = head_size * 0.6
            if bot.mouth_open:
                pygame.draw.rect(
                    screen,
                    (50, 0, 0),
                    (center_x - mouth_w / 2, mouth_y, mouth_w, head_size * 0.3),
                )
                # Teeth
                pygame.draw.line(
                    screen,
                    C.WHITE,
                    (center_x - mouth_w / 2, mouth_y),
                    (center_x - mouth_w / 4, mouth_y + 5),
                    2,
                )
                pygame.draw.line(
                    screen,
                    C.WHITE,
                    (center_x - mouth_w / 4, mouth_y + 5),
                    (center_x, mouth_y),
                    2,
                )
                pygame.draw.line(
                    screen,
                    C.WHITE,
                    (center_x, mouth_y),
                    (center_x + mouth_w / 4, mouth_y + 5),
                    2,
                )
                pygame.draw.line(
                    screen,
                    C.WHITE,
                    (center_x + mouth_w / 4, mouth_y + 5),
                    (center_x + mouth_w / 2, mouth_y),
                    2,
                )
            else:
                pygame.draw.line(
                    screen,
                    (200, 200, 200),
                    (center_x - mouth_w / 2, mouth_y + 5),
                    (center_x + mouth_w / 2, mouth_y + 5),
                    3,
                )
                for i in range(4):
                    x_off = center_x - mouth_w / 2 + (i + 1) * (mouth_w / 5)
                    pygame.draw.line(screen, (50, 0, 0), (x_off, mouth_y), (x_off, mouth_y + 10), 1)

        # 3. Arms
        if not bot.dead:
            arm_y = render_y + render_height * 0.3
            # Left
            pygame.draw.line(screen, base_color, (body_x, arm_y + 10), (body_x - 15, arm_y + 30), 6)
            pygame.draw.polygon(
                screen,
                (200, 200, 200),
                [
                    (body_x - 15, arm_y + 30),
                    (body_x - 20, arm_y + 40),
                    (body_x - 5, arm_y + 35),
                ],
            )
            # Right
            weapon_x = body_x + render_width
            pygame.draw.line(
                screen,
                base_color,
                (weapon_x, arm_y + 10),
                (weapon_x + 15, arm_y + 30),
                6,
            )
            pygame.draw.rect(screen, (30, 30, 30), (weapon_x + 10, arm_y + 25, 25, 10))
            if bot.shoot_animation > 0.5:
                pygame.draw.circle(
                    screen,
                    C.YELLOW,
                    (weapon_x + 35, arm_y + 30),
                    8 + random.randint(0, 4),
                )
                pygame.draw.circle(screen, C.WHITE, (weapon_x + 35, arm_y + 30), 4)

        # 4. Legs
        if not bot.dead:
            leg_w = render_width * 0.3
            leg_h = render_height * 0.25
            leg_y = render_y + render_height * 0.75
            pygame.draw.rect(screen, base_color, (body_x + 5, leg_y, leg_w, leg_h))
            pygame.draw.rect(
                screen,
                base_color,
                (body_x + render_width - 5 - leg_w, leg_y, leg_w, leg_h),
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
        wall_colors = cast("Dict[int, Tuple[int, int, int]]", theme["walls"])

        # Collect all bots to render as sprites
        bots_to_render = []
        for bot in bots:
            if bot.removed:
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

        # Z-Buffer to track wall distance per screen column
        z_buffer = [float("inf")] * C.SCREEN_WIDTH

        for ray in range(C.NUM_RAYS):
            distance, wall_type, hit_bot = self.cast_ray_with_bots(
                player.x,
                player.y,
                ray_angle,
                player.angle,
                bots,
            )

            # Update Z-Buffer for this ray's columns

            # Map ray to screen columns
            col_start = ray * 2
            col_end = min(col_start + 2, C.SCREEN_WIDTH)
            for col in range(col_start, col_end):
                z_buffer[col] = distance

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

                # Fog Logic
                fog_factor = max(
                    0.0,
                    min(
                        1.0,
                        (distance - C.MAX_DEPTH * C.FOG_START) / (C.MAX_DEPTH * (1 - C.FOG_START)),
                    ),
                )

                # Local lighting (Shade)
                shade = max(0.4, 1.0 - distance / 20.0)

                lit_r = base_color[0] * shade
                lit_g = base_color[1] * shade
                lit_b = base_color[2] * shade

                # Mix with Fog
                final_r = lit_r * (1 - fog_factor) + C.FOG_COLOR[0] * fog_factor
                final_g = lit_g * (1 - fog_factor) + C.FOG_COLOR[1] * fog_factor
                final_b = lit_b * (1 - fog_factor) + C.FOG_COLOR[2] * fog_factor

                color = (int(final_r), int(final_g), int(final_b))

                # Pitch Adjustment
                wall_top = (C.SCREEN_HEIGHT - wall_height) // 2 + player.pitch

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
        # Note: We still sort far-to-near to handle sprite-on-sprite overlap correctly
        # But we use z_buffer to handle sprite-behind-wall occlusion.
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
            sprite_y = C.SCREEN_HEIGHT / 2 - sprite_size / 2 + player.pitch

            # Optimization: If sprite is off screen, skip
            if sprite_x + sprite_size < 0 or sprite_x > C.SCREEN_WIDTH:
                continue

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

            # Column-based rendering for proper occlusion
            start_x = int(sprite_x)
            end_x = int(sprite_x + sprite_size)

            # Optimization: Pre-calculate scaling
            tex_width = sprite_surface.get_width()
            tex_height = sprite_surface.get_height()

            # Iterate through screen columns covered by sprite
            for x in range(start_x, end_x):
                # Bounds check
                if x < 0 or x >= C.SCREEN_WIDTH:
                    continue

                # Z-Buffer check
                if bot_dist >= z_buffer[x]:
                    continue

                # Calculate corresponding column in sprite texture
                tex_x = int(x - start_x)
                if tex_x < 0 or tex_x >= tex_width:
                    continue

                # Blit this 1-pixel wide strip
                area = pygame.Rect(tex_x, 0, 1, tex_height)
                screen.blit(sprite_surface, (x, int(sprite_y)), area=area)

    def render_floor_ceiling(self, screen: pygame.Surface, player: Player, level: int) -> None:
        """Render floor and sky with stars"""
        theme_idx = (level - 1) % len(C.LEVEL_THEMES)
        theme = C.LEVEL_THEMES[theme_idx]
        player_angle = player.angle

        horizon = C.SCREEN_HEIGHT // 2 + int(player.pitch)

        # Sky/Ceiling
        ceiling_color = cast("Tuple[int, int, int]", theme["ceiling"])
        pygame.draw.rect(screen, ceiling_color, (0, 0, C.SCREEN_WIDTH, horizon))

        # Draw stars (randomized but consistent)
        # Use player angle to offset stars for parallax effect
        star_offset = int(player_angle * 200) % C.SCREEN_WIDTH

        for sx, sy, size, color in self.stars:
            # Parallax x
            x = (sx + star_offset) % C.SCREEN_WIDTH
            # Parallax y (move with pitch)
            y = sy + player.pitch

            if 0 <= y < horizon:
                pygame.draw.circle(screen, color, (x, int(y)), int(size))

        # Draw Moon
        moon_x = (C.SCREEN_WIDTH - 200 - int(player_angle * 100)) % (
            C.SCREEN_WIDTH * 2
        ) - C.SCREEN_WIDTH // 2
        moon_y = 100 + int(player.pitch)

        if -100 < moon_x < C.SCREEN_WIDTH + 100:
            if 0 <= moon_y < horizon + 40:  # Check visibility
                pygame.draw.circle(screen, (220, 220, 200), (int(moon_x), moon_y), 40)
                pygame.draw.circle(
                    screen, ceiling_color, (int(moon_x) - 10, moon_y), 40
                )  # Crescent, match sky color

        # Floor
        floor_color = cast("Tuple[int, int, int]", theme["floor"])
        pygame.draw.rect(
            screen,
            floor_color,
            (0, horizon, C.SCREEN_WIDTH, C.SCREEN_HEIGHT - horizon),
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
                proj_y = C.SCREEN_HEIGHT / 2 + player.pitch

                # Draw projectile as a glowing circle
                pygame.draw.circle(screen, C.RED, (int(proj_x), int(proj_y)), int(proj_size))
                pygame.draw.circle(
                    screen,
                    C.ORANGE,
                    (int(proj_x), int(proj_y)),
                    int(proj_size * 0.6),
                )
