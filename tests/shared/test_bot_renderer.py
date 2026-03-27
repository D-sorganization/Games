from unittest.mock import MagicMock, patch

import pygame
import pytest

from games.shared.bot_renderer import BotRenderer
from games.shared.config import RaycasterConfig


@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.enemy_type = "monster"
    bot.type_data = {"color": (255, 0, 0), "visual_style": "monster"}
    bot.dead = False
    bot.death_timer = 0
    bot.disintegrate_timer = 0
    bot.shoot_animation = 0
    return bot


@pytest.fixture
def base_config():
    config = MagicMock(spec=RaycasterConfig)
    return config


@pytest.fixture
def mock_screen():
    screen = MagicMock(spec=pygame.Surface)
    return screen


@pytest.fixture(autouse=True)
def mock_pygame_draw():
    with patch("pygame.draw") as draw:
        yield draw


class TestBotRenderer:
    def test_render_sprite_normal(self, mock_screen, mock_bot, base_config):
        BotRenderer.render_sprite(mock_screen, mock_bot, 100, 100, 50, base_config)

    def test_render_sprite_item_health(self, mock_screen, mock_bot, base_config):
        mock_bot.enemy_type = "health_pack"
        mock_bot.type_data = {"color": (0, 255, 0), "visual_style": "health_pack"}
        BotRenderer.render_sprite(mock_screen, mock_bot, 100, 100, 50, base_config)

    def test_render_sprite_item_pickup(self, mock_screen, mock_bot, base_config):
        mock_bot.enemy_type = "pickup_shotgun"
        mock_bot.type_data = {"color": (0, 255, 0), "visual_style": "pickup_shotgun"}
        BotRenderer.render_sprite(mock_screen, mock_bot, 100, 100, 50, base_config)

    def test_render_sprite_unhandled_item_type(
        self, mock_screen, mock_bot, base_config
    ):
        mock_bot.enemy_type = "unknown_item"
        mock_bot.type_data = {"color": (0, 255, 0), "visual_style": "unknown_item"}
        BotRenderer.render_sprite(mock_screen, mock_bot, 100, 100, 50, base_config)

    def test_render_sprite_dead_melting(self, mock_screen, mock_bot, base_config):
        mock_bot.dead = True
        mock_bot.death_timer = 30
        BotRenderer.render_sprite(mock_screen, mock_bot, 100, 100, 50, base_config)

    def test_render_sprite_dead_disintegrating(
        self, mock_screen, mock_bot, base_config
    ):
        mock_bot.dead = True
        mock_bot.death_timer = 60
        mock_bot.disintegrate_timer = 50
        BotRenderer.render_sprite(mock_screen, mock_bot, 100, 100, 50, base_config)

    def test_render_sprite_dead_fully_disintegrated(
        self, mock_screen, mock_bot, base_config
    ):
        mock_bot.dead = True
        mock_bot.death_timer = 60
        mock_bot.disintegrate_timer = 100
        BotRenderer.render_sprite(mock_screen, mock_bot, 100, 100, 50, base_config)

    def test_render_sprite_other_visual_style(self, mock_screen, mock_bot, base_config):
        mock_bot.type_data["visual_style"] = "ball"
        BotRenderer.render_sprite(mock_screen, mock_bot, 100, 100, 50, base_config)

    @patch(
        "games.shared.bot_renderer.BotStyleRendererFactory.get_renderer",
        return_value=None,
    )
    def test_render_sprite_missing_renderer(
        self, mock_get_renderer, mock_screen, mock_bot, base_config
    ):
        BotRenderer.render_sprite(mock_screen, mock_bot, 100, 100, 50, base_config)

    @patch(
        "games.shared.bot_renderer.BotStyleRendererFactory.get_renderer",
        return_value=None,
    )
    def test_render_sprite_missing_item_renderers(
        self, mock_get_renderer, mock_screen, mock_bot, base_config
    ):
        mock_bot.enemy_type = "health_pack"
        BotRenderer.render_sprite(mock_screen, mock_bot, 100, 100, 50, base_config)
        mock_bot.enemy_type = "pickup_shotgun"
        BotRenderer.render_sprite(mock_screen, mock_bot, 100, 100, 50, base_config)
