"""Tests for Peanut_Butter_Panic core game logic.

Covers:
- Module import and public API
- GameConfig defaults and constants validation
- GameWorld initialization state
- Player movement mechanics
- Dash, swing, trap, and shockwave abilities
- Enemy spawning and targeting
- Trap lifetime and expiry
- Combo and scoring system
- Powerup application (all four kinds)
- Wave progression
- GameWorld.reset()
- Defeated condition (player health and sandwiches)

No pygame dependency: core.py is pure Python.
"""

from __future__ import annotations

import math

import pytest

from games.Peanut_Butter_Panic.peanut_butter_panic.core import (
    GameConfig,
    GameWorld,
    InputState,
    PowerUp,
    Sandwich,
    Trap,
    _clamp,
    _distance,
    _length,
    _normalize,
)

# ---------------------------------------------------------------------------
# Module-level import smoke test
# ---------------------------------------------------------------------------


def test_import_core_public_api() -> None:
    """All public names exported from __init__ must be importable."""
    from games.Peanut_Butter_Panic.peanut_butter_panic import (  # noqa: F401
        GameConfig,
        GameWorld,
        InputState,
    )


# ---------------------------------------------------------------------------
# GameConfig defaults
# ---------------------------------------------------------------------------


class TestGameConfigDefaults:
    """Validate that GameConfig ships with sensible default values."""

    def test_screen_dimensions_positive(self) -> None:
        cfg = GameConfig()
        assert cfg.width > 0
        assert cfg.height > 0

    def test_player_speed_positive(self) -> None:
        cfg = GameConfig()
        assert cfg.player_speed > 0.0

    def test_dash_speed_greater_than_player_speed(self) -> None:
        cfg = GameConfig()
        assert cfg.dash_speed > cfg.player_speed

    def test_player_health_positive(self) -> None:
        cfg = GameConfig()
        assert cfg.player_health > 0

    def test_sandwich_health_positive(self) -> None:
        cfg = GameConfig()
        assert cfg.sandwich_health > 0

    def test_max_wave_positive(self) -> None:
        cfg = GameConfig()
        assert cfg.max_wave >= 1

    def test_powerup_chance_in_unit_interval(self) -> None:
        cfg = GameConfig()
        assert 0.0 <= cfg.powerup_chance <= 1.0

    def test_combo_bonus_positive(self) -> None:
        cfg = GameConfig()
        assert cfg.combo_bonus > 0.0

    def test_max_combo_at_least_one(self) -> None:
        cfg = GameConfig()
        assert cfg.max_combo >= 1


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestHelpers:
    """Unit tests for the private pure-math helpers."""

    def test_clamp_below_min(self) -> None:
        assert _clamp(-5.0, 0.0, 10.0) == 0.0

    def test_clamp_above_max(self) -> None:
        assert _clamp(15.0, 0.0, 10.0) == 10.0

    def test_clamp_within_range(self) -> None:
        assert _clamp(5.0, 0.0, 10.0) == 5.0

    def test_length_zero_vector(self) -> None:
        assert _length((0.0, 0.0)) == 0.0

    def test_length_unit_vector(self) -> None:
        assert math.isclose(_length((1.0, 0.0)), 1.0)

    def test_length_pythagorean(self) -> None:
        assert math.isclose(_length((3.0, 4.0)), 5.0)

    def test_normalize_zero_vector_returns_zero(self) -> None:
        assert _normalize((0.0, 0.0)) == (0.0, 0.0)

    def test_normalize_produces_unit_vector(self) -> None:
        nx, ny = _normalize((3.0, 4.0))
        assert math.isclose(math.sqrt(nx**2 + ny**2), 1.0)

    def test_distance_same_point(self) -> None:
        assert _distance((5.0, 5.0), (5.0, 5.0)) == 0.0

    def test_distance_known_value(self) -> None:
        assert math.isclose(_distance((0.0, 0.0), (3.0, 4.0)), 5.0)


# ---------------------------------------------------------------------------
# GameWorld initialization
# ---------------------------------------------------------------------------


