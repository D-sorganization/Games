from unittest.mock import MagicMock, patch

import pygame
import pytest

from games.Zombie_Survival.src.ui_renderer import UIRenderer


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
        with patch("games.Zombie_Survival.src.ui_renderer.pygame.Surface") as mock_surf:
            mock_surf_instance = MagicMock()
            mock_surf_base.return_value = mock_surf_instance
            mock_surf.return_value = mock_surf_instance
            yield mock_surf_instance

@pytest.fixture(autouse=True)
def setup_pygame_draw():
    with patch("pygame.draw") as draw:
        yield draw


@pytest.fixture(autouse=True)
def setup_pygame_display():
    with patch("pygame.display.flip") as flip:
        yield flip


@pytest.fixture
def mock_screen():
    screen = MagicMock()
    screen.blit = MagicMock()
    screen.get_width.return_value = 800
    screen.get_height.return_value = 600
    return screen


@pytest.fixture
def mock_game():
    game = MagicMock()
    game.selected_map_size = 50
    game.selected_difficulty = "Normal"
    game.selected_start_level = 1
    game.selected_lives = 3

    # Player state for HUD
    game.player = MagicMock()
    game.player.health = 100
    game.player.max_health = 100
    game.player.shield_timer = 100
    game.player.secondary_cooldown = 0
    game.player.stamina = 100
    game.player.max_stamina = 100
    game.player.shield_recharge_delay = 0
    game.player.shield_active = False
    game.player.current_weapon = "pistol"
    game.player.ammo = {"pistol": 100}

    game.damage_texts = [{"text": "-10", "color": (255, 0, 0), "x": 100, "y": 100}]
    game.damage_flash_timer = 0
    game.paused = False

    # Game over and Level Complete state
    game.level = 2
    game.level_times = [60.0]
    game.kills = 15
    game.particle_system = MagicMock()
    game.particle_system.particles = [
        MagicMock(timer=10, max_timer=20, x=100, y=100, size=5, color=(255, 0, 0))
    ]

    # Key config state
    game.input_manager = MagicMock()
    game.input_manager.bindings = {"move_forward": "W", "move_backward": "S"}
    game.input_manager.get_key_name.return_value = "W"
    game.binding_action = None

    return game


class TestUIRenderer:
    def test_ui_renderer_init(self, mock_screen):
        renderer = UIRenderer(mock_screen)
        assert renderer.screen == mock_screen
        assert renderer.start_button is not None

    def test_render_menu(self, mock_screen):
        renderer = UIRenderer(mock_screen)
        renderer.render_menu()

    def test_render_map_select(self, mock_screen, mock_game):
        with patch("pygame.mouse.get_pos", return_value=(400, 300)):
            renderer = UIRenderer(mock_screen)
            renderer.render_map_select(mock_game)

    def test_render_hud(self, mock_screen, mock_game):
        renderer = UIRenderer(mock_screen)
        renderer.render_hud(mock_game)

    def test_render_hud_paused(self, mock_screen, mock_game):
        # Additional coverage for paused mode
        mock_game.paused = True
        mock_game.cheat_mode_active = False
        mock_game.movement_speed_multiplier = 1.0
        with patch("pygame.mouse.get_pos", return_value=(400, 300)):
            renderer = UIRenderer(mock_screen)
            renderer.render_hud(mock_game)

    def test_render_hud_paused_cheat_mode(self, mock_screen, mock_game):
        mock_game.paused = True
        mock_game.cheat_mode_active = True
        mock_game.current_cheat_input = "IDDQD"
        with patch("pygame.mouse.get_pos", return_value=(400, 300)):
            renderer = UIRenderer(mock_screen)
            renderer.render_hud(mock_game)

    def test_render_level_complete(self, mock_screen, mock_game):
        renderer = UIRenderer(mock_screen)
        renderer.render_level_complete(mock_game)

    def test_render_game_over(self, mock_screen, mock_game):
        renderer = UIRenderer(mock_screen)
        renderer.render_game_over(mock_game)

    @pytest.mark.parametrize("phase", [0, 1, 2])
    def test_render_intro(self, mock_screen, phase):
        renderer = UIRenderer(mock_screen)
        # Mock intro images to reach code paths
        renderer.intro_images = {"willy": MagicMock(), "deadfish": MagicMock()}
        renderer.intro_video = None
        # Mock sys._MEIPASS logic so it doesn't fail

        for step in range(4):
            renderer.render_intro(phase, step, 1000)

    def test_render_intro_slide_types(self, mock_screen):
        renderer = UIRenderer(mock_screen)
        # Hit `distortion`, `story`, `static`
        for step in range(4):
            renderer._render_intro_slide(step, 2000)

    def test_render_key_config(self, mock_screen, mock_game):
        with patch("pygame.mouse.get_pos", return_value=(400, 300)):
            renderer = UIRenderer(mock_screen)
            renderer.render_key_config(mock_game)

    def test_blood_drips(self, mock_screen):
        renderer = UIRenderer(mock_screen)
        rect = pygame.Rect(0, 0, 100, 50)
        renderer.update_blood_drips(rect)
        renderer._draw_blood_drips(renderer.title_drips)
