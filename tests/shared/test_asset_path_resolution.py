"""Test for ensuring asset path resolution correctly IDs each game."""

import pygame

from src.games.Duum.src.sound import SoundManager as DuumSoundManager
from src.games.Duum.src.ui_renderer import UIRenderer as DuumUIRenderer
from src.games.Force_Field.src.sound import SoundManager as FFSoundManager
from src.games.Force_Field.src.ui_renderer import UIRenderer as FFUIRenderer
from src.games.Zombie_Survival.src.sound import SoundManager as ZSSoundManager
from src.games.Zombie_Survival.src.ui_renderer import UIRenderer as ZSUIRenderer


def get_mock_screen() -> pygame.Surface:
    """Return a mock pygame surface."""
    return pygame.Surface((800, 600))


def test_duum_asset_resolution() -> None:
    """Test Duum correctly identifies its name regardless of sys.path."""
    sound_mgr = DuumSoundManager()
    assert sound_mgr.get_game_name() == "Duum"

    ui_mgr = DuumUIRenderer.__new__(DuumUIRenderer)
    assert ui_mgr._get_game_name() == "Duum"


def test_force_field_asset_resolution() -> None:
    """Test Force_Field correctly identifies its name regardless of sys.path."""
    sound_mgr = FFSoundManager()
    assert sound_mgr.get_game_name() == "Force_Field"

    ui_mgr = FFUIRenderer.__new__(FFUIRenderer)
    assert ui_mgr._get_game_name() == "Force_Field"


def test_zombie_survival_asset_resolution() -> None:
    """Test Zombie_Survival correctly identifies its name regardless of sys.path."""
    sound_mgr = ZSSoundManager()
    assert sound_mgr.get_game_name() == "Zombie_Survival"

    ui_mgr = ZSUIRenderer.__new__(ZSUIRenderer)
    assert ui_mgr._get_game_name() == "Zombie_Survival"
