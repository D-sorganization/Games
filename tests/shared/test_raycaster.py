import math
from unittest.mock import MagicMock, patch

import pygame
import pytest

from games.shared.config import RaycasterConfig
from games.shared.raycaster import Raycaster


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def mock_texture_generator():
    with patch("games.shared.raycaster.TextureGenerator") as mock_gen:
        mock_surf = MagicMock()
        mock_surf.get_width.return_value = 64
        mock_surf.get_height.return_value = 64
        mock_surf.subsurface.return_value = MagicMock()
        mock_gen.generate_textures.return_value = {
            "stone": mock_surf,
            "brick": mock_surf,
            "metal": mock_surf,
        }
        yield mock_gen


@pytest.fixture
def mock_map():
    map_obj = MagicMock()
    map_obj.grid = [
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 2, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1],
    ]
    map_obj.size = 5
    map_obj.width = 5
    map_obj.height = 5
    return map_obj


@pytest.fixture
def test_config():
    return RaycasterConfig(
        SCREEN_WIDTH=800,
        SCREEN_HEIGHT=600,
        FOV=math.pi / 3,
        HALF_FOV=math.pi / 6,
        LEVEL_THEMES=[{"walls": {1: (100, 100, 100), 2: (150, 0, 0)}}],
    )


@pytest.fixture
def mock_player():
    player = MagicMock()
    player.x = 2.5
    player.y = 2.5
    player.angle = 0.0
    player.pitch = 0.0
    player.zoomed = False
    player.weapon_sway = 0.0
    return player


@pytest.fixture(autouse=True)
def mock_pygame_surface():
    """Mock pygame.Surface globally so we don't hit MagicMock spec errors."""
    mock_surf = MagicMock()
    mock_surf.get_width.return_value = 800
    mock_surf.get_height.return_value = 600
    with patch("games.shared.raycaster.pygame.Surface", return_value=mock_surf):
        yield mock_surf


class TestRaycaster:
    def test_init(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        assert rc.map_width == 5
        assert rc.num_rays == 800
        assert len(rc.shading_surfaces) == 256
        assert len(rc.fog_surfaces) == 256

    def test_set_render_scale(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        rc.set_render_scale(2)
        assert rc.num_rays == 400
        assert rc.z_buffer.shape == (400,)

    def test_update_cache(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        rc.update_cache()

    @patch("games.shared.raycaster.cast_ray_dda")
    def test_cast_ray(self, mock_dda, mock_map, test_config):
        # dist, wall_type, hit_x, hit_y, side, map_x, map_y
        mock_dda.return_value = (5.0, 1, 2.0, 3.5, 0, 2, 3)
        rc = Raycaster(mock_map, test_config)
        dist, wtype, w_x_hit, mx, my = rc.cast_ray(1.0, 1.0, 0.0)
        assert dist == 5.0
        assert wtype == 1
        assert w_x_hit == 0.5  # hit_y - math.floor(hit_y) -> 3.5 - 3
        assert mx == 2
        assert my == 3

    def test_render_3d(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        surf = pygame.Surface((800, 600))
        rc.render_3d(surf, mock_player, [], 1)
        # Verify zoom
        mock_player.zoomed = True
        rc.render_3d(surf, mock_player, [], 1)

    @patch("games.shared.raycaster.pygame.draw")
    @patch("games.shared.raycaster.pygame.BLEND_MULT", 3, create=True)
    def test_render_sprites(self, mock_draw, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        bot = MagicMock()
        bot.x = 3.5
        bot.y = 2.5
        bot.removed = False
        bot.sprite = pygame.Surface((32, 32))
        bot.width = 0.5
        bot.height = 0.5
        bot.z_offset = 0

        proj = MagicMock()
        proj.x = 2.0
        proj.y = 2.5
        proj.alive = True
        proj.radius = 0.1
        proj.color = (255, 0, 0)

        part = MagicMock()
        part.x = 2.5
        part.y = 3.5
        part.alive = True
        part.type = "blood"
        part.size = 2
        part.color = (200, 0, 0)

        surf = pygame.Surface((800, 600))
        rc.render_3d(surf, mock_player, [bot], 1, projectiles=[proj], particles=[part])
