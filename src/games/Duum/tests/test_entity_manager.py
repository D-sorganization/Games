import unittest

from src.bot import Bot
from src.entity_manager import EntityManager


class TestEntityManager(unittest.TestCase):
    """Tests for the EntityManager class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.em = EntityManager()
        self.em.grid_cell_size = 5

    def test_add_bot(self) -> None:
        """Test adding a bot to the manager."""
        bot = Bot(10.0, 10.0, 1)
        self.em.add_bot(bot)
        assert len(self.em.bots) == 1
        assert bot in self.em.bots

    def test_spatial_grid_update(self) -> None:
        """Test that the spatial grid updates correctly."""
        bot1 = Bot(2.0, 2.0, 1)  # Cell 0,0
        bot2 = Bot(7.0, 2.0, 1)  # Cell 1,0
        self.em.add_bot(bot1)
        self.em.add_bot(bot2)

        self.em._update_spatial_grid()

        assert len(self.em.spatial_grid.cells[(0, 0)]) == 1
        assert self.em.spatial_grid.cells[(0, 0)][0] == bot1

        assert len(self.em.spatial_grid.cells[(1, 0)]) == 1
        assert self.em.spatial_grid.cells[(1, 0)][0] == bot2

    def test_get_nearby_bots(self) -> None:
        """Test retrieving nearby bots."""
        # Bot at 5,5 (Cell 1,1)
        # Nearby should include cells 0,0 to 2,2
        bot_center = Bot(5.5, 5.5, 1)

        # Bot at 20,20 (Cell 4,4) - Far
        bot_far = Bot(20.0, 20.0, 1)

        self.em.add_bot(bot_center)
        self.em.add_bot(bot_far)
        self.em._update_spatial_grid()

        nearby = self.em.get_nearby_bots(5.0, 5.0)
        assert bot_center in nearby
        assert bot_far not in nearby

    def test_reset(self) -> None:
        """Test resetting the entity manager."""
        self.em.add_bot(Bot(10.0, 10.0, 1))
        from src.projectile import Projectile

        proj = Projectile(10.0, 10.0, 0.0, 10.0, 10, True, "plasma")
        self.em.add_projectile(proj)
        self.em._update_spatial_grid()
        self.em.reset()
        assert not self.em.bots
        assert not self.em.projectiles
        assert not self.em.spatial_grid.cells

    def test_update_bots(self) -> None:
        """Test updating bots generating projectiles."""
        import unittest.mock

        game_map = unittest.mock.MagicMock()
        player = unittest.mock.MagicMock()
        game = unittest.mock.MagicMock()

        bot = Bot(10.0, 10.0, 1)
        from src.projectile import Projectile

        new_proj = Projectile(10.0, 10.0, 0.0, 10.0, 10, False, "plasma")
        # Mock bot.update to return a projectile
        with unittest.mock.patch.object(bot, "update", return_value=new_proj):
            self.em.add_bot(bot)
            self.em.update_bots(game_map, player, game)

            assert len(self.em.projectiles) == 1
            assert self.em.projectiles[0] == new_proj
            game.sound_manager.play_sound.assert_called_with("enemy_shoot")

    def test_update_projectiles_enemy_hit_player(self) -> None:
        """Test enemy projectile hitting the player."""
        import unittest.mock

        game_map = unittest.mock.MagicMock()
        game_map.is_wall.return_value = False
        player = unittest.mock.MagicMock()
        game = unittest.mock.MagicMock()
        game.damage_flash_timer = 0

        player.x, player.y = 5.0, 5.0
        player.health = 100

        def fake_take_damage(dmg: int) -> None:
            player.health -= dmg

        player.take_damage.side_effect = fake_take_damage

        from src.projectile import Projectile

        proj = Projectile(
            x=5.1,
            y=5.1,
            angle=0.0,
            speed=0.01,
            damage=20,
            is_player=False,
            weapon_type="plasma",
        )
        self.em.add_projectile(proj)
        self.em.update_projectiles(game_map, player, game)

        assert not proj.alive
        assert player.health == 80
        assert game.damage_flash_timer == 10
        game.sound_manager.play_sound.assert_called_with("oww")

    def test_update_projectiles_enemy_hit_player_invulnerable(self) -> None:
        """Test enemy projectile hitting invulnerable player."""
        import unittest.mock

        game_map = unittest.mock.MagicMock()
        game_map.is_wall.return_value = False
        player = unittest.mock.MagicMock()
        player.x, player.y = 5.0, 5.0
        player.health = 100

        def fake_take_damage(dmg: int) -> None:
            pass

        player.take_damage.side_effect = fake_take_damage
        game = unittest.mock.MagicMock()
        game.damage_flash_timer = 0

        from src.projectile import Projectile

        proj = Projectile(
            x=5.1,
            y=5.1,
            angle=0.0,
            speed=0.01,
            damage=20,
            is_player=False,
            weapon_type="plasma",
        )
        self.em.add_projectile(proj)
        self.em.update_projectiles(game_map, player, game)

        assert game.damage_flash_timer == 0
        assert not proj.alive

    def test_update_projectiles_player_hit_enemy(self) -> None:
        """Test player projectile hitting an enemy bot."""
        import unittest.mock

        game_map = unittest.mock.MagicMock()
        game_map.is_wall.return_value = False
        player = unittest.mock.MagicMock()
        game = unittest.mock.MagicMock()
        game.kills = 0
        game.kill_combo_count = 0
        bot = Bot(5.1, 5.1, 1)
        # Mock take_damage to return True (bot killed)
        with unittest.mock.patch.object(bot, "take_damage", return_value=True):
            self.em.add_bot(bot)
            self.em._update_spatial_grid()

            from src.projectile import Projectile

            proj = Projectile(
                x=5.2,
                y=5.2,
                angle=0.0,
                speed=0.01,
                damage=20,
                is_player=True,
                weapon_type="rocket",
            )
            self.em.add_projectile(proj)

            self.em.update_projectiles(game_map, player, game)

            game.sound_manager.play_sound.assert_called_with("scream")
            assert game.kills == 1
            assert game.kill_combo_count == 1
            assert not proj.alive
            game.explode_rocket.assert_called_with(proj)

    def test_cleanup_dead_bots(self) -> None:
        """Test removing bots that have been completely removed visually."""
        bot1 = Bot(1.0, 1.0, 1)
        bot1.removed = True
        bot2 = Bot(2.0, 2.0, 1)

        self.em.add_bot(bot1)
        self.em.add_bot(bot2)
        self.em.cleanup_dead_bots()
        assert len(self.em.bots) == 1
        assert self.em.bots[0] == bot2

    def test_get_active_enemies(self) -> None:
        """Test active enemies fetching, excluding items and dead bots."""
        bot1 = Bot(1.0, 1.0, 1)
        bot1.alive = False

        bot2 = Bot(2.0, 2.0, 1)
        bot2.type_data = {"visual_style": "item"}

        bot3 = Bot(3.0, 3.0, 1, enemy_type="ninja")

        self.em.add_bot(bot1)
        self.em.add_bot(bot2)
        self.em.add_bot(bot3)

        active = self.em.get_active_enemies()
        assert len(active) == 1
        assert active[0] == bot3

    def test_update_projectiles_hit_wall(self) -> None:
        """Test projectile hitting a wall explodes depending on type."""
        import unittest.mock

        game_map = unittest.mock.MagicMock()
        game_map.is_wall.return_value = True
        player = unittest.mock.MagicMock()
        game = unittest.mock.MagicMock()

        from src.projectile import Projectile

        proj_plasma = Projectile(
            x=5.1,
            y=5.1,
            angle=0.0,
            speed=10.0,
            damage=20,
            is_player=True,
            weapon_type="plasma",
        )
        proj_rocket = Projectile(
            x=5.2,
            y=5.2,
            angle=0.0,
            speed=10.0,
            damage=20,
            is_player=True,
            weapon_type="rocket",
        )

        self.em.add_projectile(proj_plasma)
        self.em.add_projectile(proj_rocket)
        self.em.update_projectiles(game_map, player, game)

        assert not proj_plasma.alive
        assert not proj_rocket.alive
        game.explode_plasma.assert_called_with(proj_plasma)
        game.explode_rocket.assert_called_with(proj_rocket)

    def test_update_projectiles_player_hit_enemy_but_not_dead(self) -> None:
        """Test player projectile hitting an enemy bot but not killing it."""
        import unittest.mock

        game_map = unittest.mock.MagicMock()
        game_map.is_wall.return_value = False
        player = unittest.mock.MagicMock()
        game = unittest.mock.MagicMock()
        game.kills = 0

        bot = Bot(5.1, 5.1, 1)
        # Mock take_damage to return False (bot NOT killed)
        with unittest.mock.patch.object(bot, "take_damage", return_value=False):
            self.em.add_bot(bot)
            self.em._update_spatial_grid()

            from src.projectile import Projectile

            proj = Projectile(
                x=5.2,
                y=5.2,
                angle=0.0,
                speed=0.01,
                damage=20,
                is_player=True,
                weapon_type="rocket",
            )
            self.em.add_projectile(proj)

            self.em.update_projectiles(game_map, player, game)

            assert game.kills == 0
            assert not proj.alive
            game.explode_rocket.assert_called_with(proj)

    def test_update_projectiles_player_misses(self) -> None:
        import unittest.mock

        game_map = unittest.mock.MagicMock()
        game_map.is_wall.return_value = False
        player = unittest.mock.MagicMock()
        game = unittest.mock.MagicMock()

        from src.projectile import Projectile

        proj = Projectile(
            x=5.2,
            y=5.2,
            angle=0.0,
            speed=0.01,
            damage=20,
            is_player=True,
            weapon_type="normal",
        )
        self.em.add_projectile(proj)
        self.em.update_projectiles(game_map, player, game)
        assert proj.alive

    def test_update_projectiles_enemy_misses(self) -> None:
        import unittest.mock

        game_map = unittest.mock.MagicMock()
        game_map.is_wall.return_value = False
        player = unittest.mock.MagicMock()
        player.x, player.y = 100.0, 100.0
        game = unittest.mock.MagicMock()

        from src.projectile import Projectile

        proj = Projectile(
            x=5.1,
            y=5.1,
            angle=0.0,
            speed=0.01,
            damage=20,
            is_player=False,
            weapon_type="plasma",
        )
        self.em.add_projectile(proj)
        self.em.update_projectiles(game_map, player, game)
        assert proj.alive

    def test_update_projectiles_with_dead_bot(self) -> None:
        import unittest.mock

        game_map = unittest.mock.MagicMock()
        game_map.is_wall.return_value = False
        player = unittest.mock.MagicMock()
        game = unittest.mock.MagicMock()

        bot = Bot(5.1, 5.1, 1)
        bot.alive = False
        self.em.add_bot(bot)
        self.em._update_spatial_grid()

        from src.projectile import Projectile

        proj = Projectile(
            x=5.1,
            y=5.1,
            angle=0.0,
            speed=0.01,
            damage=20,
            is_player=True,
            weapon_type="normal",
        )
        self.em.add_projectile(proj)
        self.em.update_projectiles(game_map, player, game)

        assert proj.alive


if __name__ == "__main__":
    unittest.main()
