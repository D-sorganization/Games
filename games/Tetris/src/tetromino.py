from .constants import SHAPES, SHAPE_COLORS

class Tetromino:
    """Represents a Tetris piece"""

    def __init__(self, x: int, y: int, shape_type: str) -> None:
        """Initialize tetromino with position and shape type"""
        self.x = x
        self.y = y
        self.shape_type = shape_type
        self.shape = SHAPES[shape_type]
        self.color = SHAPE_COLORS[shape_type]
        self.rotation = 0

    def get_rotated_shape(self) -> list[list[int]]:
        """Get the current rotated shape"""
        shape = self.shape
        for _ in range(self.rotation % 4):
            shape = self._rotate_clockwise(shape)
        return shape

    def _rotate_clockwise(self, shape: list[list[int]]) -> list[list[int]]:
        """Rotate a shape 90 degrees clockwise"""
        return [[shape[y][x] for y in range(len(shape) - 1, -1, -1)] for x in range(len(shape[0]))]

    def rotate(self) -> None:
        """Rotate the tetromino"""
        self.rotation = (self.rotation + 1) % 4
