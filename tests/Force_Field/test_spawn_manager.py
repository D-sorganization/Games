from unittest.mock import MagicMock

from games.Force_Field.src.bot import Bot
from games.Force_Field.src.spawn_manager import FFSpawnManager


def test_ff_spawn_manager_init():
    """Test initialization of FFSpawnManager."""
    mock_entity_manager = MagicMock()
    manager = FFSpawnManager(mock_entity_manager)
    assert "ball" in manager.BOSS_OPTIONS
    assert "pickup_plasma" in manager.WEAPON_PICKUPS
    assert "demon" in manager.SPAWN_EXCLUSIONS


def test_ff_make_bot():
    """Test creating a bot via FFSpawnManager."""
    mock_entity_manager = MagicMock()
    manager = FFSpawnManager(mock_entity_manager)

    bot = manager._make_bot(1.0, 2.0, 3, "ball", difficulty="HARD")
    assert isinstance(bot, Bot)
    assert bot.x == 1.0
    assert bot.y == 2.0
    assert bot.level == 3
    assert bot.enemy_type == "ball"
