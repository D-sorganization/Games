import math
import random

from .constants import DEFAULT_MAP_SIZE


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

    @property
    def width(self) -> int:
        """Get map width"""
        return self.size

    @property
    def height(self) -> int:
        """Get map height"""
        return self.size

    def create_map(self) -> None:
        """Create the map layout using Cellular Automata for organic caves/rooms"""
        size = self.size

        for _ in range(20):
            # 1. Initialize random grid
            # 45% chance of being a wall
            self.grid = [[0 for _ in range(size)] for _ in range(size)]

            for i in range(size):
                for j in range(size):
                    if random.random() < 0.45:
                        self.grid[i][j] = 1
                    else:
                        self.grid[i][j] = 0

            # Border walls
            for i in range(size):
                self.grid[0][i] = 1
                self.grid[size - 1][i] = 1
                self.grid[i][0] = 1
                self.grid[i][size - 1] = 1

            # 2. Cellular Automata Smoothing (5 iterations)
            for _ in range(5):
                new_grid = [row[:] for row in self.grid]
                for i in range(1, size - 1):
                    for j in range(1, size - 1):
                        # Count neighbors
                        neighbors = 0
                        for ni in range(-1, 2):
                            for nj in range(-1, 2):
                                if ni == 0 and nj == 0:
                                    continue
                                if self.grid[i + ni][j + nj] > 0:
                                    neighbors += 1

                        if neighbors > 4:
                            new_grid[i][j] = 1
                        elif neighbors < 4:
                            new_grid[i][j] = 0
                self.grid = new_grid

            # 3. Add Buildings / Rooms overlay (Rectangular structures for variety)
            # Randomly place 3-5 rectangular rooms
            num_rooms = random.randint(3, 5)
            for _ in range(num_rooms):
                w = random.randint(5, 10)
                h = random.randint(5, 10)
                # Ensure within bounds
                if size - w - 2 < 2 or size - h - 2 < 2:
                    continue

                x = random.randint(2, size - w - 2)
                y = random.randint(2, size - h - 2)

                # Carve room (set to 0)
                for i in range(y, y + h):
                    for j in range(x, x + w):
                        if 0 <= i < size and 0 <= j < size:
                            self.grid[i][j] = 0

                # Add walls around room (type 2, 3, 4)
                wall_type = random.choice([2, 3, 4])
                for i in range(y, y + h):
                    if 0 <= i < size:
                        if 0 <= x < size:
                            self.grid[i][x] = wall_type
                        if 0 <= x + w - 1 < size:
                            self.grid[i][x + w - 1] = wall_type
                for j in range(x, x + w):
                    if 0 <= j < size:
                        if 0 <= y < size:
                            self.grid[y][j] = wall_type
                        if 0 <= y + h - 1 < size:
                            self.grid[y + h - 1][j] = wall_type

            # 4. Ensure connectivity (Flood fill)
            cx, cy = size // 2, size // 2
            start_x, start_y = -1, -1
            # Find valid start point near center
            for r in range(size // 2):
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    tx = int(cx + math.cos(rad) * r)
                    ty = int(cy + math.sin(rad) * r)
                    if 0 < tx < size and 0 < ty < size and self.grid[ty][tx] == 0:
                        start_x, start_y = tx, ty
                        break
                if start_x != -1:
                    break

            if start_x == -1:
                start_x, start_y = cx, cy
                self.grid[cy][cx] = 0

            # Identify connected region
            queue = [(start_x, start_y)]
            visited = {(start_x, start_y)}

            while queue:
                x, y = queue.pop(0)

                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < size
                        and 0 <= ny < size
                        and self.grid[ny][nx] == 0
                        and (nx, ny) not in visited
                    ):
                        visited.add((nx, ny))
                        queue.append((nx, ny))

            # 5. Check if map is big enough
            # Minimum 15% of map area should be walkable
            min_walkable = int(size * size * 0.15)
            if len(visited) >= min_walkable:
                # Valid map found, finalize it
                # Close off unconnected areas
                for i in range(size):
                    for j in range(size):
                        if self.grid[i][j] == 0 and (j, i) not in visited:
                            self.grid[i][j] = 1
                break
            else:
                # Retry
                continue
        else:
            # Fallback if all attempts fail (unlikely)
            return

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
