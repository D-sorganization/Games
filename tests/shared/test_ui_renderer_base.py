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

    def test_get_game_name_valid(self, mock_pygame_surface):
        class ValidGameRenderer(UIRendererBase):
            def _get_base_dir(self):
                from pathlib import Path
                return Path("/fake_dir")

        ValidGameRenderer.__module__ = "games.MyTestGame.ui_renderer"
        with patch("games.shared.ui_renderer_base.pygame"):
            renderer = ValidGameRenderer(mock_pygame_surface, 800, 600)
            assert renderer._get_game_name() == "MyTestGame"

    def test_get_game_name_unknown(self, mock_pygame_surface):
        # We need to test the real get_game_name
        class UnknownGameRenderer(UIRendererBase):
            def _get_base_dir(self):
                # Fake path to prevent real file operations
                from pathlib import Path

                return Path("/fake_dir")

        # Test default
        UnknownGameRenderer.__module__ = "some.weird.module"
        with patch("games.shared.ui_renderer_base.pygame"):
            renderer = UnknownGameRenderer(mock_pygame_surface, 800, 600)
            assert renderer._get_game_name() == "unknown"

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

    def test_load_assets_no_scale(self, mock_pygame_surface):
        with patch("games.shared.ui_renderer_base.pygame") as mock_pg:
            with patch(
                "games.shared.ui_renderer_base.os.path.exists", return_value=True
            ):
                with patch("games.shared.ui_renderer_base.cv2"):
                    surf_mock = MagicMock()
                    # Small enough width and height that scale >= 1
                    surf_mock.get_width.return_value = 100
                    surf_mock.get_height.return_value = 100
                    mock_pg.image.load.return_value = surf_mock
                    mock_pg.transform.rotate.return_value = surf_mock

                    renderer = DummyRenderer(mock_pygame_surface, 800, 600)
                    assert renderer is not None
                    assert mock_pg.transform.scale.called is False  # Scale < 1 is false

    def test_load_assets_exception(self, mock_pygame_surface):
        with patch("games.shared.ui_renderer_base.pygame") as mock_pg:
            mock_pg.image.load.side_effect = Exception("Load error")
            with patch(
                "games.shared.ui_renderer_base.os.path.exists", return_value=True
            ):
                with patch(
                    "games.shared.ui_renderer_base.logger.exception"
                ) as mock_log:
                    # Should silently log and not crash
                    renderer = DummyRenderer(mock_pygame_surface, 800, 600)
                    assert renderer is not None
                    assert mock_log.called

    def test_load_assets_no_cv2(self, mock_pygame_surface):
        with patch("games.shared.ui_renderer_base.HAS_CV2", False):
            with patch(
                "games.shared.ui_renderer_base.os.path.exists", return_value=True
            ):
                renderer = DummyRenderer(mock_pygame_surface, 800, 600)
                assert renderer.intro_video is None

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

    def test_update_blood_drips_no_spawn(self, mock_pygame_surface):
        with patch("games.shared.ui_renderer_base.pygame"):
            with patch("games.shared.ui_renderer_base.random") as mock_random:
                mock_random.random.return_value = 0.99  # Do not spawn

                renderer = DummyRenderer(mock_pygame_surface, 800, 600)
                rect = MagicMock()
                renderer.update_blood_drips(rect)
                assert len(renderer.title_drips) == 0

    def test_draw_blood_drips(self, mock_pygame_surface):
        with patch("games.shared.ui_renderer_base.pygame") as mock_pg:
            renderer = DummyRenderer(mock_pygame_surface, 800, 600)
            drips = [{"x": 10, "y": 50, "speed": 1, "length": 20}]
            renderer._draw_blood_drips(drips)
            assert mock_pg.draw.line.called

    def test_draw_blood_drips_out_of_bounds(self, mock_pygame_surface):
        with patch("games.shared.ui_renderer_base.pygame") as mock_pg:
            renderer = DummyRenderer(mock_pygame_surface, 800, 600)
            drips = [
                {"x": 10, "y": 700, "speed": 1, "length": 20}
            ]  # start_y >= screen_height
            renderer._draw_blood_drips(drips)
            assert not mock_pg.draw.line.called
