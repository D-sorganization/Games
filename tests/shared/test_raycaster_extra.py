"""Extra unit tests for raycaster.py — targeting remaining coverage gaps."""

from __future__ import annotations

import math
from unittest.mock import MagicMock, patch

import pygame
import pytest

from games.shared.config import RaycasterConfig
from games.shared.raycaster import Raycaster

# ---------------------------------------------------------------------------
# Autouse lifecycle fixture
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def init_pygame():
    """Initialise the fake pygame so TextureGenerator.get_init() returns True."""
    pygame.init()
    yield
    pygame.quit()


# ---------------------------------------------------------------------------
# Fixtures (duplicated from test_raycaster.py for standalone test discovery)
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_map():
    m = MagicMock()
    m.grid = [
        [1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1],
    ]
    m.width = 5
    m.height = 5
    m.textures = {}
    return m


@pytest.fixture
def test_config():
    return RaycasterConfig(
        SCREEN_WIDTH=800,
        SCREEN_HEIGHT=600,
        FOV=math.pi / 3,
        HALF_FOV=math.pi / 6,
        LEVEL_THEMES=[
            {
                "walls": {1: (100, 100, 100), 2: (150, 0, 0)},
                "ceiling": (20, 20, 40),
                "floor": (30, 25, 20),
            }
        ],
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
    """Prevent real SDL Surface construction."""
    mock_surf = MagicMock()
    mock_surf.get_width.return_value = 800
    mock_surf.get_height.return_value = 600
    with patch("games.shared.raycaster.pygame.Surface", return_value=mock_surf):
        yield mock_surf


@pytest.fixture(autouse=True)
def mock_pygame_draw():
    """Replace pygame.draw with MagicMock (C extension cannot be attributed-patched)."""
    draw_mock = MagicMock()
    draw_mock.rect = MagicMock()
    draw_mock.circle = MagicMock()
    draw_mock.line = MagicMock()
    with patch("games.shared.raycaster.pygame.draw", draw_mock):
        yield draw_mock


@pytest.fixture(autouse=True)
def mock_texture_generator():
    """Bypass TextureGenerator.generate_textures to avoid real surfarray calls."""
    with patch(
        "games.shared.raycaster.TextureGenerator.generate_textures",
        return_value={},
    ):
        yield


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDrawSingleSpriteEdgeCases:
    """_draw_single_sprite early-exit paths (lines 908, 918, 923, 929)."""

    def test_sprite_fully_off_screen_large_angle(
        self, mock_map, test_config, mock_player
    ):
        """Very large positive angle -> sprite ray_x+width < 0 -> return at line 908."""
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.full(rc.num_rays, float("inf"))
        bot = MagicMock()
        bot.type_data = {"scale": 1.0}
        with patch("games.shared.raycaster.BotRenderer.render_sprite"):
            rc._draw_single_sprite(
                mock_player,
                bot,
                dist=1.0,
                angle=math.pi * 0.9,
                half_fov=math.pi / 6,
            )

    def test_sprite_tiny_scale_far_dist_zero_width(
        self, mock_map, test_config, mock_player
    ):
        """Tiny scale + far dist -> target_width <= 0 -> return at line 923."""
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.full(rc.num_rays, float("inf"))
        bot = MagicMock()
        bot.type_data = {"scale": 0.001}
        with patch("games.shared.raycaster.BotRenderer.render_sprite"):
            rc._draw_single_sprite(
                mock_player,
                bot,
                dist=test_config.MAX_DEPTH - 0.01,
                angle=0.0,
                half_fov=math.pi / 6,
            )

    def test_sprite_all_rays_occluded_no_runs(self, mock_map, test_config, mock_player):
        """All z_buffer at 0 -> visible_runs=[] -> return at line 929."""
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.zeros(rc.num_rays)
        bot = MagicMock()
        bot.type_data = {"scale": 1.0}
        with patch("games.shared.raycaster.BotRenderer.render_sprite"):
            rc._draw_single_sprite(
                mock_player, bot, dist=2.0, angle=0.0, half_fov=math.pi / 6
            )

    def test_sprite_fully_visible_full_path(self, mock_map, test_config, mock_player):
        """All rays clear, sprite in FOV -> complete render path."""
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.full(rc.num_rays, float("inf"))
        bot = MagicMock()
        bot.type_data = {"scale": 1.0}
        with patch("games.shared.raycaster.BotRenderer.render_sprite"):
            rc._draw_single_sprite(
                mock_player, bot, dist=2.0, angle=0.0, half_fov=math.pi / 6
            )


class TestRenderSpritesAngleWrap:
    """Angle normalisation while-loops (lines 787, 789)."""

    def test_positive_wrap(self, mock_map, test_config, mock_player):
        """Entity almost directly behind player (slight +y) triggers >pi wrap."""
        rc = Raycaster(mock_map, test_config)
        bot = MagicMock()
        bot.removed = False
        bot.x = mock_player.x - 0.5
        bot.y = mock_player.y + 0.01
        surf = pygame.Surface((800, 600))
        rc.render_3d(surf, mock_player, [bot], 1)

    def test_negative_wrap(self, mock_map, test_config, mock_player):
        """Entity almost directly behind player (slight -y) triggers <-pi wrap."""
        rc = Raycaster(mock_map, test_config)
        bot = MagicMock()
        bot.removed = False
        bot.x = mock_player.x - 0.5
        bot.y = mock_player.y - 0.01
        surf = pygame.Surface((800, 600))
        rc.render_3d(surf, mock_player, [bot], 1)


class TestRenderSpritesEntityDispatch:
    """Projectile/particle dispatch inside _render_sprites (799-805)."""

    def test_alive_projectile_in_fov_dispatched(
        self, mock_map, test_config, mock_player
    ):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.full(rc.num_rays, float("inf"))
        proj = MagicMock()
        proj.alive = True
        proj.size = 0.1
        proj.color = (255, 100, 0)
        proj.z = 0.5
        proj.weapon_type = "rocket"
        proj.x = mock_player.x + 2.0
        proj.y = mock_player.y
        surf = pygame.Surface((800, 600))
        rc.render_3d(surf, mock_player, [], 1, projectiles=[proj])

    def test_alive_particle_in_fov_dispatched(self, mock_map, test_config, mock_player):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.full(rc.num_rays, float("inf"))
        part = MagicMock()
        part.alive = True
        part.size = 3
        part.color = (200, 200, 0)
        part.z = 0.5
        part.x = mock_player.x + 2.0
        part.y = mock_player.y
        surf = pygame.Surface((800, 600))
        rc.render_3d(surf, mock_player, [], 1, particles=[part])


class TestParticleDrawException:
    """_draw_single_particle ValueError catch (lines 869-870)."""

    def test_value_error_swallowed(self, mock_map, test_config, mock_player):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.full(rc.num_rays, float("inf"))
        part = MagicMock()
        part.size = 5
        part.color = (200, 200, 0)
        part.z = 0.5
        with patch(
            "games.shared.raycaster.pygame.draw.circle",
            side_effect=ValueError("test error"),
        ):
            # Must not raise — falls into except block at line 869
            rc._draw_single_particle(
                mock_player, part, dist=2.0, angle=0.0, half_fov=math.pi / 6
            )


class TestBlitWholeScaled:
    """_blit_whole_scaled cache and shade branches (1100-1122)."""

    def test_cache_miss_then_hit(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        surf = MagicMock()
        surf.get_width.return_value = 200
        surf.get_height.return_value = 200
        runs = [(0, 50), (80, 150)]
        # Miss
        rc._blit_whole_scaled(surf, "key_ws_a", runs, 200, 150, 0.0, 10.0, 1.0)
        # Hit — same key
        rc._blit_whole_scaled(surf, "key_ws_a", runs, 200, 150, 0.0, 10.0, 1.0)

    def test_with_shade_overlay(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        surf = MagicMock()
        surf.get_width.return_value = 200
        surf.get_height.return_value = 200
        runs = [(0, 50)]
        rc._blit_whole_scaled(surf, "key_ws_b", runs, 200, 150, 0.0, 10.0, 1.0)


class TestBlitStripScaled:
    """_blit_strip_scaled strip rendering and cache hit (1161, 1170-1171)."""

    def test_strip_renders(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        surf = MagicMock()
        surf.get_height.return_value = 200
        surf.get_width.return_value = 200
        visible_runs = [(0, 10)]
        # sprite_ray_width=100.0 (non-zero to avoid ZeroDivisionError)
        rc._blit_strip_scaled(surf, visible_runs, 100, 200, 0.0, 100.0, 10.0, 1.0)

    def test_strip_cache_hit(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        surf = MagicMock()
        surf.get_height.return_value = 200
        surf.get_width.return_value = 200
        visible_runs = [(0, 10)]
        rc._blit_strip_scaled(surf, visible_runs, 100, 200, 0.0, 100.0, 10.0, 1.0)
        rc._blit_strip_scaled(surf, visible_runs, 100, 200, 0.0, 100.0, 10.0, 1.0)


class TestMapCacheEqualityBranchExtra:
    """_update_map_cache_if_needed line 304-305: equal but not identical grid."""

    def test_shallow_copy_triggers_update(self, mock_map, test_config):
        import copy

        rc = Raycaster(mock_map, test_config)
        new_grid = copy.copy(mock_map.grid)  # different id, equal content
        mock_map.grid = new_grid
        rc._update_map_cache_if_needed()
        assert rc.grid is new_grid
