"""
Game constants for Wizard of Wor remake.
"""

# Screen dimensions
SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 760
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
DEEP_BLUE = (12, 28, 68)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PALE_YELLOW = (255, 232, 150)
PURPLE = (200, 0, 200)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
DARK_GRAY = (50, 50, 50)
GRAY = (128, 128, 128)
SLATE = (105, 142, 176)

# Game area (main dungeon area excluding UI)
GAME_AREA_X = 40
GAME_AREA_Y = 60
GAME_AREA_WIDTH = 720
GAME_AREA_HEIGHT = 576

# Radar
RADAR_X = GAME_AREA_X + GAME_AREA_WIDTH + 60
RADAR_Y = 80
RADAR_SIZE = 160
RADAR_SWEEP_SPEED = 3

# Cell size for dungeon grid
CELL_SIZE = 24

# Visual polish
FLOOR_GRID_ALPHA = 35
VIGNETTE_ALPHA = 110
RESPAWN_SHIELD_FRAMES = 180
FOOTSTEP_INTERVAL = 12
SPARKLE_LIFETIME = 28
MUZZLE_FLASH_TIME = 8
RADAR_PING_INTERVAL = 80

# Player settings
PLAYER_SIZE = 22
PLAYER_SPEED = 3.4
PLAYER_LIVES = 3
PLAYER_ANIMATION_SPEED = 10
PLAYER_SHIELD_FLASH = 12

# Bullet settings
BULLET_SIZE = 8
BULLET_SPEED = 7

# Enemy settings
ENEMY_SIZE = 22
ENEMY_OUTLINE = 4
ENEMY_GLOW = 10
BURWOR_SPEED = 1.8
GARWOR_SPEED = 2.2
THORWOR_SPEED = 2.8
WORLUK_SPEED = 1.3
WIZARD_SPEED = 3.2
ENEMY_ANIMATION_SPEED = 12
INVISIBILITY_INTERVAL = 240
INVISIBILITY_DURATION = 90
INVISIBILITY_FLICKER_PERIOD = 14
INVISIBILITY_FLICKER_ON_FRAMES = 7

# Scoring
BURWOR_POINTS = 100
GARWOR_POINTS = 200
THORWOR_POINTS = 300
WORLUK_POINTS = 1000
WIZARD_POINTS = 2500

# Enemy spawn counts per level
ENEMIES_PER_LEVEL = {
    1: {"burwor": 4, "garwor": 0, "thorwor": 0},
    2: {"burwor": 3, "garwor": 2, "thorwor": 0},
    3: {"burwor": 2, "garwor": 2, "thorwor": 2},
    4: {"burwor": 1, "garwor": 3, "thorwor": 2},
    5: {"burwor": 0, "garwor": 3, "thorwor": 3},
}

# Direction constants
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
