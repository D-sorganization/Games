import math
from unittest.mock import MagicMock, patch

from games.shared.constants import DEATH_ANIMATION_FRAMES, DISINTEGRATE_FRAMES
from src.bot import Bot


def test_bot_init_no_type():
    with patch("src.bot.random.choice", return_value="ninja"):
        bot = Bot(0, 0, 1)
        assert bot.enemy_type == "ninja"


def test_bot_update_dead():
    bot = Bot(0, 0, 1, enemy_type="ninja")
    bot.dead = True
    bot.death_timer = 0
    assert bot.update(MagicMock(), MagicMock(), []) is None
    assert bot.death_timer == 1

    # Faster forward death - disintegrating but not complete
    bot.death_timer = DEATH_ANIMATION_FRAMES + 1
    bot.disintegrate_timer = DISINTEGRATE_FRAMES - 1
    bot.update(MagicMock(), MagicMock(), [])
    assert bot.removed is False

    # Fast forward death complete
    bot.death_timer = DEATH_ANIMATION_FRAMES + 1
    bot.disintegrate_timer = DISINTEGRATE_FRAMES + 1
    bot.update(MagicMock(), MagicMock(), [])
    assert bot.removed is True


def test_bot_update_health_pack():
    bot = Bot(0, 0, 1, enemy_type="health_pack")
    assert bot.update(MagicMock(), MagicMock(), []) is None


def test_bot_visual_animations():
    bot = Bot(0, 0, 1, enemy_type="ninja")
    bot.shoot_animation = 0.15
    bot.mouth_timer = 30

    bot.update(MagicMock(), MagicMock(), [])
    assert math.isclose(bot.shoot_animation, 0.05)
    assert bot.mouth_open is True
    assert bot.mouth_timer == 0


def _make_ball_bot_fixtures():
    """Return a (bot, player, game_map) triple for ball-bot tests."""
    bot = Bot(0, 0, 1, enemy_type="ball")
    player = MagicMock()
    player.x = 10.0
    player.y = 0.0
    player.god_mode = False
    game_map = MagicMock()
    game_map.is_wall.return_value = False
    return bot, player, game_map


def test_behavior_ball():
    bot, player, game_map = _make_ball_bot_fixtures()

    # Normal roll
    bot.update(game_map, player, [])
    assert bot.vx > 0
    assert bot.x > 0

    _test_ball_wall_bounces(bot, player, game_map)
    _test_ball_player_crush(bot, player, game_map)


def _test_ball_wall_bounces(bot, player, game_map):
    """Assert ball bounces off X and Y walls."""
    bot.x = 0.0
    bot.vx = 0.1
    bot.speed = 100.0
    game_map.is_wall.side_effect = lambda x, y: x > 0.05
    bot.update(game_map, player, [])
    assert bot.vx < 0
    assert bot.x == 0.0

    bot.y = 0.0
    bot.vy = 0.1
    bot.speed = 100.0
    game_map.is_wall.side_effect = lambda x, y: y > 0.05
    bot.update(game_map, player, [])
    assert bot.vy < 0
    assert bot.y == 0.0

    # Max speed cap
    bot.speed = 0.1
    bot.vx = 100.0
    bot.vy = 100.0
    bot.x = 0.0
    bot.y = 0.0
    game_map.is_wall.side_effect = None
    game_map.is_wall.return_value = False
    bot.update(game_map, player, [])
    assert bot.vx < 100.0
    assert bot.vy < 100.0

    # Distance == 0 edge case
    bot.x = 10.0
    bot.y = 0.0
    player.x = 10.0
    player.y = 0.0
    bot.vx = 0.0
    bot.vy = 0.0
    bot.update(game_map, player, [])
    assert abs(bot.vx) < 0.0001


def _test_ball_player_crush(bot, player, game_map):
    """Assert ball crushes player and respects god mode."""
    player.x = 10.0
    player.y = 0.0
    game_map.is_wall.side_effect = None
    game_map.is_wall.return_value = False

    bot.vx = 1.0
    bot.vy = 0.0
    bot.x = 9.5
    bot.y = 0.0
    player.god_mode = False
    bot.update(game_map, player, [])
    player.take_damage.assert_called()
    assert bot.vx < 0

    player.take_damage.reset_mock()
    bot.vx = 1.0
    bot.vy = 0.0
    bot.x = 9.5
    bot.y = 0.0
    player.god_mode = True
    bot.update(game_map, player, [])
    player.take_damage.assert_not_called()
    assert bot.vx < 0


def test_behavior_ninja():
    bot = Bot(0, 0, 1, enemy_type="ninja")
    bot.attack_timer = 5

    player = MagicMock()
    player.x = 10.0
    player.y = 10.0

    game_map = MagicMock()
    game_map.is_wall.return_value = False

    # Attack timer decrease
    bot.update(game_map, player, [])
    assert bot.attack_timer == 4

    # Melee attack god mode disabled
    bot.x = 9.5
    bot.y = 10.0
    bot.attack_timer = 0
    player.god_mode = False
    bot.update(game_map, player, [])
    player.take_damage.assert_called()

    # Melee attack god mode
    player.take_damage.reset_mock()
    bot.x = 9.5
    bot.y = 10.0
    bot.attack_timer = 0
    player.god_mode = True
    bot.update(game_map, player, [])
    player.take_damage.assert_not_called()
    assert bot.attack_timer == 30

    # Out of range, timer <= 0
    bot.x = 0.0
    bot.y = 0.0
    bot.attack_timer = 0
    bot.update(game_map, player, [])
    assert bot.attack_timer == 0


