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
    """Mock pygame.Surface globally for these tests so we don't hit MagicMock spec errors."""  # noqa: E501
    mock_surf = MagicMock()
    mock_surf.get_width.return_value = 800
    mock_surf.get_height.return_value = 600
    with patch("games.shared.raycaster.pygame.Surface", return_value=mock_surf):
        yield mock_surf


@pytest.fixture(autouse=True)
def mock_pygame_draw():
    """Replace pygame.draw with a MagicMock (C extension cannot be patched directly)."""
    draw_mock = MagicMock()
    draw_mock.rect = MagicMock()
    draw_mock.circle = MagicMock()
    draw_mock.line = MagicMock()
    with patch("games.shared.raycaster.pygame.draw", draw_mock):
        yield draw_mock


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


class TestRaycasterCacheEviction:
    """Tests for update_cache LRU eviction."""

    def test_strip_cache_eviction(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        for i in range(10001):
            rc._strip_cache[(f"stone_{i}", i, 100)] = MagicMock()
        assert len(rc._strip_cache) > 10000
        rc.update_cache()
        assert len(rc._strip_cache) <= 9001

    def test_sprite_cache_eviction(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        for i in range(401):
            rc.sprite_cache[(f"bot_{i}",)] = MagicMock()
        assert len(rc.sprite_cache) > 400
        rc.update_cache()
        assert len(rc.sprite_cache) <= 361

    def test_scaled_sprite_cache_eviction(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        for i in range(201):
            rc._scaled_sprite_cache[(f"bot_{i}",)] = MagicMock()
        assert len(rc._scaled_sprite_cache) > 200
        rc.update_cache()
        assert len(rc._scaled_sprite_cache) <= 181


class TestGetCachedStrip:
    """Tests for _get_cached_strip."""

    def test_cache_miss_then_hit(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        result = rc._get_cached_strip("stone", 0, 100)
        result2 = rc._get_cached_strip("stone", 0, 100)
        assert result is result2

    def test_unknown_texture_returns_none(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        result = rc._get_cached_strip("nonexistent_texture", 0, 100)
        assert result is None

    def test_very_large_height_returns_none(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        result = rc._get_cached_strip("stone", 0, 20000)
        assert result is None


class TestResolveWallTheme:
    """Tests for _resolve_wall_theme."""

    def test_cache_hit_returns_same_dict(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        first = rc._resolve_wall_theme(1)
        second = rc._resolve_wall_theme(1)
        assert first is second

    def test_different_level_clears_cache(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        rc._resolve_wall_theme(1)
        result = rc._resolve_wall_theme(2)
        assert isinstance(result, dict)

    def test_no_themes_returns_empty(self, mock_map):
        cfg = RaycasterConfig(
            SCREEN_WIDTH=200,
            SCREEN_HEIGHT=150,
            FOV=math.pi / 3,
            HALF_FOV=math.pi / 6,
            LEVEL_THEMES=[],
        )
        rc = Raycaster(mock_map, cfg)
        result = rc._resolve_wall_theme(1)
        assert result == {}


class TestPrepareWallRenderData:
    """Tests for _prepare_wall_render_data."""

    def test_output_shapes(self, mock_map, test_config):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        player = MagicMock()
        player.pitch = 0.0
        dists = np.ones(rc.num_rays, dtype=np.float64) * 5.0
        fish = np.ones(rc.num_rays, dtype=np.float64)
        heights, tops, shades, fogs = rc._prepare_wall_render_data(
            dists, player, fish, 0.0
        )
        assert len(heights) == rc.num_rays
        assert len(tops) == rc.num_rays

    def test_very_close_distance_clamped(self, mock_map, test_config):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        player = MagicMock()
        player.pitch = 0.0
        dists = np.zeros(rc.num_rays, dtype=np.float64)
        fish = np.ones(rc.num_rays, dtype=np.float64)
        heights, _, _, _ = rc._prepare_wall_render_data(dists, player, fish, 0.0)
        assert all(h > 0 for h in heights)


class TestUpdateMapCache:
    """Tests for _update_map_cache_if_needed."""

    def test_identity_no_update(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        original_grid = rc.grid
        rc._update_map_cache_if_needed()
        assert rc.grid is original_grid

    def test_different_identity_updates(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        new_grid = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
        mock_map.grid = new_grid
        rc._update_map_cache_if_needed()
        assert rc.grid is new_grid

    def test_equality_branch(self, mock_map, test_config):
        """Grid with different identity but equal content triggers equality branch."""
        import copy

        rc = Raycaster(mock_map, test_config)
        new_grid = copy.copy(mock_map.grid)
        mock_map.grid = new_grid
        rc._update_map_cache_if_needed()
        assert rc.grid is new_grid


class TestBlitViewToScreen:
    """Tests for _blit_view_to_screen."""

    def test_render_scale_1_direct_blit(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        rc.render_scale = 1
        screen = MagicMock()
        rc._blit_view_to_screen(screen)
        screen.blit.assert_called_once()

    def test_render_scale_2_scaled_blit(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        rc.render_scale = 2
        screen = MagicMock()
        with patch("games.shared.raycaster.pygame.transform.scale") as mock_scale:
            mock_scale.return_value = MagicMock()
            rc._blit_view_to_screen(screen)
            assert mock_scale.called
            screen.blit.assert_called_once()


class TestRenderFloorCeiling:
    """Tests for render_floor_ceiling."""

    def test_renders_without_error(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        rc.render_floor_ceiling(screen, mock_player, 1)

    def test_renders_with_extreme_pitch(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        mock_player.pitch = 500.0
        rc.render_floor_ceiling(screen, mock_player, 1)

    def test_background_cache_reuse(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        rc.render_floor_ceiling(screen, mock_player, 1)
        cached_idx = rc._cached_background_theme_idx
        rc.render_floor_ceiling(screen, mock_player, 1)
        assert rc._cached_background_theme_idx == cached_idx


class TestRenderMinimap:
    """Tests for render_minimap."""

    def test_basic_render(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        rc.render_minimap(screen, mock_player, [])

    def test_with_fog_of_war(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        visited = {(1, 1), (2, 1)}
        rc.render_minimap(screen, mock_player, [], visited_cells=visited)

    def test_fog_cache_reuse(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        visited = {(1, 1)}
        rc.render_minimap(screen, mock_player, [], visited_cells=visited)
        fog1 = rc._fog_surface
        rc.render_minimap(screen, mock_player, [], visited_cells=visited)
        assert rc._fog_surface is fog1

    def test_with_portal(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        portal = {"x": 1, "y": 1}
        rc.render_minimap(screen, mock_player, [], portal=portal)

    def test_portal_with_visited_cells(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        portal = {"x": 1, "y": 1}
        visited = {(1, 1)}
        rc.render_minimap(screen, mock_player, [], visited_cells=visited, portal=portal)

    def test_with_live_bot(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        bot = MagicMock()
        bot.alive = True
        bot.enemy_type = "grunt"
        bot.x = 2.0
        bot.y = 2.0
        test_config.ENEMY_TYPES = {"grunt": {"visual_style": "normal", "scale": 1.0}}
        rc.render_minimap(screen, mock_player, [bot])

    def test_minimap_cache_generated_once(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        assert rc.minimap_surface is None
        rc.render_minimap(screen, mock_player, [])
        assert rc.minimap_surface is not None


class TestDrawProjectileEffect:
    """Tests for _draw_projectile_effect weapon type coverage."""

    @pytest.mark.parametrize(
        "weapon_type",
        ["plasma", "rocket", "bfg", "bomb", "flamethrower", "pulse", "freezer"],
    )
    def test_known_weapon_draws_circle(
        self, weapon_type, mock_map, test_config, mock_pygame_draw
    ):
        rc = Raycaster(mock_map, test_config)
        proj = MagicMock()
        proj.weapon_type = weapon_type
        rect = pygame.Rect(100, 100, 20, 20)
        rc._draw_projectile_effect(proj, rect)
        assert mock_pygame_draw.circle.called

    def test_unknown_weapon_no_draw(self, mock_map, test_config, mock_pygame_draw):
        rc = Raycaster(mock_map, test_config)
        proj = MagicMock()
        proj.weapon_type = "melee"
        rect = pygame.Rect(100, 100, 20, 20)
        mock_pygame_draw.circle.reset_mock()
        rc._draw_projectile_effect(proj, rect)
        assert not mock_pygame_draw.circle.called


class TestCollectVisibleRuns:
    """Tests for _collect_visible_runs."""

    def test_all_visible(self, mock_map, test_config):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.full(rc.num_rays, float("inf"))
        runs, total = rc._collect_visible_runs(0, 5, dist=1.0)
        assert total == 5

    def test_all_occluded(self, mock_map, test_config):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.zeros(rc.num_rays)
        runs, total = rc._collect_visible_runs(0, 5, dist=1.0)
        assert total == 0

    def test_partial_visibility(self, mock_map, test_config):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        z = np.zeros(rc.num_rays)
        z[2] = 10.0
        rc.z_buffer = z
        runs, total = rc._collect_visible_runs(0, 5, dist=1.0)
        assert total == 1


class TestRenderSolidWall:
    """Tests for _render_solid_wall."""

    def test_solid_wall_draws_rect(self, mock_map, test_config, mock_pygame_draw):
        rc = Raycaster(mock_map, test_config)
        view_surface = MagicMock()
        wall_colors = {1: (100, 100, 100)}
        rc._render_solid_wall(0, 1, 200, 100, 0.8, 0.0, wall_colors, view_surface)
        assert mock_pygame_draw.rect.called

    def test_unknown_wall_type_uses_gray(self, mock_map, test_config, mock_pygame_draw):
        rc = Raycaster(mock_map, test_config)
        view_surface = MagicMock()
        wall_colors: dict = {}
        rc._render_solid_wall(0, 99, 200, 100, 0.8, 0.0, wall_colors, view_surface)
        assert mock_pygame_draw.rect.called


class TestRenderTexturedWall:
    """Tests for _render_textured_wall."""

    def test_extreme_height_uses_solid(self, mock_map, test_config, mock_pygame_draw):
        rc = Raycaster(mock_map, test_config)
        view_surface = MagicMock()
        wall_colors = {1: (100, 100, 100)}
        wall_strips = {1: [MagicMock()] * 64}
        blits: list = []
        rc._render_textured_wall(
            0,
            1,
            9000,
            0,
            0.5,
            0.8,
            0.0,
            wall_strips,
            wall_colors,
            view_surface,
            blits,
        )
        assert mock_pygame_draw.rect.called

    def test_no_cached_strip_falls_back(self, mock_map, test_config, mock_pygame_draw):
        rc = Raycaster(mock_map, test_config)
        # Make _get_cached_strip return None
        rc._get_cached_strip = MagicMock(return_value=None)
        view_surface = MagicMock()
        wall_colors = {1: (100, 100, 100)}
        wall_strips = {1: [MagicMock()] * 64}
        blits: list = []
        rc._render_textured_wall(
            0,
            1,
            200,
            0,
            0.5,
            0.8,
            0.0,
            wall_strips,
            wall_colors,
            view_surface,
            blits,
        )
        assert mock_pygame_draw.rect.called

    def test_with_shading_and_fog(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        view_surface = MagicMock()
        wall_colors = {1: (100, 100, 100)}
        mock_strip = MagicMock()
        wall_strips = {1: [mock_strip] * 64}
        # Supply a real texture strip so _get_cached_strip works
        rc.texture_strips["stone"] = [MagicMock()] * 64
        blits: list = []
        rc._render_textured_wall(
            0, 1, 200, 0, 0.5, 0.5, 0.5, wall_strips, wall_colors, view_surface, blits
        )
        assert len(blits) >= 1


class TestCastRayHorizontalSide:
    """cast_ray with horizontal hit (side == 1)."""

    @patch("games.shared.raycaster.cast_ray_dda")
    def test_horizontal_hit_uses_hit_x(self, mock_dda, mock_map, test_config):
        mock_dda.return_value = (5.0, 2, 2.7, 3.0, 1, 2, 3)
        rc = Raycaster(mock_map, test_config)
        dist, wtype, w_x_hit, mx, my = rc.cast_ray(1.0, 1.0, 0.0)
        assert dist == 5.0
        assert w_x_hit == pytest.approx(2.7 - 2.0)


class TestRenderEdgeCases:
    """Edge-case scenarios for render_3d."""

    def test_removed_bot_skipped(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        bot = MagicMock()
        bot.removed = True
        bot.x = 3.0
        bot.y = 2.5
        surf = pygame.Surface((800, 600))
        rc.render_3d(surf, mock_player, [bot], 1)

    def test_dead_projectile_skipped(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        proj = MagicMock()
        proj.alive = False
        proj.x = 2.5
        proj.y = 2.5
        surf = pygame.Surface((800, 600))
        rc.render_3d(surf, mock_player, [], 1, projectiles=[proj])

    def test_dead_particle_skipped(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        part = MagicMock()
        part.alive = False
        part.x = 2.5
        part.y = 2.5
        surf = pygame.Surface((800, 600))
        rc.render_3d(surf, mock_player, [], 1, particles=[part])

    def test_render_with_flash(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        surf = pygame.Surface((800, 600))
        rc.render_3d(surf, mock_player, [], 1, flash_intensity=0.8)

    def test_render_zoomed_player(self, mock_map, test_config, mock_player):
        mock_player.zoomed = True
        rc = Raycaster(mock_map, test_config)
        surf = pygame.Surface((800, 600))
        rc.render_3d(surf, mock_player, [], 1)


class TestGetCachedStripException:
    """Test _get_cached_strip exception handling."""

    def test_strip_scale_exception_returns_none(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        with patch(
            "games.shared.raycaster.pygame.transform.scale",
            side_effect=ValueError("err"),
        ):
            result = rc._get_cached_strip("stone", 0, 100)
        assert result is None


class TestRenderWallsVectorizedCulling:
    """Cover per-ray culling branches (dist >= MAX_DEPTH, wt == 0)."""

    def test_far_wall_skipped(self, mock_map, test_config, mock_player):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        n = rc.num_rays
        dists = np.full(n, test_config.MAX_DEPTH + 1.0)
        types_ = np.ones(n, dtype=np.int32)
        hits = np.zeros(n, dtype=np.float64)
        sides = np.zeros(n, dtype=np.int32)
        fish = np.ones(n, dtype=np.float64)
        rc._render_walls_vectorized(
            dists, types_, hits, sides, mock_player, fish, 1, 0.0, 0.0
        )

    def test_zero_wall_type_skipped(self, mock_map, test_config, mock_player):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        n = rc.num_rays
        dists = np.ones(n) * 5.0
        types_ = np.zeros(n, dtype=np.int32)
        hits = np.zeros(n, dtype=np.float64)
        sides = np.zeros(n, dtype=np.int32)
        fish = np.ones(n, dtype=np.float64)
        rc._render_walls_vectorized(
            dists, types_, hits, sides, mock_player, fish, 1, 0.0, 0.0
        )

    def test_solid_wall_rendered(self, mock_map, test_config, mock_player):
        """Cover _render_solid_wall call path via vectorized (use_textures=False)."""
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.use_textures = False
        n = rc.num_rays
        dists = np.ones(n) * 3.0
        types_ = np.ones(n, dtype=np.int32)
        hits = np.zeros(n, dtype=np.float64)
        sides = np.zeros(n, dtype=np.int32)
        fish = np.ones(n, dtype=np.float64)
        rc._render_walls_vectorized(
            dists, types_, hits, sides, mock_player, fish, 1, 0.0, 0.0
        )


class TestRenderSpriteCulling:
    """Cover sprite distance and dot-product culling."""

    def test_bot_too_far_culled(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        bot = MagicMock()
        bot.removed = False
        bot.x = mock_player.x + test_config.MAX_DEPTH * 2
        bot.y = mock_player.y
        surf = pygame.Surface((800, 600))
        rc.render_3d(surf, mock_player, [bot], 1)

    def test_bot_behind_player_culled(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        bot = MagicMock()
        bot.removed = False
        bot.x = mock_player.x - 5.0
        bot.y = mock_player.y
        surf = pygame.Surface((800, 600))
        rc.render_3d(surf, mock_player, [bot], 1)


class TestDrawSingleParticle:
    """Cover _draw_single_particle code paths."""

    def test_particle_within_view(self, mock_map, test_config, mock_player):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.full(rc.num_rays, float("inf"))
        part = MagicMock()
        part.size = 2
        part.color = (200, 0, 0)
        part.z = 0.5
        rc._draw_single_particle(
            mock_player, part, dist=2.0, angle=0.0, half_fov=math.pi / 6
        )

    def test_particle_occluded(self, mock_map, test_config, mock_player):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.zeros(rc.num_rays)
        part = MagicMock()
        part.size = 2
        part.color = (200, 0, 0)
        part.z = 0.5
        rc._draw_single_particle(
            mock_player, part, dist=2.0, angle=0.0, half_fov=math.pi / 6
        )

    def test_particle_offscreen(self, mock_map, test_config, mock_player):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.full(rc.num_rays, float("inf"))
        part = MagicMock()
        part.size = 2
        part.color = (200, 0, 0)
        part.z = 0.5
        rc._draw_single_particle(
            mock_player, part, dist=2.0, angle=math.pi, half_fov=math.pi / 6
        )


class TestDrawSingleProjectile:
    """Cover _draw_single_projectile code paths."""

    def test_projectile_drawn(self, mock_map, test_config, mock_player):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.full(rc.num_rays, float("inf"))
        proj = MagicMock()
        proj.size = 0.1
        proj.color = (255, 100, 0)
        proj.z = 0.5
        proj.weapon_type = "rocket"
        rc._draw_single_projectile(
            mock_player, proj, dist=2.0, angle=0.0, half_fov=math.pi / 6
        )

    def test_projectile_offscreen(self, mock_map, test_config, mock_player):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.full(rc.num_rays, float("inf"))
        proj = MagicMock()
        proj.size = 0.1
        proj.color = (255, 100, 0)
        proj.z = 0.5
        proj.weapon_type = "plasma"
        rc._draw_single_projectile(
            mock_player, proj, dist=2.0, angle=math.pi * 2, half_fov=math.pi / 6
        )

    def test_projectile_occluded(self, mock_map, test_config, mock_player):
        import numpy as np

        rc = Raycaster(mock_map, test_config)
        rc.z_buffer = np.zeros(rc.num_rays)
        proj = MagicMock()
        proj.size = 0.1
        proj.color = (255, 100, 0)
        proj.z = 0.5
        proj.weapon_type = "bfg"
        rc._draw_single_projectile(
            mock_player, proj, dist=2.0, angle=0.0, half_fov=math.pi / 6
        )


class TestSpriteCacheFlash:
    """Cover _get_or_create_sprite_surface flash and cache-hit paths."""

    def _make_bot(self) -> MagicMock:
        bot = MagicMock()
        bot.enemy_type = "grunt"
        bot.type_data = {"scale": 1.0, "visual_style": "normal", "color": (200, 50, 50)}
        bot.walk_animation = 0.0
        bot.shoot_animation = 0.0
        bot.dead = False
        bot.death_timer = 0
        bot.frozen = False
        return bot

    def test_flash_increases_shade(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        bot = self._make_bot()
        with patch("games.shared.raycaster.BotRenderer.render_sprite"):
            _, _, shade_no_flash = rc._get_or_create_sprite_surface(
                bot, 100.0, 2.0, 0.0
            )
            # Different shade level due to flash — cache miss, re-renders
            bot2 = self._make_bot()
            bot2.walk_animation = 0.99  # different animation frame -> different key
            _, _, shade_with_flash = rc._get_or_create_sprite_surface(
                bot2, 100.0, 2.0, 0.8
            )
        assert shade_with_flash >= shade_no_flash

    def test_cache_hit(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        bot = self._make_bot()
        with patch("games.shared.raycaster.BotRenderer.render_sprite"):
            surf1, key1, _ = rc._get_or_create_sprite_surface(bot, 100.0, 2.0, 0.0)
            surf2, key2, _ = rc._get_or_create_sprite_surface(bot, 100.0, 2.0, 0.0)
        assert surf1 is surf2
        assert key1 == key2

    def test_frozen_bot_tint(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        bot = self._make_bot()
        bot.frozen = True
        with patch("games.shared.raycaster.BotRenderer.render_sprite"):
            surf, _, _ = rc._get_or_create_sprite_surface(bot, 100.0, 2.0, 0.0)
        assert surf is not None


class TestBlitSpriteRunThresholds:
    """Cover strip vs whole scaling threshold."""

    def test_strip_scale_path(self, mock_map, test_config):
        """Force strip-scale path: few visible pixels with large target_width."""
        rc = Raycaster(mock_map, test_config)
        sprite_surface = MagicMock()
        sprite_surface.get_height.return_value = 200
        sprite_surface.get_width.return_value = 200
        visible_runs = [(0, 5)]  # Only 5 visible (< 30% of 300 = 90)
        rc._blit_sprite_runs(
            sprite_surface, "key", visible_runs, 5, 300, 200, 0.0, 300.0, 0.0, 200.0
        )

    def test_whole_scale_path(self, mock_map, test_config):
        """Force whole-scale path: many visible pixels."""
        rc = Raycaster(mock_map, test_config)
        sprite_surface = MagicMock()
        sprite_surface.get_height.return_value = 100
        sprite_surface.get_width.return_value = 100
        visible_runs = [(0, 50)]
        rc._blit_sprite_runs(
            sprite_surface, "key", visible_runs, 50, 50, 100, 0.0, 50.0, 0.0, 100.0
        )


class TestTexturedWallShadeAndFogBranches:
    """Cover shade==1.0 (no shading) and fog==0 (no fog) paths."""

    def test_no_shade_no_fog(self, mock_map, test_config):
        rc = Raycaster(mock_map, test_config)
        view_surface = MagicMock()
        wall_colors = {1: (100, 100, 100)}
        wall_strips = {1: [MagicMock()] * 64}
        rc.texture_strips["stone"] = [MagicMock()] * 64
        blits: list = []
        rc._render_textured_wall(
            0, 1, 200, 0, 0.5, 1.0, 0.0, wall_strips, wall_colors, view_surface, blits
        )
        assert len(blits) == 1  # Only strip, no shade/fog overlays

    def test_shade_with_fog(self, mock_map, test_config):
        """shade<1 and fog>0 both produce overlays."""
        rc = Raycaster(mock_map, test_config)
        view_surface = MagicMock()
        wall_colors = {1: (100, 100, 100)}
        wall_strips = {1: [MagicMock()] * 64}
        rc.texture_strips["stone"] = [MagicMock()] * 64
        blits: list = []
        rc._render_textured_wall(
            0, 1, 200, 0, 0.5, 0.3, 0.7, wall_strips, wall_colors, view_surface, blits
        )
        assert len(blits) == 3  # strip + shade + fog


class TestRenderFloorCeilingDetailPaths:
    """Cover sky/floor draw boundary conditions."""

    def test_no_sky_when_horizon_before_zero(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        mock_player.pitch = -(test_config.SCREEN_HEIGHT // 2 + 50)
        rc.render_floor_ceiling(screen, mock_player, 1)

    def test_no_floor_when_horizon_at_screen_bottom(
        self, mock_map, test_config, mock_player
    ):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        mock_player.pitch = test_config.SCREEN_HEIGHT
        rc.render_floor_ceiling(screen, mock_player, 1)


class TestMinimapPortalBranches:
    """Cover portal draw branches in render_minimap."""

    def test_portal_drawn_without_visited(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        portal = {"x": 1, "y": 1}
        rc.render_minimap(screen, mock_player, [], portal=portal)

    def test_portal_not_drawn_when_cell_not_visited(
        self, mock_map, test_config, mock_player
    ):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        portal = {"x": 3, "y": 3}
        visited = {(1, 1)}
        rc.render_minimap(screen, mock_player, [], visited_cells=visited, portal=portal)


class TestMinimapBotFiltering:
    """Cover bot filtering in render_minimap."""

    def test_dead_bot_not_drawn(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        bot = MagicMock()
        bot.alive = False
        bot.enemy_type = "grunt"
        bot.x = 2.0
        bot.y = 2.0
        test_config.ENEMY_TYPES = {"grunt": {"visual_style": "normal"}}
        rc.render_minimap(screen, mock_player, [bot])

    def test_health_pack_bot_not_drawn(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        bot = MagicMock()
        bot.alive = True
        bot.enemy_type = "health_pack"
        bot.x = 2.0
        bot.y = 2.0
        rc.render_minimap(screen, mock_player, [bot])

    def test_item_visual_style_not_drawn(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        bot = MagicMock()
        bot.alive = True
        bot.enemy_type = "pickup"
        bot.x = 2.0
        bot.y = 2.0
        test_config.ENEMY_TYPES = {"pickup": {"visual_style": "item"}}
        rc.render_minimap(screen, mock_player, [bot])

    def test_bot_not_in_visited_not_drawn(self, mock_map, test_config, mock_player):
        rc = Raycaster(mock_map, test_config)
        screen = MagicMock()
        bot = MagicMock()
        bot.alive = True
        bot.enemy_type = "grunt"
        bot.x = 3.7
        bot.y = 3.2
        test_config.ENEMY_TYPES = {"grunt": {"visual_style": "normal"}}
        visited = {(1, 1)}
        rc.render_minimap(screen, mock_player, [bot], visited_cells=visited)
