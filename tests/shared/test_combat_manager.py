"""Tests for games.shared.combat_manager module.

Covers kill handling, combo tracking, and explosion logic
using mock dependencies to avoid any pygame or rendering calls.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from games.shared.combat_manager import CombatManagerBase

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_constants(**overrides: Any) -> SimpleNamespace:
    """Create a minimal constants namespace."""
    defaults = dict(
        SCREEN_WIDTH=800,
        SCREEN_HEIGHT=600,
        SPREAD_ZOOM=0.01,
        SPREAD_BASE=0.04,
        HEADSHOT_THRESHOLD=0.05,
        RED=(255, 0, 0),
        WHITE=(255, 255, 255),
        ORANGE=(255, 165, 0),
        CYAN=(0, 255, 255),
        YELLOW=(255, 255, 0),
        FOV=1.0,
        BOMB_RADIUS=10.0,
        LASER_AOE_RADIUS=5.0,
        LASER_DURATION=10,
        LASER_WIDTH=5,
        BLUE_BLOOD=(0, 0, 200),
        PARTICLE_LIFETIME=30,
        DAMAGE_TEXT_COLOR=(255, 255, 255),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_entity_manager(bots: list[Any] | None = None) -> MagicMock:
    """Create a mock entity manager."""
    em = MagicMock()
    em.bots = bots if bots is not None else []
    return em


def _make_bot(
    x: float = 5.0,
    y: float = 5.0,
    alive: bool = True,
    health: int = 100,
) -> SimpleNamespace:
    """Create a mock bot with take_damage support."""
    bot = SimpleNamespace(x=x, y=y, alive=alive, health=health)

    def take_damage(amount: int, is_headshot: bool = False) -> bool:
        bot.health -= amount
        if bot.health <= 0:
            bot.health = 0
            bot.alive = False
            return True
        return False

    bot.take_damage = take_damage
    return bot


@pytest.fixture()
def cm() -> CombatManagerBase:
    """Standard CombatManagerBase with mocked dependencies."""
    return CombatManagerBase(
        entity_manager=_make_entity_manager(),
        particle_system=MagicMock(),
        sound_manager=MagicMock(),
        constants=_make_constants(),
    )


# ---------------------------------------------------------------------------
# Kill tracking
# ---------------------------------------------------------------------------


class TestHandleKill:
    """Tests for handle_kill and combo tracking."""

    def test_kill_increments_kills(self, cm: CombatManagerBase) -> None:
        """Kill count should increase by one."""
        bot = _make_bot()
        cm.handle_kill(bot)
        assert cm.kills == 1

    def test_kill_increments_combo(self, cm: CombatManagerBase) -> None:
        """Combo count should increase."""
        bot = _make_bot()
        cm.handle_kill(bot)
        assert cm.kill_combo_count == 1

    def test_kill_sets_combo_timer(self, cm: CombatManagerBase) -> None:
        """Combo timer should be set after a kill."""
        bot = _make_bot()
        cm.handle_kill(bot)
        assert cm.kill_combo_timer > 0

    def test_kill_records_death_position(self, cm: CombatManagerBase) -> None:
        """Last death position should record the bot's coordinates."""
        bot = _make_bot(x=3.5, y=7.2)
        cm.handle_kill(bot)
        assert cm.last_death_pos == (3.5, 7.2)

    def test_kill_plays_sound(self, cm: CombatManagerBase) -> None:
        """Sound manager should play scream on kill."""
        bot = _make_bot()
        cm.handle_kill(bot)
        cm.sound_manager.play_sound.assert_called_with("scream")

    def test_kill_invokes_on_kill_callback(self) -> None:
        """Optional on_kill callback should be called."""
        killed_bots: list[Any] = []
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
            on_kill=lambda b: killed_bots.append(b),
        )
        bot = _make_bot()
        mgr.handle_kill(bot)
        assert killed_bots == [bot]

    def test_multiple_kills_accumulate(self, cm: CombatManagerBase) -> None:
        """Multiple kills should accumulate counts."""
        for _ in range(5):
            cm.handle_kill(_make_bot())
        assert cm.kills == 5
        assert cm.kill_combo_count == 5

    def test_initial_state(self, cm: CombatManagerBase) -> None:
        """Initial state should have zero kills and no death position."""
        assert cm.kills == 0
        assert cm.kill_combo_count == 0
        assert cm.kill_combo_timer == 0
        assert cm.last_death_pos is None


# ---------------------------------------------------------------------------
# Bomb explosion
# ---------------------------------------------------------------------------


