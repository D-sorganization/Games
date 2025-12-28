import math

from .custom_types import EnemyData, LevelTheme, WeaponData

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600  # Reduced from 768 to fit better on laptop screens
FPS = 60

# Map settings
MAP_SIZE = 40  # Will be set by user
TILE_SIZE = 64
MIN_BUILDING_OFFSET = 3  # Minimum offset from map edges for building generation
WALL_SECRET = 5
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
WEAPON_RANGE_STORMTROOPER = 30
WEAPON_RANGE_MINIGUN = 20
WEAPON_RANGE_SNIPER = 40

# Weapon settings
WEAPONS: dict[str, WeaponData] = {
    "pistol": {
        "name": "Pistol",
        "damage": 25,
        "range": WEAPON_RANGE_PISTOL,
        "ammo": 48,  # Reasonable starting ammo
        "cooldown": 10,
        "clip_size": 12,
        "reload_time": 60,  # 1 second
        "key": "1",
        "automatic": True,  # Semi-auto, but felt "broken" if clicks missed.
    },
    "rifle": {
        "name": "Rifle",
        "damage": 40,  # Increased damage (was 20)
        "range": WEAPON_RANGE_RIFLE,
        "ammo": 90,  # 3 clips
        "cooldown": 8,  # Faster fire rate (was 40, then 20)
        "automatic": True,  # Fix: Make it automatic
        "clip_size": 15,  # Reduced clip size (was 30)
        "reload_time": 120,  # 2 seconds
        "key": "2",
    },
    "shotgun": {
        "name": "Shotgun",
        "damage": 20,
        "range": WEAPON_RANGE_SHOTGUN,
        "ammo": 24,  # 12 shots
        "cooldown": 30,
        "clip_size": 2,  # Two shots
        "reload_time": 80,
        "pellets": 8,
        "spread": 0.15,
        "key": "3",
        "automatic": True,
    },
    "minigun": {
        "name": "Minigun",
        "damage": 12,
        "range": WEAPON_RANGE_MINIGUN,
        "ammo": 200,  # 2 belts
        "cooldown": 3,
        "automatic": True,
        "clip_size": 100,
        "reload_time": 150,
        "key": "7",
        "spin_up_time": 30,
    },
    "plasma": {
        "name": "Plasma",
        "damage": 100,
        "range": WEAPON_RANGE_PLASMA,
        "ammo": 100,
        "cooldown": 8,
        "automatic": True,
        "clip_size": 999,
        "heat_per_shot": 0.25,
        "max_heat": 1.0,
        "cooling_rate": 0.01,
        "overheat_penalty": 180,
        "projectile_speed": 0.5,
        "projectile_color": (0, 191, 255),
        "key": "5",
    },
    "laser": {
        "name": "Laser",
        "damage": 50,  # Continuous damage capability
        "range": 50,  # Long range
        "ammo": 100,
        "cooldown": 5,  # Very fast fire
        "automatic": True,
        "clip_size": 100,
        "reload_time": 100,
        "key": "4",
        "beam_color": (255, 0, 0),  # Red laser
        "beam_width": 15,  # Thicker beam (STAR WARS style)
    },
    "rocket": {
        "name": "Rocket Launcher",
        "damage": 150,
        "range": 100,
        "ammo": 10,
        "cooldown": 45,
        "clip_size": 1,
        "reload_time": 180,
        "key": "6",
        "projectile_speed": 0.3,
        "projectile_color": (255, 100, 0),
        "aoe_radius": 6.0,
    },
    "bfg": {
        "name": "BFG 9000",
        "damage": 500,
        "range": 100,
        "ammo": 5,
        "cooldown": 60,
        "clip_size": 1,
        "reload_time": 200,
        "key": "8",
        "projectile_speed": 0.2,
        "projectile_color": (0, 255, 0),
        "aoe_radius": 15.0,
    },
    "flamethrower": {
        "name": "Flamethrower",
        "damage": 8,
        "range": 18,
        "ammo": 300,
        "cooldown": 2,
        "automatic": True,
        "clip_size": 100,
        "reload_time": 180,
        "key": "9",
        "projectile_speed": 0.35,
        "projectile_color": (255, 140, 0),
    },
}

# Combat settings
HEADSHOT_THRESHOLD = 0.05
SPAWN_SAFETY_MARGIN = 3
PLASMA_AOE_RADIUS = 3.0  # Reduced AOE (was 6.0)

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

