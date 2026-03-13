import math
import os

from games.shared.asset_catalog import AssetCatalog

from .custom_types import EnemyData, LevelTheme, WeaponData

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600  # Reduced from 768 to fit better on laptop screens
FPS = 60

# Map settings
MAP_SIZE = 40  # Will be set by user
TILE_SIZE = 64
MIN_BUILDING_OFFSET = 3  # Minimum offset from map edges for building generation
WALL_HIDDEN = 5
BOMBS_START = 3

# Rendering Quality
# 1 = Ultra (Full Res), 2 = High (Half Res),
# 4 = Medium/Retro (Quarter Res), 8 = Low (Blocky)
DEFAULT_RENDER_SCALE = 2

# Player settings
# Speeds reduced to improve game pacing - further reduced for better control
PLAYER_SPEED = 0.19  # Reduced from 0.375 (about half)
PLAYER_SPRINT_SPEED = 0.29  # Reduced from 0.575 (about half)
PLAYER_ROT_SPEED = 0.0015
SENSITIVITY_X = 1.0
DASH_SPEED_MULT = 2.5
DASH_STAMINA_COST = 20
DASH_DURATION = 10
DASH_COOLDOWN = 60
MAX_RAYCAST_STEPS = 1000  # Maximum steps for raycasting

FOV = math.pi / 3  # 60 degrees
HALF_FOV = FOV / 2

MAX_DEPTH = 100  # Increased render distance (2x)

DEFAULT_PLAYER_SPAWN = (2.5, 2.5, 0.0)
SPAWN_SAFE_ZONE_RADIUS = 10.0  # Reduced safe zone (was 15.0)
MIN_BOSS_DISTANCE = 10.0
MAP_SIZES = [20, 30, 40, 50, 60]

# New Game Defaults
DEFAULT_LIVES = 3
DEFAULT_DIFFICULTY = "NORMAL"
DEFAULT_START_LEVEL = 1

# Difficulty Settings
DIFFICULTIES = {
    "EASY": {"damage_mult": 0.5, "health_mult": 0.7, "score_mult": 0.5},
    "NORMAL": {"damage_mult": 1.0, "health_mult": 1.0, "score_mult": 1.0},
    "HARD": {"damage_mult": 1.5, "health_mult": 1.5, "score_mult": 2.0},
    "NIGHTMARE": {"damage_mult": 2.5, "health_mult": 2.0, "score_mult": 4.0},
}

# Weapon Ranges
WEAPON_RANGE_PISTOL = 15
WEAPON_RANGE_RIFLE = 25
WEAPON_RANGE_SHOTGUN = 12  # Increased range (was 8)
WEAPON_RANGE_PLASMA = 30
WEAPON_RANGE_PULSE = 35
WEAPON_RANGE_STORMTROOPER = 30
WEAPON_RANGE_MINIGUN = 20
WEAPON_RANGE_SNIPER = 40
WEAPON_RANGE_FREEZER = 15

# Weapon settings
_catalog_path = os.path.dirname(os.path.dirname(__file__))
_catalog = AssetCatalog(_catalog_path)
WEAPONS: dict[str, WeaponData] = _catalog.load_json("config/weapons.json") or {}
for k in WEAPONS:
    if "projectile_color" in WEAPONS[k]:
        pc = WEAPONS[k]["projectile_color"]
        WEAPONS[k]["projectile_color"] = (int(pc[0]), int(pc[1]), int(pc[2]))
    if "beam_color" in WEAPONS[k]:
        bc = WEAPONS[k]["beam_color"]
        WEAPONS[k]["beam_color"] = (int(bc[0]), int(bc[1]), int(bc[2]))

# Combat settings
HEADSHOT_THRESHOLD = 0.05
SPAWN_SAFETY_MARGIN = 3
PLASMA_AOE_RADIUS = 3.0  # Reduced AOE (was 6.0)
PULSE_AOE_RADIUS = 1.5
MAX_COLLISION_DIST = 2.0  # Max distance to check for collisions

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

# Fog
FOG_COLOR = SKY_COLOR  # Fade to sky color
FOG_START = 0.4  # Percentage of MAX_DEPTH where fog starts

