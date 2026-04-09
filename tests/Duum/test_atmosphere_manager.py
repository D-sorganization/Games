"""Focused tests for the extracted Duum atmosphere manager."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock


def test_update_fog_reveal_marks_player_neighborhood() -> None:
    """Fog reveal should mark the player cell and nearby in-radius cells."""
    from games.Duum.src.atmosphere_manager import AtmosphereManager

    game = SimpleNamespace(
        player=SimpleNamespace(x=10.5, y=12.4),
        visited_cells=set(),
    )

    AtmosphereManager(game).update_fog_reveal()

    assert (10, 12) in game.visited_cells
    assert (11, 12) in game.visited_cells


def test_check_kill_combo_announces_phrase_and_syncs_combat_state(
    monkeypatch,
) -> None:
    """Combo expiry should announce high combos and sync state back to combat."""
    from games.Duum.src.atmosphere_manager import AtmosphereManager

    monkeypatch.setattr(
        "games.Duum.src.atmosphere_manager.random.choice",
        lambda phrases: phrases[0],
    )
    combat_manager = SimpleNamespace(kill_combo_timer=99, kill_combo_count=99)
    sound_manager = SimpleNamespace(play_sound=MagicMock())
    game = SimpleNamespace(
        kill_combo_timer=1,
        kill_combo_count=3,
        damage_texts=[],
        combat_manager=combat_manager,
        sound_manager=sound_manager,
    )

    AtmosphereManager(game).check_kill_combo()

    sound_manager.play_sound.assert_called_once_with("phrase_cool")
    assert game.kill_combo_count == 0
    assert combat_manager.kill_combo_timer == 0
    assert combat_manager.kill_combo_count == 0
    assert game.damage_texts[0]["text"] == "COOL!"
