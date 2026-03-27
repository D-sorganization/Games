from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import src.constants as C
from src.weapon_renderer import WeaponRenderer


@pytest.fixture
def screen() -> Any:
    return MagicMock()


@pytest.fixture
def player() -> Any:
    p = MagicMock()
    p.sway_amount = 0.0
    p.is_moving = False
    p.bob_phase = 0.0
    p.weapon_state = {
        "pistol": {"reloading": False, "reload_timer": 0},
        "shotgun": {"reloading": False, "reload_timer": 0},
        "rifle": {"reloading": True, "reload_timer": 30},
        "minigun": {"reloading": False, "reload_timer": 0},
        "plasma": {"reloading": False, "reload_timer": 0, "overheated": False},
        "unknown": {"reloading": False, "reload_timer": 0},
    }
    p.current_weapon = "pistol"
    p.shooting = False
    p.zoomed = False
    return p


def test_render_weapon_pistol_idle(screen, player) -> Any:
    wr = WeaponRenderer(screen)
    with patch("pygame.time.get_ticks", return_value=0):
        with patch("pygame.draw.rect", create=True) as mock_rect:
            with patch("pygame.draw.line", create=True) as mock_line:
                with patch("pygame.draw.polygon", create=True) as mock_poly:
                    cx, cy = wr.render_weapon(player)
                    assert cx == C.SCREEN_WIDTH // 2
                    assert cy == C.SCREEN_HEIGHT
                    mock_rect.assert_called()
                    mock_poly.assert_called()
                    mock_line.assert_called()


def test_render_weapon_moving_bob_and_sway(screen, player) -> Any:
    wr = WeaponRenderer(screen)
    player.is_moving = True
    player.bob_phase = 1.0
    player.sway_amount = 0.5
    with (
        patch("pygame.draw.polygon", create=True),
        patch("pygame.draw.rect", create=True),
        patch("pygame.draw.line", create=True),
    ):
        cx, cy = wr.render_weapon(player)
        assert cx == C.SCREEN_WIDTH // 2 - 150 + 9
        assert cy == C.SCREEN_HEIGHT + 10


def test_render_weapon_shooting_pistol(screen, player) -> Any:
    wr = WeaponRenderer(screen)
    player.shooting = True
    with (
        patch("pygame.draw.polygon", create=True) as mock_poly,
        patch("pygame.draw.rect", create=True),
        patch("pygame.draw.line", create=True),
    ):
        cx, cy = wr.render_weapon(player)
        mock_poly.assert_called()


def test_render_weapon_rifle(screen, player) -> Any:
    wr = WeaponRenderer(screen)
    player.current_weapon = "rifle"
    player.zoomed = True
    with (
        patch("pygame.draw.rect", create=True),
        patch("pygame.draw.polygon", create=True),
        patch("pygame.draw.line", create=True),
        patch("pygame.draw.ellipse", create=True),
        patch("pygame.draw.circle", create=True),
        patch("pygame.time.get_ticks", return_value=0),
    ):
        cx, cy = wr.render_weapon(player)
        assert cy == 906

    player.zoomed = False
    with (
        patch("pygame.draw.rect", create=True),
        patch("pygame.draw.polygon", create=True),
        patch("pygame.draw.line", create=True),
        patch("pygame.draw.ellipse", create=True),
        patch("pygame.draw.circle", create=True),
        patch("pygame.time.get_ticks", return_value=0),
    ):
        cx, cy = wr.render_weapon(player)


def test_render_weapon_shotgun(screen, player) -> Any:
    wr = WeaponRenderer(screen)
    player.current_weapon = "shotgun"
    with (
        patch("pygame.draw.circle", create=True) as mock_circle,
        patch("pygame.draw.rect", create=True),
        patch("pygame.draw.polygon", create=True),
    ):
        wr.render_weapon(player)
        mock_circle.assert_called()


def test_render_weapon_minigun(screen, player) -> Any:
    wr = WeaponRenderer(screen)
    player.current_weapon = "minigun"
    player.shooting = True
    with patch("pygame.time.get_ticks", return_value=38):
        with patch("pygame.draw.rect", create=True) as mock_rect:
            wr.render_weapon(player)
            mock_rect.assert_called()

    player.shooting = False
    with patch("pygame.time.get_ticks", return_value=0):
        with patch("pygame.draw.rect", create=True):
            wr.render_weapon(player)


def test_render_weapon_plasma(screen, player) -> Any:
    wr = WeaponRenderer(screen)
    player.current_weapon = "plasma"
    player.shooting = True
    player.weapon_state["plasma"]["overheated"] = True
    with (
        patch("pygame.draw.polygon", create=True),
        patch("pygame.time.get_ticks", return_value=1000),
        patch("pygame.draw.rect", create=True),
        patch("pygame.draw.line", create=True),
    ):
        wr.render_weapon(player)

    player.shooting = False
    with (
        patch("pygame.draw.polygon", create=True),
        patch("pygame.time.get_ticks", return_value=0),
        patch("pygame.draw.rect", create=True),
        patch("pygame.draw.line", create=True),
    ):
        wr.render_weapon(player)


def test_render_weapon_unknown_zero_reload_max(screen, player) -> Any:
    wr = WeaponRenderer(screen)
    player.current_weapon = "unknown"
    player.weapon_state["unknown"]["reloading"] = True
    # We will temporarily mock the constant WEAPONS to have reload_time 0
    with patch.dict(C.WEAPONS, {"unknown": {"reload_time": 0}}):
        with patch("pygame.time.get_ticks", return_value=0):
            cx, cy = wr.render_weapon(player)
    assert cx == C.SCREEN_WIDTH // 2


def test_render_muzzle_flash_plasma(screen) -> Any:
    wr = WeaponRenderer(screen)
    with patch("pygame.draw.circle", create=True) as mock_circle:
        wr.render_muzzle_flash("plasma", (400, 600))
        assert mock_circle.call_count == 3


def test_render_muzzle_flash_shotgun(screen) -> Any:
    wr = WeaponRenderer(screen)
    with patch("pygame.draw.circle", create=True) as mock_circle:
        wr.render_muzzle_flash("shotgun", (400, 600))
        assert mock_circle.call_count == 3


def test_render_muzzle_flash_minigun(screen) -> Any:
    wr = WeaponRenderer(screen)
    with patch("pygame.draw.circle", create=True) as mock_circle:
        wr.render_muzzle_flash("minigun", (400, 600))
        assert mock_circle.call_count == 2


def test_render_muzzle_flash_default(screen) -> Any:
    wr = WeaponRenderer(screen)
    with patch("pygame.draw.circle", create=True) as mock_circle:
        wr.render_muzzle_flash("pistol", (400, 600))
        assert mock_circle.call_count == 3
