"""Tests for the games.shared.player_base module."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from games.shared.contracts import ContractViolation
from games.shared.player_base import PlayerBase


def _make_constants(**overrides: Any) -> SimpleNamespace:
    """Create a mock constants module with default weapon configs.

    Args:
        **overrides: Key-value pairs to override default constants.

    Returns:
        A SimpleNamespace acting as a constants module.
    """
    defaults: dict[str, Any] = {
        "WEAPONS": {
            "pistol": {
                "name": "Pistol",
                "damage": 25,
                "range": 15,
                "ammo": 999,
                "cooldown": 10,
                "clip_size": 12,
                "reload_time": 60,
                "key": "1",
            },
            "rifle": {
                "name": "Rifle",
                "damage": 20,
                "range": 25,
                "ammo": 999,
                "cooldown": 20,
                "clip_size": 30,
                "reload_time": 120,
                "key": "2",
            },
        },
        "SHIELD_MAX_DURATION": 600,
        "BOMBS_START": 1,
        "PITCH_LIMIT": 1.0,
        "SECONDARY_COOLDOWN": 60,
        "SHIELD_COOLDOWN_NORMAL": 60,
        "BOMB_COOLDOWN": 300,
        "SHIELD_COOLDOWN_DEPLETED": 300,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_player(**kwargs: Any) -> PlayerBase:
    """Create a PlayerBase with sensible defaults.

    Args:
        **kwargs: Override default construction parameters.

    Returns:
        Initialized PlayerBase.
    """
    defaults = {
        "x": 5.0,
        "y": 5.0,
        "angle": 0.0,
    }
    defaults.update(kwargs)
    constants = defaults.pop("constants", None) or _make_constants()
    weapons_config = defaults.pop("weapons_config", None) or constants.WEAPONS
    return PlayerBase(
        x=defaults["x"],
        y=defaults["y"],
        angle=defaults["angle"],
        weapons_config=weapons_config,
        constants=constants,
    )


class TestPlayerBaseInit:
    """Tests for PlayerBase initialization."""

    def test_init_sets_position(self) -> None:
        """PlayerBase should store initial position."""
        player = _make_player(x=3.0, y=7.0, angle=1.5)
        assert player.x == pytest.approx(3.0)
        assert player.y == pytest.approx(7.0)
        assert player.angle == pytest.approx(1.5)

    def test_init_sets_health(self) -> None:
        """PlayerBase should initialize with full health."""
        player = _make_player()
        assert player.health == 100
        assert player.max_health == 100

    def test_init_sets_weapon_states(self) -> None:
        """PlayerBase should create weapon state for each weapon."""
        player = _make_player()
        assert "pistol" in player.weapon_state
        assert "rifle" in player.weapon_state

    def test_init_sets_ammo(self) -> None:
        """PlayerBase should track ammo per weapon."""
        player = _make_player()
        assert player.ammo["pistol"] == 999
        assert player.ammo["rifle"] == 999

    def test_init_rejects_none_config(self) -> None:
        """PlayerBase should reject None weapons_config."""
        with pytest.raises(ContractViolation, match="weapons_config"):
            PlayerBase(
                x=0.0,
                y=0.0,
                angle=0.0,
                weapons_config=None,  # type: ignore[arg-type]
                constants=_make_constants(),
            )

    def test_init_rejects_none_constants(self) -> None:
        """PlayerBase should reject None constants."""
        with pytest.raises(ContractViolation, match="constants"):
            PlayerBase(
                x=0.0,
                y=0.0,
                angle=0.0,
                weapons_config={"pistol": {"ammo": 999, "clip_size": 12}},
                constants=None,
            )


class TestPlayerRotation:
    """Tests for player rotation mechanics."""

    def test_rotate_positive(self) -> None:
        """Rotating positive should increase angle."""
        player = _make_player(angle=0.0)
        player.rotate(0.5)
        assert player.angle == pytest.approx(0.5)

    def test_rotate_wraps_around(self) -> None:
        """Angle should wrap around 2*pi."""
        import math

        player = _make_player(angle=math.pi * 1.9)
        player.rotate(math.pi * 0.2)
        expected = (math.pi * 1.9 + math.pi * 0.2) % (2 * math.pi)
        assert player.angle == pytest.approx(expected)

    def test_rotate_tracks_frame_turn(self) -> None:
        """Rotation should accumulate in frame_turn for sway."""
        player = _make_player()
        player.rotate(0.3)
        assert player.frame_turn == pytest.approx(0.3)

    def test_pitch_view_clamps(self) -> None:
        """Pitch should be clamped to PITCH_LIMIT."""
        player = _make_player()
        player.pitch_view(5.0)
        assert player.pitch == pytest.approx(1.0)  # Default PITCH_LIMIT

        player.pitch_view(-10.0)
        assert player.pitch == pytest.approx(-1.0)


class TestPlayerWeapons:
    """Tests for weapon management."""

    def test_switch_weapon(self) -> None:
        """Should switch to a valid weapon."""
        player = _make_player()
        player.switch_weapon("pistol")
        assert player.current_weapon == "pistol"

    def test_switch_weapon_ignores_invalid(self) -> None:
        """Should not switch to an invalid weapon."""
        player = _make_player()
        original = player.current_weapon
        player.switch_weapon("rocket_launcher")
        assert player.current_weapon == original

    def test_switch_weapon_rejects_none(self) -> None:
        """Should reject None weapon name."""
        player = _make_player()
        with pytest.raises(ContractViolation, match="weapon"):
            player.switch_weapon(None)  # type: ignore[arg-type]

    def test_get_current_weapon_damage(self) -> None:
        """Should return correct weapon damage."""
        player = _make_player()
        player.switch_weapon("pistol")
        assert player.get_current_weapon_damage() == 25

    def test_get_current_weapon_range(self) -> None:
        """Should return correct weapon range."""
        player = _make_player()
        player.switch_weapon("rifle")
        assert player.get_current_weapon_range() == 25


class TestPlayerShooting:
    """Tests for shooting mechanics."""

    def test_shoot_fires_when_ready(self) -> None:
        """Should fire when cooldown is clear and clip has ammo."""
        player = _make_player()
        player.switch_weapon("pistol")
        result = player.shoot()
        assert result is True
        assert player.shooting is True

    def test_shoot_sets_cooldown(self) -> None:
        """Shooting should set the shoot_timer."""
        player = _make_player()
        player.switch_weapon("pistol")
        player.shoot()
        assert player.shoot_timer > 0

    def test_shoot_consumes_clip(self) -> None:
        """Shooting should decrease clip count."""
        player = _make_player()
        player.switch_weapon("pistol")
        initial_clip = player.weapon_state["pistol"]["clip"]
        player.shoot()
        assert player.weapon_state["pistol"]["clip"] == initial_clip - 1

    def test_shoot_fails_on_cooldown(self) -> None:
        """Should not fire when on cooldown."""
        player = _make_player()
        player.switch_weapon("pistol")
        player.shoot()
        # Second shot should fail due to cooldown
        result = player.shoot()
        assert result is False


class TestPlayerReload:
    """Tests for reloading mechanics."""

    def test_reload_starts_when_clip_not_full(self) -> None:
        """Should start reloading when clip is not full."""
        player = _make_player()
        player.switch_weapon("pistol")
        player.weapon_state["pistol"]["clip"] = 5
        player.reload()
        assert player.weapon_state["pistol"]["reloading"] is True

    def test_reload_skips_when_full(self) -> None:
        """Should not reload when clip is already full."""
        player = _make_player()
        player.switch_weapon("pistol")
        # Clip is at full capacity
        player.reload()
        assert player.weapon_state["pistol"]["reloading"] is False


class TestPlayerTimers:
    """Tests for timer updates."""

    def test_update_timers_decrements_shoot_timer(self) -> None:
        """Shoot timer should count down."""
        player = _make_player()
        player.shoot_timer = 5
        player.update_timers()
        assert player.shoot_timer == 4

    def test_update_timers_regenerates_stamina(self) -> None:
        """Stamina should regenerate when below max."""
        player = _make_player()
        player.stamina = 50.0
        player.stamina_recharge_delay = 0
        player.update_timers()
        assert player.stamina > 50.0

    def test_update_weapon_state_completes_reload(self) -> None:
        """Weapon should complete reload when timer expires."""
        player = _make_player()
        player.switch_weapon("pistol")
        player.weapon_state["pistol"]["reloading"] = True
        player.weapon_state["pistol"]["reload_timer"] = 1
        player.weapon_state["pistol"]["clip"] = 0
        player.update_weapon_state()
        assert player.weapon_state["pistol"]["reloading"] is False
        assert player.weapon_state["pistol"]["clip"] == 12  # Full clip


class TestPlayerShield:
    """Tests for shield mechanics."""

    def test_shield_activation(self) -> None:
        """Shield should activate when timer is available."""
        player = _make_player()
        player.shield_timer = 100
        player.shield_recharge_delay = 0
        player.set_shield(True)
        assert player.shield_active is True

    def test_shield_blocked_during_cooldown(self) -> None:
        """Shield should not activate during recharge delay."""
        player = _make_player()
        player.shield_recharge_delay = 10
        player.set_shield(True)
        assert player.shield_active is False


class TestPlayerBomb:
    """Tests for bomb mechanics."""

    def test_activate_bomb_success(self) -> None:
        """Should activate bomb when available."""
        player = _make_player()
        player.bombs = 2
        player.bomb_cooldown = 0
        result = player.activate_bomb()
        assert result is True
        assert player.bombs == 1
        assert player.bomb_cooldown > 0

    def test_activate_bomb_fails_no_bombs(self) -> None:
        """Should fail when no bombs available."""
        player = _make_player()
        player.bombs = 0
        result = player.activate_bomb()
        assert result is False
