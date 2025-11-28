#!/usr/bin/env python3
"""
First-Person Shooter Game
A raycasting-based FPS game with a 90x90 map featuring walls and buildings.
Uses WASD for movement, mouse for looking, and left-click to shoot.
"""

import math
import sys
from typing import List, Tuple

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

# Wall colors (different walls have different colors)
WALL_COLORS = {
    1: (100, 100, 100),  # Gray walls
    2: (139, 69, 19),     # Brown buildings
    3: (150, 75, 0),      # Dark orange buildings
    4: (180, 180, 180),   # Light gray walls
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

        # Additional scattered walls
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
        self.ammo = 100
        self.shooting = False
        self.shoot_timer = 0

    def move(self, game_map: Map, forward: bool = True):
        """Move player forward or backward"""
        dx = math.cos(self.angle) * PLAYER_SPEED * (1 if forward else -1)
        dy = math.sin(self.angle) * PLAYER_SPEED * (1 if forward else -1)

        new_x = self.x + dx
        new_y = self.y + dy

        if not game_map.is_wall(new_x, self.y):
            self.x = new_x
        if not game_map.is_wall(self.x, new_y):
            self.y = new_y

    def strafe(self, game_map: Map, right: bool = True):
        """Strafe left or right"""
        angle = self.angle + math.pi / 2 * (1 if right else -1)
        dx = math.cos(angle) * PLAYER_SPEED
        dy = math.sin(angle) * PLAYER_SPEED

        new_x = self.x + dx
        new_y = self.y + dy

        if not game_map.is_wall(new_x, self.y):
            self.x = new_x
        if not game_map.is_wall(self.x, new_y):
            self.y = new_y

    def rotate(self, delta: float):
        """Rotate player view"""
        self.angle += delta
        self.angle %= 2 * math.pi

    def shoot(self):
        """Initiate shooting"""
        if self.ammo > 0 and self.shoot_timer <= 0:
            self.shooting = True
            self.shoot_timer = 20  # Cooldown frames
            self.ammo -= 1

    def update(self):
        """Update player state"""
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shooting = False


class Raycaster:
    """Raycasting engine for 3D rendering"""

    def __init__(self, game_map: Map):
        """Initialize raycaster"""
        self.game_map = game_map

    def cast_ray(self, player: Player, ray_angle: float) -> Tuple[float, int]:
        """Cast a single ray and return distance and wall type"""
        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)

        # Cast ray
        for depth in range(1, int(MAX_DEPTH * 100)):
            target_x = player.x + depth * 0.01 * cos_a
            target_y = player.y + depth * 0.01 * sin_a

            if self.game_map.is_wall(target_x, target_y):
                wall_type = self.game_map.get_wall_type(target_x, target_y)
                # Fix fish-eye effect
                distance = depth * 0.01 * math.cos(player.angle - ray_angle)
                return distance, wall_type

        return MAX_DEPTH, 0

    def render_3d(self, screen: pygame.Surface, player: Player):
        """Render 3D view using raycasting"""
        ray_angle = player.angle - HALF_FOV

        for ray in range(NUM_RAYS):
            distance, wall_type = self.cast_ray(player, ray_angle)

            # Calculate wall height
            if distance > 0:
                wall_height = min(SCREEN_HEIGHT, (SCREEN_HEIGHT / distance))
            else:
                wall_height = SCREEN_HEIGHT

            # Get wall color
            color = WALL_COLORS.get(wall_type, GRAY)

            # Add depth shading
            shade = max(0, 255 - int(distance * 25))
            color = tuple(min(255, max(0, c * shade // 255)) for c in color)

            # Draw wall slice
            wall_top = (SCREEN_HEIGHT - wall_height) // 2
            wall_bottom = wall_top + wall_height

            pygame.draw.rect(
                screen,
                color,
                (ray * 2, wall_top, 2, wall_height)
            )

            ray_angle += DELTA_ANGLE

    def render_floor_ceiling(self, screen: pygame.Surface):
        """Render floor and ceiling"""
        pygame.draw.rect(screen, DARK_GRAY, (0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
        pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT // 2))

    def render_minimap(self, screen: pygame.Surface, player: Player):
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
                        screen,
                        color,
                        (
                            minimap_x + j * minimap_scale,
                            minimap_y + i * minimap_scale,
                            minimap_scale,
                            minimap_scale
                        )
                    )

        # Draw player
        player_screen_x = minimap_x + player.y * minimap_scale
        player_screen_y = minimap_y + player.x * minimap_scale
        pygame.draw.circle(screen, GREEN, (int(player_screen_x), int(player_screen_y)), 3)

        # Draw direction line
        dir_x = player_screen_x + math.sin(player.angle) * 10
        dir_y = player_screen_y + math.cos(player.angle) * 10
        pygame.draw.line(screen, GREEN, (player_screen_x, player_screen_y), (dir_x, dir_y), 2)


class Game:
    """Main game class"""

    def __init__(self):
        """Initialize game"""
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("FPS Shooter - 90x90 Map")
        self.clock = pygame.time.Clock()
        self.running = True

        # Game objects
        self.game_map = Map()
        self.player = Player(45, 45, 0)  # Start in center of map
        self.raycaster = Raycaster(self.game_map)

        # Mouse control
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        # Font for HUD
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

    def handle_events(self):
        """Handle input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.player.shoot()
            elif event.type == pygame.MOUSEMOTION:
                # Mouse look
                self.player.rotate(event.rel[0] * PLAYER_ROT_SPEED)

    def update(self):
        """Update game state"""
        keys = pygame.key.get_pressed()

        # Movement
        if keys[pygame.K_w]:
            self.player.move(self.game_map, forward=True)
        if keys[pygame.K_s]:
            self.player.move(self.game_map, forward=False)
        if keys[pygame.K_a]:
            self.player.strafe(self.game_map, right=False)
        if keys[pygame.K_d]:
            self.player.strafe(self.game_map, right=True)

        # Arrow keys for rotation (alternative to mouse)
        if keys[pygame.K_LEFT]:
            self.player.rotate(-0.05)
        if keys[pygame.K_RIGHT]:
            self.player.rotate(0.05)

        self.player.update()

    def render(self):
        """Render game"""
        # Render 3D view
        self.raycaster.render_floor_ceiling(self.screen)
        self.raycaster.render_3d(self.screen, self.player)

        # Render minimap
        self.raycaster.render_minimap(self.screen, self.player)

        # Render HUD
        self.render_hud()

        # Render crosshair
        self.render_crosshair()

        # Render shooting effect
        if self.player.shooting:
            self.render_shoot_effect()

        pygame.display.flip()

    def render_hud(self):
        """Render heads-up display"""
        # Health
        health_text = self.font.render(f"Health: {self.player.health}", True, GREEN)
        self.screen.blit(health_text, (20, 20))

        # Ammo
        ammo_text = self.font.render(f"Ammo: {self.player.ammo}", True, YELLOW)
        self.screen.blit(ammo_text, (20, 60))

        # Instructions
        inst_text = self.small_font.render("WASD: Move | Mouse: Look | Click: Shoot | ESC: Quit", True, WHITE)
        self.screen.blit(inst_text, (20, SCREEN_HEIGHT - 40))

    def render_crosshair(self):
        """Render crosshair in center of screen"""
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        crosshair_size = 10

        # Draw crosshair
        pygame.draw.line(self.screen, RED,
                        (center_x - crosshair_size, center_y),
                        (center_x + crosshair_size, center_y), 2)
        pygame.draw.line(self.screen, RED,
                        (center_x, center_y - crosshair_size),
                        (center_x, center_y + crosshair_size), 2)

    def render_shoot_effect(self):
        """Render muzzle flash when shooting"""
        center_x = SCREEN_WIDTH // 2
        bottom_y = SCREEN_HEIGHT - 100

        # Muzzle flash
        pygame.draw.circle(self.screen, YELLOW, (center_x, bottom_y), 30, 0)
        pygame.draw.circle(self.screen, ORANGE, (center_x, bottom_y), 20, 0)
        pygame.draw.circle(self.screen, WHITE, (center_x, bottom_y), 10, 0)

    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def main():
    """Main entry point"""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
