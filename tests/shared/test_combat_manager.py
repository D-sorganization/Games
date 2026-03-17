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

    def test_bomb_survives_high_health(self) -> None:
        """Bot within bomb radius but not killed (very high health)."""
        bot = _make_bot(x=2.0, y=0.0, health=9999)
        bots = [bot]
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(bots),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(BOMB_RADIUS=10.0),
        )
        player = SimpleNamespace(x=0.0, y=0.0)
        mgr.handle_bomb_explosion(player, bots, [])
        # Bot survived but took damage – no kill
        assert bot.health < 9999
        assert mgr.kills == 0

    def test_bomb_medium_range_no_inner_explosion(self) -> None:
        """Bot at 6 units: inside BOMB_RADIUS but NOT within 5 – no inner explosion."""
        bot = _make_bot(x=6.0, y=0.0, health=100)
        bots = [bot]
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(bots),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(BOMB_RADIUS=10.0),
        )
        player = SimpleNamespace(x=0.0, y=0.0)
        mgr.handle_bomb_explosion(player, bots, [])
        # The bot is killed (high bomb damage) but no inner particle explosion
        assert mgr.particle_system.add_explosion.call_count == 0


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


class TestCheckShotHit:
    """Tests for check_shot_hit, applying hit damage, and secondary hits."""

    def test_check_shot_hit_primary(self) -> None:
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr._apply_hit_damage = MagicMock()

        player = SimpleNamespace(
            x=0.0,
            y=0.0,
            angle=0.0,
            zoomed=False,
            get_current_weapon_range=lambda: 100.0,
            get_current_weapon_damage=lambda: 10,
        )
        bot = _make_bot(x=10.0, y=0.0, alive=True)
        mgr.entity_manager.bots = [bot]

        mock_rc = MagicMock()
        mock_rc.cast_ray.return_value = (50.0, 0, 0, 0, 0)

        mgr.check_shot_hit(player, mock_rc, [bot], [], angle_offset=0.0)
        assert mock_rc.cast_ray.called
        assert mgr._apply_hit_damage.called

    def test_check_shot_hit_dead_bot_skipped(self) -> None:
        """Dead bots in the bots list are skipped (line 146 continue)."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr._apply_hit_damage = MagicMock()
        player = SimpleNamespace(
            x=0.0,
            y=0.0,
            angle=0.0,
            zoomed=False,
            get_current_weapon_range=lambda: 100.0,
            get_current_weapon_damage=lambda: 10,
        )
        dead_bot = _make_bot(x=5.0, y=0.0, alive=False)
        mock_rc = MagicMock()
        mock_rc.cast_ray.return_value = (50.0, 0, 0, 0, 0)
        mgr.check_shot_hit(player, mock_rc, [dead_bot], [], angle_offset=0.0)
        assert not mgr._apply_hit_damage.called

    def test_check_shot_hit_bot_beyond_wall(self) -> None:
        """Bot farther than wall distance is skipped (line 153 continue)."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr._apply_hit_damage = MagicMock()
        player = SimpleNamespace(
            x=0.0,
            y=0.0,
            angle=0.0,
            zoomed=False,
            get_current_weapon_range=lambda: 100.0,
            get_current_weapon_damage=lambda: 10,
        )
        # Wall is at 3.0 units, bot is at 10 units → beyond wall → skipped
        bot = _make_bot(x=10.0, y=0.0, alive=True)
        mock_rc = MagicMock()
        mock_rc.cast_ray.return_value = (3.0, 0, 0, 0, 0)
        mgr.check_shot_hit(player, mock_rc, [bot], [], angle_offset=0.0)
        assert not mgr._apply_hit_damage.called

    def test_check_shot_hit_wide_angle_bot_not_selected(self) -> None:
        """Bot at angle diff >= 0.15 is not selected as closest (line 165 false)."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr._apply_hit_damage = MagicMock()
        player = SimpleNamespace(
            x=0.0,
            y=0.0,
            angle=0.0,
            zoomed=False,
            get_current_weapon_range=lambda: 100.0,
            get_current_weapon_damage=lambda: 10,
            pitch=0,
        )
        # Bot is directly to the right but at a 90° angle offset from aim
        bot = _make_bot(x=0.0, y=5.0, alive=True)  # angle diff ~pi/2
        mock_rc = MagicMock()
        mock_rc.cast_ray.return_value = (50.0, 0, 0, 0, 0)
        mgr.check_shot_hit(player, mock_rc, [bot], [], angle_offset=0.0)
        assert not mgr._apply_hit_damage.called

    def test_check_shot_hit_second_bot_farther_not_selected(self) -> None:
        """Second bot farther than first is not selected (line 166->144 false)."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr._apply_hit_damage = MagicMock()
        player = SimpleNamespace(
            x=0.0,
            y=0.0,
            angle=0.0,
            zoomed=False,
            get_current_weapon_range=lambda: 100.0,
            get_current_weapon_damage=lambda: 10,
            pitch=0,
        )
        # Two bots in line of sight; closer one picked first, farther one skipped
        bot_close = _make_bot(x=5.0, y=0.0, alive=True)
        bot_far = _make_bot(x=10.0, y=0.0, alive=True)
        mock_rc = MagicMock()
        mock_rc.cast_ray.return_value = (50.0, 0, 0, 0, 0)
        mgr.check_shot_hit(player, mock_rc, [bot_close, bot_far], [], angle_offset=0.0)
        # The function should have hit exactly once with the closest bot
        assert mgr._apply_hit_damage.call_count == 1

    def test_check_shot_hit_laser(self) -> None:
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        player = SimpleNamespace(
            x=0.0,
            y=0.0,
            angle=0.0,
            zoomed=False,
            get_current_weapon_range=lambda: 100.0,
            get_current_weapon_damage=lambda: 10,
        )

        mock_rc = MagicMock()
        mock_rc.cast_ray.return_value = (50.0, 0, 0, 0, 0)

        mgr.check_shot_hit(player, mock_rc, [], [], angle_offset=0.0, is_laser=True)
        assert mgr.particle_system.add_laser.called

    def test_check_shot_hit_secondary(self) -> None:
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr._handle_secondary_hit = MagicMock()

        player = SimpleNamespace(
            x=0.0,
            y=0.0,
            angle=0.0,
            zoomed=False,
            get_current_weapon_range=lambda: 100.0,
            get_current_weapon_damage=lambda: 10,
        )

        mock_rc = MagicMock()
        mock_rc.cast_ray.return_value = (50.0, 0, 0, 0, 0)

        mgr.check_shot_hit(player, mock_rc, [], [], angle_offset=0.0, is_secondary=True)
        assert mgr._handle_secondary_hit.called

    def test_handle_secondary_hit_creates_explosion(self) -> None:
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr.explode_laser = MagicMock()
        player = SimpleNamespace(x=0.0, y=0.0, angle=0.0)

        mgr._handle_secondary_hit(player, None, float("inf"), 10.0, [])
        assert mgr.explode_laser.called
        assert mgr.particle_system.add_laser.called

    def test_apply_hit_damage(self) -> None:
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        bot = _make_bot(alive=True, health=100)
        player = SimpleNamespace(x=0.0, y=0.0, angle=0.0)

        mgr._apply_hit_damage(
            player,
            bot,
            distance=5.0,
            weapon_range=100.0,
            base_damage=50,
            is_headshot=False,
            damage_texts=[],
            show_damage=True,
        )
        assert bot.health < 100
        assert mgr.particle_system.add_particle.called

    def test_apply_hit_damage_no_show(self) -> None:
        """show_damage=False skips appending damage text."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        bot = _make_bot(alive=True, health=100)
        player = SimpleNamespace(x=0.0, y=0.0, angle=0.0)
        texts: list = []
        mgr._apply_hit_damage(
            player,
            bot,
            distance=5.0,
            weapon_range=100.0,
            base_damage=50,
            is_headshot=False,
            damage_texts=texts,
            show_damage=False,
        )
        assert texts == []  # No damage text appended

    def test_apply_hit_damage_kills_bot(self) -> None:
        """_apply_hit_damage should call handle_kill when bot dies."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        bot = _make_bot(alive=True, health=1)
        player = SimpleNamespace(x=0.0, y=0.0, angle=0.0)
        mgr._apply_hit_damage(player, bot, 1.0, 100.0, 1000, False, [], True)
        assert not bot.alive
        assert mgr.kills == 1

    def test_apply_hit_damage_negative_bot_angle(self) -> None:
        """Branch: bot_angle < 0 adds 2*pi."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        # Bot is up-left of player – atan2 will return negative angle
        bot = _make_bot(x=-1.0, y=-1.0, alive=True, health=100)
        player = SimpleNamespace(x=0.0, y=0.0, angle=0.0)
        texts: list = []
        mgr._apply_hit_damage(player, bot, 1.42, 100.0, 10, False, texts, True)
        assert bot.health < 100

    def test_apply_hit_damage_large_angle_diff(self) -> None:
        """Branch: angle_diff > pi wraps around."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )

        # Player facing east (angle=0), bot is directly west (angle=pi).
        # angle_diff = pi, then 2*pi - pi = pi (wrap lands on boundary)
        bot = _make_bot(x=-5.0, y=0.0, alive=True, health=100)
        player = SimpleNamespace(x=0.0, y=0.0, angle=0.0)
        mgr._apply_hit_damage(player, bot, 5.0, 100.0, 50, False, [], True)
        assert bot.health < 100

    def test_apply_hit_damage_headshot(self) -> None:
        """Headshot appends '!' to damage text and uses RED color."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        bot = _make_bot(alive=True, health=100)
        player = SimpleNamespace(x=0.0, y=0.0, angle=0.0)
        texts: list = []
        mgr._apply_hit_damage(player, bot, 1.0, 100.0, 10, True, texts, True)
        assert any("!" in t["text"] for t in texts)

    def test_check_shot_hit_with_angle_offset(self) -> None:
        """angle_offset != 0 uses fixed aim angle instead of spread."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        player = SimpleNamespace(
            x=0.0,
            y=0.0,
            angle=0.0,
            zoomed=False,
            get_current_weapon_range=lambda: 100.0,
            get_current_weapon_damage=lambda: 10,
        )
        mock_rc = MagicMock()
        mock_rc.cast_ray.return_value = (50.0, 0, 0, 0, 0)
        # Should not raise; angle_offset != 0 hits different branch
        mgr.check_shot_hit(player, mock_rc, [], [], angle_offset=0.1)
        assert mock_rc.cast_ray.called

    def test_check_shot_hit_wall_clamps(self) -> None:
        """When wall_dist > weapon_range, wall_dist is clamped."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        player = SimpleNamespace(
            x=0.0,
            y=0.0,
            angle=0.0,
            zoomed=False,
            get_current_weapon_range=lambda: 5.0,  # very short range
            get_current_weapon_damage=lambda: 10,
        )
        mock_rc = MagicMock()
        mock_rc.cast_ray.return_value = (100.0, 0, 0, 0, 0)  # far wall
        mgr.check_shot_hit(player, mock_rc, [], [], angle_offset=0.0)
        assert mock_rc.cast_ray.called

    def test_check_shot_hit_bot_negative_angle(self) -> None:
        """Bots in 3rd/4th quadrant have negative atan2 – trigger wrap branch."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr._apply_hit_damage = MagicMock()

        player = SimpleNamespace(
            x=0.0,
            y=0.0,
            angle=5.5,  # Near 2*pi so bot south-east triggers wrap
            zoomed=False,
            get_current_weapon_range=lambda: 100.0,
            get_current_weapon_damage=lambda: 10,
            pitch=0,
        )
        bot = _make_bot(x=2.0, y=-2.0, alive=True)  # south = negative y
        mock_rc = MagicMock()
        mock_rc.cast_ray.return_value = (50.0, 0, 0, 0, 0)
        mgr.check_shot_hit(player, mock_rc, [bot], [], angle_offset=0.0)

    def test_check_shot_hit_angle_diff_wrap(self) -> None:
        """angle_diff > pi triggers the 2*pi subtraction branch."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr._apply_hit_damage = MagicMock()

        player = SimpleNamespace(
            x=0.0,
            y=0.0,
            angle=0.0,
            zoomed=False,
            get_current_weapon_range=lambda: 100.0,
            get_current_weapon_damage=lambda: 10,
            pitch=0,
        )
        # Bot angle will be ~pi which causes angle_diff > pi after offset
        bot = _make_bot(x=-3.0, y=0.001, alive=True)
        mock_rc = MagicMock()
        mock_rc.cast_ray.return_value = (50.0, 0, 0, 0, 0)
        mgr.check_shot_hit(player, mock_rc, [bot], [], angle_offset=0.0)

    def test_check_shot_hit_exception_handled(self) -> None:
        """Exceptions inside check_shot_hit are caught and logged."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        # Make raycaster raise
        mock_rc = MagicMock()
        mock_rc.cast_ray.side_effect = RuntimeError("test error")
        player = SimpleNamespace(
            x=0.0,
            y=0.0,
            angle=0.0,
            zoomed=False,
            get_current_weapon_range=lambda: 100.0,
            get_current_weapon_damage=lambda: 10,
        )
        # Should NOT raise; exception is swallowed
        result = mgr.check_shot_hit(player, mock_rc, [], [], angle_offset=0.0)
        assert isinstance(result, list)

    def test_handle_secondary_hit_bot_closer(self) -> None:
        """When bot is closer than wall, impact uses bot distance."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr.explode_laser = MagicMock()
        bot = _make_bot(x=3.0, y=0.0, alive=True)
        player = SimpleNamespace(x=0.0, y=0.0, angle=0.0)
        mgr._handle_secondary_hit(
            player, bot, closest_dist=3.0, wall_dist=10.0, damage_texts=[]
        )
        assert mgr.explode_laser.called

    def test_handle_secondary_hit_explode_exception(self) -> None:
        """Exception in explode_laser during secondary hit is caught."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr.explode_laser = MagicMock(side_effect=RuntimeError("oops"))
        player = SimpleNamespace(x=0.0, y=0.0, angle=0.0)
        # Should not raise
        mgr._handle_secondary_hit(player, None, float("inf"), 5.0, [])


