#!/usr/bin/env python3
"""
First-Person Shooter Game
A raycasting-based FPS game with a 90x90 map featuring walls, buildings, and bot enemies.
Uses WASD for movement, mouse for looking and aiming, left-click to aim, and right-click to shoot.
Fight waves of increasingly difficult bots across multiple levels!
"""

import math
import random
import sys
from typing import Any, Dict, List, Optional, Tuple

import pygame

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Map settings
DEFAULT_MAP_SIZE = 50
MAP_SIZE = DEFAULT_MAP_SIZE  # Will be set by user
TILE_SIZE = 64
MIN_BUILDING_OFFSET = 3  # Minimum offset from map edges for building generation

# Player settings
PLAYER_SPEED = 1
PLAYER_SPRINT_SPEED = 1.5
PLAYER_ROT_SPEED = 0.003
FOV = math.pi / 3  # 60 degrees
HALF_FOV = FOV / 2
NUM_RAYS = SCREEN_WIDTH // 2
MAX_DEPTH = 50  # Increased render distance
DELTA_ANGLE = FOV / NUM_RAYS

# Weapon settings
WEAPONS = {
    "pistol": {
        "name": "Pistol",
        "damage": 20,
        "range": 12,
        "ammo": 999,
        "cooldown": 10,
        "key": "1",
    },
    "rifle": {
        "name": "Rifle",
        "damage": 25,
        "range": 15,
        "ammo": 999,
        "cooldown": 15,
        "key": "2",
    },
    "shotgun": {
        "name": "Shotgun",
        "damage": 30,
        "range": 8,
        "ammo": 999,
        "cooldown": 20,
        "key": "3",
    },
    "plasma": {
        "name": "Plasma",
        "damage": 35,
        "range": 18,
        "ammo": 999,
        "cooldown": 12,
        "key": "4",
    },
}

# Bot settings - increased health for 5-shot kill
# Exactly 5 shots with rifle (25 damage each) in base case (no enemy type multipliers)
# e.g., brute (1.5x health = 187.5 HP) requires 8 shots,
# demon (1.2x health = 150 HP) requires 6 shots
BASE_BOT_HEALTH = 125
BASE_BOT_DAMAGE = 10
BOT_SPEED = 0.05
BOT_ATTACK_RANGE = 12
BOT_ATTACK_COOLDOWN = 90
BOT_PROJECTILE_SPEED = 0.3
BOT_PROJECTILE_DAMAGE = 15

# Combat settings
HEADSHOT_THRESHOLD = (
    0.05  # Angle difference in radians for headshot detection (2.86 degrees)
)
SPAWN_SAFETY_MARGIN = 3  # Minimum tiles away from building start for spawn positions

# UI settings
HINT_BG_PADDING_H = 10  # Horizontal padding for hint background
HINT_BG_PADDING_V = 4  # Vertical padding for hint background
HINT_BG_COLOR = (30, 30, 30, 180)  # Semi-transparent dark background color for hints

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
DARK_RED = (139, 0, 0)
MAROON = (128, 0, 0)
CRIMSON = (220, 20, 60)
DARK_GREEN = (0, 100, 0)
LIME = (50, 205, 50)

# Enemy types (matching doom game colors and adding more variety)
# Colors from doom games: zombie (#6b8a6f = grayish-green), boss (#8c3f3f = dark red),
# demon (#b52b1d = red), dinosaur (#3fa34d = green), raider (#7a5cff = purple)
ZOMBIE_COLOR = (107, 138, 111)  # #6b8a6f
BOSS_COLOR = (140, 63, 63)  # #8c3f3f
DEMON_COLOR = (181, 43, 29)  # #b52b1d
DINOSAUR_COLOR = (63, 163, 77)  # #3fa34d
RAIDER_COLOR = (122, 92, 255)  # #7a5cff

ENEMY_TYPES = {
    "zombie": {
        "color": ZOMBIE_COLOR,
        "health_mult": 1.0,
        "speed_mult": 1.0,
        "damage_mult": 1.0,
        "scale": 1.0,
    },
    "boss": {
        "color": BOSS_COLOR,
        "health_mult": 2.0,
        "speed_mult": 0.7,
        "damage_mult": 1.8,
        "scale": 1.5,
    },
    "demon": {
        "color": DEMON_COLOR,
        "health_mult": 1.3,
        "speed_mult": 1.2,
        "damage_mult": 1.3,
        "scale": 1.1,
    },
    "dinosaur": {
        "color": DINOSAUR_COLOR,
        "health_mult": 1.4,
        "speed_mult": 1.4,
        "damage_mult": 1.4,
        "scale": 1.2,
    },
    "raider": {
        "color": RAIDER_COLOR,
        "health_mult": 1.1,
        "speed_mult": 1.3,
        "damage_mult": 1.2,
        "scale": 1.0,
    },
}

# Wall colors
WALL_COLORS = {
    1: (100, 100, 100),
    2: (139, 69, 19),
    3: (150, 75, 0),
    4: (180, 180, 180),
}


