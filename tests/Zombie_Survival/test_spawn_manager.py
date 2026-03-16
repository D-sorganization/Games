from unittest.mock import MagicMock

from games.Zombie_Survival.src.bot import Bot
from games.Zombie_Survival.src.spawn_manager import ZSSpawnManager


def test_zs_spawn_manager_init():
    """Test initialization of ZSSpawnManager."""
    mock_entity_manager = MagicMock()
    manager = ZSSpawnManager(mock_entity_manager)
    assert "ball" in manager.BOSS_OPTIONS
    assert "pickup_plasma" in manager.WEAPON_PICKUPS


def test_zs_make_bot():
    """Test creating a bot via ZSSpawnManager."""
    mock_entity_manager = MagicMock()
    manager = ZSSpawnManager(mock_entity_manager)

    bot = manager._make_bot(1.0, 2.0, 3, "zombie", difficulty="HARD")
    assert isinstance(bot, Bot)
    assert bot.x == 1.0
    assert bot.y == 2.0
    assert bot.level == 3
    assert bot.enemy_type == "zombie"
