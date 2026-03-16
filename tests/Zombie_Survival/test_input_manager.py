import pygame

from games.Zombie_Survival.src.input_manager import InputManager


def test_input_manager_bindings():
    """Test that the default bindings for Zombie Survival are correctly defined."""
    bindings = InputManager.DEFAULT_BINDINGS
    assert bindings["move_forward"] == pygame.K_w
    assert bindings["sprint"] == pygame.K_LSHIFT
    assert bindings["shield"] == pygame.K_SPACE
