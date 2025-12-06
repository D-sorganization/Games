from enum import Enum

# Constants
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
GRID_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
PLAY_WIDTH = GRID_WIDTH * GRID_SIZE
PLAY_HEIGHT = GRID_HEIGHT * GRID_SIZE
TOP_LEFT_X = 50
TOP_LEFT_Y = SCREEN_HEIGHT - PLAY_HEIGHT - 50
REWIND_HISTORY_LIMIT = 360
REWIND_STEP = 30
BUTTON_WIDTH = 160
BUTTON_HEIGHT = 36

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (200, 200, 200)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)

# Tetromino shapes
SHAPES = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
}

SHAPE_COLORS = {
    "I": CYAN,
    "O": YELLOW,
    "T": PURPLE,
    "S": GREEN,
    "Z": RED,
    "J": BLUE,
    "L": ORANGE,
}


class GameState(Enum):
    """Game states"""

    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4
    SETTINGS = 5
