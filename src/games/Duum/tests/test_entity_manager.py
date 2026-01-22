import unittest

from src.bot import Bot
from src.entity_manager import EntityManager


class TestEntityManager(unittest.TestCase):
    """Tests for the EntityManager class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.em = EntityManager()
        self.em.grid_cell_size = 5

    def test_add_bot(self) -> None:
        """Test adding a bot to the manager."""
        bot = Bot(10.0, 10.0, 1)
        self.em.add_bot(bot)
        assert len(self.em.bots) == 1
        assert bot in self.em.bots

    def test_spatial_grid_update(self) -> None:
        """Test that the spatial grid updates correctly."""
        bot1 = Bot(2.0, 2.0, 1)  # Cell 0,0
        bot2 = Bot(7.0, 2.0, 1)  # Cell 1,0
        self.em.add_bot(bot1)
        self.em.add_bot(bot2)

        self.em._update_spatial_grid()

        assert len(self.em.spatial_grid[(0, 0)]) == 1
        assert self.em.spatial_grid[(0, 0)][0] == bot1

        assert len(self.em.spatial_grid[(1, 0)]) == 1
        assert self.em.spatial_grid[(1, 0)][0] == bot2

    def test_get_nearby_bots(self) -> None:
        """Test retrieving nearby bots."""
        # Bot at 5,5 (Cell 1,1)
        # Nearby should include cells 0,0 to 2,2
        bot_center = Bot(5.5, 5.5, 1)

        # Bot at 20,20 (Cell 4,4) - Far
        bot_far = Bot(20.0, 20.0, 1)

        self.em.add_bot(bot_center)
        self.em.add_bot(bot_far)
        self.em._update_spatial_grid()

        nearby = self.em.get_nearby_bots(5.0, 5.0)
        assert bot_center in nearby
        assert bot_far not in nearby


if __name__ == "__main__":
    unittest.main()
