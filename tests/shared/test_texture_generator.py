from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from games.shared.contracts import ContractViolation
from games.shared.texture_generator import TextureGenerator


@pytest.fixture
def mock_pygame_surfarray():
    with patch(
        "games.shared.texture_generator.pygame.surfarray", create=True
    ) as mock_sa:
        mock_sa.make_surface = MagicMock(return_value=MagicMock())

        def fake_pixels(surf):
            try:
                w, h = surf.get_width() or 32, surf.get_height() or 32
            except Exception:  # noqa: BLE001
                w, h = 32, 32
            return np.zeros((w, h, 3), dtype=np.uint8)

        def fake_pixels2d(surf):
            try:
                w, h = surf.get_width() or 32, surf.get_height() or 32
            except Exception:  # noqa: BLE001
                w, h = 32, 32
            return np.zeros((w, h), dtype=np.uint8)

        mock_sa.pixels3d = MagicMock(side_effect=fake_pixels)
        mock_sa.pixels2d = MagicMock(side_effect=fake_pixels2d)
        yield mock_sa


@pytest.fixture
def mock_pygame_surface():
    with patch("games.shared.texture_generator.pygame.Surface") as mock_surf_class:

        def fake_surface(size):
            surf = MagicMock()
            surf.get_width.return_value = size[0]
            surf.get_height.return_value = size[1]
            return surf

        mock_surf_class.side_effect = fake_surface
        yield mock_surf_class


class TestTextureGenerator:
    def test_generate_noise(self, mock_pygame_surfarray):
        # Noise does not use Surface() directly, rather surfarray.make_surface
        surf = TextureGenerator.generate_noise(10, 10, (100, 100, 100), 5)
        assert surf is not None
        assert mock_pygame_surfarray.make_surface.called

    def test_generate_bricks(self, mock_pygame_surfarray, mock_pygame_surface):
        surf = TextureGenerator.generate_bricks(32, 32, (200, 100, 50), (100, 100, 100))
        assert surf is not None
        assert mock_pygame_surface.called

    def test_generate_stone(self, mock_pygame_surfarray, mock_pygame_surface):
        surf = TextureGenerator.generate_stone(32, 32)
        assert surf is not None

    def test_generate_metal(self, mock_pygame_surfarray, mock_pygame_surface):
        surf = TextureGenerator.generate_metal(32, 32)
        assert surf is not None

    def test_generate_tech(self, mock_pygame_surfarray, mock_pygame_surface):
        surf = TextureGenerator.generate_tech(32, 32)
        assert surf is not None

    def test_generate_hidden(self, mock_pygame_surfarray, mock_pygame_surface):
        # It relies on generate_bricks internally
        surf = TextureGenerator.generate_hidden(32, 32)
        assert surf is not None

    def test_generate_textures(self, mock_pygame_surfarray, mock_pygame_surface):
        with patch(
            "games.shared.texture_generator.pygame.get_init",
            return_value=False,
            create=True,
        ):
            with patch(
                "games.shared.texture_generator.pygame.init", create=True
            ) as mock_init:
                textures = TextureGenerator.generate_textures()
                assert mock_init.called
                assert "brick" in textures

    @pytest.mark.parametrize("width,height", [(-1, 10), (10, -1), (0, 10)])
    def test_invalid_dimensions(
        self, width, height, mock_pygame_surfarray, mock_pygame_surface
    ):
        with pytest.raises(ContractViolation):
            TextureGenerator.generate_stone(width, height)

    def test_generate_metal_small(self, mock_pygame_surfarray, mock_pygame_surface):
        # Trigger out of bounds check for rivets (152->147)
        surf = TextureGenerator.generate_metal(5, 5)
        assert surf is not None

    def test_generate_hidden_out_of_bounds(
        self, mock_pygame_surfarray, mock_pygame_surface
    ):
        # Trigger crack going out of bounds (217->224, 221->219)
        with patch("games.shared.texture_generator.random.randint", return_value=-10):
            surf = TextureGenerator.generate_hidden(2, 30)
            assert surf is not None

    def test_generate_textures_already_init(
        self, mock_pygame_surfarray, mock_pygame_surface
    ):
        # Trigger true branch of pygame.get_init() (233->236)
        with patch(
            "games.shared.texture_generator.pygame.get_init",
            return_value=True,
            create=True,
        ):
            with patch(
                "games.shared.texture_generator.pygame.init", create=True
            ) as mock_init:
                textures = TextureGenerator.generate_textures()
                assert not mock_init.called
                assert "brick" in textures
