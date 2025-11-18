"""
Game constants for Wizard of Wor remake.
"""

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (200, 0, 200)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
DARK_GRAY = (50, 50, 50)
GRAY = (128, 128, 128)

# Game area (main dungeon area excluding UI)
GAME_AREA_X = 50
GAME_AREA_Y = 50
GAME_AREA_WIDTH = 600
GAME_AREA_HEIGHT = 450

# Radar
RADAR_X = 670
RADAR_Y = 50
RADAR_SIZE = 100

# Cell size for dungeon grid
CELL_SIZE = 30

# Player settings
PLAYER_SIZE = 20
PLAYER_SPEED = 3
PLAYER_LIVES = 3

# Bullet settings
BULLET_SIZE = 8
BULLET_SPEED = 7

# Enemy settings
ENEMY_SIZE = 20
BURWOR_SPEED = 1.5
GARWOR_SPEED = 2.0
THORWOR_SPEED = 2.5
WORLUK_SPEED = 1.0
WIZARD_SPEED = 3.0

# Scoring
BURWOR_POINTS = 100
GARWOR_POINTS = 200
THORWOR_POINTS = 300
WORLUK_POINTS = 1000
WIZARD_POINTS = 2500

# Enemy spawn counts per level
ENEMIES_PER_LEVEL = {
    1: {'burwor': 4, 'garwor': 0, 'thorwor': 0},
    2: {'burwor': 3, 'garwor': 2, 'thorwor': 0},
    3: {'burwor': 2, 'garwor': 2, 'thorwor': 2},
    4: {'burwor': 1, 'garwor': 3, 'thorwor': 2},
    5: {'burwor': 0, 'garwor': 3, 'thorwor': 3},
}

# Direction constants
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