class Map:
    """Game map with walls and buildings"""

    def __init__(self, size: int = DEFAULT_MAP_SIZE):
        """Initialize a map with walls and buildings
        Args:
            size: Map size (default: DEFAULT_MAP_SIZE)
        """
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        self.create_map()

    def create_map(self) -> None:
        """Create the map layout with walls and buildings"""
        size = self.size
        # Border walls
        for i in range(size):
            self.grid[0][i] = 1
            self.grid[size - 1][i] = 1
            self.grid[i][0] = 1
            self.grid[i][size - 1] = 1

        # Scale building positions based on map size
        # Use proportional minimums that scale with map size
        # to ensure buildings generate for all sizes
        building_edge_margin = max(
            MIN_BUILDING_OFFSET, int(size * 0.1)
        )  # Minimum distance from map edges where buildings can spawn

        # Building 1 - Large rectangular building (top-left area)
        b1_start_i = max(building_edge_margin, int(size * 0.15))
        b1_end_i = max(b1_start_i + 2, min(int(size * 0.3), size - 1))
        b1_start_j = max(building_edge_margin, int(size * 0.15))
        b1_end_j = max(b1_start_j + 2, min(int(size * 0.4), size - 1))
        if b1_end_i > b1_start_i and b1_end_j > b1_start_j:
            for i in range(b1_start_i, b1_end_i):
                for j in range(b1_start_j, b1_end_j):
                    if i in {b1_start_i, b1_end_i - 1} or j in {
                        b1_start_j,
                        b1_end_j - 1,
                    }:
                        self.grid[i][j] = 2

        # Building 2 - Medium building (top-right area)
        b2_start_i = max(building_edge_margin, int(size * 0.15))
        b2_end_i = max(b2_start_i + 2, min(int(size * 0.25), size - 1))
        b2_start_j = max(building_edge_margin, int(size * 0.7))
        b2_end_j = max(b2_start_j + 2, min(int(size * 0.9), size - 1))
        if b2_end_i > b2_start_i and b2_end_j > b2_start_j:
            for i in range(b2_start_i, b2_end_i):
                for j in range(b2_start_j, b2_end_j):
                    if i in {b2_start_i, b2_end_i - 1} or j in {
                        b2_start_j,
                        b2_end_j - 1,
                    }:
                        self.grid[i][j] = 3

        # Building 3 - L-shaped building (bottom-left)
        b3_start_i = max(building_edge_margin, int(size * 0.7))
        b3_end_i = max(b3_start_i + 2, min(int(size * 0.95), size - 1))
        b3_start_j = max(building_edge_margin, int(size * 0.15))
        b3_end_j = max(b3_start_j + 2, min(int(size * 0.35), size - 1))
        if b3_end_i > b3_start_i and b3_end_j > b3_start_j:
            for i in range(b3_start_i, b3_end_i):
                for j in range(b3_start_j, b3_end_j):
                    if i in {b3_start_i, b3_end_i - 1} or j in {
                        b3_start_j,
                        b3_end_j - 1,
                    }:
                        self.grid[i][j] = 2
            # L-shape extension
            b3_ext_start_i = min(max(int(size * 0.8), b3_start_i), b3_end_i - 1)
            b3_ext_end_j = min(int(size * 0.5), size - 1)
            if b3_ext_start_i < b3_end_i and b3_ext_end_j > b3_start_j:
                for i in range(b3_ext_start_i, b3_end_i):
                    for j in range(b3_start_j, b3_ext_end_j):
                        if i in {b3_ext_start_i, b3_end_i - 1} or j in {
                            b3_start_j,
                            b3_ext_end_j - 1,
                        }:
                            self.grid[i][j] = 2

        # Building 4 - Square building (bottom-right)
        b4_start_i = int(size * 0.75)
        b4_end_i = min(int(size * 0.95), size - 1)
        b4_start_j = int(size * 0.75)
        b4_end_j = min(int(size * 0.95), size - 1)
        if b4_end_i > b4_start_i and b4_end_j > b4_start_j:
            for i in range(b4_start_i, b4_end_i):
                for j in range(b4_start_j, b4_end_j):
                    if i in {b4_start_i, b4_end_i - 1} or j in {
                        b4_start_j,
                        b4_end_j - 1,
                    }:
                        self.grid[i][j] = 3

        # Central courtyard walls (only if map is large enough)
        center_start = int(size * 0.45)
        center_end = min(int(size * 0.55), size - 1)
        if center_end > center_start:
            for i in range(center_start, center_end):
                self.grid[i][center_start] = 4
                self.grid[i][center_end] = 4
            for j in range(center_start, min(center_end + 1, size)):
                self.grid[center_start][j] = 4
                if center_end < size:
                    self.grid[center_end][j] = 4

        # Scattered walls for cover (scale with map size)
        if size >= 30:
            wall1_i = int(size * 0.4)
            wall1_j = int(size * 0.6)
            if wall1_i < size and wall1_j < size:
                for i in range(wall1_i, min(wall1_i + 5, size)):
                    self.grid[i][wall1_j] = 1

        if size >= 40:
            wall2_i = int(size * 0.6)
            wall2_j = int(size * 0.7)
            if wall2_i < size and wall2_j < size:
                for j in range(wall2_j, min(wall2_j + 5, size)):
                    self.grid[wall2_i][j] = 1

        if size >= 50:
            wall3_i = int(size * 0.35)
            wall3_j = int(size * 0.7)
            if wall3_i < size and wall3_j < size:
                for i in range(wall3_i, min(wall3_i + 5, size)):
                    self.grid[i][wall3_j] = 1

        if size >= 60:
            wall4_j = int(size * 0.4)
            wall4_i = int(size * 0.75)
            if wall4_i < size and wall4_j < size:
                for j in range(wall4_j, min(wall4_j + 5, size)):
                    self.grid[wall4_i][j] = 1

    def is_wall(self, x: float, y: float) -> bool:
        """Check if position contains a wall"""
        map_x = int(x)
        map_y = int(y)
        if 0 <= map_x < self.size and 0 <= map_y < self.size:
            return self.grid[map_y][map_x] != 0
        return True

    def get_wall_type(self, x: float, y: float) -> int:
        """Get the wall type at position"""
        map_x = int(x)
        map_y = int(y)
        if 0 <= map_x < self.size and 0 <= map_y < self.size:
            return self.grid[map_y][map_x]
        return 1

    def is_inside_building(self, x: float, y: float) -> bool:
        """Check if position is inside a building (not just on the wall)"""
        i = int(y)
        j = int(x)
        if i < 0 or i >= self.size or j < 0 or j >= self.size:
            return False

        # Check if it's a wall (on the edge)
        if self.grid[i][j] != 0:
            return False

        # Check surrounding area to see if we're inside a building
        size = self.size
        building_edge_margin = max(MIN_BUILDING_OFFSET, int(size * 0.1))

        # Building 1 (top-left)
        b1_start_i = max(building_edge_margin, int(size * 0.15))
        b1_end_i = max(b1_start_i + 2, min(int(size * 0.3), size - 1))
        b1_start_j = max(building_edge_margin, int(size * 0.15))
        b1_end_j = max(b1_start_j + 2, min(int(size * 0.4), size - 1))
        if b1_start_i < i < b1_end_i and b1_start_j < j < b1_end_j:
            return True

        # Building 2 (top-right)
        b2_start_i = max(building_edge_margin, int(size * 0.15))
        b2_end_i = max(b2_start_i + 2, min(int(size * 0.25), size - 1))
        b2_start_j = max(building_edge_margin, int(size * 0.7))
        b2_end_j = max(b2_start_j + 2, min(int(size * 0.9), size - 1))
        if b2_start_i < i < b2_end_i and b2_start_j < j < b2_end_j:
            return True

        # Building 3 (bottom-left)
        b3_start_i = max(building_edge_margin, int(size * 0.7))
        b3_end_i = max(b3_start_i + 2, min(int(size * 0.95), size - 1))
        b3_start_j = max(building_edge_margin, int(size * 0.15))
        b3_end_j = max(b3_start_j + 2, min(int(size * 0.35), size - 1))
        if b3_start_i < i < b3_end_i and b3_start_j < j < b3_end_j:
            return True

        # Building 4 (bottom-right)
        b4_start_i = int(size * 0.75)
        b4_end_i = min(int(size * 0.95), size - 1)
        b4_start_j = int(size * 0.75)
        b4_end_j = min(int(size * 0.95), size - 1)
        if b4_start_i < i < b4_end_i and b4_start_j < j < b4_end_j:
            return True

        # Central courtyard
        center_start = int(size * 0.45)
        center_end = min(int(size * 0.55), size - 1)
        return center_start < i < center_end and center_start < j < center_end


