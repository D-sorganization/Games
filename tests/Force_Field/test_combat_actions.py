"""Tests for Force Field combat_actions module."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


def _make_player(x: float = 5.0, y: float = 5.0, angle: float = 0.0) -> SimpleNamespace:
    return SimpleNamespace(x=x, y=y, angle=angle)


def _make_bot(
    x: float = 5.5,
    y: float = 5.0,
    alive: bool = True,
    take_damage_returns: bool = True,
) -> MagicMock:
    bot = MagicMock()
    bot.x = x
    bot.y = y
    bot.alive = alive
    bot.take_damage.return_value = take_damage_returns
    return bot


_SENTINEL = object()


def _make_game(player: object = _SENTINEL, bots: list | None = None) -> SimpleNamespace:
    if player is _SENTINEL:
        player = _make_player()
    return SimpleNamespace(
        player=player,
        bots=bots or [],
        kills=0,
        kill_combo_count=0,
        kill_combo_timer=0,
        last_death_pos=(0.0, 0.0),
        sound_manager=MagicMock(),
        particle_system=MagicMock(),
        event_bus=MagicMock(),
        add_message=MagicMock(),
    )


# ---------------------------------------------------------------------------
# _require_player
# ---------------------------------------------------------------------------


def test_require_player_none_raises() -> None:
    """_require_player must raise ValueError when player is None."""
    from games.Force_Field.src.combat_actions import _require_player

    game = _make_game(player=None)
    with pytest.raises(ValueError, match="DbC"):
        _require_player(game)


def test_require_player_returns_player() -> None:
    """_require_player returns the player when present."""
    from games.Force_Field.src.combat_actions import _require_player

    player = _make_player()
    game = _make_game(player=player)
    assert _require_player(game) is player


# ---------------------------------------------------------------------------
# _bot_in_melee_arc
# ---------------------------------------------------------------------------


def test_bot_in_melee_arc_close_and_in_front_returns_true() -> None:
    """Bot directly in front and within range is in the arc."""
    from games.Force_Field.src.combat_actions import _bot_in_melee_arc

    player = _make_player(x=5.0, y=5.0, angle=0.0)
    bot = _make_bot(x=6.5, y=5.0)

    assert _bot_in_melee_arc(player, bot) is True


def test_bot_in_melee_arc_too_far_returns_false() -> None:
    """Bot beyond MELEE_RANGE is not in the arc."""
    from games.Force_Field.src.combat_actions import _bot_in_melee_arc

    player = _make_player(x=5.0, y=5.0, angle=0.0)
    bot = _make_bot(x=15.0, y=5.0)

    assert _bot_in_melee_arc(player, bot) is False


def test_bot_in_melee_arc_behind_player_returns_false() -> None:
    """Bot directly behind the player (outside arc) returns False."""
    from games.Force_Field.src.combat_actions import _bot_in_melee_arc

    player = _make_player(x=5.0, y=5.0, angle=0.0)
    bot = _make_bot(x=3.5, y=5.0)

    assert _bot_in_melee_arc(player, bot) is False


# ---------------------------------------------------------------------------
# _layer_color
# ---------------------------------------------------------------------------


def test_layer_color_layer0() -> None:
    from games.Force_Field.src.combat_actions import _layer_color

    assert _layer_color(0) == (255, 255, 200)


def test_layer_color_layer1() -> None:
    from games.Force_Field.src.combat_actions import _layer_color

    assert _layer_color(1) == (255, 150, 0)


def test_layer_color_layer2() -> None:
    from games.Force_Field.src.combat_actions import _layer_color

    assert _layer_color(2) == (255, 50, 0)


# ---------------------------------------------------------------------------
# _record_melee_kill
# ---------------------------------------------------------------------------


def test_record_melee_kill_increments_counters() -> None:
    """_record_melee_kill bumps kill/combo counts and emits event."""
    from games.Force_Field.src.combat_actions import _record_melee_kill

    game = _make_game()
    bot = _make_bot(x=7.0, y=8.0)

    _record_melee_kill(game, bot)

    assert game.kills == 1
    assert game.kill_combo_count == 1
    assert game.kill_combo_timer > 0
    assert game.last_death_pos == (7.0, 8.0)
    game.event_bus.emit.assert_called_once_with("bot_killed", x=7.0, y=8.0)
    game.sound_manager.play_sound.assert_called_once_with("scream")


# ---------------------------------------------------------------------------
# _spawn_bot_hit_particles
# ---------------------------------------------------------------------------


def test_spawn_bot_hit_particles_calls_add_particle() -> None:
    """_spawn_bot_hit_particles must add BOT_PARTICLE_COUNT particles."""
    from games.Force_Field.src.combat_actions import (
        BOT_PARTICLE_COUNT,
        _spawn_bot_hit_particles,
    )

    game = _make_game()
    bot = _make_bot(x=5.0, y=5.0)

    _spawn_bot_hit_particles(game, bot)

    assert game.particle_system.add_particle.call_count == BOT_PARTICLE_COUNT


# ---------------------------------------------------------------------------
# create_melee_sweep_effect
# ---------------------------------------------------------------------------


def test_create_melee_sweep_effect_requires_player() -> None:
    """create_melee_sweep_effect raises when player is None."""
    from games.Force_Field.src.combat_actions import create_melee_sweep_effect

    game = _make_game(player=None)
    with pytest.raises(ValueError, match="DbC"):
        create_melee_sweep_effect(game)


def test_create_melee_sweep_effect_adds_particles() -> None:
    """create_melee_sweep_effect adds sweep + burst particles."""
    from games.Force_Field.src.combat_actions import (
        SWEEP_LAYERS,
        SWEEP_SEGMENTS,
        SWEEP_SPARK_COUNT,
        create_melee_sweep_effect,
    )

    game = _make_game()
    create_melee_sweep_effect(game)

    expected_minimum = SWEEP_LAYERS * SWEEP_SEGMENTS + SWEEP_SPARK_COUNT
    assert game.particle_system.add_particle.call_count >= expected_minimum


# ---------------------------------------------------------------------------
# execute_melee_attack
# ---------------------------------------------------------------------------


def test_execute_melee_attack_no_player_raises() -> None:
    """execute_melee_attack raises when player is None."""
    from games.Force_Field.src.combat_actions import execute_melee_attack

    game = _make_game(player=None)
    with pytest.raises(ValueError, match="DbC"):
        execute_melee_attack(game)


def test_execute_melee_attack_no_bots_no_kills() -> None:
    """With no bots present, kills should remain at zero."""
    from games.Force_Field.src.combat_actions import execute_melee_attack

    game = _make_game(bots=[])
    execute_melee_attack(game)

    assert game.kills == 0
    game.add_message.assert_not_called()


def test_execute_melee_attack_hit_one_bot() -> None:
    """Single bot hit triggers 'CRITICAL HIT!' message."""
    from games.Force_Field.src.combat_actions import execute_melee_attack

    player = _make_player(x=5.0, y=5.0, angle=0.0)
    bot = _make_bot(x=5.5, y=5.0, alive=True, take_damage_returns=True)
    game = _make_game(player=player, bots=[bot])

    execute_melee_attack(game)

    game.add_message.assert_called_once_with("CRITICAL HIT!", (255, 0, 0))


def test_execute_melee_attack_hit_multiple_bots() -> None:
    """Multiple bots hit triggers a COMBO message."""
    from games.Force_Field.src.combat_actions import execute_melee_attack

    player = _make_player(x=5.0, y=5.0, angle=0.0)
    bot1 = _make_bot(x=5.5, y=5.0, alive=True, take_damage_returns=True)
    bot2 = _make_bot(x=5.5, y=5.2, alive=True, take_damage_returns=True)
    game = _make_game(player=player, bots=[bot1, bot2])

    execute_melee_attack(game)

    assert game.add_message.call_count == 1
    message_text = game.add_message.call_args.args[0]
    assert "COMBO" in message_text


def test_execute_melee_attack_dead_bot_skipped() -> None:
    """Dead bots must not receive damage."""
    from games.Force_Field.src.combat_actions import execute_melee_attack

    player = _make_player(x=5.0, y=5.0, angle=0.0)
    bot = _make_bot(x=5.5, y=5.0, alive=False)
    game = _make_game(player=player, bots=[bot])

    execute_melee_attack(game)

    bot.take_damage.assert_not_called()
    assert game.kills == 0


# ---------------------------------------------------------------------------
# _play_melee_sound
# ---------------------------------------------------------------------------


def test_play_melee_sound_calls_play_sound() -> None:
    """_play_melee_sound should call sound_manager.play_sound."""
    from games.Force_Field.src.combat_actions import _play_melee_sound

    game = _make_game()
    _play_melee_sound(game)

    game.sound_manager.play_sound.assert_called_once_with("shoot_shotgun")


def test_play_melee_sound_swallows_pygame_error() -> None:
    """_play_melee_sound must not propagate pygame.error exceptions."""
    import pygame

    from games.Force_Field.src.combat_actions import _play_melee_sound

    game = _make_game()
    game.sound_manager.play_sound.side_effect = pygame.error("no audio")

    _play_melee_sound(game)
