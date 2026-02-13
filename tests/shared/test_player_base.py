"""Tests for the games.shared.player_base module.

Uses shared fixtures from conftest.py. Adds parametrized weapon
and rotation tests for comprehensive coverage.
"""

from __future__ import annotations

import math

import pytest

from games.shared.contracts import ContractViolation
from games.shared.player_base import PlayerBase
from tests.conftest import make_constants


class TestPlayerBaseInit:
    """Tests for PlayerBase initialization."""

    def test_init_sets_position(self) -> None:
        """PlayerBase should store initial position."""
        c = make_constants()
        p = PlayerBase(3.0, 7.0, 1.5, c.WEAPONS, c)
        assert p.x == pytest.approx(3.0)
        assert p.y == pytest.approx(7.0)
        assert p.angle == pytest.approx(1.5)

    def test_init_sets_health(self, player: PlayerBase) -> None:
        """PlayerBase should initialize with full health."""
        assert player.health == 100
        assert player.max_health == 100

    def test_init_sets_weapon_states(self, player: PlayerBase) -> None:
        """PlayerBase should create weapon state for each weapon."""
        assert "pistol" in player.weapon_state
        assert "rifle" in player.weapon_state
        assert "shotgun" in player.weapon_state

    def test_init_sets_ammo(self, player: PlayerBase) -> None:
        """PlayerBase should track ammo per weapon."""
        assert player.ammo["pistol"] == 999
        assert player.ammo["rifle"] == 999

    def test_init_clip_matches_config(self, player: PlayerBase) -> None:
        """Clip should be initialized to clip_size from config."""
        assert player.weapon_state["pistol"]["clip"] == 12
        assert player.weapon_state["rifle"]["clip"] == 30
        assert player.weapon_state["shotgun"]["clip"] == 2

    def test_init_rejects_none_config(self) -> None:
        """PlayerBase should reject None weapons_config."""
        with pytest.raises(ContractViolation, match="weapons_config"):
            PlayerBase(
                x=0.0,
                y=0.0,
                angle=0.0,
                weapons_config=None,  # type: ignore[arg-type]
                constants=make_constants(),
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

    @pytest.mark.parametrize(
        "delta",
        [0.1, 0.5, 1.0, math.pi],
        ids=["small", "half", "one", "pi"],
    )
    def test_rotate_various_deltas(self, player: PlayerBase, delta: float) -> None:
        """Rotating by delta should change angle by delta."""
        initial = player.angle
        player.rotate(delta)
        expected = (initial + delta) % (2 * math.pi)
        assert player.angle == pytest.approx(expected)

    def test_rotate_wraps_around(self) -> None:
        """Angle should wrap around 2*pi."""
        c = make_constants()
        p = PlayerBase(0.0, 0.0, math.pi * 1.9, c.WEAPONS, c)
        p.rotate(math.pi * 0.2)
        expected = (math.pi * 1.9 + math.pi * 0.2) % (2 * math.pi)
        assert p.angle == pytest.approx(expected)

    def test_rotate_tracks_frame_turn(self, player: PlayerBase) -> None:
        """Rotation should accumulate in frame_turn for sway."""
        player.rotate(0.3)
        assert player.frame_turn == pytest.approx(0.3)

    @pytest.mark.parametrize(
        "delta,expected",
        [(5.0, 1.0), (-5.0, -1.0), (0.5, 0.5)],
        ids=["clamp_positive", "clamp_negative", "within_limit"],
    )
    def test_pitch_view_clamps(
        self,
        player: PlayerBase,
        delta: float,
        expected: float,
    ) -> None:
        """Pitch should be clamped to PITCH_LIMIT."""
        player.pitch_view(delta)
        assert player.pitch == pytest.approx(expected)


class TestPlayerWeapons:
    """Tests for weapon management."""

    @pytest.mark.parametrize(
        "weapon",
        ["pistol", "rifle", "shotgun"],
    )
    def test_switch_to_valid_weapon(self, player: PlayerBase, weapon: str) -> None:
        """Should switch to any valid weapon."""
        player.switch_weapon(weapon)
        assert player.current_weapon == weapon

    def test_switch_weapon_ignores_invalid(self, player: PlayerBase) -> None:
        """Should not switch to an invalid weapon."""
        original = player.current_weapon
        player.switch_weapon("rocket_launcher")
        assert player.current_weapon == original

    def test_switch_weapon_rejects_none(self, player: PlayerBase) -> None:
        """Should reject None weapon name."""
        with pytest.raises(ContractViolation, match="weapon"):
            player.switch_weapon(None)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "weapon,expected_damage",
        [("pistol", 25), ("rifle", 20), ("shotgun", 20)],
    )
    def test_get_weapon_damage(
        self,
        player: PlayerBase,
        weapon: str,
        expected_damage: int,
    ) -> None:
        """Should return correct damage for each weapon."""
        player.switch_weapon(weapon)
        assert player.get_current_weapon_damage() == expected_damage

    @pytest.mark.parametrize(
        "weapon,expected_range",
        [("pistol", 15), ("rifle", 25), ("shotgun", 12)],
    )
    def test_get_weapon_range(
        self,
        player: PlayerBase,
        weapon: str,
        expected_range: int,
    ) -> None:
        """Should return correct range for each weapon."""
        player.switch_weapon(weapon)
        assert player.get_current_weapon_range() == expected_range