class TestBombExplosionExtra:
    """Extra coverage for handle_bomb_explosion branches."""

    def test_bomb_kills_and_close_explosion(self) -> None:
        """Bot within 5 units triggers inner explosion particle."""
        bot_close = _make_bot(x=1.0, y=1.0, health=100)
        bots = [bot_close]
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager(bots),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(BOMB_RADIUS=10.0),
        )
        player = SimpleNamespace(x=0.0, y=0.0)
        mgr.handle_bomb_explosion(player, bots, [])
        assert not bot_close.alive
        assert mgr.particle_system.add_explosion.called

    def test_bomb_sound_exception_handled(self) -> None:
        """Exception from sound_manager.play_sound is caught."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager([]),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr.sound_manager.play_sound.side_effect = Exception("no audio")
        player = SimpleNamespace(x=0.0, y=0.0)
        # Should not raise
        mgr.handle_bomb_explosion(player, [], [])


class TestExplodeLaserExtra:
    """Extra coverage for explode_laser branches."""

    def test_laser_sound_exception_handled(self) -> None:
        """Exception from play_sound(boom_real) is caught."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager([]),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr.sound_manager.play_sound.side_effect = Exception("no audio")
        # Should not raise
        mgr.explode_laser(0.0, 0.0, [])

    def test_laser_particle_exception_handled(self) -> None:
        """Exception thrown inside try block of explode_laser is caught."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager([]),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr.particle_system.add_world_explosion.side_effect = RuntimeError("oops")
        # Should not raise – exception caught inside try/except
        mgr.explode_laser(0.0, 0.0, [])

    def test_laser_not_killed_bot(self) -> None:
        """Bot takes damage but survives – no handle_kill called."""
        bot = _make_bot(x=1.0, y=1.0, health=9999)
        em = _make_entity_manager([bot])
        mgr = CombatManagerBase(
            entity_manager=em,
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(LASER_AOE_RADIUS=5.0),
        )
        mgr.explode_laser(1.0, 1.0, [])
        assert bot.alive
        assert mgr.kills == 0


class TestExplodeGenericExtra:
    """Extra coverage for explode_generic branches."""

    def test_explode_generic_plasma_color(self) -> None:
        """weapon_type==plasma uses CYAN color."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager([]),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        projectile = SimpleNamespace(x=0.0, y=0.0, damage=100, z=0.5)
        player = SimpleNamespace(x=0.0, y=0.0)
        mgr.explode_generic(projectile, 5.0, "plasma", player, 0)
        # CYAN branch covered; no assertion needed beyond no crash
        assert mgr.particle_system.add_world_explosion.called

    def test_explode_generic_player_close_triggers_particles(self) -> None:
        """Player within 20 units triggers screen explosion."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager([]),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        projectile = SimpleNamespace(x=0.0, y=0.0, damage=100, z=0.5)
        player = SimpleNamespace(x=1.0, y=1.0)
        mgr.explode_generic(projectile, 5.0, "rocket", player, 0)
        assert mgr.particle_system.add_explosion.called

    def test_explode_generic_plasma_player_close(self) -> None:
        """weapon_type==plasma + player close triggers count=3 explosion."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager([]),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        projectile = SimpleNamespace(x=0.0, y=0.0, damage=100, z=0.5)
        player = SimpleNamespace(x=1.0, y=1.0)
        mgr.explode_generic(projectile, 5.0, "plasma", player, 0)
        assert mgr.particle_system.add_explosion.called

    def test_explode_generic_sound_exception(self) -> None:
        """Exception from play_sound is suppressed."""
        mgr = CombatManagerBase(
            entity_manager=_make_entity_manager([]),
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        mgr.sound_manager.play_sound.side_effect = Exception("no audio")
        projectile = SimpleNamespace(x=100.0, y=100.0, damage=100, z=0.5)
        player = SimpleNamespace(x=0.0, y=0.0)
        mgr.explode_generic(projectile, 5.0, "rocket", player, 0)

    def test_explode_generic_kills_bot(self) -> None:
        """Bot killed by explode_generic increments kill count."""
        bot = _make_bot(x=1.0, y=1.0, health=50)
        em = _make_entity_manager([bot])
        mgr = CombatManagerBase(
            entity_manager=em,
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        projectile = SimpleNamespace(x=1.0, y=1.0, damage=1000, z=0.5)
        player = SimpleNamespace(x=50.0, y=50.0)
        mgr.explode_generic(projectile, 5.0, "rocket", player, 0)
        assert not bot.alive
        assert mgr.kills == 1

    def test_explode_generic_bot_survives(self) -> None:
        """Bot takes damage but survives – not counted as kill."""
        bot = _make_bot(x=1.0, y=1.0, health=9999)
        em = _make_entity_manager([bot])
        mgr = CombatManagerBase(
            entity_manager=em,
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        projectile = SimpleNamespace(x=1.0, y=1.0, damage=1, z=0.5)
        player = SimpleNamespace(x=50.0, y=50.0)
        mgr.explode_generic(projectile, 5.0, "rocket", player, 0)
        assert bot.alive
        assert mgr.kills == 0

    def test_explode_generic_dead_bot_skipped(self) -> None:
        """Dead bot in entity_manager.bots is skipped (line 567 continue)."""
        dead_bot = _make_bot(x=1.0, y=1.0, health=0, alive=False)
        em = _make_entity_manager([dead_bot])
        mgr = CombatManagerBase(
            entity_manager=em,
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        projectile = SimpleNamespace(x=1.0, y=1.0, damage=1000, z=0.5)
        player = SimpleNamespace(x=50.0, y=50.0)
        mgr.explode_generic(projectile, 5.0, "rocket", player, 0)
        assert mgr.kills == 0

    def test_explode_generic_bot_outside_radius(self) -> None:
        """Bot alive but outside radius is not damaged (line 572->565 false branch)."""
        bot = _make_bot(x=100.0, y=100.0, health=100)
        em = _make_entity_manager([bot])
        mgr = CombatManagerBase(
            entity_manager=em,
            particle_system=MagicMock(),
            sound_manager=MagicMock(),
            constants=_make_constants(),
        )
        projectile = SimpleNamespace(x=0.0, y=0.0, damage=1000, z=0.5)
        player = SimpleNamespace(x=50.0, y=50.0)
        mgr.explode_generic(projectile, 5.0, "rocket", player, 0)
        assert bot.alive
        assert bot.health == 100  # untouched