ENEMY_TYPES: dict[str, EnemyData] = {
    "zombie": {
        "color": ZOMBIE_COLOR,
        "health_mult": 1.0,
        "speed_mult": 0.8,
        "damage_mult": 1.0,
        "scale": 1.0,
        "visual_style": "monster",
    },
    "ghost": {
        "color": (200, 200, 255),
        "health_mult": 0.6,
        "speed_mult": 0.6,
        "damage_mult": 1.5,
        "scale": 0.9,
        "visual_style": "ghost",
    },
    "boss": {
        "color": BOSS_COLOR,
        "health_mult": 5.0,
        "speed_mult": 0.5,
        "damage_mult": 2.0,
        "scale": 1.4,
        "visual_style": "monster",
    },
    "demon": {
        "color": DEMON_COLOR,
        "health_mult": 0.5,
        "speed_mult": 1.2,
        "damage_mult": 1.5,
        "scale": 0.8,
        "visual_style": "monster",
    },
    "dinosaur": {
        "color": DINOSAUR_COLOR,
        "health_mult": 2.0,
        "speed_mult": 0.9,
        "damage_mult": 1.0,
        "scale": 1.0,
        "visual_style": "monster",
    },
    "raider": {
        "color": RAIDER_COLOR,
        "health_mult": 1.1,
        "speed_mult": 1.0,
        "damage_mult": 1.2,
        "scale": 1.0,
        "visual_style": "monster",
    },
    "ninja": {
        "color": NINJA_COLOR,
        "health_mult": 0.5,
        "speed_mult": 1.5,
        "damage_mult": 1.2,
        "scale": 0.9,
        "visual_style": "ghost",
    },
    "sniper": {
        "color": SNIPER_COLOR,
        "health_mult": 0.5,
        "speed_mult": 0.9,
        "damage_mult": 3.0,
        "scale": 0.8,
        "visual_style": "ghost",
    },
    # Baby Variants (Cute/Creepy Round Style)
    "baby_zombie": {
        "color": (200, 255, 200),
        "health_mult": 0.4,
        "speed_mult": 1.3,
        "damage_mult": 0.5,
        "scale": 0.5,
        "visual_style": "baby",
    },
    "mutant_baby": {
        "color": (255, 180, 200),
        "health_mult": 0.6,
        "speed_mult": 1.1,
        "damage_mult": 0.7,
        "scale": 0.6,
        "visual_style": "baby",
    },
    "health_pack": {
        "color": (0, 255, 0),
        "health_mult": 1.0,
        "speed_mult": 0.0,
        "damage_mult": 0.0,
        "scale": 0.5,
        "visual_style": "item",
    },
    "pickup_rocket": {
        "color": (255, 100, 0),
        "health_mult": 1.0,
        "speed_mult": 0.0,
        "damage_mult": 0.0,
        "scale": 0.5,
        "visual_style": "item",
    },
    "ammo_box": {
        "color": (255, 255, 0),
        "health_mult": 1.0,
        "speed_mult": 0.0,
        "damage_mult": 0.0,
        "scale": 0.4,
        "visual_style": "item",
    },
    "bomb_item": {
        "color": (50, 50, 50),
        "health_mult": 1.0,
        "speed_mult": 0.0,
        "damage_mult": 0.0,
        "scale": 0.4,
        "visual_style": "item",
    },
    "pickup_rifle": {
        "color": (100, 100, 255),
        "health_mult": 1.0,
        "speed_mult": 0.0,
        "damage_mult": 0.0,
        "scale": 0.5,
        "visual_style": "item",
    },
    "pickup_shotgun": {
        "color": (150, 75, 0),
        "health_mult": 1.0,
        "speed_mult": 0.0,
        "damage_mult": 0.0,
        "scale": 0.5,
        "visual_style": "item",
    },
    "pickup_plasma": {
        "color": (0, 255, 255),
        "health_mult": 1.0,
        "speed_mult": 0.0,
        "damage_mult": 0.0,
        "scale": 0.5,
        "visual_style": "item",
    },
    "pickup_minigun": {
        "color": (150, 150, 255),
        "health_mult": 1.0,
        "speed_mult": 0.0,
        "damage_mult": 0.0,
        "scale": 0.5,
        "visual_style": "item",
    },
    "pickup_flamethrower": {
        "color": (255, 140, 0),
        "health_mult": 1.0,
        "speed_mult": 0.0,
        "damage_mult": 0.0,
        "scale": 0.5,
        "visual_style": "item",
    },
    "minigunner": {
        "color": (100, 100, 150),
        "health_mult": 2.0,
        "speed_mult": 0.5,
        "damage_mult": 0.8,
        "scale": 1.2,
        "visual_style": "monster",
    },
    "ball": {
        "color": (50, 50, 50),  # Metallic
        "health_mult": 3.0,
        "speed_mult": 2.5,  # Very fast
        "damage_mult": 3.0,  # Crushing damage
        "scale": 1.5,
        "visual_style": "ball",
    },
    "beast": {
        "color": (160, 40, 40),  # Dark Red
        "health_mult": 6.0,
        "speed_mult": 0.4,  # Slow
        "damage_mult": 2.5,
        "scale": 3.0,  # Huge
        "visual_style": "beast",
    },
    "cyber_demon": {
        "color": (50, 50, 50),
        "health_mult": 15.0,
        "speed_mult": 0.3,
        "damage_mult": 4.0,
        "scale": 4.0,  # Massive
        "visual_style": "cyber_demon",
    },
}

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
