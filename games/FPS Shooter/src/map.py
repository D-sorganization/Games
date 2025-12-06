from .constants import DEFAULT_MAP_SIZE, MIN_BUILDING_OFFSET

class Map:
    """Game map with walls and buildings"""

    def __init__(self, size: int = DEFAULT_MAP_SIZE):
        """Initialize a map with walls and buildings
        Args:
            size: Map size (default: DEFAULT_MAP_SIZE)
        """
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        self.create_map()

    def create_map(self) -> None:
        """Create the map layout with walls and buildings"""
        size = self.size
        # Border walls
        for i in range(size):
            self.grid[0][i] = 1
            self.grid[size - 1][i] = 1
            self.grid[i][0] = 1
            self.grid[i][size - 1] = 1

        building_edge_margin = max(
            MIN_BUILDING_OFFSET,
            int(size * 0.1),
        )

        # Building 1 - Large rectangular building (top-left area)
        b1_start_i = max(building_edge_margin, int(size * 0.15))
        b1_end_i = max(b1_start_i + 2, min(int(size * 0.3), size - 1))
        b1_start_j = max(building_edge_margin, int(size * 0.15))
        b1_end_j = max(b1_start_j + 2, min(int(size * 0.4), size - 1))
        if b1_end_i > b1_start_i and b1_end_j > b1_start_j:
            for i in range(b1_start_i, b1_end_i):
                for j in range(b1_start_j, b1_end_j):
                    if i in {b1_start_i, b1_end_i - 1} or j in {
                        b1_start_j,
                        b1_end_j - 1,
                    }:
                        self.grid[i][j] = 2

        # Building 2 - Medium building (top-right area)
        b2_start_i = max(building_edge_margin, int(size * 0.15))
        b2_end_i = max(b2_start_i + 2, min(int(size * 0.25), size - 1))
        b2_start_j = max(building_edge_margin, int(size * 0.7))
        b2_end_j = max(b2_start_j + 2, min(int(size * 0.9), size - 1))
        if b2_end_i > b2_start_i and b2_end_j > b2_start_j:
            for i in range(b2_start_i, b2_end_i):
                for j in range(b2_start_j, b2_end_j):
                    if i in {b2_start_i, b2_end_i - 1} or j in {
                        b2_start_j,
                        b2_end_j - 1,
                    }:
                        self.grid[i][j] = 3

        # Building 3 - L-shaped building (bottom-left)
        b3_start_i = max(building_edge_margin, int(size * 0.7))
        b3_end_i = max(b3_start_i + 2, min(int(size * 0.95), size - 1))
        b3_start_j = max(building_edge_margin, int(size * 0.15))
        b3_end_j = max(b3_start_j + 2, min(int(size * 0.35), size - 1))
        if b3_end_i > b3_start_i and b3_end_j > b3_start_j:
            for i in range(b3_start_i, b3_end_i):
                for j in range(b3_start_j, b3_end_j):
                    if i in {b3_start_i, b3_end_i - 1} or j in {
                        b3_start_j,
                        b3_end_j - 1,
                    }:
                        self.grid[i][j] = 2
            # L-shape extension
            b3_ext_start_i = min(max(int(size * 0.8), b3_start_i), b3_end_i - 1)
            b3_ext_end_j = min(int(size * 0.5), size - 1)
            if b3_ext_start_i < b3_end_i and b3_ext_end_j > b3_start_j:
                for i in range(b3_ext_start_i, b3_end_i):
                    for j in range(b3_start_j, b3_ext_end_j):
                        if i in {b3_ext_start_i, b3_end_i - 1} or j in {
                            b3_start_j,
                            b3_ext_end_j - 1,
                        }:
                            self.grid[i][j] = 2

        # Building 4 - Square building (bottom-right)
        b4_start_i = int(size * 0.75)
        b4_end_i = min(int(size * 0.95), size - 1)
        b4_start_j = int(size * 0.75)
        b4_end_j = min(int(size * 0.95), size - 1)
        if b4_end_i > b4_start_i and b4_end_j > b4_start_j:
            for i in range(b4_start_i, b4_end_i):
                for j in range(b4_start_j, b4_end_j):
                    if i in {b4_start_i, b4_end_i - 1} or j in {
                        b4_start_j,
                        b4_end_j - 1,
                    }:
                        self.grid[i][j] = 3

        # Central courtyard walls
        center_start = int(size * 0.45)
        center_end = min(int(size * 0.55), size - 1)
        if center_end > center_start:
            for i in range(center_start, center_end):
                self.grid[i][center_start] = 4
                self.grid[i][center_end] = 4
            for j in range(center_start, min(center_end + 1, size)):
                self.grid[center_start][j] = 4
                if center_end < size:
                    self.grid[center_end][j] = 4

        # Scattered walls
        if size >= 30:
            wall1_i = int(size * 0.4)
            wall1_j = int(size * 0.6)
            if wall1_i < size and wall1_j < size:
                for i in range(wall1_i, min(wall1_i + 5, size)):
                    self.grid[i][wall1_j] = 1

        if size >= 40:
            wall2_i = int(size * 0.6)
            wall2_j = int(size * 0.7)
            if wall2_i < size and wall2_j < size:
                for j in range(wall2_j, min(wall2_j + 5, size)):
                    self.grid[wall2_i][j] = 1

        if size >= 50:
            wall3_i = int(size * 0.35)
            wall3_j = int(size * 0.7)
            if wall3_i < size and wall3_j < size:
                for i in range(wall3_i, min(wall3_i + 5, size)):
                    self.grid[i][wall3_j] = 1

        if size >= 60:
            wall4_j = int(size * 0.4)
            wall4_i = int(size * 0.75)
            if wall4_i < size and wall4_j < size:
                for j in range(wall4_j, min(wall4_j + 5, size)):
                    self.grid[wall4_i][j] = 1

    def is_wall(self, x: float, y: float) -> bool:
        """Check if position contains a wall"""
        map_x = int(x)
        map_y = int(y)
        if 0 <= map_x < self.size and 0 <= map_y < self.size:
            return self.grid[map_y][map_x] != 0
        return True

    def get_wall_type(self, x: float, y: float) -> int:
        """Get the wall type at position"""
        map_x = int(x)
        map_y = int(y)
        if 0 <= map_x < self.size and 0 <= map_y < self.size:
            return self.grid[map_y][map_x]
        return 1

    def is_inside_building(self, x: float, y: float) -> bool:
        """Check if position is inside a building (not just on the wall)"""
        i = int(y)
        j = int(x)
        if i < 0 or i >= self.size or j < 0 or j >= self.size:
            return False

        if self.grid[i][j] != 0:
            return False

        size = self.size
        building_edge_margin = max(MIN_BUILDING_OFFSET, int(size * 0.1))

        # Re-calculating bounds is repetitive.
        # Ideally we'd store building bounds, but for this refactor I'll copy logic or simplify.
        # Copying logic for now to ensure behavior matches.

        b1_start_i = max(building_edge_margin, int(size * 0.15))
        b1_end_i = max(b1_start_i + 2, min(int(size * 0.3), size - 1))
        b1_start_j = max(building_edge_margin, int(size * 0.15))
        b1_end_j = max(b1_start_j + 2, min(int(size * 0.4), size - 1))
        if b1_start_i < i < b1_end_i and b1_start_j < j < b1_end_j:
            return True

        b2_start_i = max(building_edge_margin, int(size * 0.15))
        b2_end_i = max(b2_start_i + 2, min(int(size * 0.25), size - 1))
        b2_start_j = max(building_edge_margin, int(size * 0.7))
        b2_end_j = max(b2_start_j + 2, min(int(size * 0.9), size - 1))
        if b2_start_i < i < b2_end_i and b2_start_j < j < b2_end_j:
            return True

        b3_start_i = max(building_edge_margin, int(size * 0.7))
        b3_end_i = max(b3_start_i + 2, min(int(size * 0.95), size - 1))
        b3_start_j = max(building_edge_margin, int(size * 0.15))
        b3_end_j = max(b3_start_j + 2, min(int(size * 0.35), size - 1))
        if b3_start_i < i < b3_end_i and b3_start_j < j < b3_end_j:
            return True

        b4_start_i = int(size * 0.75)
        b4_end_i = min(int(size * 0.95), size - 1)
        b4_start_j = int(size * 0.75)
        b4_end_j = min(int(size * 0.95), size - 1)
        if b4_start_i < i < b4_end_i and b4_start_j < j < b4_end_j:
            return True

        center_start = int(size * 0.45)
        center_end = min(int(size * 0.55), size - 1)
        return center_start < i < center_end and center_start < j < center_end
