"""Tests for the games.shared.bot_base module."""

from __future__ import annotations

from typing import Any

import pytest

from games.shared.bot_base import BotBase
from games.shared.contracts import ContractViolation

ENEMY_TYPES: dict[str, dict[str, Any]] = {
    "zombie": {
        "color": (80, 100, 80),
        "health_mult": 1.0,
        "speed_mult": 1.0,
        "damage_mult": 1.0,
        "scale": 1.0,
        "visual_style": "monster",
    },
    "demon": {
        "color": (200, 50, 50),
        "health_mult": 2.0,
        "speed_mult": 0.8,
        "damage_mult": 1.5,
        "scale": 1.2,
        "visual_style": "beast",
    },
    "fast": {
        "color": (100, 200, 100),
        "health_mult": 0.5,
        "speed_mult": 2.0,
        "damage_mult": 0.5,
        "scale": 0.8,
        "visual_style": "ghost",
    },
    "health_pack": {
        "color": (0, 255, 0),
        "health_mult": 0.0,
        "speed_mult": 0.0,
        "damage_mult": 0.0,
        "scale": 0.5,
    },
}

DIFFICULTIES: dict[str, dict[str, float]] = {
    "EASY": {"damage_mult": 0.5, "health_mult": 0.7, "score_mult": 0.5},
    "NORMAL": {
        "damage_mult": 1.0,
        "health_mult": 1.0,
        "score_mult": 1.0,
    },
    "HARD": {"damage_mult": 1.5, "health_mult": 1.5, "score_mult": 2.0},
    "NIGHTMARE": {
        "damage_mult": 2.5,
        "health_mult": 2.0,
        "score_mult": 4.0,
    },
}


def _make_bot(
    enemy_type: str | None = "zombie",
    level: int = 1,
    difficulty: str = "NORMAL",
    **kwargs: Any,
) -> BotBase:
    """Create a BotBase with sensible defaults.

    Args:
        enemy_type: Enemy type name or None for random.
        level: Current level.
        difficulty: Difficulty setting.
        **kwargs: Override default construction parameters.

    Returns:
        Initialized BotBase.
    """
    defaults: dict[str, Any] = {
        "x": 5.0,
        "y": 5.0,
        "base_bot_health": 100,
        "base_bot_damage": 10,
        "bot_speed": 0.05,
    }
    defaults.update(kwargs)
    return BotBase(
        x=defaults["x"],
        y=defaults["y"],
        level=level,
        enemy_types=ENEMY_TYPES,
        base_bot_health=defaults["base_bot_health"],
        base_bot_damage=defaults["base_bot_damage"],
        bot_speed=defaults["bot_speed"],
        difficulties=DIFFICULTIES,
        enemy_type=enemy_type,
        difficulty=difficulty,
    )


class TestBotBaseInit:
    """Tests for BotBase initialization."""

    def test_init_sets_position(self) -> None:
        """Bot should store initial position."""
        bot = _make_bot(x=3.0, y=7.0)
        assert bot.x == pytest.approx(3.0)
        assert bot.y == pytest.approx(7.0)

    def test_init_sets_enemy_type(self) -> None:
        """Bot should store the specified enemy type."""
        bot = _make_bot(enemy_type="demon")
        assert bot.enemy_type == "demon"

    def test_init_random_type_excludes_health_pack(self) -> None:
        """Random type selection should exclude health_pack."""
        for _ in range(50):
            bot = _make_bot(enemy_type=None)
            assert bot.enemy_type != "health_pack"

    def test_init_alive_by_default(self) -> None:
        """Bot should be alive on creation."""
        bot = _make_bot()
        assert bot.alive is True
        assert bot.dead is False
        assert bot.removed is False

    def test_init_sets_type_data(self) -> None:
        """Bot should store full type data dict."""
        bot = _make_bot(enemy_type="zombie")
        assert bot.type_data["color"] == (80, 100, 80)
        assert bot.type_data["visual_style"] == "monster"


