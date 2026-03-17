from unittest.mock import MagicMock, patch

import pytest

from games.Force_Field.src.weapon_renderer import WeaponRenderer


@pytest.fixture(autouse=True)
def setup_pygame_font():
    with patch("pygame.font.SysFont") as mock_sysfont:
        mock_font = MagicMock()
        mock_font.render.return_value = MagicMock()
        mock_font.render.return_value.get_width.return_value = 50
        mock_font.render.return_value.get_height.return_value = 20
        mock_sysfont.return_value = mock_font
        yield mock_sysfont


@pytest.fixture(autouse=True)
def setup_pygame_time():
    with patch("pygame.time.get_ticks", return_value=1000):
        yield


@pytest.fixture(autouse=True)
def setup_pygame_draw():
    with patch("pygame.draw") as draw:
        yield draw


@pytest.fixture
def mock_screen():
    screen = MagicMock()
    screen.blit = MagicMock()
    return screen


@pytest.fixture
def mock_player():
    player = MagicMock()
    player.sway_amount = 0.0
    player.is_moving = False
    player.zoomed = False
    player.shooting = False

    # Base states
    player.weapon_state = {
        w: {"reloading": False, "reload_timer": 0, "clip": 10, "overheated": False}
        for w in [
            "pistol",
            "shotgun",
            "rifle",
            "minigun",
            "laser",
            "plasma",
            "pulse",
            "rocket",
            "bfg",
        ]
    }
    return player


class TestWeaponRenderer:
    def test_weapon_renderer_init(self, mock_screen):
        renderer = WeaponRenderer(mock_screen)
        assert renderer.screen == mock_screen
        assert renderer.font is not None

    @pytest.mark.parametrize(
        "weapon_name",
        [
            "pistol",
            "shotgun",
            "rifle",
            "minigun",
            "laser",
            "plasma",
            "pulse",
            "rocket",
            "bfg",
        ],
    )
    def test_render_weapons(self, mock_screen, mock_player, weapon_name):
        renderer = WeaponRenderer(mock_screen)
        mock_player.current_weapon = weapon_name
        cx, cy = renderer.render_weapon(mock_player)
        assert cx > 0
        assert cy > 0

    @pytest.mark.parametrize(
        "weapon_name",
        [
            "pistol",
            "shotgun",
            "rifle",
            "minigun",
            "laser",
            "plasma",
            "pulse",
            "rocket",
            "bfg",
        ],
    )
    def test_render_weapons_shooting(self, mock_screen, mock_player, weapon_name):
        renderer = WeaponRenderer(mock_screen)
        mock_player.current_weapon = weapon_name
        mock_player.shooting = True
        renderer.render_weapon(mock_player)

    def test_render_weapons_moving(self, mock_screen, mock_player):
        renderer = WeaponRenderer(mock_screen)
        mock_player.current_weapon = "pistol"
        mock_player.is_moving = True
        renderer.render_weapon(mock_player)

    def test_render_weapons_zoomed(self, mock_screen, mock_player):
        renderer = WeaponRenderer(mock_screen)
        mock_player.current_weapon = "rifle"
        mock_player.zoomed = True
        renderer.render_weapon(mock_player)

    def test_render_weapons_reloading(self, mock_screen, mock_player):
        renderer = WeaponRenderer(mock_screen)
        mock_player.current_weapon = "pistol"
        mock_player.weapon_state["pistol"]["reloading"] = True
        mock_player.weapon_state["pistol"]["reload_timer"] = 30
        renderer.render_weapon(mock_player)

    def test_render_weapons_overheated(self, mock_screen, mock_player):
        renderer = WeaponRenderer(mock_screen)
        mock_player.current_weapon = "plasma"
        mock_player.weapon_state["plasma"]["overheated"] = True
        renderer.render_weapon(mock_player)

    def test_render_weapons_rocket_empty(self, mock_screen, mock_player):
        renderer = WeaponRenderer(mock_screen)
        mock_player.current_weapon = "rocket"
        mock_player.weapon_state["rocket"]["clip"] = 0
        renderer.render_weapon(mock_player)

    @pytest.mark.parametrize(
        "weapon_name", ["plasma", "pulse", "shotgun", "minigun", "bfg", "unknown"]
    )
    def test_render_muzzle_flash(self, mock_screen, weapon_name):
        renderer = WeaponRenderer(mock_screen)
        renderer.render_muzzle_flash(weapon_name, (400, 300))
