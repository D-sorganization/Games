from unittest.mock import MagicMock, patch

import pygame
import pytest

from src.renderer import GameRenderer


@pytest.fixture
def screen():
    # Start pygame engine to allow Surface creation
    pygame.init()
    s = pygame.Surface((1200, 800))
    return s


@pytest.fixture
def game():
    g = MagicMock()
    g.player = MagicMock()
    g.player.is_moving = True
    g.player.x = 10.0
    g.player.y = 10.0
    g.player.angle = 0.0
    g.player.shooting = True
    g.player.current_weapon = "pistol"

    g.raycaster = MagicMock()
    g.level = 1
    g.bots = []
    g.projectiles = []

    g.particle_system = MagicMock()
    g.particle_system.world_particles = []

    p_laser = MagicMock()
    p_laser.ptype = "laser"
    p_laser.timer = 5
    p_laser.start_pos = (0, 0)
    p_laser.end_pos = (10, 10)
    p_laser.color = (255, 0, 0)
    p_laser.width = 2

    p_trace = MagicMock()
    p_trace.ptype = "trace"
    p_trace.timer = 2
    p_trace.start_pos = (0, 0)
    p_trace.end_pos = (10, 10)
    p_trace.color = (0, 255, 0)
    p_trace.width = 1

    p_normal = MagicMock()
    p_normal.ptype = "normal"
    p_normal.timer = 10
    p_normal.x = 5
    p_normal.y = 5
    p_normal.size = 2
    p_normal.color = (0, 0, 255, 255)  # RGBA

    g.particle_system.particles = [p_laser, p_trace, p_normal]

    g.portal = {"x": 10.5, "y": 10.5, "radius": 1.0, "active": True}
    g.ui_renderer = MagicMock()
    return g


def test_game_renderer_init(screen):
    r = GameRenderer(screen)
    assert r.screen == screen
    assert r.effects_surface is not None


def test_render_game(screen, game):
    r = GameRenderer(screen)
    r.screen = MagicMock()
    r.effects_surface = MagicMock()
    # mock weapon_renderer manually to avoid deep imports inside WeaponRenderer
    with patch.object(r, "weapon_renderer") as mock_wr:
        mock_wr.render_weapon.return_value = (600, 800)
        with (
            patch("pygame.display.flip"),
            patch("pygame.draw.line", create=True),
            patch("pygame.draw.circle", create=True),
        ):
            r.render_game(game, flash_intensity=0.5)
            game.raycaster.render_floor_ceiling.assert_called_once()
            game.raycaster.render_3d.assert_called_once()
            game.ui_renderer.render_hud.assert_called_once()
            mock_wr.render_muzzle_flash.assert_called_once()


def test_render_particles(screen, game):
    r = GameRenderer(screen)
    r.effects_surface = MagicMock()
    with (
        patch("pygame.draw.line", create=True) as mock_line,
        patch("pygame.draw.circle", create=True) as mock_circle,
    ):
        r._render_particles(game.particle_system.particles)
        assert mock_line.call_count == 7
        assert mock_circle.call_count == 1


def test_render_portal_visible(screen, game):
    r = GameRenderer(screen)
    # Put portal directly in front of player
    game.portal = {"x": 15.0, "y": 10.0, "radius": 1.0}
    with patch("pygame.draw.circle", create=True) as mock_circle:
        r._render_portal(game.portal, game.player)
        assert mock_circle.call_count == 2


def test_render_portal_invisible(screen, game):
    r = GameRenderer(screen)
    # Put portal behind player
    game.portal = {"x": 5.0, "y": 10.0, "radius": 1.0}
    with patch("pygame.draw.circle", create=True) as mock_circle:
        r._render_portal(game.portal, game.player)
        mock_circle.assert_not_called()

    # None portal
    r._render_portal(None, game.player)