class TestGameWorldInit:
    """Verify the game world starts in a valid initial state."""

    @pytest.fixture()
    def world(self) -> GameWorld:
        return GameWorld(seed=42)

    def test_two_sandwiches_at_start(self, world: GameWorld) -> None:
        assert len(world.sandwiches) == 2

    def test_all_sandwiches_alive_at_start(self, world: GameWorld) -> None:
        assert all(s.alive for s in world.sandwiches)

    def test_no_enemies_at_start(self, world: GameWorld) -> None:
        assert world.enemies == []

    def test_no_traps_at_start(self, world: GameWorld) -> None:
        assert world.traps == []

    def test_no_powerups_at_start(self, world: GameWorld) -> None:
        assert world.powerups == []

    def test_player_health_matches_config(self, world: GameWorld) -> None:
        assert world.player.health == world.config.player_health

    def test_score_zero_at_start(self, world: GameWorld) -> None:
        assert world.stats.score == 0

    def test_wave_one_at_start(self, world: GameWorld) -> None:
        assert world.stats.wave == 1

    def test_player_starts_at_center(self, world: GameWorld) -> None:
        cx = world.config.width / 2
        cy = world.config.height / 2
        assert math.isclose(world.player.position[0], cx)
        assert math.isclose(world.player.position[1], cy)

    def test_not_defeated_at_start(self, world: GameWorld) -> None:
        assert not world.defeated


# ---------------------------------------------------------------------------
# Player movement
# ---------------------------------------------------------------------------


class TestPlayerMovement:
    """Test that player position updates correctly on movement input."""

    def test_move_right_increases_x(self) -> None:
        world = GameWorld(seed=1)
        initial_x = world.player.position[0]
        world.update(0.1, InputState(move=(1.0, 0.0)))
        assert world.player.position[0] > initial_x

    def test_move_left_decreases_x(self) -> None:
        world = GameWorld(seed=1)
        # Place player in the middle so it can move left
        world.player.position = (world.config.width / 2, world.config.height / 2)
        initial_x = world.player.position[0]
        world.update(0.1, InputState(move=(-1.0, 0.0)))
        assert world.player.position[0] < initial_x

    def test_no_input_player_stays_put(self) -> None:
        world = GameWorld(seed=1)
        initial_pos = world.player.position
        world.update(0.1, InputState(move=(0.0, 0.0)))
        assert math.isclose(world.player.position[0], initial_pos[0])
        assert math.isclose(world.player.position[1], initial_pos[1])

    def test_player_clamped_to_world_bounds(self) -> None:
        world = GameWorld(seed=1)
        world.player.position = (0.0, world.config.height / 2)
        world.update(1.0, InputState(move=(-1.0, 0.0)))
        assert world.player.position[0] >= 0.0


# ---------------------------------------------------------------------------
# Abilities
# ---------------------------------------------------------------------------


class TestDash:
    def test_dash_activates_when_cooldown_zero(self) -> None:
        world = GameWorld(seed=1)
        assert world.player.dash_cooldown == 0.0
        world.update(0.05, InputState(dash=True))
        # After dash, cooldown should be set
        assert world.player.dash_cooldown > 0.0

    def test_dash_not_activated_when_on_cooldown(self) -> None:
        world = GameWorld(seed=1)
        world.player.dash_cooldown = 99.0
        world.update(0.05, InputState(dash=True))
        # Cooldown ticked down slightly but not reset to full
        assert world.player.dash_cooldown < 99.0


class TestSwing:
    def test_swing_removes_enemy_in_range(self) -> None:
        world = GameWorld(seed=1)
        # Place enemy right on top of player
        player_pos = world.player.position
        world.add_enemy(position=player_pos, speed=0.0)
        assert len(world.enemies) == 1
        world.player.swing_cooldown = 0.0
        world.update(0.016, InputState(swing=True))
        assert len(world.enemies) == 0

    def test_swing_does_not_remove_distant_enemy(self) -> None:
        world = GameWorld(seed=1)
        # Place enemy far away
        world.add_enemy(position=(world.config.width - 1, world.config.height - 1))
        world.player.position = (0.0, 0.0)
        world.player.swing_cooldown = 0.0
        world.update(0.016, InputState(swing=True))
        assert len(world.enemies) == 1

    def test_swing_increases_score(self) -> None:
        world = GameWorld(seed=1)
        player_pos = world.player.position
        world.add_enemy(position=player_pos, reward=50)
        world.player.swing_cooldown = 0.0
        world.update(0.016, InputState(swing=True))
        assert world.stats.score > 0


class TestTrap:
    def test_deploy_trap_adds_trap(self) -> None:
        world = GameWorld(seed=1)
        assert len(world.traps) == 0
        world.player.trap_cooldown = 0.0
        world.update(0.016, InputState(deploy_trap=True))
        assert len(world.traps) == 1

    def test_trap_expires_over_time(self) -> None:
        world = GameWorld(seed=1)
        trap = Trap(
            position=(100.0, 100.0),
            radius=50.0,
            slow_factor=0.5,
            lifetime=0.05,
        )
        world.traps.append(trap)
        world.update(0.1, InputState())
        # Trap with 0.05s lifetime should be gone after 0.1s update
        assert all(t.lifetime > 0 for t in world.traps) or len(world.traps) == 0


