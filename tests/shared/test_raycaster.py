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

    def __bool__(self):
        return True

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
        raycaster.render_minimap(screen, player, [])

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

    def test_get_cached_strip_large_height(self, raycaster: Raycaster) -> None:
        """Test preventing memory crashes from large height values."""
        assert raycaster._get_cached_strip("stone", 0, 20000) is None

    def test_get_cached_strip_exception(self, raycaster: Raycaster) -> None:
        """Test catching exceptions during scaling."""
        with (
            patch(
                "games.shared.raycaster.pygame.transform.scale", side_effect=ValueError
            ),
            patch("games.shared.raycaster.pygame.error", ValueError, create=True),
        ):
            assert raycaster._get_cached_strip("stone", 0, 100) is None

    def test_resolve_wall_theme_empty(self, raycaster: Raycaster) -> None:
        """Test defaulting when theme walls are empty."""
        raycaster.config.LEVEL_THEMES = [{"floor": (0, 0, 0)}]
        colors = raycaster._resolve_wall_theme(1)
        assert colors == {}

    def test_perform_dda_loop_coverage(self, raycaster: Raycaster) -> None:
        """Test _perform_dda_loop to hit out of bounds and max depth."""
        import numpy as np

        raycaster.num_rays = 3
        raycaster.map_width = 2
        raycaster.map_height = 2
        raycaster.np_grid = np.array([[0, 0], [0, 1]], dtype=np.int8)

        # Ray 0: Out of bounds immediately
        # Ray 1: Stays at 0,0, never hits (step is 0, deltadist > 0)
        # Ray 2: Hits the block at (1, 1)

        map_x = np.array([-1, 0, 1])
        map_y = np.array([-1, 0, 1])
        side_dist_x = np.array([0.0, 0.0, 0.0])
        side_dist_y = np.array([0.0, 0.0, 0.0])
        delta_dist_x = np.array([1.0, 1.0, 1.0])
        delta_dist_y = np.array([1.0, 1.0, 1.0])
        step_x = np.array([1, 0, 0])
        step_y = np.array([1, 0, 0])

        hits, wall_types, side = raycaster._perform_dda_loop(
            map_x,
            map_y,
            side_dist_x,
            side_dist_y,
            delta_dist_x,
            delta_dist_y,
            step_x,
            step_y,
        )
        assert hits[0]  # OOB
        assert not hits[1]  # Never hit
        assert hits[2]  # Hit
        assert wall_types[2] == 1

    def test_minimap_features(self, raycaster: Raycaster) -> None:
        """Test minimap with visited cells, portals, and bots."""
        screen = DummySurface((800, 600))
        player = MagicMock(angle=0.0, pitch=0.0, x=1.0, y=1.0, alive=True)
        raycaster.minimap_surface = DummySurface((64, 64))
        raycaster.config.CYAN = (0, 255, 255)
        raycaster.config.ENEMY_TYPES = {"demon": {"visual_style": "default"}}

        bot = MagicMock(x=1.5, y=1.5, alive=True, enemy_type="demon")
        visited = set([(1, 1)])
        portal = {"x": 1.0, "y": 1.0}

        raycaster.render_minimap(
            screen,
            player,
            [bot],
            visited_cells=visited,
            portal=portal,
        )
        # Call again to test fog surface caching condition doesn't crash
        raycaster.render_minimap(
            screen,
            player,
            [bot],
            visited_cells=visited,
            portal=portal,
        )

        # Test falsy minimap_surface
        raycaster.minimap_surface = []  # type: ignore
        raycaster.render_minimap(
            screen,
            player,
            [bot],
            visited_cells=visited,
            portal=portal,
        )

    def test_blit_strip_scaled_coverage(self, raycaster: Raycaster) -> None:
        """Test fallback _blit_strip_scaled logic."""
        sprite_surf = DummySurface((32, 32))
        sprite_surf.subsurface = MagicMock(return_value=DummySurface((5, 32)))  # type: ignore
        raycaster.view_surface = DummySurface((800, 600))
        raycaster._blit_strip_scaled(
            sprite_surface=sprite_surf,  # type: ignore
            visible_runs=[(10, 20), (30, 40)],
            target_width=100,
            target_height=100,
            sprite_ray_x=15.0,
            sprite_ray_width=50.0,
            sprite_y=200.0,
            visual_scale=1.0,
        )

        # Test 0 width run
        raycaster._blit_strip_scaled(
            sprite_surface=sprite_surf,  # type: ignore
            visible_runs=[(10, 10)],
            target_width=100,
            target_height=100,
            sprite_ray_x=15.0,
            sprite_ray_width=50.0,
            sprite_y=200.0,
            visual_scale=1.0,
        )

        with patch("games.shared.raycaster.pygame.error", ValueError, create=True):
            # Test exception
            sprite_surf.subsurface.side_effect = ValueError  # type: ignore
            raycaster._blit_strip_scaled(
                sprite_surface=sprite_surf,  # type: ignore
                visible_runs=[(10, 20)],
                target_width=100,
                target_height=100,
                sprite_ray_x=15.0,
                sprite_ray_width=50.0,
                sprite_y=200.0,
                visual_scale=1.0,
            )

    def test_draw_single_projectile(self, raycaster: Raycaster) -> None:
        """Test drawing projectile with occlusion."""
        import numpy as np

        player = MagicMock(x=1.0, y=1.0, angle=0.0, pitch=0)
        proj = MagicMock(
            x=2.0, y=1.0, alive=True, weapon_type="plasma", color=(255, 0, 0)
        )
        raycaster.z_buffer = np.full(800, 5.0)
        raycaster.view_surface = DummySurface((800, 600))

        with patch("games.shared.raycaster.pygame.error", ValueError, create=True):
            # Drawn
            raycaster._draw_single_projectile(
                player, proj, dist=2.0, angle=0.0, half_fov=0.5, view_offset_y=0.0
            )

            # Occluded
            raycaster._draw_single_projectile(
                player, proj, dist=10.0, angle=0.0, half_fov=0.5, view_offset_y=0.0
            )

            # Out of bounds
            raycaster._draw_single_projectile(
                player, proj, dist=2.0, angle=3.14, half_fov=0.5, view_offset_y=0.0
            )

    def test_floor_ceiling_coverage(self, raycaster: Raycaster) -> None:
        """Test floor ceiling generation and scaling conditions."""
        screen = DummySurface((800, 600))
        player = MagicMock(angle=0.0, pitch=100, x=1.0, y=1.0, alive=True)
        raycaster._scaled_background_surface = None
        raycaster._background_surface = DummySurface((800, 600))
        raycaster.stars = [(10, 10, 2, (255, 255, 255))]
        raycaster.render_floor_ceiling(screen, player, 1, view_offset_y=50.0)

        # Change horizon
        player.pitch = -400
        raycaster.render_floor_ceiling(screen, player, 1, view_offset_y=-50.0)

    def test_render_walls_vectorized_coverage(self, raycaster: Raycaster) -> None:
        import numpy as np

        player = MagicMock(angle=0.0, pitch=0.0, x=1.0, y=1.0, alive=True)
        distances = np.array([raycaster.config.MAX_DEPTH + 1.0, 5.0, 5.0])
        wall_types = np.array([1, 0, 1])
        wall_x_hits = np.array([0.5, 0.5, 0.5])
        sides = np.array([0, 0, 0])
        fisheye_factors = np.array([1.0, 1.0, 1.0])

        raycaster.num_rays = 3
        # Ensure solid wall rendering
        raycaster.use_textures = False
        raycaster._render_walls_vectorized(
            distances=distances,
            wall_types=wall_types,
            wall_x_hits=wall_x_hits,
            sides=sides,
            player=player,
            fisheye_factors=fisheye_factors,
            level=1,
            view_offset_y=0.0,
            flash_intensity=0.0,
        )

        # Textured but missing from strips
        raycaster.use_textures = True
        raycaster.config.LEVEL_THEMES = [{"walls": {1: (255, 255, 255)}}]
        raycaster._cached_level = -1
        raycaster.texture_map = {1: "missing_texture"}
        raycaster.texture_strips = {}
        raycaster._render_walls_vectorized(
            distances=distances,
            wall_types=wall_types,
            wall_x_hits=wall_x_hits,
            sides=sides,
            player=player,
            fisheye_factors=fisheye_factors,
            level=1,
            view_offset_y=0.0,
            flash_intensity=0.0,
        )

    def test_blit_view_to_screen_render_scale(self, raycaster: Raycaster) -> None:
        screen = DummySurface((800, 600))
        raycaster.render_scale = 2
        raycaster._blit_view_to_screen(screen)

    def test_render_textured_wall_specifics(self, raycaster: Raycaster) -> None:
        """Test textured walls with shading, fog and edge cases."""
        raycaster.config.LEVEL_THEMES = [{"walls": {1: (255, 255, 255)}}]
        raycaster.texture_map = {1: "stone"}
        raycaster.texture_strips = {"stone": [DummySurface((1, 32))]}
        wall_strips = {1: raycaster.texture_strips["stone"]}
        wall_colors = {1: (255, 255, 255)}
        blits_sequence: list = []
        view_surface = DummySurface((800, 600))

        # Extreme height fallback
        raycaster._render_textured_wall(
            i=0,
            wt=1,
            h=9000,
            top=0,
            wall_x_hit=0.5,
            shade=0.5,
            fog=0.0,
            wall_strips=wall_strips,
            wall_colors=wall_colors,
            view_surface=view_surface,
            blits_sequence=blits_sequence,
        )
        assert len(blits_sequence) == 0

        # Cached strip is None
        with patch.object(raycaster, "_get_cached_strip", return_value=None):
            raycaster._render_textured_wall(
                i=0,
                wt=1,
                h=100,
                top=0,
                wall_x_hit=0.5,
                shade=0.5,
                fog=0.0,
                wall_strips=wall_strips,
                wall_colors=wall_colors,
                view_surface=view_surface,
                blits_sequence=blits_sequence,
            )
            assert len(blits_sequence) == 0

        # Valid strip, with shade and fog alpha
        surf = DummySurface((1, 100))
        with patch.object(raycaster, "_get_cached_strip", return_value=surf):
            raycaster._render_textured_wall(
                i=0,
                wt=1,
                h=100,
                top=0,
                wall_x_hit=0.5,
                shade=0.5,
                fog=0.5,
                wall_strips=wall_strips,
                wall_colors=wall_colors,
                view_surface=view_surface,
                blits_sequence=blits_sequence,
            )
            assert len(blits_sequence) == 3
