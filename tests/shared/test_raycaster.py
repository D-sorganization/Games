"""Tests for games.shared.raycaster."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pygame
import pytest

from games.shared.interfaces import Map
from games.shared.raycaster import Raycaster


def _make_mock_config() -> MagicMock:
    config = MagicMock()
    config.SCREEN_WIDTH = 800
    config.SCREEN_HEIGHT = 600
    config.DEFAULT_RENDER_SCALE = 4
    config.FOV = 1.0
    config.HALF_FOV = 0.5
    config.ZOOM_FOV_MULT = 0.5
    config.MAX_DEPTH = 20.0
    config.FOG_COLOR = (100, 100, 100)
    config.FOG_START = 0.6
    config.GRAY = (128, 128, 128)
    config.LEVEL_THEMES = [
        {
            "walls": {1: (255, 0, 0), 2: (0, 255, 0)},
            "ceiling": (50, 50, 50),
            "floor": (20, 20, 20),
        }
    ]
    return config


def _make_mock_map() -> MagicMock:
    map_obj = MagicMock(spec=Map)
    map_obj.grid = [
        [1, 1, 1, 1],
        [1, 0, 0, 1],
        [1, 0, 0, 1],
        [1, 1, 1, 1],
    ]
    map_obj.size = 4
    map_obj.width = 4
    map_obj.height = 4
    return map_obj


class DummySurface:
    def __init__(self, size=(64, 64), *args, **kwargs):
        self._w = size[0]
        self._h = size[1]

    def get_width(self):
        return self._w

    def get_height(self):
        return self._h

    def subsurface(self, rect):
        return DummySurface((rect[2], rect[3]))

    def fill(self, color, rect=None, special_flags=0):
        pass

    def blits(self, blits_sequence, doreturn=False):
        pass

    def blit(self, source, dest, area=None, special_flags=0):
        pass

    def set_at(self, pos, color):
        pass


@pytest.fixture
def raycaster() -> Raycaster:
    pygame.init()
    try:
        pygame.display.set_mode((1, 1), pygame.HIDDEN)
    except Exception:
        pass

    with (
        patch("games.shared.raycaster.TextureGenerator.generate_textures") as mock_gen,
        patch("games.shared.raycaster.pygame.Surface", side_effect=DummySurface),
        patch(
            "games.shared.raycaster.pygame.transform.scale",
            side_effect=lambda s, size: DummySurface(size),
        ),
        patch("games.shared.raycaster.pygame.draw", new=MagicMock()),
        patch("games.shared.raycaster.pygame.BLEND_MULT", 1, create=True),
    ):
        mock_gen.return_value = {
            "stone": DummySurface(),
            "brick": DummySurface(),
            "metal": DummySurface(),
            "tech": DummySurface(),
            "hidden": DummySurface(),
        }
        rc = Raycaster(_make_mock_map(), _make_mock_config())
        yield rc
    pygame.quit()


class TestRaycasterInit:
    def test_init(self, raycaster: Raycaster) -> None:
        assert raycaster.map_width == 4
        assert raycaster.num_rays == 200

    def test_set_render_scale(self, raycaster: Raycaster) -> None:
        raycaster.set_render_scale(2)
        assert raycaster.render_scale == 2
        assert raycaster.num_rays == 400

    def test_update_cache(self, raycaster: Raycaster) -> None:
        # Fill caches
        for i in range(11000):
            raycaster._strip_cache[("stone", i, 64)] = DummySurface()
        for i in range(450):
            raycaster.sprite_cache[("bot", i)] = DummySurface()
        for i in range(250):
            raycaster._scaled_sprite_cache[("bot", i)] = DummySurface()

        raycaster.update_cache()
        assert len(raycaster._strip_cache) == 10000
        assert len(raycaster.sprite_cache) == 410
        assert len(raycaster._scaled_sprite_cache) == 230

    def test_get_cached_strip(self, raycaster: Raycaster) -> None:
        strip = raycaster._get_cached_strip("stone", 0, 64)
        assert strip is not None
        strip2 = raycaster._get_cached_strip("stone", 0, 64)
        assert strip is strip2
        assert raycaster._get_cached_strip("stone", 0, 20000) is None
        assert raycaster._get_cached_strip("bogus", 0, 64) is None

    @patch("games.shared.raycaster.cast_ray_dda")
    def test_cast_ray(self, mock_dda: MagicMock, raycaster: Raycaster) -> None:
        # Side 0
        mock_dda.return_value = (5.0, 1, 0.5, 0.25, 0, 2, 2)
        dist, wall_type, wall_x_hit, map_x, map_y = raycaster.cast_ray(0, 0, 0)
        assert wall_x_hit == 0.25

        # Side 1
        mock_dda.return_value = (5.0, 1, 0.75, 0.25, 1, 2, 2)
        dist, wall_type, wall_x_hit, map_x, map_y = raycaster.cast_ray(0, 0, 0)
        assert wall_x_hit == 0.75

    @patch("games.shared.raycaster.cast_ray_dda")
    def test_render_3d(self, mock_dda: MagicMock, raycaster: Raycaster) -> None:
        screen = DummySurface((800, 600))
        player = MagicMock()
        player.x = 1.0
        player.y = 1.0
        player.angle = 0.0
        player.zoomed = False
        player.pitch = 0
        bots = [MagicMock(x=2.0, y=1.0, alive=True, removed=False)]
        projectiles = [MagicMock(x=1.5, y=1.5, alive=True)]
        particles = [MagicMock(x=1.2, y=1.0, alive=True)]
        # Add a removed bot and dead projectiles to test culling
        bots.append(MagicMock(removed=True))
        projectiles.append(MagicMock(alive=False))
        particles.append(MagicMock(alive=False))

        # Test basic render
        raycaster.render_3d(
            screen,
            player,
            bots,
            1,
            view_offset_y=10.0,
            projectiles=projectiles,
            particles=particles,
        )
        # Test zoomed
        player.zoomed = True
        raycaster.render_3d(screen, player, bots, 1)

    def test_update_map_cache(self, raycaster: Raycaster) -> None:
        raycaster.game_map.grid = [[1], [1]]
        raycaster._update_map_cache_if_needed()
        assert raycaster.grid == [[1], [1]]

    def test_render_misc(self, raycaster: Raycaster) -> None:
        screen = DummySurface((800, 600))
        player = MagicMock(angle=0.0, pitch=0.0, x=1.0, y=1.0, alive=True)
        raycaster.render_floor_ceiling(screen, player, 1)
        raycaster.render_minimap(screen, player, [], [])

    def test_projectile_effects(self, raycaster: Raycaster) -> None:
        rect = MagicMock()
        rect.width = 10
        rect.center = (5, 5)
        rect.centerx = 5
        rect.centery = 5
        rect.top = 0
        for w in [
            "plasma",
            "rocket",
            "bfg",
            "bomb",
            "flamethrower",
            "pulse",
            "freezer",
        ]:
            proj = MagicMock(weapon_type=w)
            raycaster._draw_projectile_effect(proj, rect)
