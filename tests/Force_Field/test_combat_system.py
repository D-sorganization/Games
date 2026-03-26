"""Tests for games.Force_Field.src.combat_system."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from games.Force_Field.src.combat_system import CombatSystem
from games.Force_Field.src.projectile import Projectile


def _make_game(
    player_x: float = 5.0,
    player_y: float = 5.0,
    bots: list | None = None,
) -> MagicMock:
    """Create a mock game object with a configured player."""
    game = MagicMock()
    player = MagicMock()
    player.x = player_x
    player.y = player_y
    player.angle = 0.0
    player.current_weapon = "pistol"
    player.zoomed = False
    player.pitch = 0.0
    player.stamina = 100
    player.shield_active = False
    player.god_mode = False
    player.alive = True

    def get_damage() -> int:
        return 25

    def get_range() -> float:
        return 20.0

    player.get_current_weapon_damage.side_effect = get_damage
    player.get_current_weapon_range.side_effect = get_range

    game.player = player
    game.bots = bots or []
    game.show_damage = False
    game.kills = 0
    game.kill_combo_count = 0
    game.kill_combo_timer = 0
    game.last_death_pos = (0, 0)
    game.damage_texts = []
    game.screen_shake = 0.0
    game.damage_flash_timer = 0

    # Raycaster mock — cast_ray returns (wall_dist, ...) tuple
    game.raycaster = MagicMock()
    game.raycaster.cast_ray.return_value = (100.0, 0, 0, 0, 0)

    return game


@pytest.fixture()
def game() -> MagicMock:
    return _make_game()


@pytest.fixture()
def cs(game: MagicMock) -> CombatSystem:
    return CombatSystem(game)


class TestCombatSystemPlayerProperty:
    def test_player_property_returns_player(self, cs: CombatSystem, game: MagicMock) -> None:
        assert cs.player is game.player

    def test_player_property_raises_when_none(self, game: MagicMock) -> None:
        game.player = None
        cs = CombatSystem(game)
        with pytest.raises(ValueError, match="Player is None"):
            _ = cs.player


class TestFireWeapon:
    def test_fire_weapon_hitscan(self, cs: CombatSystem, game: MagicMock) -> None:
        game.player.current_weapon = "pistol"
        with patch.object(cs, "check_shot_hit") as mock_hit:
            cs.fire_weapon()
            mock_hit.assert_called_once()

    def test_fire_weapon_secondary(self, cs: CombatSystem, game: MagicMock) -> None:
        game.player.current_weapon = "pistol"
        with patch.object(cs, "check_shot_hit") as mock_hit:
            cs.fire_weapon(is_secondary=True)
            mock_hit.assert_called_once_with(is_secondary=True)

    def test_fire_weapon_spread_shotgun(self, game: MagicMock) -> None:
        game.player.current_weapon = "shotgun"
        cs = CombatSystem(game)
        with patch.object(cs, "_fire_spread") as mock_spread:
            cs.fire_weapon()
            mock_spread.assert_called_once()

    def test_fire_weapon_projectile_plasma(self, game: MagicMock) -> None:
        game.player.current_weapon = "plasma"
        cs = CombatSystem(game)
        with patch.object(cs, "_fire_plasma") as mock_plasma:
            cs.fire_weapon()
            mock_plasma.assert_called_once()

    def test_fire_weapon_recoil_when_zoomed(self, game: MagicMock) -> None:
        game.player.current_weapon = "pistol"
        game.player.zoomed = True
        cs = CombatSystem(game)
        with patch.object(cs, "check_shot_hit"):
            cs.fire_weapon()
        assert game.player.pitch == 0.5  # Zoomed recoil

    def test_fire_weapon_recoil_shotgun(self, game: MagicMock) -> None:
        game.player.current_weapon = "shotgun"
        game.player.zoomed = False
        cs = CombatSystem(game)
        initial_pitch = game.player.pitch
        with patch.object(cs, "_fire_spread"):
            cs.fire_weapon()
        assert game.player.pitch == initial_pitch + 4.0


class TestFireMethods:
    def test_fire_spread_calls_check_hit_multiple(self, cs: CombatSystem) -> None:
        from games.Force_Field.src import constants as C

        weapon_data = C.WEAPONS.get("shotgun", {"pellets": 8, "spread": 0.15})
        with patch.object(cs, "check_shot_hit") as mock_hit:
            cs._fire_spread(weapon_data, "shotgun")
            pellets = int(weapon_data.get("pellets", 8))
            assert mock_hit.call_count == pellets

    def test_fire_beam_uses_laser(self, cs: CombatSystem) -> None:
        with patch.object(cs, "check_shot_hit") as mock_hit:
            cs._fire_beam({}, "laser")
            mock_hit.assert_called_once_with(is_secondary=False, is_laser=True)

    def test_fire_burst_delegates_to_minigun(self, cs: CombatSystem) -> None:
        with patch.object(cs, "_fire_minigun") as mock_mm:
            cs._fire_burst({}, "minigun")
            mock_mm.assert_called_once()

    def test_fire_hitscan(self, cs: CombatSystem) -> None:
        with patch.object(cs, "check_shot_hit") as mock_hit:
            cs._fire_hitscan({}, "pistol")
            mock_hit.assert_called_once_with(is_secondary=False)

    def test_fire_projectile_plasma(self, cs: CombatSystem, game: MagicMock) -> None:
        with patch.object(cs, "_fire_plasma") as mock_p:
            cs._fire_projectile({}, "plasma")
            mock_p.assert_called_once()

    def test_fire_projectile_generic_fallback(self, cs: CombatSystem, game: MagicMock) -> None:
        with patch.object(cs, "_fire_generic_projectile") as mock_gp:
            cs._fire_projectile({"fire_mode": "projectile"}, "unknown_weapon")
            mock_gp.assert_called_once()

    def test_fire_plasma_adds_projectile(self, cs: CombatSystem, game: MagicMock) -> None:
        cs._fire_plasma()
        game.entity_manager.add_projectile.assert_called_once()
        proj = game.entity_manager.add_projectile.call_args[0][0]
        assert isinstance(proj, Projectile)
        assert proj.weapon_type == "plasma"

    def test_fire_pulse_adds_projectile(self, cs: CombatSystem, game: MagicMock) -> None:
        cs._fire_pulse()
        game.entity_manager.add_projectile.assert_called_once()

    def test_fire_rocket_adds_projectile(self, cs: CombatSystem, game: MagicMock) -> None:
        cs._fire_rocket()
        game.entity_manager.add_projectile.assert_called_once()
        proj = game.entity_manager.add_projectile.call_args[0][0]
        assert proj.weapon_type == "rocket"

    def test_fire_flamethrower_adds_two_projectiles(
        self, cs: CombatSystem, game: MagicMock
    ) -> None:
        cs._fire_flamethrower()
        assert game.entity_manager.add_projectile.call_count == 2

    def test_fire_freezer_adds_projectile(self, cs: CombatSystem, game: MagicMock) -> None:
        cs._fire_freezer()
        game.entity_manager.add_projectile.assert_called_once()
        proj = game.entity_manager.add_projectile.call_args[0][0]
        assert proj.weapon_type == "freezer"

    def test_fire_minigun_adds_three_projectiles(self, cs: CombatSystem, game: MagicMock) -> None:
        cs._fire_minigun()
        assert game.entity_manager.add_projectile.call_count == 3

    def test_fire_generic_projectile(self, cs: CombatSystem, game: MagicMock) -> None:
        weapon_data = {"projectile_speed": 0.5, "projectile_color": (255, 0, 0)}
        cs._fire_generic_projectile(weapon_data, "custom")
        game.entity_manager.add_projectile.assert_called_once()


class TestCheckShotHit:
    def test_no_hit_when_no_bots(self, cs: CombatSystem, game: MagicMock) -> None:
        game.bots = []
        cs.check_shot_hit()
        # No crash, no kill

    def test_hits_bot_in_range(self, cs: CombatSystem, game: MagicMock) -> None:
        bot = MagicMock()
        bot.alive = True
        bot.x = game.player.x + 1.0  # Directly in front (angle=0)
        bot.y = game.player.y
        bot.take_damage.return_value = False
        game.bots = [bot]
        game.raycaster.cast_ray.return_value = (50.0, 0, 0, 0, 0)
        # angle_offset=0.001 (non-zero) bypasses random spread
        cs.check_shot_hit(angle_offset=0.001)
        bot.take_damage.assert_called_once()

    def test_show_damage_text_on_hit(self, cs: CombatSystem, game: MagicMock) -> None:
        game.show_damage = True
        bot = MagicMock()
        bot.alive = True
        bot.x = game.player.x + 1.0
        bot.y = game.player.y
        bot.take_damage.return_value = False
        game.bots = [bot]
        game.raycaster.cast_ray.return_value = (50.0, 0, 0, 0, 0)
        cs.check_shot_hit(angle_offset=0.001)
        assert len(game.damage_texts) > 0

    def test_kill_triggers_handle_kill(self, cs: CombatSystem, game: MagicMock) -> None:
        bot = MagicMock()
        bot.alive = True
        bot.x = game.player.x + 1.0
        bot.y = game.player.y
        bot.enemy_type = "zombie"
        # _apply_damage checks `bot.alive` (not take_damage return value)
        # so we must set bot.alive=False as a side effect

        def take_dmg(dmg: int, **kw: object) -> bool:
            bot.alive = False
            return True

        bot.take_damage.side_effect = take_dmg
        game.bots = [bot]
        game.raycaster.cast_ray.return_value = (50.0, 0, 0, 0, 0)
        cs.check_shot_hit(angle_offset=0.001)
        game.sound_manager.play_sound.assert_any_call("scream")

    def test_laser_adds_particle_effect(self, cs: CombatSystem, game: MagicMock) -> None:
        game.bots = []
        cs.check_shot_hit(is_laser=True)
        game.particle_system.add_laser.assert_called_once()

    def test_secondary_delegates_to_handle_secondary(
        self, cs: CombatSystem, game: MagicMock
    ) -> None:
        game.bots = []
        with patch.object(cs, "_handle_secondary_hit") as mock_sh:
            cs.check_shot_hit(is_secondary=True)
            mock_sh.assert_called_once()

    def test_angle_offset_used_when_provided(self, cs: CombatSystem, game: MagicMock) -> None:
        game.bots = []
        # Should not crash with explicit angle_offset
        cs.check_shot_hit(angle_offset=0.1)

    def test_dead_bot_skipped(self, cs: CombatSystem, game: MagicMock) -> None:
        bot = MagicMock()
        bot.alive = False
        game.bots = [bot]
        cs.check_shot_hit()
        bot.take_damage.assert_not_called()


class TestExplosions:
    def test_explode_bomb_near_player(self, cs: CombatSystem, game: MagicMock) -> None:
        proj = MagicMock(spec=Projectile)
        proj.x = game.player.x  # Same position as player
        proj.y = game.player.y
        game.bots = []
        cs.explode_bomb(proj)
        # Should cause screen shake
        assert game.screen_shake > 0

    def test_explode_bomb_kills_nearby_bot(self, cs: CombatSystem, game: MagicMock) -> None:
        proj = MagicMock(spec=Projectile)
        proj.x = game.player.x + 50  # Far from player
        proj.y = game.player.y
        bot = MagicMock()
        bot.alive = True
        bot.x = proj.x + 0.1  # Right next to bomb
        bot.y = proj.y
        bot.take_damage.return_value = True
        game.bots = [bot]
        game.player.x = proj.x + 100  # Player far from explosion
        cs.explode_bomb(proj)
        bot.take_damage.assert_called_once()

    def test_explode_laser_hits_nearby_bots(self, cs: CombatSystem, game: MagicMock) -> None:
        bot = MagicMock()
        bot.alive = True
        bot.x = 5.0
        bot.y = 5.0
        bot.take_damage.return_value = False
        game.bots = [bot]
        # Impact right on top of the bot
        cs.explode_laser(5.0, 5.0)
        bot.take_damage.assert_called_once()

    def test_explode_laser_kills_bot(self, cs: CombatSystem, game: MagicMock) -> None:
        bot = MagicMock()
        bot.alive = True
        bot.x = 5.0
        bot.y = 5.0
        bot.take_damage.return_value = True
        game.bots = [bot]
        cs.explode_laser(5.0, 5.0)
        game.sound_manager.play_sound.assert_any_call("scream")

    def test_explode_laser_no_bots(self, cs: CombatSystem, game: MagicMock) -> None:
        game.bots = []
        cs.explode_laser(5.0, 5.0)
        # No crash, no damage texts when hits == 0
        assert game.damage_texts == []

    def test_explode_plasma(self, cs: CombatSystem, game: MagicMock) -> None:
        proj = MagicMock(spec=Projectile)
        proj.x = 5.0
        proj.y = 5.0
        proj.damage = 100
        game.bots = []
        cs.explode_plasma(proj)

    def test_explode_rocket(self, cs: CombatSystem, game: MagicMock) -> None:
        proj = MagicMock(spec=Projectile)
        proj.x = 5.0
        proj.y = 5.0
        proj.damage = 200
        game.bots = []
        cs.explode_rocket(proj)

    def test_explode_pulse(self, cs: CombatSystem, game: MagicMock) -> None:
        proj = MagicMock(spec=Projectile)
        proj.x = 5.0
        proj.y = 5.0
        proj.damage = 75
        game.bots = []
        cs.explode_pulse(proj)

    def test_explode_freezer_freezes_bot(self, cs: CombatSystem, game: MagicMock) -> None:
        proj = MagicMock(spec=Projectile)
        proj.x = 5.0
        proj.y = 5.0
        proj.damage = 50
        bot = MagicMock()
        bot.alive = True
        bot.x = 5.0
        bot.y = 5.0
        bot.take_damage.return_value = False  # Survives
        game.bots = [bot]
        cs.explode_freezer(proj)
        bot.freeze.assert_called_once_with(180)

    def test_explode_bomb_damage_text(self, cs: CombatSystem, game: MagicMock) -> None:
        proj = MagicMock(spec=Projectile)
        proj.x = game.player.x + 1000  # Far from player
        proj.y = game.player.y
        game.bots = []
        cs.explode_bomb(proj)
        assert any(t.get("text") == "BOOM!" for t in game.damage_texts)


class TestHandleSecondaryHit:
    def test_handle_secondary_with_bot(self, cs: CombatSystem, game: MagicMock) -> None:
        bot = MagicMock()
        bot.x = 5.0
        bot.y = 5.0
        with patch.object(cs, "explode_laser"):
            cs._handle_secondary_hit(bot, 2.0, 10.0)
            cs.explode_laser.assert_called_once()

    def test_handle_secondary_no_bot(self, cs: CombatSystem, game: MagicMock) -> None:
        with patch.object(cs, "explode_laser") as mock_el:
            cs._handle_secondary_hit(None, float("inf"), 10.0)
            mock_el.assert_called_once()


class TestApplyDamage:
    def test_apply_damage_kills_bot(self, cs: CombatSystem, game: MagicMock) -> None:
        bot = MagicMock()
        bot.alive = True
        bot.x = game.player.x + 1.0
        bot.y = game.player.y
        bot.enemy_type = "zombie"

        def take_dmg(dmg: int, **kw: object) -> bool:
            bot.alive = False
            return True

        bot.take_damage.side_effect = take_dmg
        cs._apply_damage(bot, 1.0, 20.0, 100, False)
        game.sound_manager.play_sound.assert_any_call("scream")

    def test_apply_damage_headshot_color(self, cs: CombatSystem, game: MagicMock) -> None:
        game.show_damage = True
        bot = MagicMock()
        bot.alive = True
        bot.x = game.player.x + 1.0
        bot.y = game.player.y
        bot.enemy_type = "zombie"
        bot.take_damage.return_value = False
        cs._apply_damage(bot, 1.0, 20.0, 100, True)
        assert len(game.damage_texts) > 0
        assert game.damage_texts[0]["text"].endswith("!")

    def test_apply_damage_ball_blood_color(self, cs: CombatSystem, game: MagicMock) -> None:
        bot = MagicMock()
        bot.alive = True
        bot.x = game.player.x + 1.0
        bot.y = game.player.y
        bot.enemy_type = "ball"
        bot.take_damage.return_value = False
        cs._apply_damage(bot, 1.0, 20.0, 50, False)
        # No crash — blood color changes for ball type

    def test_apply_damage_demon_blood_color(self, cs: CombatSystem, game: MagicMock) -> None:
        bot = MagicMock()
        bot.alive = True
        bot.x = game.player.x + 1.0
        bot.y = game.player.y
        bot.enemy_type = "demon"
        bot.take_damage.return_value = False
        cs._apply_damage(bot, 1.0, 20.0, 50, False)
        # No crash — green slime blood color for demons