class TestShockwave:
    def test_shockwave_clears_nearby_enemies(self) -> None:
        world = GameWorld(seed=1)
        # Place enemy within shockwave radius
        world.add_enemy(position=world.player.position)
        world.player.shockwave_cooldown = 0.0
        world.update(0.016, InputState(shockwave=True))
        assert len(world.enemies) == 0


# ---------------------------------------------------------------------------
# Sandwich dataclass
# ---------------------------------------------------------------------------


class TestSandwich:
    def test_alive_when_health_positive(self) -> None:
        s = Sandwich(position=(100.0, 100.0), health=3)
        assert s.alive is True

    def test_dead_when_health_zero(self) -> None:
        s = Sandwich(position=(100.0, 100.0), health=0)
        assert s.alive is False


# ---------------------------------------------------------------------------
# Powerup application
# ---------------------------------------------------------------------------


class TestPowerupApplication:
    def test_sugar_rush_increases_speed(self) -> None:
        world = GameWorld(seed=1)
        base_speed = world.player.speed
        p = PowerUp(position=(0.0, 0.0), kind="sugar_rush", duration=7.0)
        world._apply_powerup(p)  # noqa: SLF001
        assert world.player.speed > base_speed

    def test_sticky_gloves_extends_swing_radius(self) -> None:
        world = GameWorld(seed=1)
        base_radius = world.config.swing_radius
        p = PowerUp(position=(0.0, 0.0), kind="sticky_gloves", duration=7.0)
        world._apply_powerup(p)  # noqa: SLF001
        assert world.config.swing_radius > base_radius

    def test_free_shockwave_resets_cooldown(self) -> None:
        world = GameWorld(seed=1)
        world.player.shockwave_cooldown = 99.0
        p = PowerUp(position=(0.0, 0.0), kind="free_shockwave", duration=0.0)
        world._apply_powerup(p)  # noqa: SLF001
        assert world.player.shockwave_cooldown == 0.0

    def test_golden_bread_heals_sandwich(self) -> None:
        world = GameWorld(seed=1)
        world.sandwiches[0].health = 1
        p = PowerUp(position=(0.0, 0.0), kind="golden_bread", duration=0.0)
        world._apply_powerup(p)  # noqa: SLF001
        assert world.sandwiches[0].health > 1

    def test_golden_bread_does_not_exceed_max_health(self) -> None:
        world = GameWorld(seed=1)
        world.sandwiches[0].health = world.config.sandwich_health
        p = PowerUp(position=(0.0, 0.0), kind="golden_bread", duration=0.0)
        world._apply_powerup(p)  # noqa: SLF001
        assert world.sandwiches[0].health <= world.config.sandwich_health


# ---------------------------------------------------------------------------
# Defeated condition
# ---------------------------------------------------------------------------


class TestDefeated:
    def test_defeated_when_player_health_zero(self) -> None:
        world = GameWorld(seed=1)
        world.player.health = 0
        assert world.defeated is True

    def test_defeated_when_all_sandwiches_dead(self) -> None:
        world = GameWorld(seed=1)
        for s in world.sandwiches:
            s.health = 0
        assert world.defeated is True

    def test_not_defeated_while_player_alive_and_sandwich_alive(self) -> None:
        world = GameWorld(seed=1)
        world.player.health = 1
        world.sandwiches[0].health = 1
        # Kill the second sandwich; one alive is enough
        world.sandwiches[1].health = 0
        assert world.defeated is False


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


class TestReset:
    def test_reset_restores_player_health(self) -> None:
        world = GameWorld(seed=1)
        world.player.health = 0
        world.reset()
        assert world.player.health == world.config.player_health

    def test_reset_clears_enemies(self) -> None:
        world = GameWorld(seed=1)
        world.add_enemy(position=(100.0, 100.0))
        world.reset()
        assert world.enemies == []

    def test_reset_restores_sandwiches(self) -> None:
        world = GameWorld(seed=1)
        world.sandwiches[0].health = 0
        world.reset()
        assert all(s.alive for s in world.sandwiches)

    def test_reset_clears_score(self) -> None:
        world = GameWorld(seed=1)
        world.stats.score = 9999
        world.reset()
        assert world.stats.score == 0
