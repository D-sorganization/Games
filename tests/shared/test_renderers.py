from unittest.mock import MagicMock, patch

import pygame
import pytest

from games.shared.config import RaycasterConfig
from games.shared.renderers.__init__ import BotStyleRendererFactory
from games.shared.renderers.baby_renderer import BabyStyleRenderer
from games.shared.renderers.ball_renderer import BallStyleRenderer
from games.shared.renderers.base import BaseBotStyleRenderer
from games.shared.renderers.beast_renderer import BeastStyleRenderer
from games.shared.renderers.cyber_demon_renderer import CyberDemonStyleRenderer
from games.shared.renderers.ghost_renderer import GhostStyleRenderer
from games.shared.renderers.item_renderer import ItemRenderer
from games.shared.renderers.minigunner_renderer import MinigunnerStyleRenderer
from games.shared.renderers.monster_renderer import MonsterStyleRenderer
from games.shared.renderers.weapon_pickup_renderer import WeaponPickupRenderer


@pytest.fixture
def mock_surface():
    """Provides a mocked pygame.Surface."""
    return MagicMock(spec=pygame.Surface)


@pytest.fixture
def mock_bot():
    """Provides a mocked Bot."""
    bot = MagicMock()
    bot.x = 0
    bot.y = 0
    bot.angle = 0
    bot.dir_x = 1
    bot.dir_y = 0
    # Provide various properties that renderers might use
    bot.moving = False
    bot.mouth_open = False
    bot.attack_frame = 0
    bot.time_alive = 0
    bot.eye_angle = 0
    bot.shoot_animation = 0
    bot.dead = False
    bot.death_timer = 0
    return bot


@pytest.fixture
def base_config():
    """Provides a basic RaycasterConfig."""
    config = MagicMock(spec=RaycasterConfig)
    config.SCREEN_WIDTH = 800
    config.SCREEN_HEIGHT = 600
    config.FOV = 3.14159 / 3
    config.HALF_FOV = config.FOV / 2
    return config


@pytest.fixture(autouse=True)
def mock_pygame_draw():
    with patch("pygame.draw") as mock_draw:
        yield mock_draw


class TestRenderers:
    def test_ball_renderer(self, mock_surface, mock_bot, base_config):
        renderer = BallStyleRenderer()
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )

    def test_baby_renderer(self, mock_surface, mock_bot, base_config):
        renderer = BabyStyleRenderer()
        # Test normal
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )
        # Test mouth open
        mock_bot.mouth_open = True
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )

    def test_beast_renderer(self, mock_surface, mock_bot, base_config):
        renderer = BeastStyleRenderer()
        mock_bot.attack_frame = 1  # test different attacks
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )
        mock_bot.moving = True
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )

    def test_cyber_demon_renderer(self, mock_surface, mock_bot, base_config):
        renderer = CyberDemonStyleRenderer()
        mock_bot.attack_frame = 2
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )
        mock_bot.shoot_animation = 1
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )

    def test_ghost_renderer(self, mock_surface, mock_bot, base_config):
        renderer = GhostStyleRenderer()
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )

    @patch("games.shared.renderers.item_renderer.random.random", return_value=0.1)
    def test_item_renderer(self, mock_random, mock_surface, mock_bot, base_config):
        # The bot argument is actually used as an item here, but the signature matches.
        mock_item = MagicMock()
        mock_item.enemy_type = "health_pack"
        renderer = ItemRenderer()
        renderer.render(
            mock_surface, mock_item, 100, 100, 50, 50, (0, 255, 0), base_config
        )

        mock_item.enemy_type = "ammo_box"
        renderer.render(
            mock_surface, mock_item, 100, 100, 50, 50, (0, 255, 0), base_config
        )

        mock_item.enemy_type = "bomb_item"
        renderer.render(
            mock_surface, mock_item, 100, 100, 50, 50, (0, 255, 0), base_config
        )

        mock_item.enemy_type = "unknown"
        renderer.render(
            mock_surface, mock_item, 100, 100, 50, 50, (0, 255, 0), base_config
        )

    @patch("games.shared.renderers.item_renderer.random.random", return_value=0.9)
    def test_item_renderer_no_spark(
        self, mock_random, mock_surface, mock_bot, base_config
    ):  # noqa: E501
        mock_item = MagicMock()
        mock_item.enemy_type = "bomb_item"
        renderer = ItemRenderer()
        renderer.render(
            mock_surface, mock_item, 100, 100, 50, 50, (0, 255, 0), base_config
        )

    def test_minigunner_renderer(self, mock_surface, mock_bot, base_config):
        renderer = MinigunnerStyleRenderer()
        mock_bot.attack_frame = 0
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )
        mock_bot.shoot_animation = 1
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )

    def test_monster_renderer(self, mock_surface, mock_bot, base_config):
        renderer = MonsterStyleRenderer()
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )
        mock_bot.moving = True
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )
        mock_bot.enemy_type = "boss"
        mock_bot.mouth_open = True
        mock_bot.shoot_animation = 1
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )
        mock_bot.dead = True
        mock_bot.death_timer = 20
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )
        mock_bot.death_timer = 40
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )

    def test_weapon_pickup_renderer(self, mock_surface, mock_bot, base_config):
        mock_item = MagicMock()
        mock_item.enemy_type = "pickup_shotgun"
        renderer = WeaponPickupRenderer()
        renderer.render(
            mock_surface, mock_item, 100, 100, 50, 50, (255, 255, 255), base_config
        )

        mock_item.enemy_type = "pickup_minigun"
        renderer.render(
            mock_surface, mock_item, 100, 100, 50, 50, (255, 255, 255), base_config
        )

        mock_item.enemy_type = "pickup_plasma"
        renderer.render(
            mock_surface, mock_item, 100, 100, 50, 50, (255, 255, 255), base_config
        )

        mock_item.enemy_type = "pickup_rocket"
        renderer.render(
            mock_surface, mock_item, 100, 100, 50, 50, (255, 255, 255), base_config
        )


class TestRendererFactory:
    def test_factory_registration(self):
        # Our __init__.py automatically registers these
        renderer1 = BotStyleRendererFactory.get_renderer("monster")
        assert isinstance(renderer1, MonsterStyleRenderer)

        renderer2 = BotStyleRendererFactory.get_renderer("beast")
        assert isinstance(renderer2, BeastStyleRenderer)

        # Retrieve a non-existent renderer
        renderer_none = BotStyleRendererFactory.get_renderer("non_existent_style")
        assert renderer_none is None

    def test_base_renderer_protocol(self, mock_surface, mock_bot, base_config):
        class DummyRenderer(BaseBotStyleRenderer):
            def render(self, *args, **kwargs):
                super().render(*args, **kwargs)

        renderer = DummyRenderer()
        renderer.render(
            mock_surface, mock_bot, 100, 100, 50, 50, (255, 0, 0), base_config
        )