# Input
JOYSTICK_DEADZONE = 0.1
PITCH_LIMIT = 390  # Pixels up/down
SENSITIVITY_Y = 1.0

# Shield Settings
SHIELD_MAX_DURATION = 600  # 10 seconds at 60 FPS
SHIELD_COOLDOWN_NORMAL = 600  # 10 seconds
SHIELD_COOLDOWN_DEPLETED = 900  # 15 seconds
BOMB_RADIUS = 10
BOMB_COOLDOWN = 1800  # 30 seconds
# (if we want cooldown, user didn't specify, but implies rare use)

# System Constants
SAVE_FILE_PATH = "savegame.txt"
SPAWN_RETRY_RADIUS = 4

# Start Menu Map Size
DEFAULT_MAP_SIZE = 40

# Balancing
BOT_SPEED = 0.02  # Slower enemies (was 0.03)
PLAYER_HEALTH = 100
BASE_BOT_HEALTH = 30
BASE_BOT_DAMAGE = 2  # Reduced from 3
BOT_ATTACK_RANGE = 5
BOT_ATTACK_COOLDOWN = 60
BOT_PROJECTILE_SPEED = 0.08  # Reduced from 0.1
BOT_PROJECTILE_DAMAGE = 5  # Reduced from 6

# Spread (Aiming randomness)
SPREAD_BASE = 0.05
SPREAD_ZOOM = 0.005

# Zoom
ZOOM_FOV_MULT = 0.5  # 2x Zoom (Half FOV)

# Secondary Fire
SECONDARY_COOLDOWN = 600  # 10 seconds
SECONDARY_DAMAGE_MULT = 10.0  # Massively destructive
LASER_DURATION = 30  # Longer show
LASER_WIDTH = 40  # Huge beam
LASER_AOE_RADIUS = 8.0

ZOMBIE_COLOR = (107, 138, 111)
BOSS_COLOR = (140, 63, 63)
DEMON_COLOR = (181, 43, 29)
DINOSAUR_COLOR = (63, 163, 77)
RAIDER_COLOR = (122, 92, 255)
NINJA_COLOR = (0, 0, 100)
SNIPER_COLOR = (70, 70, 70)
ICE_ZOMBIE_COLOR = (150, 200, 255)

ENEMY_TYPES: dict[str, EnemyData] = _catalog.load_json("config/enemies.json") or {}
for k in ENEMY_TYPES:
    if "color" in ENEMY_TYPES[k]:
        ec = ENEMY_TYPES[k]["color"]
        ENEMY_TYPES[k]["color"] = (int(ec[0]), int(ec[1]), int(ec[2]))

# Wall colors
WALL_COLORS = {
    1: (100, 100, 100),
    2: (139, 69, 19),
    3: (150, 75, 0),
    4: (180, 180, 180),
    5: (80, 80, 90),
}

# Level Themes (Wall Color Palette per level modulo)
LEVEL_THEMES: list[LevelTheme] = [
    # 0: Standard (Gray/Brown)
    {
        "floor": DARK_GRAY,
        "ceiling": SKY_COLOR,
        "walls": {
            1: GRAY,
            2: BROWN,
            3: DARK_BROWN,
            4: (180, 180, 180),
            5: (80, 80, 90),
        },
    },
    # 1: Mars (Red/Orange)
    {
        "floor": (50, 20, 20),
        "ceiling": (40, 10, 10),
        "walls": {
            1: (150, 50, 50),
            2: (180, 80, 40),
            3: (100, 30, 30),
            4: (200, 100, 50),
            5: (100, 40, 40),
        },
    },
    # 2: Cyber (Neon/Dark)
    {
        "floor": (10, 10, 20),
        "ceiling": (5, 5, 20),
        "walls": {
            1: (0, 100, 200),
            2: (0, 200, 200),
            3: (0, 50, 150),
            4: (100, 0, 200),
            5: (50, 0, 100),
        },
    },
    # 3: Toxic (Green)
    {
        "floor": (20, 40, 20),
        "ceiling": (10, 30, 10),
        "walls": {
            1: (50, 150, 50),
            2: (100, 180, 40),
            3: (30, 100, 30),
            4: (150, 200, 100),
            5: (40, 100, 40),
        },
    },
]
