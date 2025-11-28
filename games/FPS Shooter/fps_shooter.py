#!/usr/bin/env python3
"""
First-Person Shooter Game
A raycasting-based FPS game with a 90x90 map featuring walls, buildings, and bot enemies.
Uses WASD for movement, mouse for looking, and left-click to shoot.
Fight waves of increasingly difficult bots across multiple levels!
"""

import math
import random
import sys
from typing import List, Tuple, Optional

import pygame

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Map settings
MAP_SIZE = 90
TILE_SIZE = 64

# Player settings
PLAYER_SPEED = 0.1
PLAYER_ROT_SPEED = 0.003
FOV = math.pi / 3  # 60 degrees
HALF_FOV = FOV / 2
NUM_RAYS = SCREEN_WIDTH // 2
MAX_DEPTH = 20
DELTA_ANGLE = FOV / NUM_RAYS

# Weapon settings
RIFLE_DAMAGE = 25
RIFLE_RANGE = 15

# Bot settings
BASE_BOT_HEALTH = 50
BASE_BOT_DAMAGE = 10
BOT_SPEED = 0.05
BOT_ATTACK_RANGE = 10
BOT_ATTACK_COOLDOWN = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
BROWN = (139, 69, 19)
DARK_BROWN = (101, 67, 33)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (200, 0, 200)
CYAN = (0, 255, 255)

# Wall colors
WALL_COLORS = {
    1: (100, 100, 100),
    2: (139, 69, 19),
    3: (150, 75, 0),
    4: (180, 180, 180),
}