class Player:
    """Player with position, rotation, and shooting capabilities"""

    def __init__(self, x: float, y: float, angle: float):
        """Initialize player"""
        self.x = x
        self.y = y
        self.angle = angle
        self.health = 100
        self.max_health = 100
        self.ammo: Dict[str, int] = {
            weapon: int(WEAPONS[weapon].get("ammo", 0)) for weapon in WEAPONS
        }
        self.current_weapon = "rifle"
        self.shooting = False
        self.shoot_timer = 0
        self.alive = True

    def move(
        self,
        game_map: Map,
        bots: List["Bot"],
        forward: bool = True,
        speed: float = PLAYER_SPEED,
    ) -> None:
        """Move player forward or backward"""
        dx = math.cos(self.angle) * speed * (1 if forward else -1)
        dy = math.sin(self.angle) * speed * (1 if forward else -1)

        new_x = self.x + dx
        new_y = self.y + dy

        # Check wall collision
        if not game_map.is_wall(new_x, self.y):
            # Check bot collision
            collision = False
            for bot in bots:
                if bot.alive:
                    dist = math.sqrt((new_x - bot.x) ** 2 + (self.y - bot.y) ** 2)
                    if dist < 0.5:
                        collision = True
                        break
            if not collision:
                self.x = new_x

        if not game_map.is_wall(self.x, new_y):
            collision = False
            for bot in bots:
                if bot.alive:
                    dist = math.sqrt((self.x - bot.x) ** 2 + (new_y - bot.y) ** 2)
                    if dist < 0.5:
                        collision = True
                        break
            if not collision:
                self.y = new_y

    def strafe(
        self,
        game_map: Map,
        bots: List["Bot"],
        right: bool = True,
        speed: float = PLAYER_SPEED,
    ) -> None:
        """Strafe left or right"""
        angle = self.angle + math.pi / 2 * (1 if right else -1)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed

        new_x = self.x + dx
        new_y = self.y + dy

        if not game_map.is_wall(new_x, self.y):
            collision = False
            for bot in bots:
                if bot.alive:
                    dist = math.sqrt((new_x - bot.x) ** 2 + (self.y - bot.y) ** 2)
                    if dist < 0.5:
                        collision = True
                        break
            if not collision:
                self.x = new_x

        if not game_map.is_wall(self.x, new_y):
            collision = False
            for bot in bots:
                if bot.alive:
                    dist = math.sqrt((self.x - bot.x) ** 2 + (new_y - bot.y) ** 2)
                    if dist < 0.5:
                        collision = True
                        break
            if not collision:
                self.y = new_y

    def rotate(self, delta: float) -> None:
        """Rotate player view"""
        self.angle += delta
        self.angle %= 2 * math.pi

    def shoot(self) -> bool:
        """Initiate shooting, return True if shot was fired"""
        weapon_data: Dict[str, Any] = WEAPONS[self.current_weapon]
        if self.ammo[self.current_weapon] > 0 and self.shoot_timer <= 0:
            self.shooting = True
            self.shoot_timer = int(weapon_data["cooldown"])
            self.ammo[self.current_weapon] -= 1
            return True
        return False

    def switch_weapon(self, weapon: str) -> None:
        """Switch to a different weapon"""
        if weapon in WEAPONS:
            self.current_weapon = weapon

    def get_current_weapon_damage(self) -> int:
        """Get damage of current weapon"""
        weapon_data: Dict[str, Any] = WEAPONS[self.current_weapon]
        return int(weapon_data["damage"])

    def get_current_weapon_range(self) -> int:
        """Get range of current weapon"""
        weapon_data: Dict[str, Any] = WEAPONS[self.current_weapon]
        return int(weapon_data["range"])

    def take_damage(self, damage: int) -> None:
        """Take damage"""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def update(self) -> None:
        """Update player state"""
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shooting = False


class Projectile:
    """Projectile shot by bots"""

    def __init__(
        self,
        x: float,
        y: float,
        angle: float,
        damage: int,
        speed: float,
        is_player: bool = False,
    ):
        """Initialize projectile"""
        self.x = x
        self.y = y
        self.angle = angle
        self.damage = damage
        self.speed = speed
        self.is_player = is_player
        self.alive = True

    def update(self, game_map: Map) -> None:
        """Update projectile position"""
        if not self.alive:
            return

        dx = math.cos(self.angle) * self.speed
        dy = math.sin(self.angle) * self.speed

        new_x = self.x + dx
        new_y = self.y + dy

        # Check wall collision
        if game_map.is_wall(new_x, new_y):
            self.alive = False
            return

        self.x = new_x
        self.y = new_y


class Bot:
    """Enemy bot with AI"""

    def __init__(self, x: float, y: float, level: int, enemy_type: str | None = None):
        """Initialize bot
        Args:
            x, y: Position
            level: Current level (affects stats)
            enemy_type: Type of enemy (zombie, boss, demon, dinosaur, raider)
        """
        self.x = x
        self.y = y
        self.angle: float = 0.0
        self.enemy_type = (
            enemy_type if enemy_type else random.choice(list(ENEMY_TYPES.keys()))
        )
        self.type_data = ENEMY_TYPES[self.enemy_type]

        type_data: Dict[str, Any] = self.type_data
        base_health = int(BASE_BOT_HEALTH * float(type_data["health_mult"]))
        self.health = base_health + (level - 1) * 3
        self.max_health = self.health

        base_damage = int(BASE_BOT_DAMAGE * float(type_data["damage_mult"]))
        self.damage = base_damage + (level - 1) * 2

        self.speed = float(BOT_SPEED * float(type_data["speed_mult"]))
        self.alive = True
        self.attack_timer = 0
        self.level = level
        self.walk_animation = 0.0  # For walk animation
        self.last_x = x
        self.last_y = y
        self.shoot_animation = 0.0  # For shoot animation

    def update(
        self, game_map: Map, player: Player, other_bots: List["Bot"]
    ) -> Optional[Projectile]:
        """Update bot AI
        Returns:
            Projectile if bot shoots, None otherwise
        """
        if not self.alive:
            return None

        # Update animations
        if self.shoot_animation > 0:
            self.shoot_animation -= 0.1
            if self.shoot_animation < 0:
                self.shoot_animation = 0

        # Calculate distance to player
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        # Face player
        self.angle = float(math.atan2(dy, dx))

        # Attack if in range
        if distance < BOT_ATTACK_RANGE:
            if self.attack_timer <= 0:
                # Check line of sight
                if self.has_line_of_sight(game_map, player):
                    # Shoot projectile instead of direct damage
                    projectile = Projectile(
                        self.x,
                        self.y,
                        self.angle,
                        BOT_PROJECTILE_DAMAGE + self.damage,
                        BOT_PROJECTILE_SPEED,
                        is_player=False,
                    )
                    self.attack_timer = BOT_ATTACK_COOLDOWN
                    self.shoot_animation = 1.0  # Start shoot animation
                    return projectile  # Return projectile to be added to list
        else:
            # Move toward player
            move_dx = math.cos(self.angle) * self.speed
            move_dy = math.sin(self.angle) * self.speed

            new_x = self.x + move_dx
            new_y = self.y + move_dy

            # Check wall collision
            can_move_x = not game_map.is_wall(new_x, self.y)
            can_move_y = not game_map.is_wall(self.x, new_y)

            # Check collision with other bots
            for other_bot in other_bots:
                if other_bot != self and other_bot.alive:
                    other_dist = math.sqrt(
                        (new_x - other_bot.x) ** 2 + (self.y - other_bot.y) ** 2
                    )
                    if other_dist < 0.5:
                        can_move_x = False
                    other_dist = math.sqrt(
                        (self.x - other_bot.x) ** 2 + (new_y - other_bot.y) ** 2
                    )
                    if other_dist < 0.5:
                        can_move_y = False

            if can_move_x:
                self.x = new_x
            if can_move_y:
                self.y = new_y

            # Update walk animation
            moved = self.x != self.last_x or self.y != self.last_y
            if moved:
                self.walk_animation += 0.3
                if self.walk_animation > 2 * math.pi:
                    self.walk_animation -= 2 * math.pi
            self.last_x = self.x
            self.last_y = self.y

        # Update attack timer
        if self.attack_timer > 0:
            self.attack_timer -= 1

        return None  # No projectile shot this frame

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

    def take_damage(self, damage: int, is_headshot: bool = False) -> None:
        """Take damage
        Args:
            damage: Base damage amount
            is_headshot: If True, do 3x damage instead of instant kill
        """
        if is_headshot:
            self.health -= damage * 3  # Headshot does 3x damage, not instant kill
        else:
            self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False