class TestHandleBombExplosion:
    """Tests for handle_bomb_explosion."""

    def test_bomb_kills_nearby_bots(self) -> None:
        """Bots within bomb radius should be killed."""
        bot_close = _make_bot(x=2.0, y=2.0, health=100)
        bots = [bot_close]
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(bots),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(BOMB_RADIUS=10.0),
        )
        player = SimpleNamespace(x=1.0, y=1.0)
        damage_texts: list[dict[str, Any]] = []
        result = mgr.handle_bomb_explosion(player, bots, damage_texts)
        assert not bot_close.alive
        assert mgr.kills == 1
        assert any("BOMB" in t["text"] for t in result)

    def test_bomb_spares_far_bots(self) -> None:
        """Bots outside bomb radius should survive."""
        bot_far = _make_bot(x=100.0, y=100.0, health=100)
        bots = [bot_far]
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(bots),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(BOMB_RADIUS=10.0),
        )
        player = SimpleNamespace(x=1.0, y=1.0)
        mgr.handle_bomb_explosion(player, bots, [])
        assert bot_far.alive

    def test_bomb_skips_dead_bots(self) -> None:
        """Dead bots should not be damaged again."""
        bot = _make_bot(alive=False)
        bots = [bot]
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(bots),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(BOMB_RADIUS=10.0),
        )
        player = SimpleNamespace(x=5.0, y=5.0)
        mgr.handle_bomb_explosion(player, bots, [])
        assert mgr.kills == 0

    def test_bomb_plays_sound(self) -> None:
        """Bomb explosion should play bomb sound."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager([]),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        player = SimpleNamespace(x=0.0, y=0.0)
        mgr.handle_bomb_explosion(player, [], [])
        mgr.sound_manager.play_sound.assert_called_with("bomb")


# ---------------------------------------------------------------------------
# Laser explosion
# ---------------------------------------------------------------------------


class TestExplodeLaser:
    """Tests for explode_laser."""

    def test_laser_kills_nearby_bots(self) -> None:
        """Bots within laser AOE radius should be killed."""
        bot = _make_bot(x=1.0, y=1.0, health=100)
        em = _make_entity_manager([bot])
        mgr = CombatManagerBase(
            entity_manager=em,
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(LASER_AOE_RADIUS=5.0),
        )
        damage_texts: list[dict[str, Any]] = []
        result = mgr.explode_laser(1.0, 1.0, damage_texts)
        assert not bot.alive
        assert mgr.kills == 1
        assert any("LASER" in t["text"] for t in result)

    def test_laser_spares_far_bots(self) -> None:
        """Bots outside laser AOE should survive."""
        bot = _make_bot(x=100.0, y=100.0, health=100)
        em = _make_entity_manager([bot])
        mgr = CombatManagerBase(
            entity_manager=em,
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(LASER_AOE_RADIUS=5.0),
        )
        mgr.explode_laser(0.0, 0.0, [])
        assert bot.alive

    def test_laser_skips_dead_bots(self) -> None:
        """Dead bots should not be processed."""
        bot = _make_bot(alive=False)
        em = _make_entity_manager([bot])
        mgr = CombatManagerBase(
            entity_manager=em,
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr.explode_laser(5.0, 5.0, [])
        assert mgr.kills == 0


# ---------------------------------------------------------------------------
# Generic explosion
# ---------------------------------------------------------------------------


class TestExplodeGeneric:
    """Tests for explode_generic."""

    def test_generic_explosion_kills_within_radius(self) -> None:
        """Bots within explosion radius should take damage."""
        bot = _make_bot(x=1.0, y=1.0, health=50)
        em = _make_entity_manager([bot])
        projectile = SimpleNamespace(x=1.0, y=1.0, damage=1000, z=0.5)
        player = SimpleNamespace(x=50.0, y=50.0)
        mgr = CombatManagerBase(
            entity_manager=em,
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr.explode_generic(
            projectile,
            radius=5.0,
            weapon_type="rocket",
            player=player,
            damage_flash_timer=0,
        )
        assert not bot.alive
        assert mgr.kills == 1

    def test_generic_explosion_returns_flash_timer(self) -> None:
        """Flash timer should be set when player is close to explosion."""
        projectile = SimpleNamespace(x=1.0, y=1.0, damage=100, z=0.5)
        player = SimpleNamespace(x=2.0, y=2.0)
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager([]),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        result = mgr.explode_generic(
            projectile,
            radius=5.0,
            weapon_type="rocket",
            player=player,
            damage_flash_timer=0,
        )
        assert result == 15  # Close enough to trigger flash

    def test_generic_explosion_no_flash_when_far(self) -> None:
        """Flash timer should not change when player is far."""
        projectile = SimpleNamespace(x=100.0, y=100.0, damage=100, z=0.5)
        player = SimpleNamespace(x=0.0, y=0.0)
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager([]),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        result = mgr.explode_generic(
            projectile,
            radius=5.0,
            weapon_type="plasma",
            player=player,
            damage_flash_timer=0,
        )
        assert result == 0