class Map:
    """Game map with walls and buildings"""

    def __init__(self):
        """Initialize a 90x90 map with walls and buildings"""
        self.size = MAP_SIZE
        self.grid = [[0 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        self.create_map()

    def create_map(self):
        """Create the map layout with walls and buildings"""
        # Border walls
        for i in range(MAP_SIZE):
            self.grid[0][i] = 1
            self.grid[MAP_SIZE - 1][i] = 1
            self.grid[i][0] = 1
            self.grid[i][MAP_SIZE - 1] = 1

        # Building 1 - Large rectangular building (top-left area)
        for i in range(10, 25):
            for j in range(10, 30):
                if i == 10 or i == 24 or j == 10 or j == 29:
                    self.grid[i][j] = 2

        # Building 2 - Medium building (top-right area)
        for i in range(10, 20):
            for j in range(60, 75):
                if i == 10 or i == 19 or j == 60 or j == 74:
                    self.grid[i][j] = 3

        # Building 3 - L-shaped building (bottom-left)
        for i in range(60, 80):
            for j in range(10, 25):
                if i == 60 or i == 79 or j == 10 or j == 24:
                    self.grid[i][j] = 2
        for i in range(60, 80):
            for j in range(10, 40):
                if i >= 70 and (i == 70 or i == 79 or j == 10 or j == 39):
                    self.grid[i][j] = 2

        # Building 4 - Square building (bottom-right)
        for i in range(65, 80):
            for j in range(65, 80):
                if i == 65 or i == 79 or j == 65 or j == 79:
                    self.grid[i][j] = 3

        # Central courtyard walls
        for i in range(40, 50):
            self.grid[i][40] = 4
            self.grid[i][50] = 4
        for j in range(40, 51):
            self.grid[40][j] = 4
            self.grid[50][j] = 4

        # Scattered walls for cover
        for i in range(30, 35):
            self.grid[i][45] = 1

        for j in range(55, 60):
            self.grid[45][j] = 1

        for i in range(25, 30):
            self.grid[i][60] = 1

        for j in range(30, 35):
            self.grid[55][j] = 1

    def is_wall(self, x: float, y: float) -> bool:
        """Check if position contains a wall"""
        map_x = int(x)
        map_y = int(y)
        if 0 <= map_x < MAP_SIZE and 0 <= map_y < MAP_SIZE:
            return self.grid[map_x][map_y] != 0
        return True

    def get_wall_type(self, x: float, y: float) -> int:
        """Get the wall type at position"""
        map_x = int(x)
        map_y = int(y)
        if 0 <= map_x < MAP_SIZE and 0 <= map_y < MAP_SIZE:
            return self.grid[map_x][map_y]
        return 1


class Player:
    """Player with position, rotation, and shooting capabilities"""

    def __init__(self, x: float, y: float, angle: float):
        """Initialize player"""
        self.x = x
        self.y = y
        self.angle = angle
        self.health = 100
        self.max_health = 100
        self.ammo = 999
        self.shooting = False
        self.shoot_timer = 0
        self.alive = True

    def move(self, game_map: Map, bots: List['Bot'], forward: bool = True):
        """Move player forward or backward"""
        dx = math.cos(self.angle) * PLAYER_SPEED * (1 if forward else -1)
        dy = math.sin(self.angle) * PLAYER_SPEED * (1 if forward else -1)

        new_x = self.x + dx
        new_y = self.y + dy

        # Check wall collision
        if not game_map.is_wall(new_x, self.y):
            # Check bot collision
            collision = False
            for bot in bots:
                if bot.alive:
                    dist = math.sqrt((new_x - bot.x)**2 + (self.y - bot.y)**2)
                    if dist < 0.5:
                        collision = True
                        break
            if not collision:
                self.x = new_x

        if not game_map.is_wall(self.x, new_y):
            collision = False
            for bot in bots:
                if bot.alive:
                    dist = math.sqrt((self.x - bot.x)**2 + (new_y - bot.y)**2)
                    if dist < 0.5:
                        collision = True
                        break
            if not collision:
                self.y = new_y

    def strafe(self, game_map: Map, bots: List['Bot'], right: bool = True):
        """Strafe left or right"""
        angle = self.angle + math.pi / 2 * (1 if right else -1)
        dx = math.cos(angle) * PLAYER_SPEED
        dy = math.sin(angle) * PLAYER_SPEED

        new_x = self.x + dx
        new_y = self.y + dy

        if not game_map.is_wall(new_x, self.y):
            collision = False
            for bot in bots:
                if bot.alive:
                    dist = math.sqrt((new_x - bot.x)**2 + (self.y - bot.y)**2)
                    if dist < 0.5:
                        collision = True
                        break
            if not collision:
                self.x = new_x

        if not game_map.is_wall(self.x, new_y):
            collision = False
            for bot in bots:
                if bot.alive:
                    dist = math.sqrt((self.x - bot.x)**2 + (new_y - bot.y)**2)
                    if dist < 0.5:
                        collision = True
                        break
            if not collision:
                self.y = new_y

    def rotate(self, delta: float):
        """Rotate player view"""
        self.angle += delta
        self.angle %= 2 * math.pi

    def shoot(self) -> bool:
        """Initiate shooting, return True if shot was fired"""
        if self.ammo > 0 and self.shoot_timer <= 0:
            self.shooting = True
            self.shoot_timer = 15
            self.ammo -= 1
            return True
        return False

    def take_damage(self, damage: int):
        """Take damage"""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def update(self):
        """Update player state"""
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shooting = False


class Bot:
    """Enemy bot with AI"""

    def __init__(self, x: float, y: float, level: int):
        """Initialize bot"""
        self.x = x
        self.y = y
        self.angle = 0
        self.health = BASE_BOT_HEALTH + (level - 1) * 3
        self.max_health = self.health
        self.damage = BASE_BOT_DAMAGE + (level - 1) * 2
        self.alive = True
        self.attack_timer = 0
        self.level = level

    def update(self, game_map: Map, player: Player, other_bots: List['Bot']):
        """Update bot AI"""
        if not self.alive:
            return

        # Calculate distance to player
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        # Face player
        self.angle = math.atan2(dy, dx)

        # Attack if in range
        if distance < BOT_ATTACK_RANGE:
            if self.attack_timer <= 0:
                # Check line of sight
                if self.has_line_of_sight(game_map, player):
                    player.take_damage(self.damage)
                    self.attack_timer = BOT_ATTACK_COOLDOWN
        else:
            # Move toward player
            move_dx = math.cos(self.angle) * BOT_SPEED
            move_dy = math.sin(self.angle) * BOT_SPEED

            new_x = self.x + move_dx
            new_y = self.y + move_dy

            # Check wall collision
            can_move_x = not game_map.is_wall(new_x, self.y)
            can_move_y = not game_map.is_wall(self.x, new_y)

            # Check collision with other bots
            for other_bot in other_bots:
                if other_bot != self and other_bot.alive:
                    other_dist = math.sqrt((new_x - other_bot.x)**2 + (self.y - other_bot.y)**2)
                    if other_dist < 0.5:
                        can_move_x = False
                    other_dist = math.sqrt((self.x - other_bot.x)**2 + (new_y - other_bot.y)**2)
                    if other_dist < 0.5:
                        can_move_y = False

            if can_move_x:
                self.x = new_x
            if can_move_y:
                self.y = new_y

        # Update attack timer
        if self.attack_timer > 0:
            self.attack_timer -= 1

    def has_line_of_sight(self, game_map: Map, player: Player) -> bool:
        """Check if bot has line of sight to player"""
        steps = 50
        for i in range(1, steps):
            t = i / steps
            check_x = self.x + (player.x - self.x) * t
            check_y = self.y + (player.y - self.y) * t
            if game_map.is_wall(check_x, check_y):
                return False
        return True

    def take_damage(self, damage: int):
        """Take damage"""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False


class Raycaster:
    """Raycasting engine for 3D rendering"""

    def __init__(self, game_map: Map):
        """Initialize raycaster"""
        self.game_map = game_map

    def cast_ray(self, origin_x: float, origin_y: float, angle: float) -> Tuple[float, int, Optional['Bot']]:
        """Cast a single ray and return distance, wall type, and hit bot"""
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        closest_bot = None
        closest_bot_dist = float('inf')

        # Cast ray
        for depth in range(1, int(MAX_DEPTH * 100)):
            target_x = origin_x + depth * 0.01 * cos_a
            target_y = origin_y + depth * 0.01 * sin_a
            distance = depth * 0.01

            if self.game_map.is_wall(target_x, target_y):
                wall_type = self.game_map.get_wall_type(target_x, target_y)
                return distance, wall_type, closest_bot

        return MAX_DEPTH, 0, None

    def cast_ray_with_bots(self, origin_x: float, origin_y: float, angle: float,
                           player_angle: float, bots: List[Bot]) -> Tuple[float, int, Optional[Bot]]:
        """Cast ray and detect bots"""
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        closest_bot = None
        closest_bot_dist = float('inf')

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
            angle_diff = abs(bot_angle - angle)
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff

            # Bot hitbox
            if angle_diff < 0.1 and bot_dist < closest_bot_dist:
                closest_bot = bot
                closest_bot_dist = bot_dist

        # Cast ray for walls
        for depth in range(1, int(MAX_DEPTH * 100)):
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

        return MAX_DEPTH, 0, None

    def render_3d(self, screen: pygame.Surface, player: Player, bots: List[Bot]):
        """Render 3D view using raycasting"""
        ray_angle = player.angle - HALF_FOV

        for ray in range(NUM_RAYS):
            distance, wall_type, hit_bot = self.cast_ray_with_bots(
                player.x, player.y, ray_angle, player.angle, bots
            )

            if hit_bot:
                # Render bot
                if distance > 0:
                    sprite_height = min(SCREEN_HEIGHT, (SCREEN_HEIGHT / distance))
                else:
                    sprite_height = SCREEN_HEIGHT

                # Bot color (purple/magenta)
                color = PURPLE
                shade = max(0, 255 - int(distance * 25))
                color = tuple(min(255, max(0, c * shade // 255)) for c in color)

                sprite_top = (SCREEN_HEIGHT - sprite_height) // 2
                pygame.draw.rect(screen, color, (ray * 2, sprite_top, 2, sprite_height))

            elif wall_type > 0:
                # Render wall
                if distance > 0:
                    wall_height = min(SCREEN_HEIGHT, (SCREEN_HEIGHT / distance))
                else:
                    wall_height = SCREEN_HEIGHT

                color = WALL_COLORS.get(wall_type, GRAY)
                shade = max(0, 255 - int(distance * 25))
                color = tuple(min(255, max(0, c * shade // 255)) for c in color)

                wall_top = (SCREEN_HEIGHT - wall_height) // 2
                pygame.draw.rect(screen, color, (ray * 2, wall_top, 2, wall_height))

            ray_angle += DELTA_ANGLE

    def render_floor_ceiling(self, screen: pygame.Surface):
        """Render floor and ceiling"""
        pygame.draw.rect(screen, DARK_GRAY, (0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
        pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT // 2))

    def render_minimap(self, screen: pygame.Surface, player: Player, bots: List[Bot]):
        """Render 2D minimap"""
        minimap_size = 200
        minimap_scale = minimap_size / MAP_SIZE
        minimap_x = SCREEN_WIDTH - minimap_size - 20
        minimap_y = 20

        # Draw minimap background
        pygame.draw.rect(screen, BLACK, (minimap_x - 2, minimap_y - 2, minimap_size + 4, minimap_size + 4))
        pygame.draw.rect(screen, DARK_GRAY, (minimap_x, minimap_y, minimap_size, minimap_size))

        # Draw walls
        for i in range(MAP_SIZE):
            for j in range(MAP_SIZE):
                if self.game_map.grid[i][j] != 0:
                    wall_type = self.game_map.grid[i][j]
                    color = WALL_COLORS.get(wall_type, WHITE)
                    pygame.draw.rect(
                        screen, color,
                        (minimap_x + j * minimap_scale, minimap_y + i * minimap_scale,
                         minimap_scale, minimap_scale)
                    )

        # Draw bots
        for bot in bots:
            if bot.alive:
                bot_x = minimap_x + bot.y * minimap_scale
                bot_y = minimap_y + bot.x * minimap_scale
                pygame.draw.circle(screen, RED, (int(bot_x), int(bot_y)), 3)

        # Draw player
        player_x = minimap_x + player.y * minimap_scale
        player_y = minimap_y + player.x * minimap_scale
        pygame.draw.circle(screen, GREEN, (int(player_x), int(player_y)), 3)

        # Draw direction
        dir_x = player_x + math.sin(player.angle) * 10
        dir_y = player_y + math.cos(player.angle) * 10
        pygame.draw.line(screen, GREEN, (player_x, player_y), (dir_x, dir_y), 2)


class Button:
    """UI Button"""

    def __init__(self, x: int, y: int, width: int, height: int, text: str, color: Tuple[int, int, int]):
        """Initialize button"""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = tuple(min(255, c + 30) for c in color)
        self.hovered = False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font):
        """Draw button"""
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 3)

        text_surface = font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def update(self, mouse_pos: Tuple[int, int]):
        """Update button hover state"""
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos: Tuple[int, int]) -> bool:
        """Check if button was clicked"""
        return self.rect.collidepoint(mouse_pos)


class Game:
    """Main game class"""

    def __init__(self):
        """Initialize game"""
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("FPS Shooter - Arena Combat")
        self.clock = pygame.time.Clock()
        self.running = True

        # Game state
        self.state = "menu"  # menu, playing, game_over, level_complete
        self.level = 1
        self.kills = 0

        # Game objects
        self.game_map = Map()
        self.player = None
        self.bots = []
        self.raycaster = Raycaster(self.game_map)

        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
        self.tiny_font = pygame.font.Font(None, 24)

        # Menu button
        self.start_button = Button(
            SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50,
            300, 80, "START GAME", GREEN
        )

    def get_corner_positions(self) -> List[Tuple[float, float, float]]:
        """Get spawn positions for four corners (x, y, angle)"""
        offset = 5
        return [
            (offset, offset, math.pi / 4),  # Top-left
            (offset, MAP_SIZE - offset, 3 * math.pi / 4),  # Bottom-left
            (MAP_SIZE - offset, offset, 7 * math.pi / 4),  # Top-right
            (MAP_SIZE - offset, MAP_SIZE - offset, 5 * math.pi / 4),  # Bottom-right
        ]

    def start_game(self):
        """Start new game"""
        self.level = 1
        self.kills = 0
        self.start_level()

    def start_level(self):
        """Start a new level"""
        corners = self.get_corner_positions()
        random.shuffle(corners)

        # Player spawns in first corner
        player_pos = corners[0]
        self.player = Player(player_pos[0], player_pos[1], player_pos[2])

        # Bots spawn in other three corners
        self.bots = []
        for i in range(1, 4):
            bot_pos = corners[i]
            self.bots.append(Bot(bot_pos[0], bot_pos[1], self.level))

        self.state = "playing"

        # Enable mouse capture
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

    def handle_menu_events(self):
        """Handle menu events"""
        mouse_pos = pygame.mouse.get_pos()
        self.start_button.update(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.start_button.is_clicked(mouse_pos):
                    self.start_game()

    def handle_game_events(self):
        """Handle gameplay events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.player.shoot():
                        self.check_shot_hit()
            elif event.type == pygame.MOUSEMOTION:
                self.player.rotate(event.rel[0] * PLAYER_ROT_SPEED)

    def check_shot_hit(self):
        """Check if player's shot hit a bot"""
        # Cast ray in player's view direction
        sin_a = math.sin(self.player.angle)
        cos_a = math.cos(self.player.angle)

        # Find closest bot in crosshair
        closest_bot = None
        closest_dist = float('inf')

        for bot in self.bots:
            if not bot.alive:
                continue

            # Calculate bot position relative to player
            dx = bot.x - self.player.x
            dy = bot.y - self.player.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > RIFLE_RANGE:
                continue

            # Check if bot is in front of player
            bot_angle = math.atan2(dy, dx)
            angle_diff = abs(bot_angle - self.player.angle)
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff

            # Narrow hit detection (accurate shooting)
            if angle_diff < 0.15:
                # Check line of sight
                hit = True
                steps = int(distance * 10)
                for i in range(1, steps):
                    t = i / steps
                    check_x = self.player.x + dx * t
                    check_y = self.player.y + dy * t
                    if self.game_map.is_wall(check_x, check_y):
                        hit = False
                        break

                if hit and distance < closest_dist:
                    closest_bot = bot
                    closest_dist = distance

        # Damage the closest bot in crosshair
        if closest_bot:
            closest_bot.take_damage(RIFLE_DAMAGE)
            if not closest_bot.alive:
                self.kills += 1

    def update_game(self):
        """Update game state"""
        if not self.player.alive:
            self.state = "game_over"
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
            return

        # Check if all bots are dead
        all_dead = all(not bot.alive for bot in self.bots)
        if all_dead:
            self.state = "level_complete"
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
            return

        keys = pygame.key.get_pressed()

        # Movement
        if keys[pygame.K_w]:
            self.player.move(self.game_map, self.bots, forward=True)
        if keys[pygame.K_s]:
            self.player.move(self.game_map, self.bots, forward=False)
        if keys[pygame.K_a]:
            self.player.strafe(self.game_map, self.bots, right=False)
        if keys[pygame.K_d]:
            self.player.strafe(self.game_map, self.bots, right=True)

        # Arrow keys
        if keys[pygame.K_LEFT]:
            self.player.rotate(-0.05)
        if keys[pygame.K_RIGHT]:
            self.player.rotate(0.05)

        self.player.update()

        # Update bots
        for bot in self.bots:
            bot.update(self.game_map, self.player, self.bots)

    def render_menu(self):
        """Render main menu"""
        self.screen.fill(BLACK)

        # Title
        title = self.title_font.render("FPS ARENA", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        # Subtitle
        subtitle = self.small_font.render("90x90 Combat Zone", True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(subtitle, subtitle_rect)

        # Instructions
        instructions = [
            "Fight waves of enemy bots!",
            "Each level, bots get stronger (+3 HP, +DMG)",
            "",
            "WASD: Move | Mouse: Look | Click: Shoot"
        ]

        y = 320
        for line in instructions:
            text = self.tiny_font.render(line, True, CYAN)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 35

        # Start button
        self.start_button.draw(self.screen, self.font)

        pygame.display.flip()

    def render_game(self):
        """Render gameplay"""
        # 3D view
        self.raycaster.render_floor_ceiling(self.screen)
        self.raycaster.render_3d(self.screen, self.player, self.bots)

        # Render rifle
        self.render_rifle()

        # Minimap
        self.raycaster.render_minimap(self.screen, self.player, self.bots)

        # HUD
        self.render_hud()

        # Crosshair
        self.render_crosshair()

        # Muzzle flash
        if self.player.shooting:
            self.render_muzzle_flash()

        pygame.display.flip()

    def render_rifle(self):
        """Render rifle weapon in first-person view"""
        # Rifle body (brown/black)
        rifle_color = DARK_BROWN
        barrel_color = (30, 30, 30)

        # Rifle position (bottom-right of screen)
        rifle_x = SCREEN_WIDTH - 250
        rifle_y = SCREEN_HEIGHT - 200

        # Stock
        pygame.draw.rect(self.screen, rifle_color, (rifle_x + 150, rifle_y + 120, 80, 40))

        # Main body
        pygame.draw.rect(self.screen, rifle_color, (rifle_x + 80, rifle_y + 100, 120, 30))

        # Barrel
        pygame.draw.rect(self.screen, barrel_color, (rifle_x, rifle_y + 105, 120, 20))

        # Front sight
        pygame.draw.rect(self.screen, BLACK, (rifle_x + 10, rifle_y + 95, 5, 15))

        # Magazine
        pygame.draw.rect(self.screen, BLACK, (rifle_x + 110, rifle_y + 125, 30, 50))

        # Trigger guard
        pygame.draw.rect(self.screen, barrel_color, (rifle_x + 140, rifle_y + 125, 15, 25))

    def render_hud(self):
        """Render HUD"""
        # Health bar
        health_width = 200
        health_height = 30
        health_x = 20
        health_y = 20

        # Background
        pygame.draw.rect(self.screen, DARK_GRAY, (health_x, health_y, health_width, health_height))

        # Health fill
        health_percent = max(0, self.player.health / self.player.max_health)
        fill_width = int(health_width * health_percent)
        health_color = GREEN if health_percent > 0.5 else (ORANGE if health_percent > 0.25 else RED)
        pygame.draw.rect(self.screen, health_color, (health_x, health_y, fill_width, health_height))

        # Border
        pygame.draw.rect(self.screen, WHITE, (health_x, health_y, health_width, health_height), 2)

        # Text
        health_text = self.tiny_font.render(f"HP: {self.player.health}/{self.player.max_health}", True, WHITE)
        self.screen.blit(health_text, (health_x + 5, health_y + 5))

        # Level and kills
        level_text = self.small_font.render(f"Level: {self.level}", True, YELLOW)
        self.screen.blit(level_text, (20, 60))

        bots_alive = sum(1 for bot in self.bots if bot.alive)
        kills_text = self.small_font.render(f"Enemies: {bots_alive}/3", True, RED)
        self.screen.blit(kills_text, (20, 95))

        # Ammo
        ammo_text = self.small_font.render(f"Ammo: {self.player.ammo}", True, CYAN)
        self.screen.blit(ammo_text, (20, 130))

    def render_crosshair(self):
        """Render crosshair"""
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        size = 12

        # Crosshair lines
        pygame.draw.line(self.screen, RED, (cx - size, cy), (cx + size, cy), 2)
        pygame.draw.line(self.screen, RED, (cx, cy - size), (cx, cy + size), 2)

        # Center dot
        pygame.draw.circle(self.screen, RED, (cx, cy), 2)

    def render_muzzle_flash(self):
        """Render muzzle flash"""
        # Flash near rifle barrel
        flash_x = SCREEN_WIDTH - 350
        flash_y = SCREEN_HEIGHT - 85

        pygame.draw.circle(self.screen, YELLOW, (flash_x, flash_y), 25)
        pygame.draw.circle(self.screen, ORANGE, (flash_x, flash_y), 15)
        pygame.draw.circle(self.screen, WHITE, (flash_x, flash_y), 8)

    def render_level_complete(self):
        """Render level complete screen"""
        self.screen.fill(BLACK)

        # Title
        title = self.title_font.render("LEVEL COMPLETE!", True, GREEN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        # Stats
        stats = [
            f"Level {self.level} cleared!",
            f"Total Kills: {self.kills}",
            "",
            "Next level: Bots get stronger!",
            "",
            "Press SPACE for next level",
            "Press ESC for menu"
        ]

        y = 320
        for line in stats:
            color = YELLOW if "stronger" in line else WHITE
            text = self.small_font.render(line, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 45

        pygame.display.flip()

        # Handle input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.level += 1
                    self.start_level()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"

    def render_game_over(self):
        """Render game over screen"""
        self.screen.fill(BLACK)

        # Title
        title = self.title_font.render("GAME OVER", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        # Stats
        stats = [
            f"You survived {self.level} level{'s' if self.level != 1 else ''}",
            f"Total Kills: {self.kills}",
            "",
            "Press SPACE to restart",
            "Press ESC for menu"
        ]

        y = 350
        for line in stats:
            text = self.small_font.render(line, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 50

        pygame.display.flip()

        # Handle input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.start_game()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"

    def run(self):
        """Main game loop"""
        while self.running:
            if self.state == "menu":
                self.handle_menu_events()
                self.render_menu()
            elif self.state == "playing":
                self.handle_game_events()
                self.update_game()
                self.render_game()
            elif self.state == "level_complete":
                self.render_level_complete()
            elif self.state == "game_over":
                self.render_game_over()

            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def main():
    """Main entry point"""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
