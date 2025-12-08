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
        """Render a detailed enemy sprite with shape relative to type (Doom Style) - Hi-Res"""
        center_x = sprite_x + sprite_size / 2
        
        type_data: Dict[str, Any] = bot.type_data
        base_color: Tuple[int, int, int] = type_data["color"]

        # Health Pack
        if bot.enemy_type == "health_pack":
            # Draw Detailed Medkit
            rect_w = sprite_size * 0.4
            rect_h = sprite_size * 0.3
            kit_y = sprite_y + sprite_size * 0.7
            
            # Box
            pygame.draw.rect(screen, (220, 220, 220), (center_x - rect_w/2, kit_y, rect_w, rect_h), border_radius=4)
            # Red Cross
            cross_thick = rect_w * 0.2
            pygame.draw.rect(screen, (200, 0, 0), (center_x - cross_thick/2, kit_y + 5, cross_thick, rect_h - 10))
            pygame.draw.rect(screen, (200, 0, 0), (center_x - rect_w/2 + 5, kit_y + rect_h/2 - cross_thick/2, rect_w - 10, cross_thick))
            return

        # Death / Goo Logic
        render_height = sprite_size
        render_width = sprite_size * 0.6
        render_y = sprite_y
        
        if bot.dead:
            # Melting animation
            melt_pct = min(1.0, bot.death_timer / 60.0)
            
            # Interpolate Color to Goo (Greenish Slime)
            goo_color = (50, 150, 50)
            base_color = tuple(
                int(c * (1 - melt_pct) + g * melt_pct) 
                for c, g in zip(base_color, goo_color)
            )
            
            # Squish
            scale_y = 1.0 - (melt_pct * 0.85) # Squash to 15% height
            scale_x = 1.0 + (melt_pct * 0.8)  # Widen to 180%
            
            current_h = render_height * scale_y
            current_w = render_width * scale_x
            
            # Align bottom
            render_y = sprite_y + (render_height - current_h) + (render_height * 0.05)
            render_height = current_h
            render_width = current_w
            
            if bot.disintegrate_timer > 0:
                # Fade out / Shrink puddle
                dis_pct = bot.disintegrate_timer / 100.0
                radius_mult = 1.0 - dis_pct
                if radius_mult <= 0:
                    return
                # Render just a puddle circle
                pygame.draw.ellipse(screen, base_color, (
                    center_x - render_width/2 * radius_mult, 
                    render_y + render_height - 10, 
                    render_width * radius_mult, 
                    20 * radius_mult
                ))
                return

        body_x = center_x - render_width / 2
        
        # High-Res Procedural Drawing
        
        # 1. Body (Rounded Rectangle)
        body_rect = pygame.Rect(body_x, render_y + render_height * 0.1, render_width, render_height * 0.6)
        pygame.draw.rect(screen, base_color, body_rect, border_radius=int(render_width*0.2))
        
        # Shading/Gradient effect (simple inset)
        pygame.draw.rect(screen, tuple(max(0, c-40) for c in base_color), body_rect.inflate(-4, -4), width=2, border_radius=int(render_width*0.2))

        # 2. Head
        if not bot.dead or bot.death_timer < 30: # Head disappears into body when melting
            head_size = render_width * 0.7
            head_y = render_y
            pygame.draw.rect(screen, (200, 200, 200), (center_x - head_size/2, head_y, head_size, head_size), border_radius=int(head_size*0.2))
            
            # Eyes (High Def)
            eye_r = head_size * 0.15
            pygame.draw.circle(screen, C.WHITE, (center_x - head_size*0.25, head_y + head_size*0.4), eye_r)
            pygame.draw.circle(screen, C.WHITE, (center_x + head_size*0.25, head_y + head_size*0.4), eye_r)
            
            # Pupils (Spinning)
            pupil_r = eye_r * 0.5
            px = math.cos(bot.eye_rotation) * (eye_r * 0.4)
            py = math.sin(bot.eye_rotation) * (eye_r * 0.4)
            pygame.draw.circle(screen, C.BLACK, (center_x - head_size*0.25 + px, head_y + head_size*0.4 + py), pupil_r)
            pygame.draw.circle(screen, C.BLACK, (center_x + head_size*0.25 + px, head_y + head_size*0.4 + py), pupil_r)
            
            # Mouth
            mouth_w = head_size * 0.6
            mouth_h = head_size * 0.25 if bot.mouth_open else head_size * 0.05
            pygame.draw.rect(screen, (150, 0, 0), (center_x - mouth_w/2, head_y + head_size*0.7, mouth_w, mouth_h), border_radius=2)
            
            # Drool
            if bot.mouth_open:
                 drool_len = math.sin(bot.drool_offset)*5 + 10
                 pygame.draw.line(screen, C.CYAN, (center_x - mouth_w*0.3, head_y + head_size*0.7 + mouth_h), (center_x - mouth_w*0.3, head_y + head_size*0.7 + mouth_h + drool_len), 2)

        # 3. Arms / Weapon
        if not bot.dead:
            arm_y = render_y + render_height * 0.35
            # Left Arm
            pygame.draw.polygon(screen, base_color, [
                (body_x, arm_y), (body_x - 10, arm_y + 20), (body_x + 5, arm_y + 20)
            ])
            # Right Arm (Weapon)
            weapon_x = body_x + render_width
            pygame.draw.line(screen, (10,10,10), (weapon_x - 5, arm_y), (weapon_x + 20, arm_y + 5), 8)
            
            # Shoot Flash
            if bot.shoot_animation > 0.5:
                 pygame.draw.circle(screen, C.YELLOW, (weapon_x + 25, arm_y + 5), 10 + random.randint(0, 5))

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
