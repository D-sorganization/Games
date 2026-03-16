import pygame

from games.Duum.src.input_manager import InputManager


def test_input_manager_bindings():
    """Test that the default bindings for Duum are correctly defined."""
    bindings = InputManager.DEFAULT_BINDINGS
    assert bindings["move_forward"] == pygame.K_w
    assert bindings["shoot"] == pygame.K_SPACE
    assert bindings["shield"] == pygame.K_x
