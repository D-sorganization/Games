import math

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

# Bot settings
BASE_BOT_HEALTH = 125
BASE_BOT_DAMAGE = 10
BOT_SPEED = 0.05
BOT_ATTACK_RANGE = 12
BOT_ATTACK_COOLDOWN = 90
BOT_PROJECTILE_SPEED = 0.3
BOT_PROJECTILE_DAMAGE = 15

# Combat settings
HEADSHOT_THRESHOLD = 0.05
SPAWN_SAFETY_MARGIN = 3

# UI settings
HINT_BG_PADDING_H = 10
HINT_BG_PADDING_V = 4
HINT_BG_COLOR = (30, 30, 30, 180)

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
BLUE_BLOOD = (0, 191, 255)
SKY_COLOR = (10, 10, 25)
SHIELD_COLOR = (0, 255, 255)
DAMAGE_TEXT_COLOR = (255, 255, 255)

# Visual Constants
SHIELD_ALPHA = 30
PARTICLE_LIFETIME = 30
INTRO_FADE_MAX = 255
INTRO_FADE_SCALE = 510

# System Constants
SAVE_FILE_PATH = "savegame.txt"
SPAWN_RETRY_RADIUS = 4

ZOMBIE_COLOR = (107, 138, 111)
BOSS_COLOR = (140, 63, 63)
DEMON_COLOR = (181, 43, 29)
DINOSAUR_COLOR = (63, 163, 77)
RAIDER_COLOR = (122, 92, 255)

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
