"""Tests for raycaster render parameter objects."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from games.shared.contracts import ContractViolation
from games.shared.raycaster_render_contexts import (
    MinimapRenderContext,
    SpriteRenderContext,
    TexturedWallColumnContext,
)


class TestSpriteRenderContext:
    def test_valid_context(self) -> None:
        context = SpriteRenderContext(
            player=MagicMock(),
            bots=[],
            projectiles=[],
            particles=[],
            half_fov=0.5,
            view_offset_y=0.0,
            flash_intensity=0.0,
            config=MagicMock(),
            num_rays=64,
            render_scale=4,
            view_surface=MagicMock(),
            z_buffer=MagicMock(),
            sprite_cache={},
            sprite_cache_max=16,
            sprite_cache_evict=4,
            scaled_sprite_cache={},
            scaled_cache_max=8,
            scaled_cache_evict=2,
            evict_fn=lambda *_args, **_kwargs: None,
        )
        assert context.num_rays == 64

    def test_rejects_invalid_half_fov(self) -> None:
        with pytest.raises(ContractViolation):
            SpriteRenderContext(
                player=MagicMock(),
                bots=[],
                projectiles=[],
                particles=[],
                half_fov=0.0,
                view_offset_y=0.0,
                flash_intensity=0.0,
                config=MagicMock(),
                num_rays=64,
                render_scale=4,
                view_surface=MagicMock(),
                z_buffer=MagicMock(),
                sprite_cache={},
                sprite_cache_max=16,
                sprite_cache_evict=4,
                scaled_sprite_cache={},
                scaled_cache_max=8,
                scaled_cache_evict=2,
                evict_fn=lambda *_args, **_kwargs: None,
            )


class TestTexturedWallColumnContext:
    def test_valid_context(self) -> None:
        context = TexturedWallColumnContext(
            i=1,
            wt=2,
            h=32,
            top=4,
            wall_x_hit=0.25,
            shade=0.75,
            fog=0.1,
            wall_strips={2: [MagicMock()]},
            wall_colors={2: (10, 20, 30)},
            view_surface=MagicMock(),
            blits_sequence=[],
            gray=(128, 128, 128),
            texture_map={2: "brick"},
            shading_surfaces=[MagicMock()],
            fog_surfaces=[MagicMock()],
            get_cached_strip_fn=lambda *_args: MagicMock(),
        )
        assert context.wt == 2

    def test_rejects_out_of_range_fog(self) -> None:
        with pytest.raises(ContractViolation):
            TexturedWallColumnContext(
                i=1,
                wt=2,
                h=32,
                top=4,
                wall_x_hit=0.25,
                shade=0.75,
                fog=1.1,
                wall_strips={2: [MagicMock()]},
                wall_colors={2: (10, 20, 30)},
                view_surface=MagicMock(),
                blits_sequence=[],
                gray=(128, 128, 128),
                texture_map={2: "brick"},
                shading_surfaces=[MagicMock()],
                fog_surfaces=[MagicMock()],
                get_cached_strip_fn=lambda *_args: MagicMock(),
            )


class TestMinimapRenderContext:
    def test_valid_context(self) -> None:
        context = MinimapRenderContext(
            screen=MagicMock(),
            player=MagicMock(),
            bots=[],
            minimap_surface=None,
            minimap_size=64,
            minimap_scale=4.0,
            minimap_x=1,
            minimap_y=2,
            fog_surface=None,
            fog_visited_count=0,
            visited_cells=None,
            portal=None,
            enemy_types=None,
            black=(0, 0, 0),
            red=(255, 0, 0),
            green=(0, 255, 0),
            cyan=(0, 255, 255),
        )
        assert context.minimap_size == 64

    def test_rejects_negative_fog_visit_count(self) -> None:
        with pytest.raises(ContractViolation):
            MinimapRenderContext(
                screen=MagicMock(),
                player=MagicMock(),
                bots=[],
                minimap_surface=None,
                minimap_size=64,
                minimap_scale=4.0,
                minimap_x=1,
                minimap_y=2,
                fog_surface=None,
                fog_visited_count=-1,
                visited_cells=None,
                portal=None,
                enemy_types=None,
                black=(0, 0, 0),
                red=(255, 0, 0),
                green=(0, 255, 0),
                cyan=(0, 255, 255),
            )
