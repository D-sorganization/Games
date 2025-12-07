import math

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Map settings
MAP_SIZE = 40  # Will be set by user
TILE_SIZE = 64
MIN_BUILDING_OFFSET = 3  # Minimum offset from map edges for building generation

# Player settings
# Player settings
PLAYER_SPEED = 0.75
PLAYER_SPRINT_SPEED = 1.15
PLAYER_ROT_SPEED = 0.003
FOV = math.pi / 3  # 60 degrees
HALF_FOV = FOV / 2
NUM_RAYS = SCREEN_WIDTH // 2
MAX_DEPTH = 50  # Increased render distance
DELTA_ANGLE = FOV / NUM_RAYS

# New Game Defaults
DEFAULT_LIVES = 3
DEFAULT_DIFFICULTY = "NORMAL"
DEFAULT_START_LEVEL = 1

# Difficulty Settings
DIFFICULTIES = {
    "EASY": {"damage_mult": 0.5, "health_mult": 0.7, "score_mult": 0.5},
    "NORMAL": {"damage_mult": 1.0, "health_mult": 1.0, "score_mult": 1.0},
    "HARD": {"damage_mult": 1.5, "health_mult": 1.5, "score_mult": 2.0},
    "NIGHTMARE": {"damage_mult": 2.5, "health_mult": 2.0, "score_mult": 4.0}
}

# Weapon Ranges
WEAPON_RANGE_PISTOL = 15
WEAPON_RANGE_RIFLE = 25
WEAPON_RANGE_SHOTGUN = 8  # Short range
WEAPON_RANGE_PLASMA = 30

# Weapon settings
WEAPONS = {
    "pistol": {
        "name": "Pistol",
        "damage": 20,
        "range": WEAPON_RANGE_PISTOL,
        "ammo": 999,
        "cooldown": 10,
        "key": "1",
    },
    "rifle": {
        "name": "Rifle",
        "damage": 25,
        "range": WEAPON_RANGE_RIFLE,
        "ammo": 999,
        "cooldown": 15,
        "key": "2",
    },
    "shotgun": {
        "name": "Shotgun",
        "damage": 30,
        "range": WEAPON_RANGE_SHOTGUN,
        "ammo": 999,
        "cooldown": 20,
        "key": "3",
    },
    "plasma": {
        "name": "Plasma",
        "damage": 35,
        "range": WEAPON_RANGE_PLASMA,
        "ammo": 999,
        "cooldown": 12,
        "key": "4",
    },
}

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

# Shield Settings
SHIELD_MAX_DURATION = 600  # 10 seconds at 60 FPS
SHIELD_COOLDOWN_NORMAL = 600  # 10 seconds
SHIELD_COOLDOWN_DEPLETED = 900  # 15 seconds
BOMB_RADIUS = 10
BOMB_COOLDOWN = 1800  # 30 seconds (if we want cooldown, user didn't specify, but implies rare use)

# System Constants
SAVE_FILE_PATH = "savegame.txt"
SPAWN_RETRY_RADIUS = 4

# Start Menu Map Size
DEFAULT_MAP_SIZE = 40

# Balancing
BOT_SPEED = 0.03  # Slower enemies (was default fast?)
PLAYER_HEALTH = 100
BASE_BOT_HEALTH = 30
BASE_BOT_DAMAGE = 3
BOT_ATTACK_RANGE = 5
BOT_ATTACK_COOLDOWN = 60
BOT_PROJECTILE_SPEED = 0.1
BOT_PROJECTILE_DAMAGE = 6

# Spread (Aiming randomness)
SPREAD_BASE = 0.05
SPREAD_ZOOM = 0.01

# Zoom
ZOOM_FOV_MULT = 0.5  # 2x Zoom (Half FOV)

# Secondary Fire
SECONDARY_COOLDOWN = 600  # 10 seconds
SECONDARY_DAMAGE_MULT = 3.0
LASER_DURATION = 15
LASER_WIDTH = 5

ZOMBIE_COLOR = (107, 138, 111)
BOSS_COLOR = (140, 63, 63)
DEMON_COLOR = (181, 43, 29)
DINOSAUR_COLOR = (63, 163, 77)
RAIDER_COLOR = (122, 92, 255)

ENEMY_TYPES = {
    "zombie": {
        "color": ZOMBIE_COLOR,
        "health_mult": 1.0,
        "speed_mult": 0.8,  # slower
        "damage_mult": 1.0,
        "scale": 1.0,
    },
    "boss": {
        "color": BOSS_COLOR,
        "health_mult": 5.0,  # tough
        "speed_mult": 0.5,  # slow
        "damage_mult": 2.0,
        "scale": 1.4,
    },
    "demon": {
        "color": DEMON_COLOR,
        "health_mult": 0.5,  # weak
        "speed_mult": 1.2,  # fast
        "damage_mult": 1.5,
        "scale": 0.8,
    },
    "dinosaur": {
        "color": DINOSAUR_COLOR,
        "health_mult": 2.0,
        "speed_mult": 0.9,
        "damage_mult": 1.0,  # chomp
        "scale": 1.0,
    },
    "raider": {
        "color": RAIDER_COLOR,
        "health_mult": 1.1,
        "speed_mult": 1.0,
        "damage_mult": 1.2,
        "scale": 1.0,
    },
    "health_pack": {
        "color": (0, 255, 0),
        "health_mult": 1.0,
        "speed_mult": 0.0,
        "damage_mult": 0.0,
        "scale": 0.5,
    },
}

# Wall colors
WALL_COLORS = {
    1: (100, 100, 100),
    2: (139, 69, 19),
    3: (150, 75, 0),
    4: (180, 180, 180),
}

# Level Themes (Wall Color Palette per level modulo)
LEVEL_THEMES = [
    # 0: Standard (Gray/Brown)
    {
        "floor": DARK_GRAY,
        "ceiling": SKY_COLOR,
        "walls": {1: GRAY, 2: BROWN, 3: DARK_BROWN, 4: (180, 180, 180)},
    },
    # 1: Mars (Red/Orange)
    {
        "floor": (50, 20, 20),
        "ceiling": (40, 10, 10),
        "walls": {1: (150, 50, 50), 2: (180, 80, 40), 3: (100, 30, 30), 4: (200, 100, 50)},
    },
    # 2: Cyber (Neon/Dark)
    {
        "floor": (10, 10, 20),
        "ceiling": (5, 5, 20),
        "walls": {1: (0, 100, 200), 2: (0, 200, 200), 3: (0, 50, 150), 4: (100, 0, 200)},
    },
    # 3: Toxic (Green)
    {
        "floor": (20, 40, 20),
        "ceiling": (10, 30, 10),
        "walls": {1: (50, 150, 50), 2: (100, 180, 40), 3: (30, 100, 30), 4: (150, 200, 100)},
    },
]
