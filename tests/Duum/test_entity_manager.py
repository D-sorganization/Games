"""Tests for games.Duum.src.entity_manager."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from games.Duum.src.entity_manager import EntityManager


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
def mock_player() -> MagicMock:
    p = MagicMock()
    p.x = 5.0
    p.y = 5.0
    p.health = 100
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


@pytest.fixture()
def mock_map() -> MagicMock:
    return MagicMock()


class TestDuumEntityManagerInit:
    def test_init_empty(self, em: EntityManager) -> None:
        assert em.bots == []
        assert em.projectiles == []

    def test_reset_clears(self, em: EntityManager, mock_bot: MagicMock) -> None:
        em.bots.append(mock_bot)
        em.projectiles.append(MagicMock())
        em.reset()
        assert em.bots == []
        assert em.projectiles == []


class TestDuumEntityManagerCRUD:
    def test_add_bot(self, em: EntityManager, mock_bot: MagicMock) -> None:
        em.add_bot(mock_bot)
        assert mock_bot in em.bots

    def test_add_projectile(self, em: EntityManager) -> None:
        proj = MagicMock()
        em.add_projectile(proj)
        assert proj in em.projectiles

    def test_cleanup_dead_bots(self, em: EntityManager, mock_bot: MagicMock) -> None:
        dead = MagicMock()
        dead.removed = True
        em.bots = [mock_bot, dead]
        em.cleanup_dead_bots()
        assert dead not in em.bots
        assert mock_bot in em.bots

    def test_get_active_enemies_excludes_items(self, em: EntityManager) -> None:
        enemy = MagicMock()
        enemy.alive = True
        enemy.type_data = {"visual_style": "enemy"}
        item = MagicMock()
        item.alive = True
        item.type_data = {"visual_style": "item"}
        em.bots = [enemy, item]
        result = em.get_active_enemies()
        assert enemy in result
        assert item not in result


class TestDuumEntityManagerUpdateBots:
    def test_update_collects_projectile(
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

    def test_update_no_projectile(
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


class TestDuumEntityManagerUpdateProjectiles:
    def test_enemy_proj_hits_player(
        self,
        em: EntityManager,
        mock_player: MagicMock,
        mock_map: MagicMock,
        mock_game: MagicMock,
    ) -> None:
        proj = MagicMock()
        proj.alive = True
        proj.is_player = False
        proj.x = mock_player.x
        proj.y = mock_player.y
        proj.damage = 20
        proj.update.return_value = None
        em.projectiles = [proj]
        em.update_projectiles(mock_map, mock_player, mock_game)
        mock_player.take_damage.assert_called_with(20)

    def test_player_proj_kills_bot(
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
        mock_bot.take_damage.return_value = True
        em.bots = [mock_bot]
        em.projectiles = [proj]
        em.spatial_grid.get_nearby = MagicMock(return_value=[mock_bot])
        em.update_projectiles(mock_map, mock_player, mock_game)
        mock_game.sound_manager.play_sound.assert_called_with("scream")

    def test_plasma_explosion_on_wall(
        self,
        em: EntityManager,
        mock_player: MagicMock,
        mock_map: MagicMock,
        mock_game: MagicMock,
    ) -> None:
        proj = MagicMock()
        proj.alive = True
        proj.weapon_type = "plasma"
        proj.x = 99.0
        proj.y = 99.0

        def kill(m: object) -> None:
            proj.alive = False

        proj.update = kill
        em.projectiles = [proj]
        em.update_projectiles(mock_map, mock_player, mock_game)
        mock_game.explode_plasma.assert_called_once_with(proj)

    def test_rocket_explosion_on_wall(
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

        def kill(m: object) -> None:
            proj.alive = False

        proj.update = kill
        em.projectiles = [proj]
        em.update_projectiles(mock_map, mock_player, mock_game)
        mock_game.explode_rocket.assert_called_once_with(proj)

    def test_dead_projs_cleaned(
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
