import pygame

from games.Force_Field.src.input_manager import InputManager


def test_input_manager_bindings():
    """Test that the default bindings for Force Field are correctly defined."""
    bindings = InputManager.DEFAULT_BINDINGS
    assert bindings["move_forward"] == pygame.K_w
    assert bindings["sprint"] == pygame.K_TAB
    assert bindings["dash"] == pygame.K_LSHIFT
    assert bindings["shield"] == pygame.K_SPACE
