"""Tests for games.Zombie_Survival.src.entity_manager."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from games.Zombie_Survival.src.entity_manager import EntityManager


@pytest.fixture()
def em() -> EntityManager:
    return EntityManager()


@pytest.fixture()
def mock_bot() -> MagicMock:
    bot = MagicMock()
    bot.alive = True
    bot.removed = False
    bot.x = 3.0
    bot.y = 3.0
    bot.type_data = {"visual_style": "enemy"}
    return bot


@pytest.fixture()
def mock_map() -> MagicMock:
    m = MagicMock()
    m.grid = [[0] * 10 for _ in range(10)]
    m.width = 10
    m.height = 10
    return m


@pytest.fixture()
def mock_player() -> MagicMock:
    p = MagicMock()
    p.x = 5.0
    p.y = 5.0
    p.health = 100
    p.shield_active = False
    p.god_mode = False
    return p


@pytest.fixture()
def mock_game() -> MagicMock:
    g = MagicMock()
    g.kills = 0
    g.kill_combo_count = 0
    g.kill_combo_timer = 0
    g.last_death_pos = (0, 0)
    g.damage_flash_timer = 0
    return g


class TestEntityManagerInit:
    def test_init_empty(self, em: EntityManager) -> None:
        assert em.bots == []
        assert em.projectiles == []

    def test_reset_clears_entities(self, em: EntityManager, mock_bot: MagicMock) -> None:
        em.bots.append(mock_bot)
        proj = MagicMock()
        em.projectiles.append(proj)
        em.reset()
        assert em.bots == []
        assert em.projectiles == []


class TestEntityManagerAddRemove:
    def test_add_bot(self, em: EntityManager, mock_bot: MagicMock) -> None:
        em.add_bot(mock_bot)
        assert mock_bot in em.bots

    def test_add_projectile(self, em: EntityManager) -> None:
        proj = MagicMock()
        em.add_projectile(proj)
        assert proj in em.projectiles

    def test_cleanup_dead_bots(self, em: EntityManager, mock_bot: MagicMock) -> None:
        dead_bot = MagicMock()
        dead_bot.removed = True
        em.bots = [mock_bot, dead_bot]
        em.cleanup_dead_bots()
        assert dead_bot not in em.bots
        assert mock_bot in em.bots


class TestEntityManagerGetActive:
    def test_get_active_enemies_excludes_items(self, em: EntityManager) -> None:
        enemy = MagicMock()
        enemy.alive = True
        enemy.type_data = {"visual_style": "enemy"}
        item = MagicMock()
        item.alive = True
        item.type_data = {"visual_style": "item"}
        dead = MagicMock()
        dead.alive = False
        dead.type_data = {"visual_style": "enemy"}
        em.bots = [enemy, item, dead]
        result = em.get_active_enemies()
        assert enemy in result
        assert item not in result
        assert dead not in result


class TestEntityManagerUpdateBots:
    def test_update_bots_collects_projectiles(
        self,
        em: EntityManager,
        mock_bot: MagicMock,
        mock_map: MagicMock,
        mock_player: MagicMock,
        mock_game: MagicMock,
    ) -> None:
        proj = MagicMock()
        mock_bot.update.return_value = proj
        em.bots = [mock_bot]
        em.update_bots(mock_map, mock_player, mock_game)
        assert proj in em.projectiles
        mock_game.sound_manager.play_sound.assert_called_with("enemy_shoot")

    def test_update_bots_no_projectile(
        self,
        em: EntityManager,
        mock_bot: MagicMock,
        mock_map: MagicMock,
        mock_player: MagicMock,
        mock_game: MagicMock,
    ) -> None:
        mock_bot.update.return_value = None
        em.bots = [mock_bot]
        em.update_bots(mock_map, mock_player, mock_game)
        assert em.projectiles == []


class TestEntityManagerUpdateProjectiles:
    def test_enemy_projectile_hits_player(
        self,
        em: EntityManager,
        mock_player: MagicMock,
        mock_map: MagicMock,
        mock_game: MagicMock,
    ) -> None:
        proj = MagicMock()
        proj.alive = True
        proj.is_player = False
        proj.x = mock_player.x  # Same position as player -> hits
        proj.y = mock_player.y
        proj.damage = 25
        proj.weapon_type = "normal"
        proj.update.return_value = None
        em.projectiles = [proj]
        em.update_projectiles(mock_map, mock_player, mock_game)
        mock_player.take_damage.assert_called_with(25)

    def test_enemy_projectile_misses_player(
        self,
        em: EntityManager,
        mock_player: MagicMock,
        mock_map: MagicMock,
        mock_game: MagicMock,
    ) -> None:
        proj = MagicMock()
        proj.alive = True
        proj.is_player = False
        proj.x = 0.0  # Far from player at (5, 5)
        proj.y = 0.0
        proj.damage = 25
        proj.update.return_value = None
        em.projectiles = [proj]
        em.update_projectiles(mock_map, mock_player, mock_game)
        mock_player.take_damage.assert_not_called()

    def test_player_projectile_kills_bot(
        self,
        em: EntityManager,
        mock_bot: MagicMock,
        mock_player: MagicMock,
        mock_map: MagicMock,
        mock_game: MagicMock,
    ) -> None:
        proj = MagicMock()
        proj.alive = True
        proj.is_player = True
        proj.x = mock_bot.x
        proj.y = mock_bot.y
        proj.damage = 999
        proj.weapon_type = "normal"
        proj.update.return_value = None
        mock_bot.take_damage.return_value = True  # Bot dies
        em.bots = [mock_bot]
        em.projectiles = [proj]
        # Patch spatial grid so nearby bots are returned
        em.spatial_grid.get_nearby = MagicMock(return_value=[mock_bot])
        em.update_projectiles(mock_map, mock_player, mock_game)
        mock_game.sound_manager.play_sound.assert_called_with("scream")
        assert mock_game.kills == 1

    def test_player_projectile_hits_bot_not_killed(
        self,
        em: EntityManager,
        mock_bot: MagicMock,
        mock_player: MagicMock,
        mock_map: MagicMock,
        mock_game: MagicMock,
    ) -> None:
        proj = MagicMock()
        proj.alive = True
        proj.is_player = True
        proj.x = mock_bot.x
        proj.y = mock_bot.y
        proj.damage = 10
        proj.weapon_type = "normal"
        proj.update.return_value = None
        mock_bot.take_damage.return_value = False  # Bot survives
        em.bots = [mock_bot]
        em.projectiles = [proj]
        em.spatial_grid.get_nearby = MagicMock(return_value=[mock_bot])
        em.update_projectiles(mock_map, mock_player, mock_game)
        assert mock_game.kills == 0

    def test_plasma_projectile_explodes_on_death(
        self,
        em: EntityManager,
        mock_player: MagicMock,
        mock_map: MagicMock,
        mock_game: MagicMock,
    ) -> None:
        proj = MagicMock()
        proj.alive = False  # Already dead when we check was_alive->not alive
        proj.is_player = True
        proj.x = 99.0  # Far from anything
        proj.y = 99.0
        proj.weapon_type = "plasma"
        # was_alive=True, then proj.alive becomes False after update
        # Simulate: on entry alive=True, update sets alive=False
        call_count = [0]

        def side_effect(game_map: object) -> None:
            call_count[0] += 1
            proj.alive = False

        proj.alive = True  # Start alive
        proj.update = side_effect
        em.projectiles = [proj]
        em.update_projectiles(mock_map, mock_player, mock_game)
        mock_game.explode_plasma.assert_called_once_with(proj)

    def test_rocket_projectile_explodes_on_death(
        self,
        em: EntityManager,
        mock_player: MagicMock,
        mock_map: MagicMock,
        mock_game: MagicMock,
    ) -> None:
        proj = MagicMock()
        proj.alive = True
        proj.weapon_type = "rocket"
        proj.x = 99.0
        proj.y = 99.0

        def kill_proj(game_map: object) -> None:
            proj.alive = False

        proj.update = kill_proj
        em.projectiles = [proj]
        em.update_projectiles(mock_map, mock_player, mock_game)
        mock_game.explode_rocket.assert_called_once_with(proj)

    def test_dead_projectiles_removed(
        self,
        em: EntityManager,
        mock_player: MagicMock,
        mock_map: MagicMock,
        mock_game: MagicMock,
    ) -> None:
        proj = MagicMock()
        proj.alive = False
        proj.update.return_value = None
        em.projectiles = [proj]
        em.update_projectiles(mock_map, mock_player, mock_game)
        assert proj not in em.projectiles

    def test_player_projectile_plasma_on_bot_hit(
        self,
        em: EntityManager,
        mock_bot: MagicMock,
        mock_player: MagicMock,
        mock_map: MagicMock,
        mock_game: MagicMock,
    ) -> None:
        """Plasma projectile triggers explode_plasma when it hits a bot."""
        proj = MagicMock()
        proj.alive = True
        proj.is_player = True
        proj.x = mock_bot.x
        proj.y = mock_bot.y
        proj.damage = 10
        proj.weapon_type = "plasma"
        proj.update.return_value = None
        mock_bot.take_damage.return_value = False
        em.bots = [mock_bot]
        em.projectiles = [proj]
        em.spatial_grid.get_nearby = MagicMock(return_value=[mock_bot])
        em.update_projectiles(mock_map, mock_player, mock_game)
        mock_game.explode_plasma.assert_called()
