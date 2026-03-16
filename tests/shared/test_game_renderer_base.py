from unittest.mock import MagicMock, patch

import pytest

from games.shared.contracts import ContractViolation
from games.shared.game_renderer_base import GameRendererBase


@pytest.fixture(autouse=True)
def setup_pygame():
    """Mock pygame.Surface instead of initializing video dummy"""
    with patch("games.shared.game_renderer_base.pygame.Surface") as MockSurf:
        yield MockSurf


def test_game_renderer_base_init():
    mock_screen = MagicMock()
    renderer = GameRendererBase(mock_screen, 800, 600)
    assert renderer.screen == mock_screen
    assert renderer.screen_width == 800
    assert renderer.screen_height == 600
    assert hasattr(renderer, "effects_surface")


def test_game_renderer_base_invalid_init():
    mock_screen = MagicMock()

    with pytest.raises(ContractViolation):
        GameRendererBase(None, 800, 600)

    with pytest.raises(ContractViolation):
        GameRendererBase(mock_screen, -800, 600)

    with pytest.raises(ContractViolation):
        GameRendererBase(mock_screen, 800, -600)