class Raycaster:
    """Raycasting engine for 3D rendering"""

    def __init__(self, game_map: Map):
        """Initialize raycaster"""
        self.game_map = game_map

    def cast_ray(
        self, origin_x: float, origin_y: float, angle: float
    ) -> Tuple[float, int, Optional["Bot"]]:
        """Cast a single ray and return distance, wall type, and hit bot"""
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        closest_bot = None
        closest_bot_dist = float("inf")

        # Cast ray
        for depth in range(1, int(MAX_DEPTH * 100)):
            target_x = origin_x + depth * 0.01 * cos_a
            target_y = origin_y + depth * 0.01 * sin_a
            distance = depth * 0.01

            if self.game_map.is_wall(target_x, target_y):
                wall_type = self.game_map.get_wall_type(target_x, target_y)
                return distance, wall_type, closest_bot

        return MAX_DEPTH, 0, None

    def cast_ray_with_bots(
        self,
        origin_x: float,
        origin_y: float,
        angle: float,
        player_angle: float,
        bots: List[Bot],
    ) -> Tuple[float, int, Optional[Bot]]:
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

    def render_enemy_sprite(
        self,
        screen: pygame.Surface,
        bot: Bot,
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
            screen, base_color, (center_x - head_size / 2, head_y, head_size, head_size)
        )

        # Eyes
        eye_size = head_size * 0.15
        eye_y = head_y + head_size * 0.3
        eye_spacing = head_size * 0.25
        pygame.draw.circle(
            screen, WHITE, (int(center_x - eye_spacing), int(eye_y)), int(eye_size)
        )
        pygame.draw.circle(
            screen, WHITE, (int(center_x + eye_spacing), int(eye_y)), int(eye_size)
        )
        pygame.draw.circle(
            screen,
            BLACK,
            (int(center_x - eye_spacing), int(eye_y)),
            int(eye_size * 0.6),
        )
        pygame.draw.circle(
            screen,
            BLACK,
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
        pygame.draw.rect(
            screen, dark_color, (right_arm_x, right_arm_y, arm_width, arm_height)
        )

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
            pygame.draw.circle(
                screen, YELLOW, (int(flash_x), int(flash_y)), int(flash_size)
            )
            pygame.draw.circle(
                screen, ORANGE, (int(flash_x), int(flash_y)), int(flash_size * 0.6)
            )

    def render_3d(
        self, screen: pygame.Surface, player: Player, bots: List[Bot]
    ) -> None:
        """Render 3D view using raycasting"""
        ray_angle = player.angle - HALF_FOV

        # Collect all bots to render as sprites
        bots_to_render = []
        for bot in bots:
            if not bot.alive:
                continue

            # Calculate bot position relative to player
            dx = bot.x - player.x
            dy = bot.y - player.y
            bot_dist = math.sqrt(dx**2 + dy**2)

            if bot_dist > MAX_DEPTH:
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
            if abs(angle_to_bot) < HALF_FOV + 0.2:
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

        for ray in range(NUM_RAYS):
            distance, wall_type, hit_bot = self.cast_ray_with_bots(
                player.x, player.y, ray_angle, player.angle, bots
            )

            if hit_bot:
                # Skip bot rendering here - we'll render sprites separately
                continue

            elif wall_type > 0:
                # Render wall with texture
                if distance > 0:
                    wall_height = min(SCREEN_HEIGHT, (SCREEN_HEIGHT / distance))
                else:
                    wall_height = SCREEN_HEIGHT

                base_color = WALL_COLORS.get(wall_type, GRAY)
                shade = max(0, 255 - int(distance * 25))
                color = tuple(min(255, max(0, c * shade // 255)) for c in base_color)

                wall_top = (SCREEN_HEIGHT - wall_height) // 2

                # Draw base wall color
                pygame.draw.rect(screen, color, (ray * 2, wall_top, 2, wall_height))

                # Add texture pattern based on wall type and position
                texture_pattern = (ray + int(distance * 10)) % 8
                if texture_pattern < 4:  # Add texture stripes
                    darker_color = tuple(max(0, c - 20) for c in color)
                    # Vertical stripes for texture
                    stripe_width = 1
                    for stripe_y in range(
                        int(wall_top), int(wall_top + wall_height), 4
                    ):
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

            ray_angle += DELTA_ANGLE

        # Render enemy sprites (after walls, far to near)
        for bot, bot_dist, angle_to_bot in bots_to_render:
            # Calculate sprite size based on distance and enemy scale
            base_sprite_size = (
                SCREEN_HEIGHT / bot_dist if bot_dist > 0 else SCREEN_HEIGHT
            )
            type_data: Dict[str, Any] = bot.type_data
            sprite_size = base_sprite_size * float(type_data.get("scale", 1.0))

            # Calculate sprite position on screen
            sprite_x = (
                SCREEN_WIDTH / 2
                + (angle_to_bot / HALF_FOV) * SCREEN_WIDTH / 2
                - sprite_size / 2
            )
            sprite_y = SCREEN_HEIGHT / 2 - sprite_size / 2

            # Apply distance shading
            distance_shade: float = max(0.4, 1.0 - bot_dist / MAX_DEPTH)

            # Create a temporary surface for the sprite
            sprite_surface = pygame.Surface(
                (int(sprite_size), int(sprite_size)), pygame.SRCALPHA
            )
            self.render_enemy_sprite(sprite_surface, bot, 0, 0, sprite_size)

            # Apply shading by creating a dark overlay
            shade_surface = pygame.Surface((int(sprite_size), int(sprite_size)))
            shade_surface.fill(
                (
                    int(255 * distance_shade),
                    int(255 * distance_shade),
                    int(255 * distance_shade),
                )
            )
            sprite_surface.blit(shade_surface, (0, 0), special_flags=pygame.BLEND_MULT)

            # Blit sprite to screen
            screen.blit(sprite_surface, (int(sprite_x), int(sprite_y)))

    def render_floor_ceiling(self, screen: pygame.Surface) -> None:
        """Render floor and ceiling"""
        pygame.draw.rect(
            screen, DARK_GRAY, (0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2)
        )
        pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT // 2))

    def render_minimap(
        self, screen: pygame.Surface, player: Player, bots: List[Bot]
    ) -> None:
        """Render 2D minimap"""
        minimap_size = 200
        map_size = self.game_map.size
        minimap_scale = minimap_size / map_size
        minimap_x = SCREEN_WIDTH - minimap_size - 20
        minimap_y = 20

        # Draw minimap background
        pygame.draw.rect(
            screen,
            BLACK,
            (minimap_x - 2, minimap_y - 2, minimap_size + 4, minimap_size + 4),
        )
        pygame.draw.rect(
            screen, DARK_GRAY, (minimap_x, minimap_y, minimap_size, minimap_size)
        )

        # Draw walls
        for i in range(map_size):
            for j in range(map_size):
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
                            minimap_scale,
                        ),
                    )

        # Draw bots
        for bot in bots:
            if bot.alive:
                bot_x = minimap_x + bot.x * minimap_scale
                bot_y = minimap_y + bot.y * minimap_scale
                pygame.draw.circle(screen, RED, (int(bot_x), int(bot_y)), 3)

        # Draw player
        player_x = minimap_x + player.x * minimap_scale
        player_y = minimap_y + player.y * minimap_scale
        pygame.draw.circle(screen, GREEN, (int(player_x), int(player_y)), 3)

        # Draw direction
        dir_x = player_x + math.cos(player.angle) * 10
        dir_y = player_y + math.sin(player.angle) * 10
        pygame.draw.line(screen, GREEN, (player_x, player_y), (dir_x, dir_y), 2)


class Button:
    """UI Button"""

    HOVER_BRIGHTNESS_OFFSET = 30  # Brightness increase for hover state

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color: Tuple[int, int, int],
    ):
        """Initialize button"""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self._color = color
        self.hover_color = tuple(
            min(255, c + self.HOVER_BRIGHTNESS_OFFSET) for c in color
        )
        self.hovered = False

    @property
    def color(self) -> Tuple[int, int, int]:
        """Get button color"""
        return self._color

    @color.setter
    def color(self, value: Tuple[int, int, int]) -> None:
        """Set button color and update hover color"""
        self._color = value
        self.hover_color = tuple(
            min(255, c + self.HOVER_BRIGHTNESS_OFFSET) for c in value
        )

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw button"""
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 3)

        text_surface = font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def update(self, mouse_pos: Tuple[int, int]) -> None:
        """Update button hover state"""
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos: Tuple[int, int]) -> bool:
        """Check if button was clicked"""
        return self.rect.collidepoint(mouse_pos)


class Game:
    """Main game class"""

    def __init__(self) -> None:
        """Initialize game"""
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Force Field - Arena Combat")
        self.clock = pygame.time.Clock()
        self.running = True

        # Game state
        self.state = "intro"  # intro, menu, playing, game_over, level_complete
        self.intro_scroll_y = SCREEN_HEIGHT
        self.intro_start_time = 0
        self.level = 1
        self.kills = 0
        self.level_start_time = 0
        self.level_times = []  # Track time for each level
        self.selected_map_size = DEFAULT_MAP_SIZE

        # Game objects
        self.game_map: Optional["Map"] = None  # Will be created with selected size
        self.player: Optional["Player"] = None
        self.bots: List["Bot"] = []
        self.projectiles: List[Any] = []  # Bot projectiles
        self.raycaster: Optional["Raycaster"] = None

        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
        self.tiny_font = pygame.font.Font(None, 24)

        # Cache static UI strings
        self.weapon_hints = " ".join(
            f"{weapon_data['key']}:{weapon_data['name']}"
            for weapon_data in WEAPONS.values()
        )

        # Menu buttons
        self.start_button = Button(
            SCREEN_WIDTH // 2 - 150,
            SCREEN_HEIGHT // 2 + 50,
            300,
            60,
            "START GAME",
            GREEN,
        )
        self.map_size_buttons = []
        map_sizes = [30, 40, 50, 60, 70]
        button_width = 80
        button_spacing = 10
        total_width = len(map_sizes) * (button_width + button_spacing) - button_spacing
        start_x = SCREEN_WIDTH // 2 - total_width // 2
        for i, size in enumerate(map_sizes):
            x = start_x + i * (button_width + button_spacing)
            y = SCREEN_HEIGHT // 2 - 20
            color = GREEN if size == self.selected_map_size else DARK_GRAY
            btn = Button(x, y, button_width, 40, str(size), color)
            self.map_size_buttons.append((btn, size))

    def get_corner_positions(self) -> List[Tuple[float, float, float]]:
        """Get spawn positions for four corners (x, y, angle)
        Ensures spawns are outside buildings and not inside rooms
        """
        offset = 5
        map_size = self.game_map.size if self.game_map else self.selected_map_size

        # Try multiple positions near each corner to find one that's not in a building
        def find_safe_spawn(
            base_x: float, base_y: float, angle: float
        ) -> Tuple[float, float, float]:
            """Find a safe spawn position near the base coordinates"""
            if not self.game_map:
                return (base_x, base_y, angle)

            for attempt in range(10):
                # Try positions in a small radius around the corner
                radius = attempt * 2
                for angle_offset in [
                    0,
                    math.pi / 4,
                    math.pi / 2,
                    3 * math.pi / 4,
                    math.pi,
                    5 * math.pi / 4,
                    3 * math.pi / 2,
                    7 * math.pi / 4,
                ]:
                    test_x = base_x + math.cos(angle_offset) * radius
                    test_y = base_y + math.sin(angle_offset) * radius

                    # Ensure within bounds
                    if (
                        test_x < 2
                        or test_x >= map_size - 2
                        or test_y < 2
                        or test_y >= map_size - 2
                    ):
                        continue

                    # Check if not in building and not a wall
                    if not self.game_map.is_wall(
                        test_x, test_y
                    ) and not self.game_map.is_inside_building(test_x, test_y):
                        return (test_x, test_y, angle)

            # Fallback to base position if all attempts fail
            return (base_x, base_y, angle)

        # Building 4 occupies 0.75 * size to 0.95 * size, so bottom-right spawn must be before 0.75 * size
        # Calculate offset from map edge for bottom-right spawn (outside Building 4)
        building4_start = int(map_size * 0.75)
        bottom_right_offset = map_size - building4_start + SPAWN_SAFETY_MARGIN

        corners = [
            (offset, offset, math.pi / 4),  # Top-left
            (offset, map_size - offset, 7 * math.pi / 4),  # Bottom-left
            (map_size - offset, offset, 3 * math.pi / 4),  # Top-right
            (
                map_size - bottom_right_offset,
                map_size - bottom_right_offset,
                5 * math.pi / 4,
            ),  # Bottom-right
        ]

        # Find safe spawns for each corner
        safe_corners = []
        for x, y, angle in corners:
            safe_corners.append(find_safe_spawn(x, y, angle))

        return safe_corners

    def start_game(self) -> None:
        """Start new game"""
        self.level = 1
        self.kills = 0
        self.level_times = []
        # Create map with selected size
        self.game_map = Map(self.selected_map_size)
        self.raycaster = Raycaster(self.game_map)
        self.start_level()

    def start_level(self) -> None:
        """Start a new level"""
        assert self.game_map is not None
        self.level_start_time = pygame.time.get_ticks()
        corners = self.get_corner_positions()
        random.shuffle(corners)

        # Player spawns in first corner - ensure it's safe
        player_pos = corners[0]
        # Double-check player spawn is safe
        if self.game_map.is_wall(
            player_pos[0], player_pos[1]
        ) or self.game_map.is_inside_building(player_pos[0], player_pos[1]):
            # Find a nearby safe position
            for attempt in range(20):
                test_x = player_pos[0] + random.uniform(-3, 3)
                test_y = player_pos[1] + random.uniform(-3, 3)
                if (
                    not self.game_map.is_wall(test_x, test_y)
                    and not self.game_map.is_inside_building(test_x, test_y)
                    and 2 <= test_x < self.game_map.size - 2
                    and 2 <= test_y < self.game_map.size - 2
                ):
                    player_pos = (test_x, test_y, player_pos[2])
                    break
        self.player = Player(player_pos[0], player_pos[1], player_pos[2])

        # Bots spawn in other three corners - same enemy type per corner, 4-5 enemies per corner
        self.bots = []
        self.projectiles = []  # Reset projectiles
        enemies_per_corner = 4 + (self.level - 1)  # 4-5 enemies, increasing with level

        for i in range(1, 4):
            bot_pos = corners[i]
            # Same enemy type for all enemies in this corner
            enemy_type = random.choice(list(ENEMY_TYPES.keys()))

            # Spawn multiple enemies around this corner position
            for j in range(enemies_per_corner):
                # Spread enemies in a small radius around the corner
                angle_offset = j * 2 * math.pi / enemies_per_corner
                radius = (
                    1.5 + (j % 2) * 0.5
                )  # Alternate between close and slightly further
                spawn_x = bot_pos[0] + math.cos(angle_offset) * radius
                spawn_y = bot_pos[1] + math.sin(angle_offset) * radius

                # Ensure spawn is safe (not in wall, not in building, within bounds)
                if (
                    not self.game_map.is_wall(spawn_x, spawn_y)
                    and not self.game_map.is_inside_building(spawn_x, spawn_y)
                    and 2 <= spawn_x < self.game_map.size - 2
                    and 2 <= spawn_y < self.game_map.size - 2
                ):
                    self.bots.append(Bot(spawn_x, spawn_y, self.level, enemy_type))
                else:
                    # Try to find a nearby safe position
                    for attempt in range(10):
                        test_x = bot_pos[0] + random.uniform(-2, 2)
                        test_y = bot_pos[1] + random.uniform(-2, 2)
                        if (
                            not self.game_map.is_wall(test_x, test_y)
                            and not self.game_map.is_inside_building(test_x, test_y)
                            and 2 <= test_x < self.game_map.size - 2
                            and 2 <= test_y < self.game_map.size - 2
                        ):
                            self.bots.append(
                                Bot(test_x, test_y, self.level, enemy_type)
                            )
                            break

        self.state = "playing"

        # Enable mouse capture
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

    def handle_menu_events(self) -> None:
        """Handle menu events"""
        mouse_pos = pygame.mouse.get_pos()
        self.start_button.update(mouse_pos)
        for btn, _ in self.map_size_buttons:
            btn.update(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.start_button.is_clicked(mouse_pos):
                        self.start_game()
                    else:
                        # Check map size buttons
                        for btn, size in self.map_size_buttons:
                            if btn.is_clicked(mouse_pos):
                                self.selected_map_size = size
                                # Update button colors
                                for b, s in self.map_size_buttons:
                                    b.color = GREEN if s == size else DARK_GRAY
                                break

    def handle_game_events(self) -> None:
        """Handle gameplay events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
                # Weapon switching
                elif event.key == pygame.K_1:
                    assert self.player is not None
                    self.player.switch_weapon("pistol")
                elif event.key == pygame.K_2:
                    assert self.player is not None
                    self.player.switch_weapon("rifle")
                elif event.key == pygame.K_3:
                    assert self.player is not None
                    self.player.switch_weapon("shotgun")
                elif event.key == pygame.K_4:
                    assert self.player is not None
                    self.player.switch_weapon("plasma")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                assert self.player is not None
                if event.button == 3:  # Right-click to fire
                    if self.player.shoot():
                        self.check_shot_hit()
                elif (
                    event.button == 1
                ):  # Left-click to aim (currently no special effect)
                    pass  # No-op: Left-click aim not yet implemented
            elif event.type == pygame.MOUSEMOTION:
                assert self.player is not None
                self.player.rotate(event.rel[0] * PLAYER_ROT_SPEED)

    def check_shot_hit(self) -> None:
        """Check if player's shot hit a bot"""
        assert self.player is not None
        # Cast ray in player's view direction
        sin_a = math.sin(self.player.angle)
        cos_a = math.cos(self.player.angle)

        weapon_range = self.player.get_current_weapon_range()
        weapon_damage = self.player.get_current_weapon_damage()

        # Find closest bot in crosshair
        # "Headshot" detection: This is a precision-based mechanic.
        # Bots are rectangles without distinct head hitboxes; a very tight angular difference
        # between the player's crosshair and the bot's center is considered a "headshot".
        closest_bot = None
        closest_dist = float("inf")
        is_headshot = False

        for bot in self.bots:
            if not bot.alive:
                continue

            # Calculate bot position relative to player
            assert self.player is not None
            dx = bot.x - self.player.x
            dy = bot.y - self.player.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > weapon_range:
                continue

            # Check if bot is in front of player
            bot_angle = math.atan2(dy, dx)
            # Normalize bot_angle to [0, 2π) range for comparison (player.angle is already normalized)
            bot_angle_norm = bot_angle if bot_angle >= 0 else bot_angle + 2 * math.pi
            angle_diff = abs(bot_angle_norm - self.player.angle)
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff

            # Narrow hit detection (accurate shooting)
            if angle_diff < 0.15:
                # Check line of sight
                hit = True
                steps = int(distance * 10)
                for i in range(1, steps):
                    t = i / steps
                    assert self.player is not None
                    assert self.game_map is not None
                    check_x = self.player.x + dx * t
                    check_y = self.player.y + dy * t
                    if self.game_map.is_wall(check_x, check_y):
                        hit = False
                        break

                if hit and distance < closest_dist:
                    closest_bot = bot
                    closest_dist = distance
                    is_headshot = angle_diff < HEADSHOT_THRESHOLD

        # Damage the closest bot in crosshair
        if closest_bot:
            closest_bot.take_damage(weapon_damage, is_headshot=is_headshot)
            if not closest_bot.alive:
                self.kills += 1

    def update_game(self) -> None:
        """Update game state"""
        assert self.player is not None
        if not self.player.alive:
            self.state = "game_over"
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
            return

        # Check if all bots are dead
        all_dead = all(not bot.alive for bot in self.bots)
        if all_dead:
            # Record level completion time
            level_time = (
                pygame.time.get_ticks() - self.level_start_time
            ) / 1000.0  # Convert to seconds
            self.level_times.append(level_time)
            self.state = "level_complete"
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
            return

        assert self.player is not None
        assert self.game_map is not None
        keys = pygame.key.get_pressed()

        # Check for sprint (Shift key)
        is_sprinting = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        current_speed = PLAYER_SPRINT_SPEED if is_sprinting else PLAYER_SPEED

        # Movement
        if keys[pygame.K_w]:
            self.player.move(
                self.game_map, self.bots, forward=True, speed=current_speed
            )
        if keys[pygame.K_s]:
            self.player.move(
                self.game_map, self.bots, forward=False, speed=current_speed
            )
        if keys[pygame.K_a]:
            self.player.strafe(
                self.game_map, self.bots, right=False, speed=current_speed
            )
        if keys[pygame.K_d]:
            self.player.strafe(
                self.game_map, self.bots, right=True, speed=current_speed
            )

        # Arrow keys
        if keys[pygame.K_LEFT]:
            self.player.rotate(-0.05)
        if keys[pygame.K_RIGHT]:
            self.player.rotate(0.05)

        self.player.update()

        # Update bots and collect projectiles
        for bot in self.bots:
            projectile = bot.update(self.game_map, self.player, self.bots)
            if projectile:
                self.projectiles.append(projectile)

        # Update projectiles
        assert self.game_map is not None
        assert self.player is not None
        for projectile in self.projectiles[:]:
            projectile.update(self.game_map)

            # Check collision with player
            if not projectile.is_player:
                dx = projectile.x - self.player.x
                dy = projectile.y - self.player.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist < 0.5:  # Hit player
                    self.player.take_damage(projectile.damage)
                    projectile.alive = False

            # Remove dead projectiles
            if not projectile.alive:
                self.projectiles.remove(projectile)

    def render_menu(self) -> None:
        """Render main menu"""
        self.screen.fill(BLACK)

        # Stylized title "FORCE FIELD"
        title_y = 120
        title_text = "FORCE FIELD"
        # Draw title with outline effect
        for offset_x, offset_y in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            title_outline = self.title_font.render(title_text, True, DARK_RED)
            title_rect_outline = title_outline.get_rect(
                center=(SCREEN_WIDTH // 2 + offset_x, title_y + offset_y),
            )
            self.screen.blit(title_outline, title_rect_outline)
        title = self.title_font.render(title_text, True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        self.screen.blit(title, title_rect)

        # Subtitle
        subtitle = self.small_font.render("Arena Combat", True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, title_y + 80))
        self.screen.blit(subtitle, subtitle_rect)

        # Map size selection label
        map_label = self.small_font.render("Map Size:", True, CYAN)
        map_label_rect = map_label.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50),
        )
        self.screen.blit(map_label, map_label_rect)

        # Map size buttons
        for btn, _ in self.map_size_buttons:
            btn.draw(self.screen, self.tiny_font)

        # Instructions
        instructions = [
            "Fight waves of enemy monsters!",
            "Each level, enemies get stronger",
            "",
            "WASD: Move | Shift: Sprint | Mouse: Look | 1-4: Weapons | Right: Shoot",
        ]

        y = SCREEN_HEIGHT // 2 + 130
        for line in instructions:
            text = self.tiny_font.render(line, True, CYAN)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 30

        # Start button
        self.start_button.draw(self.screen, self.font)

        pygame.display.flip()

    def render_game(self) -> None:
        """Render gameplay"""
        # 3D view
        self.raycaster.render_floor_ceiling(self.screen)
        self.raycaster.render_3d(self.screen, self.player, self.bots)

        # Render projectiles
        self.render_projectiles()

        # Render rifle
        self.render_rifle()

        # Minimap
        self.raycaster.render_minimap(self.screen, self.player, self.bots)

        # HUD
        self.render_hud()

        # Crosshair
        self.render_crosshair()

        # Muzzle flash
        assert self.player is not None
        if self.player.shooting:
            self.render_muzzle_flash()

        pygame.display.flip()

    def render_rifle(self) -> None:
        """Render rifle weapon in first-person view"""
        # Rifle body (brown/black)
        rifle_color = DARK_BROWN
        barrel_color = (30, 30, 30)

        # Rifle position (bottom-right of screen)
        rifle_x = SCREEN_WIDTH - 250
        rifle_y = SCREEN_HEIGHT - 200

        # Stock
        pygame.draw.rect(
            self.screen, rifle_color, (rifle_x + 150, rifle_y + 120, 80, 40)
        )

        # Main body
        pygame.draw.rect(
            self.screen, rifle_color, (rifle_x + 80, rifle_y + 100, 120, 30)
        )

        # Barrel
        pygame.draw.rect(self.screen, barrel_color, (rifle_x, rifle_y + 105, 120, 20))

        # Front sight
        pygame.draw.rect(self.screen, BLACK, (rifle_x + 10, rifle_y + 95, 5, 15))

        # Magazine
        pygame.draw.rect(self.screen, BLACK, (rifle_x + 110, rifle_y + 125, 30, 50))

        # Trigger guard
        pygame.draw.rect(
            self.screen, barrel_color, (rifle_x + 140, rifle_y + 125, 15, 25)
        )

    def render_hud(self) -> None:
        """Render HUD in Doom-style"""
        hud_bottom = SCREEN_HEIGHT - 80

        # Health bar (left side)
        health_width = 150
        health_height = 25
        health_x = 20
        health_y = hud_bottom

        # Background
        pygame.draw.rect(
            self.screen, DARK_GRAY, (health_x, health_y, health_width, health_height)
        )
        # Health fill
        health_percent = max(0, self.player.health / self.player.max_health)
        fill_width = int(health_width * health_percent)
        health_color = (
            GREEN
            if health_percent > 0.5
            else (ORANGE if health_percent > 0.25 else RED)
        )
        pygame.draw.rect(
            self.screen, health_color, (health_x, health_y, fill_width, health_height)
        )
        # Border
        pygame.draw.rect(
            self.screen, WHITE, (health_x, health_y, health_width, health_height), 2
        )
        # Text
        health_text = self.tiny_font.render(f"HP: {self.player.health}", True, WHITE)
        self.screen.blit(health_text, (health_x + 5, health_y + 3))

        # Weapon display (center-bottom, Doom-style)
        weapon_x = SCREEN_WIDTH // 2 - 100
        weapon_y = hud_bottom
        weapon_width = 200
        weapon_height = 70  # Increased to accommodate hints

        # Weapon background
        pygame.draw.rect(
            self.screen, DARK_GRAY, (weapon_x, weapon_y, weapon_width, weapon_height)
        )
        pygame.draw.rect(
            self.screen, WHITE, (weapon_x, weapon_y, weapon_width, weapon_height), 2
        )

        # Current weapon name
        current_weapon_data = WEAPONS[self.player.current_weapon]
        weapon_name = self.small_font.render(current_weapon_data["name"], True, YELLOW)
        weapon_name_rect = weapon_name.get_rect(
            center=(weapon_x + weapon_width // 2, weapon_y + 15),
        )
        self.screen.blit(weapon_name, weapon_name_rect)

        # Ammo
        ammo_text = self.tiny_font.render(
            f"Ammo: {self.player.ammo[self.player.current_weapon]}", True, CYAN
        )
        ammo_rect = ammo_text.get_rect(
            center=(weapon_x + weapon_width // 2, weapon_y + 40),
        )
        self.screen.blit(ammo_text, ammo_rect)

        # Weapon selection hints (inside weapon box) - use cached string
        hints_text = self.tiny_font.render(self.weapon_hints, True, GRAY)
        hints_rect = hints_text.get_rect(
            center=(weapon_x + weapon_width // 2, weapon_y + 58),
        )
        self.screen.blit(hints_text, hints_rect)

        # Level and enemies (right side)
        level_text = self.small_font.render(f"Level: {self.level}", True, YELLOW)
        self.screen.blit(level_text, (SCREEN_WIDTH - 200, hud_bottom))

        bots_alive = sum(1 for bot in self.bots if bot.alive)
        total_enemies = (4 + (self.level - 1)) * 3  # 3 corners × enemies_per_corner
        kills_text = self.small_font.render(
            f"Enemies: {bots_alive}/{total_enemies}", True, RED
        )
        self.screen.blit(kills_text, (SCREEN_WIDTH - 200, hud_bottom + 30))

        # Controls hint (top left) - with semi-transparent background for better readability
        # Positioned on left to avoid overlapping minimap on right
        controls_hint_text = "WASD:Move | Shift:Sprint | ESC:Menu"
        controls_hint = self.tiny_font.render(controls_hint_text, True, WHITE)
        controls_hint_rect = controls_hint.get_rect(topleft=(10, 10))
        bg_surface = pygame.Surface(
            (
                controls_hint_rect.width + HINT_BG_PADDING_H,
                controls_hint_rect.height + HINT_BG_PADDING_V,
            ),
            pygame.SRCALPHA,
        )
        bg_surface.fill(HINT_BG_COLOR)
        self.screen.blit(
            bg_surface,
            (
                controls_hint_rect.x - HINT_BG_PADDING_H // 2,
                controls_hint_rect.y - HINT_BG_PADDING_V // 2,
            ),
        )
        self.screen.blit(controls_hint, controls_hint_rect)

    def render_crosshair(self) -> None:
        """Render crosshair"""
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        size = 12

        # Crosshair lines
        pygame.draw.line(self.screen, RED, (cx - size, cy), (cx + size, cy), 2)
        pygame.draw.line(self.screen, RED, (cx, cy - size), (cx, cy + size), 2)

        # Center dot
        pygame.draw.circle(self.screen, RED, (cx, cy), 2)

    def render_muzzle_flash(self) -> None:
        """Render muzzle flash"""
        # Flash near rifle barrel
        flash_x = SCREEN_WIDTH - 350
        flash_y = SCREEN_HEIGHT - 85

        pygame.draw.circle(self.screen, YELLOW, (flash_x, flash_y), 25)
        pygame.draw.circle(self.screen, ORANGE, (flash_x, flash_y), 15)
        pygame.draw.circle(self.screen, WHITE, (flash_x, flash_y), 8)

    def render_projectiles(self) -> None:
        """Render bot projectiles"""
        for projectile in self.projectiles:
            if not projectile.alive:
                continue

            # Calculate projectile position relative to player
            dx = projectile.x - self.player.x
            dy = projectile.y - self.player.y
            proj_dist = math.sqrt(dx**2 + dy**2)

            if proj_dist > MAX_DEPTH:
                continue

            # Calculate angle to projectile
            proj_angle = math.atan2(dy, dx)
            angle_to_proj = proj_angle - self.player.angle

            # Normalize angle
            while angle_to_proj > math.pi:
                angle_to_proj -= 2 * math.pi
            while angle_to_proj < -math.pi:
                angle_to_proj += 2 * math.pi

            # Check if projectile is in FOV
            if abs(angle_to_proj) < HALF_FOV:
                # Calculate screen position
                proj_size = max(2, 10 / proj_dist) if proj_dist > 0 else 10
                proj_x = (
                    SCREEN_WIDTH / 2 + (angle_to_proj / HALF_FOV) * SCREEN_WIDTH / 2
                )
                proj_y = SCREEN_HEIGHT / 2

                # Draw projectile as a glowing circle
                pygame.draw.circle(
                    self.screen, RED, (int(proj_x), int(proj_y)), int(proj_size)
                )
                pygame.draw.circle(
                    self.screen,
                    ORANGE,
                    (int(proj_x), int(proj_y)),
                    int(proj_size * 0.6),
                )

    def render_stats_lines(
        self, stats: List[Tuple[str, Tuple[int, int, int]]], start_y: int
    ) -> None:
        """Helper method to render stats lines with spacing

        Args:
            stats: List of (text, color) tuples. Empty strings create spacing.
            start_y: Starting y position for rendering
        """
        y = start_y
        for line, color in stats:
            if line:  # Skip empty lines
                text = self.small_font.render(line, True, color)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
                self.screen.blit(text, text_rect)
            y += 40  # Always increment y to create spacing, even for empty lines

    def render_level_complete(self) -> None:
        """Render level complete screen"""
        self.screen.fill(BLACK)

        # Title
        title = self.title_font.render("LEVEL COMPLETE!", True, GREEN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        # Stats
        level_time = self.level_times[-1] if self.level_times else 0
        total_time = sum(self.level_times)
        # Define stats with explicit color information
        stats = [
            (f"Level {self.level} cleared!", WHITE),
            (f"Time: {level_time:.1f}s", GREEN),
            (f"Total Time: {total_time:.1f}s", GREEN),
            (f"Total Kills: {self.kills}", WHITE),
            ("", WHITE),
            ("Next level: Enemies get stronger!", YELLOW),
            ("", WHITE),
            ("Press SPACE for next level", WHITE),
            ("Press ESC for menu", WHITE),
        ]

        self.render_stats_lines(stats, 250)

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

    def render_game_over(self) -> None:
        """Render game over screen"""
        self.screen.fill(BLACK)

        # Title
        title = self.title_font.render("GAME OVER", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        # Stats
        completed_levels = max(0, self.level - 1)
        total_time = sum(self.level_times)
        avg_time = total_time / len(self.level_times) if self.level_times else 0
        # Define stats with explicit color information
        stats = [
            (
                f"You survived {completed_levels} level{'s' if completed_levels != 1 else ''}",
                WHITE,
            ),
            (f"Total Kills: {self.kills}", WHITE),
            (f"Total Time: {total_time:.1f}s", GREEN),
            (
                (f"Average Time/Level: {avg_time:.1f}s", GREEN)
                if self.level_times
                else ("", WHITE)
            ),
            ("", WHITE),
            ("Press SPACE to restart", WHITE),
            ("Press ESC for menu", WHITE),
        ]

        self.render_stats_lines(stats, 250)

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

    def run(self) -> None:
        """Main game loop"""
        while self.running:
            if self.state == "intro":
                self.handle_intro_events()
                self.render_intro()
            elif self.state == "menu":
                self.handle_menu_events()
                self.render_menu()
            elif self.state == "playing":
                self.handle_game_events()
                self.update_game()
                self.render_game()
            elif self.state == "level_complete":
                self.handle_level_complete_events()
                self.render_level_complete()
            elif self.state == "game_over":
                self.handle_game_over_events()
                self.render_game_over()

            self.clock.tick(FPS)

    def handle_intro_events(self) -> None:
        """Handle intro screen events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                    self.intro_scroll_y = SCREEN_HEIGHT  # Reset for next time

    def render_intro(self) -> None:
        """Render Star Wars style opening crawl"""
        self.screen.fill(BLACK)

        # Star Wars style opening text
        intro_text = [
            "A long time ago in a galaxy",
            "far, far away...",
            "",
            "",
            "FORCE FIELD",
            "",
            "The arena has become a battleground",
            "for the forces of darkness.",
            "",
            "Enemy hordes have invaded the",
            "abandoned military complex,",
            "seeking to claim it as their own.",
            "",
            "You are the last defender.",
            "Armed with an arsenal of weapons,",
            "you must fight through wave after",
            "wave of increasingly powerful enemies.",
            "",
            "Each corner of the arena spawns",
            "a different enemy type, united",
            "in their goal to destroy you.",
            "",
            "Survive. Fight. Win.",
            "",
            "",
            "The battle begins now...",
        ]

        # Scroll text upward
        if self.intro_start_time == 0:
            self.intro_start_time = pygame.time.get_ticks()

        elapsed = (pygame.time.get_ticks() - self.intro_start_time) / 1000.0
        scroll_speed = 50  # pixels per second
        self.intro_scroll_y = SCREEN_HEIGHT - elapsed * scroll_speed

        # Render text
        line_height = 40
        start_y = self.intro_scroll_y

        for i, line in enumerate(intro_text):
            y = start_y + i * line_height

            # Skip if off screen
            if y < -line_height or y > SCREEN_HEIGHT + line_height:
                continue

            if line == "FORCE FIELD":
                # Title text - larger and yellow
                text = self.title_font.render(line, True, YELLOW)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
                self.screen.blit(text, text_rect)
            elif line:
                # Regular text - white
                text = self.font.render(line, True, WHITE)
                text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
                self.screen.blit(text, text_rect)

        # Auto-advance to menu after text scrolls past
        if self.intro_scroll_y < -len(intro_text) * line_height:
            self.state = "menu"
            self.intro_scroll_y = SCREEN_HEIGHT

        pygame.display.flip()

        pygame.quit()
        sys.exit()


def main() -> None:
    """Entry point of the FPS Shooter application.

    Initializes the game and starts the main game loop.
    """
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
