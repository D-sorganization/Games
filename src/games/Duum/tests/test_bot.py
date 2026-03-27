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


def test_behavior_ball():
    bot = Bot(0, 0, 1, enemy_type="ball")
    player = MagicMock()
    player.x = 10.0
    player.y = 0.0
    player.god_mode = False

    game_map = MagicMock()
    game_map.is_wall.return_value = False

    # Normal roll
    bot.update(game_map, player, [])
    assert bot.vx > 0
    assert bot.x > 0

    # Hit wall X
    bot.x = 0.0
    bot.vx = 0.1
    bot.speed = 100.0

    def wall_mock(x, y):
        return x > 0.05

    game_map.is_wall.side_effect = wall_mock
    bot.update(game_map, player, [])
    assert bot.vx < 0
    assert bot.x == 0.0

    # Hit wall Y
    bot.y = 0.0
    bot.vy = 0.1
    bot.speed = 100.0

    def wall_mock_y(x, y):
        return y > 0.05

    game_map.is_wall.side_effect = wall_mock_y
    bot.update(game_map, player, [])
    assert bot.vy < 0
    assert bot.y == 0.0

    # Hit player (crush)
    bot.vx = 1.0
    bot.vy = 0.0
    bot.x = 9.5
    bot.y = 0.0
    game_map.is_wall.side_effect = lambda x, y: False

    bot.update(game_map, player, [])
    player.take_damage.assert_called()
    assert bot.vx < 0

    # Max speed cap
    bot.speed = 0.1
    bot.vx = 100.0
    bot.vy = 100.0
    bot.x = 0.0
    bot.y = 0.0
    bot.update(game_map, player, [])
    assert bot.vx < 100.0
    assert bot.vy < 100.0

    # Distance == 0
    bot.x = 10.0
    bot.y = 0.0
    player.x = 10.0
    player.y = 0.0
    bot.vx = 0.0
    bot.vy = 0.0
    bot.update(game_map, player, [])
    assert abs(bot.vx) < 0.0001

    # Hit player (crush god mode)
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

    # Collide with another bot (X and Y axis manually separated)
    other = Bot(0, 0, 1, enemy_type="zombie")
    other.x = bot.speed
    other.y = 0
    bot.update(game_map, player, [other])
    assert bot.x == 0.0  # Blocked in X

    other.dead = True
    bot.update(game_map, player, [other])  # Should ignore dead bots
    other.dead = False

    bot.update(game_map, player, [bot])  # Should ignore self

    other.x = 0
    other.y = bot.speed
    bot.angle = math.pi / 2  # Face down
    bot.update(game_map, player, [other])
    assert bot.y == 0.0  # Blocked in Y

    # Walk animation ticking over 2*pi
    bot.walk_animation = 2 * math.pi
    bot.y = 1.0  # Force Y movement
    bot.x = 1.0
    bot.update(game_map, player, [])  # Move freely
    assert bot.walk_animation < 2 * math.pi

    # Check "pass" branch (X far away)
    other.x = 10.0
    other.y = 1.0
    bot.x = 0.0
    bot.update(game_map, player, [other])

    # Check circle vs square collision diff (inside square, outside circle)
    # radius is 0.5, so col_sq is 0.25
    # Place other bot at dx=0.45, dy=0.45.
    # dx^2+dy^2 = 0.405 > 0.25 (False for collision check)
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
