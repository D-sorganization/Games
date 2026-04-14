"""Tests for shared/game_state_types.py dataclasses."""

from __future__ import annotations

import pytest

from games.shared.game_state_types import (
    ComboState,
    DamageText,
    GameplayState,
    IntroState,
    VisualEffectState,
)


class TestIntroState:
    def test_defaults(self) -> None:
        s = IntroState()
        assert s.phase == 0
        assert s.step == 0
        assert s.timer == 0
        assert s.start_time == 0
        assert s.laugh_played is False
        assert s.water_played is False

    def test_custom_values(self) -> None:
        s = IntroState(phase=2, step=1, timer=100, laugh_played=True)
        assert s.phase == 2
        assert s.step == 1
        assert s.timer == 100
        assert s.laugh_played is True


class TestGameplayState:
    def test_defaults(self) -> None:
        s = GameplayState()
        assert s.level == 1
        assert s.kills == 0
        assert s.lives == 3
        assert s.health == 100
        assert s.level_times == []
        assert s.paused is False
        assert s.show_damage is True
        assert s.game_over_timer == 0

    def test_level_times_is_independent_per_instance(self) -> None:
        s1 = GameplayState()
        s2 = GameplayState()
        s1.level_times.append(1.5)
        assert s2.level_times == []

    def test_custom_values(self) -> None:
        s = GameplayState(level=3, kills=10, lives=1)
        assert s.level == 3
        assert s.kills == 10
        assert s.lives == 1


class TestComboState:
    def test_defaults(self) -> None:
        s = ComboState()
        assert s.kill_combo_count == 0
        assert s.kill_combo_timer == 0
        assert s.heartbeat_timer == 0
        assert s.breath_timer == 0
        assert s.groan_timer == 0
        assert s.beast_timer == 0

    def test_mutation(self) -> None:
        s = ComboState()
        s.kill_combo_count = 5
        s.kill_combo_timer = 30
        assert s.kill_combo_count == 5
        assert s.kill_combo_timer == 30


class TestVisualEffectState:
    def test_defaults(self) -> None:
        s = VisualEffectState()
        assert s.damage_flash_timer == 0
        assert s.screen_shake == 0.0
        assert s.flash_intensity == 0.0

    def test_float_fields(self) -> None:
        s = VisualEffectState(screen_shake=3.5, flash_intensity=0.8)
        assert s.screen_shake == pytest.approx(3.5)
        assert s.flash_intensity == pytest.approx(0.8)


class TestDamageText:
    def test_construction(self) -> None:
        dt = DamageText(x=1.0, y=2.0, text="5", color=(255, 0, 0), timer=30)
        assert dt.x == 1.0
        assert dt.y == 2.0
        assert dt.text == "5"
        assert dt.color == (255, 0, 0)
        assert dt.timer == 30
        assert dt.vy == pytest.approx(-0.5)

    def test_to_dict(self) -> None:
        dt = DamageText(x=3.0, y=4.0, text="10", color=(0, 255, 0), timer=15, vy=-1.0)
        d = dt.to_dict()
        assert d["x"] == 3.0
        assert d["y"] == 4.0
        assert d["text"] == "10"
        assert d["color"] == (0, 255, 0)
        assert d["timer"] == 15
        assert d["vy"] == pytest.approx(-1.0)

    def test_to_dict_keys(self) -> None:
        dt = DamageText(x=0.0, y=0.0, text="X", color=(0, 0, 0), timer=1)
        assert set(dt.to_dict().keys()) == {"x", "y", "text", "color", "timer", "vy"}
