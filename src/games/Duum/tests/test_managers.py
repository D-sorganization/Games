from unittest.mock import MagicMock

import pygame

from src.input_manager import InputManager
from src.map import Map
from src.sound import SoundManager
from src.spawn_manager import DuumSpawnManager


def test_map():
    m = Map(10)
    assert m.size == 10


def test_sound_manager():
    sm = SoundManager()
    assert sm.SOUND_FILES["shoot"] == "shoot.wav"


def test_input_manager():
    im = InputManager()
    assert im.DEFAULT_BINDINGS["shoot"] == pygame.K_SPACE


def test_spawn_manager():
    em = MagicMock()
    sm = DuumSpawnManager(em)
    bot = sm._make_bot(1.0, 1.0, 1, "ninja", "HARD")
    assert bot.enemy_type == "ninja"
    assert bot.x == 1.0
    assert bot.y == 1.0
