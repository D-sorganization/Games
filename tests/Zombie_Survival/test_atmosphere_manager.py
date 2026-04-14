"""Tests for Zombie Survival AtmosphereManager."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from games.shared.constants import BEAST_TIMER_MAX, BEAST_TIMER_MIN, GROAN_TIMER_DELAY


def _make_game(**overrides: object) -> SimpleNamespace:
    base = {
        "player_x": 5.0,
        "player_y": 5.0,
        "player_health": 100,
        "bots": [],
        "visited_cells": set(),
        "beast_timer": 10,
        "heartbeat_timer": 10,
        "groan_timer": 10,
        "kill_combo_timer": 0,
        "kill_combo_count": 0,
        "damage_texts": [],
        "sound_manager": MagicMock(),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _make_bot(x: float, y: float, alive: bool = True) -> SimpleNamespace:
    return SimpleNamespace(x=x, y=y, alive=alive)


# ---------------------------------------------------------------------------
# update_fog_reveal
# ---------------------------------------------------------------------------


def test_update_fog_reveal_adds_cells_around_player() -> None:
    from games.Zombie_Survival.src.atmosphere_manager import AtmosphereManager

    game = _make_game(player_x=5.0, player_y=5.0)
    AtmosphereManager(game).update_fog_reveal()

    assert (5, 5) in game.visited_cells


def test_update_fog_reveal_adds_multiple_cells() -> None:
    from games.Zombie_Survival.src.atmosphere_manager import AtmosphereManager

    game = _make_game(player_x=10.0, player_y=10.0)
    AtmosphereManager(game).update_fog_reveal()

    assert len(game.visited_cells) > 1


# ---------------------------------------------------------------------------
# update_atmosphere
# ---------------------------------------------------------------------------


def test_update_atmosphere_no_bots_no_sounds() -> None:
    from games.Zombie_Survival.src.atmosphere_manager import AtmosphereManager

    game = _make_game(bots=[], player_health=100)
    AtmosphereManager(game).update_atmosphere()

    game.sound_manager.play_sound.assert_not_called()


def test_update_atmosphere_close_bot_decrements_beast_timer() -> None:
    from games.Zombie_Survival.src.atmosphere_manager import AtmosphereManager

    bot = _make_bot(x=5.5, y=5.0)
    game = _make_game(bots=[bot], player_x=5.0, player_y=5.0, beast_timer=2)
    AtmosphereManager(game).update_atmosphere()

    assert game.beast_timer == 1


def test_update_atmosphere_beast_timer_zero_plays_beast_sound() -> None:
    from games.Zombie_Survival.src.atmosphere_manager import AtmosphereManager

    bot = _make_bot(x=5.5, y=5.0)
    game = _make_game(bots=[bot], player_x=5.0, player_y=5.0, beast_timer=1)
    AtmosphereManager(game).update_atmosphere()

    game.sound_manager.play_sound.assert_any_call("beast")
    assert BEAST_TIMER_MIN <= game.beast_timer <= BEAST_TIMER_MAX


def test_update_atmosphere_low_health_plays_groan_when_timer_expires() -> None:
    from games.Zombie_Survival.src.atmosphere_manager import AtmosphereManager

    game = _make_game(bots=[], player_health=30, groan_timer=1)
    AtmosphereManager(game).update_atmosphere()

    game.sound_manager.play_sound.assert_called_once_with("groan")
    assert game.groan_timer == GROAN_TIMER_DELAY


def test_update_atmosphere_high_health_no_groan() -> None:
    from games.Zombie_Survival.src.atmosphere_manager import AtmosphereManager

    game = _make_game(bots=[], player_health=100, groan_timer=1)
    AtmosphereManager(game).update_atmosphere()

    calls = [c.args[0] for c in game.sound_manager.play_sound.call_args_list]
    assert "groan" not in calls


def test_update_atmosphere_close_bot_heartbeat_when_timer_expires() -> None:
    from games.Zombie_Survival.src.atmosphere_manager import AtmosphereManager

    bot = _make_bot(x=5.5, y=5.0)
    game = _make_game(
        bots=[bot], player_x=5.0, player_y=5.0, heartbeat_timer=1, player_health=100
    )
    AtmosphereManager(game).update_atmosphere()

    game.sound_manager.play_sound.assert_any_call("heartbeat")
    game.sound_manager.play_sound.assert_any_call("breath")


# ---------------------------------------------------------------------------
# check_kill_combo
# ---------------------------------------------------------------------------


def test_check_kill_combo_no_timer_no_effect() -> None:
    from games.Zombie_Survival.src.atmosphere_manager import AtmosphereManager

    game = _make_game(kill_combo_timer=0, kill_combo_count=3)
    AtmosphereManager(game).check_kill_combo()

    game.sound_manager.play_sound.assert_not_called()
    assert game.kill_combo_count == 3


def test_check_kill_combo_decrements_timer() -> None:
    from games.Zombie_Survival.src.atmosphere_manager import AtmosphereManager

    game = _make_game(kill_combo_timer=5, kill_combo_count=1)
    AtmosphereManager(game).check_kill_combo()

    assert game.kill_combo_timer == 4


def test_check_kill_combo_resets_count_when_timer_expires() -> None:
    from games.Zombie_Survival.src.atmosphere_manager import AtmosphereManager

    game = _make_game(kill_combo_timer=1, kill_combo_count=1)
    AtmosphereManager(game).check_kill_combo()

    assert game.kill_combo_count == 0


def test_check_kill_combo_plays_phrase_for_combo_count_ge_3(monkeypatch) -> None:
    import random

    from games.Zombie_Survival.src.atmosphere_manager import AtmosphereManager

    game = _make_game(
        kill_combo_timer=1,
        kill_combo_count=3,
        damage_texts=[],
    )
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])

    AtmosphereManager(game).check_kill_combo()

    game.sound_manager.play_sound.assert_called_once_with("phrase_cool")
    assert game.kill_combo_count == 0
