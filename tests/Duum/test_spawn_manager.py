from unittest.mock import MagicMock

from games.Duum.src.bot import Bot
from games.Duum.src.spawn_manager import DuumSpawnManager


def test_duum_spawn_manager_init():
    """Test initialization of DuumSpawnManager."""
    mock_entity_manager = MagicMock()
    manager = DuumSpawnManager(mock_entity_manager)
    assert "ball" in manager.BOSS_OPTIONS
    assert "pickup_plasma" in manager.WEAPON_PICKUPS


def test_duum_make_bot():
    """Test creating a bot via DuumSpawnManager."""
    mock_entity_manager = MagicMock()
    manager = DuumSpawnManager(mock_entity_manager)

    bot = manager._make_bot(1.0, 2.0, 3, "cyber_demon", difficulty="HARD")
    assert isinstance(bot, Bot)
    assert bot.x == 1.0
    assert bot.y == 2.0
    assert bot.level == 3
    assert bot.enemy_type == "cyber_demon"
