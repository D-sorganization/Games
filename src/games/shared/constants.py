"""Shared constants for all FPS games in the Games framework.

This module contains the common gameplay constants shared across
Duum, Force Field, and Zombie Survival. Game-specific constants
(colors, themes, unique enemy types) remain in each game's own
constants module and can override these defaults.

Usage in game-specific constants.py:
    from games.shared.constants import *  # noqa: F403
    # Then override only what differs, e.g.:
    # SKY_COLOR = (20, 0, 0)
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# Screen & Display
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# ---------------------------------------------------------------------------
# Rendering Quality
# ---------------------------------------------------------------------------
# 1 = Ultra (Full Res), 2 = High (Half Res),
# 4 = Medium/Retro (Quarter Res), 8 = Low (Blocky)
DEFAULT_RENDER_SCALE = 2
RENDER_SCALE_OPTIONS = [1, 2, 4, 8]
RENDER_SCALE_NAMES: dict[int, str] = {
    1: "ULTRA",
    2: "HIGH",
    4: "MEDIUM",
    8: "LOW",
}

# ---------------------------------------------------------------------------
# Map
# ---------------------------------------------------------------------------
MAP_SIZE = 40
TILE_SIZE = 64
MIN_BUILDING_OFFSET = 3
DEFAULT_MAP_SIZE = 40
MAP_SIZES = [20, 30, 40, 50, 60]

# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------
PLAYER_SPEED = 0.375
PLAYER_SPRINT_SPEED = 0.575
PLAYER_ROT_SPEED = 0.0015
SENSITIVITY_X = 1.0
MAX_RAYCAST_STEPS = 1000

FOV = math.pi / 3  # 60 degrees
HALF_FOV = FOV / 2
ZOOM_FOV_MULT = 0.5

MAX_DEPTH = 100
FOG_START = 8

DEFAULT_PLAYER_SPAWN = (2.5, 2.5, 0.0)
SPAWN_SAFE_ZONE_RADIUS = 15.0
SPAWN_SAFETY_MARGIN = 5

# ---------------------------------------------------------------------------
# New Game Defaults
# ---------------------------------------------------------------------------
DEFAULT_LIVES = 3
DEFAULT_DIFFICULTY = "NORMAL"
DEFAULT_START_LEVEL = 1

# ---------------------------------------------------------------------------
# Difficulty Settings
# ---------------------------------------------------------------------------
DIFFICULTIES: dict[str, dict[str, float]] = {
    "EASY": {"damage_mult": 0.5, "health_mult": 0.7, "score_mult": 0.5},
    "NORMAL": {"damage_mult": 1.0, "health_mult": 1.0, "score_mult": 1.0},
    "HARD": {"damage_mult": 1.5, "health_mult": 1.5, "score_mult": 2.0},
    "NIGHTMARE": {"damage_mult": 2.5, "health_mult": 2.0, "score_mult": 4.0},
}

# ---------------------------------------------------------------------------
# Aiming
# ---------------------------------------------------------------------------
SPREAD_BASE = 0.025
SPREAD_ZOOM = 0.005

# ---------------------------------------------------------------------------
# Weapon Ranges
# ---------------------------------------------------------------------------
WEAPON_RANGE_PISTOL = 15
WEAPON_RANGE_RIFLE = 25
WEAPON_RANGE_SHOTGUN = 12
WEAPON_RANGE_PLASMA = 30
WEAPON_RANGE_STORMTROOPER = 30
WEAPON_RANGE_MINIGUN = 20

# ---------------------------------------------------------------------------
# Common Colors
# ---------------------------------------------------------------------------
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (40, 40, 40)
PURPLE = (160, 32, 240)
BROWN = (100, 80, 60)
DARK_BROWN = (70, 50, 35)

# ---------------------------------------------------------------------------
# Fog
# ---------------------------------------------------------------------------
FOG_COLOR = DARK_GRAY

# ---------------------------------------------------------------------------
# Health & Combat
# ---------------------------------------------------------------------------
MAX_HEALTH = 100
INITIAL_HEALTH = 100
HEADSHOT_MULTIPLIER = 2.0
MELEE_RANGE = 3.0
BASE_MELEE_DAMAGE = 25

# ---------------------------------------------------------------------------
# Bot / Enemy
# ---------------------------------------------------------------------------
BOT_SAFE_SPAWN_RADIUS = 15.0
BOT_SPAWN_ATTEMPTS = 20
BOSS_SPAWN_ATTEMPTS = 50
MAX_ENEMIES_PER_LEVEL = 50
BASE_ENEMIES_PER_LEVEL = 5
ENEMIES_SCALE_PER_LEVEL = 2

# ---------------------------------------------------------------------------
# Pickups
# ---------------------------------------------------------------------------
PICKUP_SPAWN_CHANCE = 0.4
AMMO_BOMB_SPAWN_COUNT = 8
BOMB_CHANCE = 0.2
AMMO_CHANCE = 0.5

# ---------------------------------------------------------------------------
# Visual Effects
# ---------------------------------------------------------------------------
DAMAGE_TEXT_DURATION = 60
RESPAWN_MESSAGE_DURATION = 120
MESSAGE_VERTICAL_SPEED = -0.5

# ---------------------------------------------------------------------------
# Music
# ---------------------------------------------------------------------------
MUSIC_TRACKS = [
    "music_loop",
    "music_drums",
    "music_wind",
    "music_horror",
    "music_piano",
    "music_action",
]
