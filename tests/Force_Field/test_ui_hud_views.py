"""Tests for Force_Field HUD view helpers extracted from UIRenderer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pygame
import pytest

from games.Force_Field.src import ui_hud_views
from games.Force_Field.src.ui_renderer import UIRenderer


@pytest.fixture(autouse=True)
def setup_pygame_font():
    with patch("pygame.font.SysFont") as mock_sysfont:
        mock_font = MagicMock()
        mock_surf = MagicMock()
        mock_surf.get_width.return_value = 50
        mock_surf.get_height.return_value = 20
        mock_surf.get_rect.return_value = pygame.Rect(0, 0, 50, 20)
        mock_font.render.return_value = mock_surf
        mock_sysfont.return_value = mock_font
        yield mock_sysfont


@pytest.fixture(autouse=True)
def setup_pygame_surface():
    with patch("games.shared.ui_renderer_base.pygame.Surface") as mock_surf_base:
        with patch("games.Force_Field.src.ui_renderer.pygame.Surface") as mock_surf:
            with patch(
                "games.Force_Field.src.ui_overlay_views.pygame.Surface"
            ) as overlay_surf:
                with patch(
                    "games.Force_Field.src.ui_hud_views.pygame.Surface"
                ) as hud_surf:
                    mock_surf_instance = MagicMock()
                    mock_surf_base.return_value = mock_surf_instance
                    mock_surf.return_value = mock_surf_instance
                    overlay_surf.return_value = mock_surf_instance
                    hud_surf.return_value = mock_surf_instance
                    yield mock_surf_instance


@pytest.fixture(autouse=True)
def setup_pygame_draw():
    with patch("pygame.draw") as draw:
        yield draw


@pytest.fixture
def mock_screen():
    screen = MagicMock()
    screen.blit = MagicMock()
    screen.get_width.return_value = 800
    screen.get_height.return_value = 600
    return screen


@pytest.fixture
def mock_renderer(mock_screen):
    return UIRenderer(mock_screen)


@pytest.fixture
def mock_game():
    game = MagicMock()
    game.player = MagicMock()
    game.player.health = 100
    game.player.max_health = 100
    game.player.shield_timer = 100
    game.player.secondary_cooldown = 0
    game.player.stamina = 100
    game.player.max_stamina = 100
    game.player.shield_recharge_delay = 0
    game.player.shield_active = False
    game.damage_texts = []
    game.damage_flash_timer = 0
    game.paused = False
    game.raycaster = MagicMock()
    return game


class TestUiHudViewsModule:
    def test_module_exposes_render_hud(self):
        assert callable(ui_hud_views.render_hud)

    def test_module_exposes_render_health_bar(self):
        assert callable(ui_hud_views.render_health_bar)

    def test_module_exposes_render_status_bars(self):
        assert callable(ui_hud_views.render_status_bars)

    def test_module_exposes_render_damage_texts(self):
        assert callable(ui_hud_views.render_damage_texts)

    def test_module_exposes_render_damage_flash(self):
        assert callable(ui_hud_views.render_damage_flash)

    def test_module_exposes_render_shield_effect(self):
        assert callable(ui_hud_views.render_shield_effect)

    def test_module_exposes_render_low_health_tint(self):
        assert callable(ui_hud_views.render_low_health_tint)

    def test_module_exposes_render_crosshair(self):
        assert callable(ui_hud_views.render_crosshair)

    def test_module_exposes_render_secondary_charge(self):
        assert callable(ui_hud_views.render_secondary_charge)

    def test_module_exposes_render_controls_hint(self):
        assert callable(ui_hud_views.render_controls_hint)


class TestRenderHud:
    def test_render_hud_runs_without_error(self, mock_renderer, mock_game):
        ui_hud_views.render_hud(mock_renderer, mock_game)

    def test_render_hud_checks_player_precondition(self, mock_renderer, mock_game):
        mock_game.player = None
        with pytest.raises(ValueError):
            ui_hud_views.render_hud(mock_renderer, mock_game)

    def test_render_hud_checks_raycaster_precondition(self, mock_renderer, mock_game):
        mock_game.raycaster = None
        with pytest.raises(ValueError):
            ui_hud_views.render_hud(mock_renderer, mock_game)

    def test_render_hud_delegates_from_ui_renderer(self, mock_renderer, mock_game):
        """UIRenderer.render_hud should delegate to ui_hud_views.render_hud."""
        with patch(
            "games.Force_Field.src.ui_renderer.ui_hud_views.render_hud"
        ) as mock_render:
            mock_renderer.render_hud(mock_game)
        mock_render.assert_called_once_with(mock_renderer, mock_game)


class TestRenderHealthBar:
    def test_render_health_bar_runs(self, mock_renderer, mock_game):
        ui_hud_views.render_health_bar(mock_renderer, mock_game)

    def test_render_health_bar_low_health_runs(self, mock_renderer, mock_game):
        mock_game.player.health = 25
        mock_game.player.max_health = 100
        # Should run without error even at low health
        ui_hud_views.render_health_bar(mock_renderer, mock_game)


class TestRenderStatusBars:
    def test_render_status_bars_runs(self, mock_renderer, mock_game):
        ui_hud_views.render_status_bars(mock_renderer, mock_game)


class TestRenderDamageFlash:
    def test_no_flash_when_timer_zero(self, mock_renderer):
        mock_renderer.overlay_surface = MagicMock()
        with patch("games.Force_Field.src.ui_hud_views.pygame") as mock_pygame:
            ui_hud_views.render_damage_flash(mock_renderer, 0)
        mock_renderer.overlay_surface.fill.assert_not_called()

    def test_flash_when_timer_positive(self, mock_renderer):
        mock_renderer.overlay_surface = MagicMock()
        with patch("games.Force_Field.src.ui_hud_views.pygame") as mock_pygame:
            mock_pygame.BLEND_RGBA_ADD = 0
            ui_hud_views.render_damage_flash(mock_renderer, 5)
        mock_renderer.overlay_surface.fill.assert_called_once()


class TestRenderShieldEffect:
    def test_shield_inactive_no_overlay(self, mock_renderer, mock_game):
        mock_game.player.shield_active = False
        mock_game.player.shield_timer = 0
        mock_game.player.shield_recharge_delay = 1
        mock_renderer.overlay_surface = MagicMock()
        with patch("pygame.draw.rect"):
            ui_hud_views.render_shield_effect(mock_renderer, mock_game.player)
        mock_renderer.overlay_surface.fill.assert_not_called()

    def test_shield_active_renders(self, mock_renderer, mock_game):
        mock_game.player.shield_active = True
        mock_game.player.shield_timer = 180
        mock_renderer.overlay_surface = MagicMock()
        with patch("pygame.draw.rect"):
            ui_hud_views.render_shield_effect(mock_renderer, mock_game.player)
        mock_renderer.overlay_surface.fill.assert_not_called()  # Uses draw.rect, not fill


class TestRenderLowHealthTint:
    def test_no_tint_when_health_high(self, mock_renderer, mock_game):
        mock_game.player.health = 100
        mock_renderer.overlay_surface = MagicMock()
        with patch("games.Force_Field.src.ui_hud_views.pygame"):
            ui_hud_views.render_low_health_tint(mock_renderer, mock_game.player)
        mock_renderer.overlay_surface.fill.assert_not_called()

    def test_tint_when_health_low(self, mock_renderer, mock_game):
        mock_game.player.health = 10
        mock_renderer.overlay_surface = MagicMock()
        with patch("games.Force_Field.src.ui_hud_views.pygame") as mock_pygame:
            mock_pygame.BLEND_RGBA_ADD = 0
            ui_hud_views.render_low_health_tint(mock_renderer, mock_game.player)
        mock_renderer.overlay_surface.fill.assert_called_once()


class TestRenderCrosshair:
    def test_render_crosshair_runs(self, mock_renderer):
        with patch("pygame.draw.line"), patch("pygame.draw.circle"):
            ui_hud_views.render_crosshair(mock_renderer)


class TestRenderSecondaryCharge:
    def test_no_bar_when_fully_charged(self, mock_renderer, mock_game):
        mock_game.player.secondary_cooldown = 0
        # charge_pct == 1.0, bar should not render
        ui_hud_views.render_secondary_charge(mock_renderer, mock_game.player)

    def test_bar_when_recharging(self, mock_renderer, mock_game):
        mock_game.player.secondary_cooldown = 30
        # Should run without error when charge < 1.0
        ui_hud_views.render_secondary_charge(mock_renderer, mock_game.player)


class TestRenderControlsHint:
    def test_render_controls_hint_runs(self, mock_renderer):
        ui_hud_views.render_controls_hint(mock_renderer)
