import os

from games.shared.asset_catalog import AssetCatalog
from games.shared.constants import FPS_SHARED_CONSTANTS

from .custom_types import EnemyData, LevelTheme, WeaponData

globals().update(FPS_SHARED_CONSTANTS)  # type: ignore[attr-defined]

# Constants (shared values pulled from shared constants)
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SPAWN_SAFETY_MARGIN = 3

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
SKY_COLOR = (20, 0, 0)  # Dark Red Sky
SHIELD_COLOR = (255, 100, 0)  # Orange Shield
DAMAGE_TEXT_COLOR = (255, 0, 0)  # Bloody text

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
CHEAT_AMMO_AMOUNT = 999  # Full ammo granted by IDFA cheat code
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
}

# Level Themes (Wall Color Palette per level modulo)
LEVEL_THEMES: list[LevelTheme] = [
    # 0: Hell Keep (Red/Brick)
    {
        "floor": (40, 0, 0),
        "ceiling": SKY_COLOR,
        "walls": {1: (100, 50, 50), 2: (80, 40, 40), 3: (120, 60, 60), 4: (60, 30, 30)},
    },
    # 1: Blood Pools (Red/Liquid)
    {
        "floor": (60, 0, 0),
        "ceiling": (20, 0, 0),
        "walls": {
            1: (150, 0, 0),
            2: (100, 0, 0),
            3: (200, 50, 50),
            4: (50, 0, 0),
        },
    },
    # 2: Gothic Tech (Dark Gray/Green)
    {
        "floor": (30, 30, 30),
        "ceiling": (10, 10, 10),
        "walls": {
            1: (80, 80, 80),
            2: (60, 60, 60),
            3: (40, 100, 40),  # Toxic pipes
            4: (100, 100, 100),
        },
    },
    # 3: Void (Purple/Black)
    {
        "floor": (20, 0, 40),
        "ceiling": (0, 0, 0),
        "walls": {
            1: (50, 0, 100),
            2: (30, 0, 80),
            3: (80, 0, 150),
            4: (20, 0, 50),
        },
    },
]
