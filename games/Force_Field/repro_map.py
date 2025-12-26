import os
import sys

# Add current dir to path
sys.path.insert(0, os.getcwd())

from src.map import Map


def test_map_size():
    print("Testing Map Generation for Small Areas...")
    small_maps = 0
    total = 100

    for i in range(total):
        # Default size 40
        m = Map(40)

        # Count walkable tiles
        walkable = 0
        for y in range(m.size):
            for x in range(m.size):
                if not m.is_wall(x, y):
                    walkable += 1

        if walkable < 200:
            print(f"Iter {i}: Map has only {walkable} walkable tiles!")
            small_maps += 1

    print(f"Total small maps (<200 tiles) out of {total}: {small_maps}")


if __name__ == "__main__":
    test_map_size()