class TestBotBaseContracts:
    """Tests for BotBase contract validation."""

    def test_rejects_none_enemy_types(self) -> None:
        """Should reject None enemy_types."""
        with pytest.raises(ContractViolation, match="enemy_types"):
            BotBase(
                x=0.0,
                y=0.0,
                level=1,
                enemy_types=None,  # type: ignore[arg-type]
                base_bot_health=100,
                base_bot_damage=10,
                bot_speed=0.05,
                difficulties=DIFFICULTIES,
            )

    def test_rejects_none_difficulties(self) -> None:
        """Should reject None difficulties."""
        with pytest.raises(ContractViolation, match="difficulties"):
            BotBase(
                x=0.0,
                y=0.0,
                level=1,
                enemy_types=ENEMY_TYPES,
                base_bot_health=100,
                base_bot_damage=10,
                bot_speed=0.05,
                difficulties=None,  # type: ignore[arg-type]
            )

    def test_rejects_zero_health(self) -> None:
        """Should reject zero base health."""
        with pytest.raises(ContractViolation, match="base_bot_health"):
            _make_bot(base_bot_health=0)

    def test_rejects_zero_damage(self) -> None:
        """Should reject zero base damage."""
        with pytest.raises(ContractViolation, match="base_bot_damage"):
            _make_bot(base_bot_damage=0)


class TestBotBaseStats:
    """Tests for bot stat calculations."""

    @pytest.mark.parametrize(
        "enemy_type,health_mult",
        [
            ("zombie", 1.0),
            ("demon", 2.0),
            ("fast", 0.5),
        ],
    )
    def test_health_scaled_by_type(self, enemy_type: str, health_mult: float) -> None:
        """Health should scale with enemy type multiplier."""
        bot = _make_bot(enemy_type=enemy_type, level=1)
        expected = int(100 * health_mult)
        assert bot.health == expected
        assert bot.max_health == expected

    @pytest.mark.parametrize(
        "difficulty,health_mult",
        [
            ("EASY", 0.7),
            ("NORMAL", 1.0),
            ("HARD", 1.5),
            ("NIGHTMARE", 2.0),
        ],
        ids=["easy", "normal", "hard", "nightmare"],
    )
    def test_health_scaled_by_difficulty(
        self, difficulty: str, health_mult: float
    ) -> None:
        """Health should scale with difficulty multiplier."""
        bot = _make_bot(enemy_type="zombie", level=1, difficulty=difficulty)
        expected = int(100 * health_mult)
        assert bot.health == expected

    def test_health_increases_with_level(self) -> None:
        """Health should increase with level."""
        bot_l1 = _make_bot(level=1)
        bot_l5 = _make_bot(level=5)
        assert bot_l5.health > bot_l1.health

    def test_damage_increases_with_level(self) -> None:
        """Damage should increase with level."""
        bot_l1 = _make_bot(level=1)
        bot_l5 = _make_bot(level=5)
        assert bot_l5.damage > bot_l1.damage

    @pytest.mark.parametrize(
        "enemy_type,speed_mult",
        [
            ("zombie", 1.0),
            ("demon", 0.8),
            ("fast", 2.0),
        ],
    )
    def test_speed_scaled_by_type(self, enemy_type: str, speed_mult: float) -> None:
        """Speed should scale with enemy type multiplier."""
        bot = _make_bot(enemy_type=enemy_type)
        assert bot.speed == pytest.approx(0.05 * speed_mult)


class TestBotBaseState:
    """Tests for bot state attributes."""

    def test_initial_animation_state(self) -> None:
        """Initial animation values should be zero."""
        bot = _make_bot()
        assert bot.walk_animation == pytest.approx(0.0)
        assert bot.shoot_animation == pytest.approx(0.0)

    def test_initial_momentum_zero(self) -> None:
        """Initial momentum should be zero."""
        bot = _make_bot()
        assert bot.vx == pytest.approx(0.0)
        assert bot.vy == pytest.approx(0.0)

    def test_initial_status_effects(self) -> None:
        """Bot should start with no status effects."""
        bot = _make_bot()
        assert bot.frozen is False
        assert bot.frozen_timer == 0

    def test_initial_death_state(self) -> None:
        """Death state should be clean on creation."""
        bot = _make_bot()
        assert bot.dead is False
        assert bot.death_timer == pytest.approx(0.0)
        assert bot.disintegrate_timer == pytest.approx(0.0)
        assert bot.removed is False

    def test_last_position_equals_spawn(self) -> None:
        """last_x/last_y should match spawn position."""
        bot = _make_bot(x=3.0, y=7.0)
        assert bot.last_x == pytest.approx(3.0)
        assert bot.last_y == pytest.approx(7.0)
