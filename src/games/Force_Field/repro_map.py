import logging
import os
import sys

logger = logging.getLogger(__name__)

# Add current dir to path
sys.path.insert(0, os.getcwd())

from src.map import Map  # noqa: E402


def test_map_size() -> None:
    logger.info("Testing Map Generation for Small Areas...")
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
            logger.warning("Iter %d: Map has only %d walkable tiles!", i, walkable)
            small_maps += 1

    logger.info("Total small maps (<200 tiles) out of %d: %d", total, small_maps)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    test_map_size()