def test_behavior_beast():
    bot = Bot(0, 0, 1, enemy_type="beast")
    bot.attack_timer = 0

    player = MagicMock()
    player.x = 10.0
    player.y = 0.0

    game_map = MagicMock()
    game_map.is_wall.return_value = False

    with patch("src.bot.Bot.has_line_of_sight", return_value=True):
        proj = bot.update(game_map, player, [])
        assert proj is not None
        assert proj.speed == 0.15
        assert bot.attack_timer == 120
        assert bot.shoot_animation == 1.0

    # Out of range, timer <= 0
    bot.attack_timer = 0
    player.x = 100.0
    bot.update(game_map, player, [])
    assert bot.attack_timer == 0


def test_behavior_minigunner():
    bot = Bot(0, 0, 1, enemy_type="minigunner")
    bot.attack_timer = 0

    player = MagicMock()
    player.x = 5.0
    player.y = 0.0

    game_map = MagicMock()
    game_map.is_wall.return_value = False

    with patch("src.bot.Bot.has_line_of_sight", return_value=True):
        proj = bot.update(game_map, player, [])
        assert proj is not None
        assert proj.speed == 0.2
        assert bot.attack_timer == 10

    # Out of range, timer <= 0
    bot.attack_timer = 0
    bot.x = 0
    bot.y = 0
    player.x = 100.0
    bot.update(game_map, player, [])
    assert bot.attack_timer == 0

    # In range, timer decrease
    bot.attack_timer = 5
    player.x = 5.0
    bot.update(game_map, player, [])
    assert bot.attack_timer == 4

    # In range, no line of sight
    bot.attack_timer = 0
    with patch("src.bot.Bot.has_line_of_sight", return_value=False):
        assert bot.update(game_map, player, []) is None


def test_behavior_standard():
    bot = Bot(0, 0, 1, enemy_type="zombie")
    bot.attack_timer = 0

    player = MagicMock()
    player.x = 2.0
    player.y = 0.0

    game_map = MagicMock()
    game_map.is_wall.return_value = False

    with patch("src.bot.Bot.has_line_of_sight", return_value=True):
        proj = bot.update(game_map, player, [])
        assert proj is not None
        assert bot.shoot_animation == 1.0

    # Out of range, timer <= 0
    bot.attack_timer = 0
    player.x = 100.0
    bot.update(game_map, player, [])
    assert bot.attack_timer == 0

    # In range, timer decrease
    bot.attack_timer = 5
    bot.update(game_map, player, [])
    assert bot.attack_timer == 4

    # Miss line of sight inside range
    bot.attack_timer = 0
    with patch("src.bot.Bot.has_line_of_sight", return_value=False):
        assert bot.update(game_map, player, []) is None


def test_update_default_movement_collisions():
    bot = Bot(0, 0, 1, enemy_type="zombie")
    player = MagicMock()
    player.x = 10.0
    player.y = 0.0
    game_map = MagicMock()
    game_map.is_wall.return_value = False

    other = Bot(0, 0, 1, enemy_type="zombie")
    _test_bot_collision_axes(bot, other, player, game_map)
    _test_bot_collision_edge_cases(bot, other, player, game_map)


def _test_bot_collision_axes(bot, other, player, game_map):
    """Verify that bots block each other on X and Y axes."""
    other.x = bot.speed
    other.y = 0
    bot.update(game_map, player, [other])
    assert bot.x == 0.0

    other.dead = True
    bot.update(game_map, player, [other])
    other.dead = False

    bot.update(game_map, player, [bot])

    other.x = 0
    other.y = bot.speed
    bot.angle = math.pi / 2
    bot.update(game_map, player, [other])
    assert bot.y == 0.0


def _test_bot_collision_edge_cases(bot, other, player, game_map):
    """Cover walk-animation wrap-around and distant/diagonal bots."""
    bot.walk_animation = 2 * math.pi
    bot.y = 1.0
    bot.x = 1.0
    bot.update(game_map, player, [])
    assert bot.walk_animation < 2 * math.pi

    other.x = 10.0
    other.y = 1.0
    bot.x = 0.0
    bot.update(game_map, player, [other])

    other.x = 0.45
    other.y = 0.45
    bot.x = 0.0
    bot.y = 0.0
    bot.update(game_map, player, [other])


def test_beast_pushing_other_bots():
    bot = Bot(0, 0, 1, enemy_type="beast")
    player = MagicMock()
    player.x = 10.0
    player.y = 10.0

    game_map = MagicMock()
    game_map.is_wall.return_value = False

    # Place another bot perfectly in the path to be pushed
    other = Bot(bot.speed, bot.speed, 1, enemy_type="zombie")

    # Manually call default movement to avoid fireballs
    bot.angle = math.pi / 4
    bot._update_default_movement(game_map, player, [other])
    assert other.x != bot.speed or other.y != bot.speed

    # Block push by wall
    other = Bot(bot.speed, bot.speed, 1, enemy_type="zombie")
    game_map.is_wall.return_value = True
    bot._update_default_movement(game_map, player, [other])
    assert other.x == bot.speed and other.y == bot.speed


def test_take_damage():
    bot = Bot(0, 0, 1, enemy_type="zombie")

    # Dead bot take damage
    bot.dead = True
    assert bot.take_damage(10) is False

    # Headshot
    bot.dead = False
    bot.health = 100
    bot.take_damage(20, is_headshot=True)
    assert bot.health == 40

    # Normal kill
    assert bot.take_damage(50) is True
    assert bot.health == 0
    assert bot.dead is True
    assert bot.alive is False


def test_has_line_of_sight():
    bot = Bot(0, 0, 1, enemy_type="zombie")
    player = MagicMock()
    game_map = MagicMock()
    with patch("src.bot.has_line_of_sight", return_value=True) as check:
        assert bot.has_line_of_sight(game_map, player) is True
        check.assert_called_with(0, 0, player.x, player.y, game_map)
