from unittest.mock import MagicMock, patch

import pytest

from games.shared.ui_renderer_base import UIRendererBase


@pytest.fixture
def mock_pygame_surface():
    surf = MagicMock()
    return surf


class DummyRenderer(UIRendererBase):
    def _get_game_name(self) -> str:
        return "Dummy"


class TestUIRendererBase:
    def test_init_base(self, mock_pygame_surface):
        with patch("games.shared.ui_renderer_base.pygame"):
            renderer = DummyRenderer(mock_pygame_surface, 800, 600)
            assert renderer.screen == mock_pygame_surface
            assert renderer.screen_width == 800
            assert renderer.screen_height == 600

    def test_init_fonts_fallback(self, mock_pygame_surface):
        with patch("games.shared.ui_renderer_base.pygame") as mock_pg:
            mock_pg.font.SysFont.side_effect = Exception("No font")
            renderer = DummyRenderer(mock_pygame_surface, 800, 600)
            assert renderer.title_font is not None

    def test_load_assets_success(self, mock_pygame_surface):
        with patch("games.shared.ui_renderer_base.pygame") as mock_pg:
            with patch(
                "games.shared.ui_renderer_base.os.path.exists", return_value=True
            ):
                with patch("games.shared.ui_renderer_base.cv2"):
                    surf_mock = MagicMock()
                    surf_mock.get_width.return_value = 800
                    surf_mock.get_height.return_value = 600
                    mock_pg.image.load.return_value = surf_mock
                    mock_pg.transform.rotate.return_value = surf_mock
                    mock_pg.transform.scale.return_value = surf_mock

                    renderer = DummyRenderer(mock_pygame_surface, 800, 600)
                    assert "willy" in renderer.intro_images
                    assert "deadfish" in renderer.intro_images

    def test_update_blood_drips(self, mock_pygame_surface):
        with patch("games.shared.ui_renderer_base.pygame"):
            with patch("games.shared.ui_renderer_base.random") as mock_random:
                mock_random.random.return_value = 0.01  # Force spawn
                mock_random.randint.return_value = 10
                mock_random.uniform.return_value = 2.0

                renderer = DummyRenderer(mock_pygame_surface, 800, 600)
                rect = MagicMock()
                rect.left = 0
                rect.width = 100
                rect.bottom = 50

                renderer.update_blood_drips(rect)
                assert len(renderer.title_drips) == 1
                renderer.update_blood_drips(rect)
                assert len(renderer.title_drips) == 2

    def test_draw_blood_drips(self, mock_pygame_surface):
        with patch("games.shared.ui_renderer_base.pygame") as mock_pg:
            renderer = DummyRenderer(mock_pygame_surface, 800, 600)
            drips = [{"x": 10, "y": 50, "speed": 1, "length": 20}]
            renderer._draw_blood_drips(drips)
            assert mock_pg.draw.line.called
