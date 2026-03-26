from unittest.mock import MagicMock, patch

import pytest

from games.Zombie_Survival.src.weapon_renderer import WeaponRenderer


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
        for w in ["pistol", "shotgun", "rifle", "minigun", "plasma"]
    }
    return player


class TestWeaponRenderer:
    def test_weapon_renderer_init(self, mock_screen):
        renderer = WeaponRenderer(mock_screen)
        assert renderer.screen == mock_screen

    @pytest.mark.parametrize("weapon_name", ["pistol", "shotgun", "rifle", "minigun", "plasma"])
    def test_render_weapons(self, mock_screen, mock_player, weapon_name):
        renderer = WeaponRenderer(mock_screen)
        mock_player.current_weapon = weapon_name
        cx, cy = renderer.render_weapon(mock_player)
        assert cx > 0
        assert cy > 0

    @pytest.mark.parametrize("weapon_name", ["pistol", "shotgun", "rifle", "minigun", "plasma"])
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

    @pytest.mark.parametrize("weapon_name", ["plasma", "shotgun", "minigun", "unknown"])
    def test_render_muzzle_flash(self, mock_screen, weapon_name):
        renderer = WeaponRenderer(mock_screen)
        renderer.render_muzzle_flash(weapon_name, (400, 300))