class TestPlayerShooting:
    """Tests for shooting mechanics."""

    def test_shoot_fires_when_ready(self, player: PlayerBase) -> None:
        """Should fire when cooldown is clear and clip has ammo."""
        player.switch_weapon("pistol")
        result = player.shoot()
        assert result is True
        assert player.shooting is True

    def test_shoot_sets_cooldown(self, player: PlayerBase) -> None:
        """Shooting should set the shoot_timer."""
        player.switch_weapon("pistol")
        player.shoot()
        assert player.shoot_timer > 0

    def test_shoot_consumes_clip(self, player: PlayerBase) -> None:
        """Shooting should decrease clip count."""
        player.switch_weapon("pistol")
        initial_clip = player.weapon_state["pistol"]["clip"]
        player.shoot()
        assert player.weapon_state["pistol"]["clip"] == initial_clip - 1

    def test_shoot_fails_on_cooldown(self, player: PlayerBase) -> None:
        """Should not fire when on cooldown."""
        player.switch_weapon("pistol")
        player.shoot()
        result = player.shoot()
        assert result is False

    def test_shoot_fails_when_reloading(self, player: PlayerBase) -> None:
        """Should not fire when weapon is reloading."""
        player.switch_weapon("pistol")
        player.weapon_state["pistol"]["reloading"] = True
        result = player.shoot()
        assert result is False

    def test_shoot_triggers_auto_reload_on_empty(self, player: PlayerBase) -> None:
        """Emptying clip should trigger auto-reload."""
        player.switch_weapon("pistol")
        player.weapon_state["pistol"]["clip"] = 1
        player.shoot()
        assert player.weapon_state["pistol"]["reloading"] is True


class TestPlayerReload:
    """Tests for reloading mechanics."""

    def test_reload_starts_when_clip_not_full(self, player: PlayerBase) -> None:
        """Should start reloading when clip is not full."""
        player.switch_weapon("pistol")
        player.weapon_state["pistol"]["clip"] = 5
        player.reload()
        assert player.weapon_state["pistol"]["reloading"] is True

    def test_reload_skips_when_full(self, player: PlayerBase) -> None:
        """Should not reload when clip is already full."""
        player.switch_weapon("pistol")
        player.reload()
        assert player.weapon_state["pistol"]["reloading"] is False

    def test_reload_skips_when_already_reloading(self, player: PlayerBase) -> None:
        """Should not restart reload when already reloading."""
        player.switch_weapon("pistol")
        player.weapon_state["pistol"]["clip"] = 0
        player.weapon_state["pistol"]["reloading"] = True
        initial_timer = player.weapon_state["pistol"]["reload_timer"]
        player.reload()
        assert player.weapon_state["pistol"]["reload_timer"] == initial_timer


class TestPlayerTimers:
    """Tests for timer updates."""

    def test_update_timers_decrements_shoot_timer(self, player: PlayerBase) -> None:
        """Shoot timer should count down."""
        player.shoot_timer = 5
        player.update_timers()
        assert player.shoot_timer == 4

    def test_update_timers_regenerates_stamina(self, player: PlayerBase) -> None:
        """Stamina should regenerate when below max."""
        player.stamina = 50.0
        player.stamina_recharge_delay = 0
        player.update_timers()
        assert player.stamina > 50.0

    def test_update_timers_stamina_delayed(self, player: PlayerBase) -> None:
        """Stamina should not regenerate during delay."""
        player.stamina = 50.0
        player.stamina_recharge_delay = 5
        initial = player.stamina
        player.update_timers()
        assert player.stamina == initial
        assert player.stamina_recharge_delay == 4

    def test_update_weapon_state_completes_reload(self, player: PlayerBase) -> None:
        """Weapon should complete reload when timer expires."""
        player.switch_weapon("pistol")
        ws = player.weapon_state["pistol"]
        ws["reloading"] = True
        ws["reload_timer"] = 1
        ws["clip"] = 0
        player.update_weapon_state()
        assert ws["reloading"] is False
        assert ws["clip"] == 12


class TestPlayerShield:
    """Tests for shield mechanics."""

    def test_shield_activation(self, player: PlayerBase) -> None:
        """Shield should activate when timer is available."""
        player.shield_timer = 100
        player.shield_recharge_delay = 0
        player.set_shield(True)
        assert player.shield_active is True

    def test_shield_blocked_during_cooldown(self, player: PlayerBase) -> None:
        """Shield should not activate during recharge delay."""
        player.shield_recharge_delay = 10
        player.set_shield(True)
        assert player.shield_active is False

    def test_shield_deactivation_sets_cooldown(self, player: PlayerBase) -> None:
        """Deactivating shield should set recharge delay."""
        player.shield_timer = 100
        player.shield_recharge_delay = 0
        player.set_shield(True)
        assert player.shield_active is True
        player.set_shield(False)
        assert player.shield_active is False
        assert player.shield_recharge_delay > 0


class TestPlayerBomb:
    """Tests for bomb mechanics."""

    def test_activate_bomb_success(self, player: PlayerBase) -> None:
        """Should activate bomb when available."""
        player.bombs = 2
        player.bomb_cooldown = 0
        result = player.activate_bomb()
        assert result is True
        assert player.bombs == 1
        assert player.bomb_cooldown > 0

    def test_activate_bomb_fails_no_bombs(self, player: PlayerBase) -> None:
        """Should fail when no bombs available."""
        player.bombs = 0
        result = player.activate_bomb()
        assert result is False

    def test_activate_bomb_fails_on_cooldown(self, player: PlayerBase) -> None:
        """Should fail when bomb cooldown is active."""
        player.bombs = 5
        player.bomb_cooldown = 100
        result = player.activate_bomb()
        assert result is False
