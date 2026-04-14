"""Tests for Zombie Survival GameRenderer."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _mock_pygame_surface(monkeypatch):
    """Mock pygame.Surface so GameRenderer can be imported without a display."""
    import pygame

    mock_surface = MagicMock()
    mock_surface.fill = MagicMock()
    mock_surface.blit = MagicMock()
    monkeypatch.setattr(pygame, "Surface", lambda *a, **kw: mock_surface)
    monkeypatch.setattr(pygame.draw, "line", MagicMock())
    monkeypatch.setattr(pygame.draw, "circle", MagicMock())
    monkeypatch.setattr(pygame.display, "flip", MagicMock())
    return mock_surface


@pytest.fixture(autouse=True)
def _mock_weapon_renderer(monkeypatch):
    """Mock WeaponRenderer to avoid pygame Surface dependency."""
    mock_wr = MagicMock()
    mock_wr.return_value = MagicMock()
    monkeypatch.setattr("games.Zombie_Survival.src.renderer.WeaponRenderer", mock_wr)
    return mock_wr


def _make_renderer():
    from games.Zombie_Survival.src.renderer import GameRenderer

    screen = MagicMock()
    screen.blit = MagicMock()
    return GameRenderer(screen)


def _make_game(**overrides):
    player = MagicMock()
    player.is_moving = False
    player.shooting = False
    player.current_weapon = "pistol"
    base = {
        "raycaster": MagicMock(),
        "player": player,
        "bots": [],
        "level": MagicMock(),
        "projectiles": [],
        "portal": None,
        "particle_system": MagicMock(),
        "ui_renderer": MagicMock(),
    }
    base["particle_system"].particles = []
    base.update(overrides)
    return SimpleNamespace(**base)


# ---------------------------------------------------------------------------
# render_game — DbC
# ---------------------------------------------------------------------------


def test_render_game_no_raycaster_raises() -> None:
    renderer = _make_renderer()
    game = _make_game(raycaster=None)
    with pytest.raises(ValueError, match="DbC"):
        renderer.render_game(game)


def test_render_game_no_player_raises() -> None:
    renderer = _make_renderer()
    game = _make_game(player=None)
    with pytest.raises(ValueError, match="DbC"):
        renderer.render_game(game)


# ---------------------------------------------------------------------------
# render_game — raycaster calls
# ---------------------------------------------------------------------------


def test_render_game_calls_raycaster_render_floor_ceiling() -> None:
    renderer = _make_renderer()
    game = _make_game()
    renderer.render_game(game)
    game.raycaster.render_floor_ceiling.assert_called_once()


def test_render_game_calls_raycaster_render_3d() -> None:
    renderer = _make_renderer()
    game = _make_game()
    renderer.render_game(game)
    game.raycaster.render_3d.assert_called_once()


# ---------------------------------------------------------------------------
# render_game — muzzle flash
# ---------------------------------------------------------------------------


def test_render_game_calls_muzzle_flash_when_shooting() -> None:
    renderer = _make_renderer()
    game = _make_game()
    game.player.shooting = True
    renderer.render_game(game)
    renderer.weapon_renderer.render_muzzle_flash.assert_called_once()


def test_render_game_no_muzzle_flash_when_not_shooting() -> None:
    renderer = _make_renderer()
    game = _make_game()
    game.player.shooting = False
    renderer.render_game(game)
    renderer.weapon_renderer.render_muzzle_flash.assert_not_called()


# ---------------------------------------------------------------------------
# _render_particles
# ---------------------------------------------------------------------------


def test_render_particles_laser_type(monkeypatch) -> None:
    import pygame

    renderer = _make_renderer()
    renderer.effects_surface = MagicMock()

    mock_draw_line = MagicMock()
    monkeypatch.setattr(pygame.draw, "line", mock_draw_line)

    p = SimpleNamespace(
        ptype="laser",
        timer=10,
        start_pos=(0, 0),
        end_pos=(100, 100),
        color=(255, 0, 0),
        width=2,
    )
    renderer._render_particles([p])
    assert mock_draw_line.call_count >= 1


def test_render_particles_normal_type(monkeypatch) -> None:
    import pygame

    renderer = _make_renderer()
    renderer.effects_surface = MagicMock()

    mock_draw_circle = MagicMock()
    monkeypatch.setattr(pygame.draw, "circle", mock_draw_circle)

    p = SimpleNamespace(
        ptype="normal",
        timer=30,
        x=100.0,
        y=100.0,
        color=(200, 0, 0),
        size=4.0,
    )
    renderer._render_particles([p])
    mock_draw_circle.assert_called_once()


def test_render_particles_empty_list_no_draws(monkeypatch) -> None:
    import pygame

    renderer = _make_renderer()
    renderer.effects_surface = MagicMock()

    mock_draw = MagicMock()
    monkeypatch.setattr(pygame.draw, "line", mock_draw)
    monkeypatch.setattr(pygame.draw, "circle", mock_draw)

    renderer._render_particles([])
    mock_draw.assert_not_called()


# ---------------------------------------------------------------------------
# _render_portal
# ---------------------------------------------------------------------------


def test_render_portal_none_does_nothing(monkeypatch) -> None:
    import pygame

    renderer = _make_renderer()
    mock_draw_circle = MagicMock()
    monkeypatch.setattr(pygame.draw, "circle", mock_draw_circle)

    player = MagicMock()
    renderer._render_portal(None, player)
    mock_draw_circle.assert_not_called()


def test_render_portal_behind_player_no_draw(monkeypatch) -> None:
    import pygame

    renderer = _make_renderer()
    mock_draw_circle = MagicMock()
    monkeypatch.setattr(pygame.draw, "circle", mock_draw_circle)

    player = SimpleNamespace(x=5.0, y=5.0, angle=0.0)
    portal = {"x": 4.0, "y": 5.0}
    renderer._render_portal(portal, player)
    mock_draw_circle.assert_not_called()


def test_render_portal_in_front_draws_circles(monkeypatch) -> None:
    import pygame

    renderer = _make_renderer()
    mock_draw_circle = MagicMock()
    monkeypatch.setattr(pygame.draw, "circle", mock_draw_circle)

    player = SimpleNamespace(x=5.0, y=5.0, angle=0.0)
    # Portal in front at angle=0: b = dx*cos(0) + dy*sin(0) = dx > 0
    portal = {"x": 10.0, "y": 5.0}
    renderer._render_portal(portal, player)
    assert mock_draw_circle.call_count >= 1
