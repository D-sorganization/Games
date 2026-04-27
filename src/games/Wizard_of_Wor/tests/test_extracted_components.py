"""Tests for extracted SRP components: RenderMixin, AudioMixin, CollisionManager.

Follows TDD: RED -> GREEN -> REFACTOR.

These tests verify that the extracted classes behave correctly in isolation
and that the WizardOfWorGame integration still works after decomposition.
"""

import unittest
from unittest.mock import MagicMock, patch

import pygame
from wizard_of_wor.audio_mixin import AudioMixin, SoundBoard
from wizard_of_wor.bullet import Bullet
from wizard_of_wor.collision_manager import CollisionManager
from wizard_of_wor.enemy import Burwor
from wizard_of_wor.player import Player

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakeEnemy:
    """Minimal enemy stub for collision tests."""

    def __init__(self, x: float, y: float, alive: bool = True) -> None:
        """Set up a fake enemy at (x, y)."""
        self.x = x
        self.y = y
        self.alive = alive
        self.color = (255, 0, 0)
        self.rect = pygame.Rect(int(x) - 12, int(y) - 12, 24, 24)
        self._damage_taken = False

    def take_damage(self) -> int:
        """Return score points and mark as dead."""
        self._damage_taken = True
        self.alive = False
        return 100


class _FakeSpatialGrid:
    """Spatial grid stub that returns all registered objects as 'nearby'."""

    def __init__(self) -> None:
        """Initialise empty grid."""
        self._objects: list = []

    def update(self, objects: list) -> None:
        """Replace registered objects."""
        self._objects = list(objects)

    def get_nearby(self, x: float, y: float) -> list:
        """Return all objects regardless of position."""
        return list(self._objects)


# ---------------------------------------------------------------------------
# SoundBoard tests
# ---------------------------------------------------------------------------


class TestSoundBoard(unittest.TestCase):
    """Tests for SoundBoard (audio_mixin module)."""

    def setUp(self) -> None:
        """Init pygame so mixer operations are safe."""
        pygame.init()

    def tearDown(self) -> None:
        """Shut down pygame."""
        pygame.quit()

    def test_play_unknown_name_does_not_raise(self) -> None:
        """Playing an unknown sound name must be a no-op."""
        sb = SoundBoard()
        sb.play("nonexistent_sound")  # Must not raise

    def test_play_intro_does_not_raise(self) -> None:
        """play_intro must not raise even in headless mode."""
        sb = SoundBoard()
        sb.play_intro()  # Must not raise

    def test_sounds_dict_populated_when_enabled(self) -> None:
        """When the mixer initialised successfully, all expected keys exist."""
        sb = SoundBoard()
        if sb.enabled:
            for key in ("shot", "enemy_hit", "player_hit", "spawn", "wizard"):
                self.assertIn(key, sb.sounds)

    def test_sounds_dict_empty_when_disabled(self) -> None:
        """When the mixer is not available, sounds dict is empty."""
        with (
            patch("pygame.mixer.get_init", return_value=False),
            patch("pygame.mixer.init", side_effect=pygame.error("no audio")),
        ):
            sb = SoundBoard()
            self.assertFalse(sb.enabled)
            self.assertEqual(sb.sounds, {})


# ---------------------------------------------------------------------------
# AudioMixin tests
# ---------------------------------------------------------------------------


class _ConcreteAudio(AudioMixin):
    """Minimal concrete class that satisfies AudioMixin's preconditions."""

    def __init__(self) -> None:
        """Set up a mock soundboard."""
        self.soundboard = MagicMock(spec=SoundBoard)


class TestAudioMixin(unittest.TestCase):
    """Tests for AudioMixin helper methods."""

    def setUp(self) -> None:
        """Init pygame."""
        pygame.init()
        self.audio = _ConcreteAudio()

    def tearDown(self) -> None:
        """Shut down pygame."""
        pygame.quit()

    def test_audio_play_spawn_delegates(self) -> None:
        """_audio_play_spawn must call soundboard.play('spawn')."""
        self.audio._audio_play_spawn()
        self.audio.soundboard.play.assert_called_once_with("spawn")

    def test_audio_play_wizard_delegates(self) -> None:
        """_audio_play_wizard must call soundboard.play('wizard')."""
        self.audio._audio_play_wizard()
        self.audio.soundboard.play.assert_called_once_with("wizard")

    def test_audio_play_shot_delegates(self) -> None:
        """_audio_play_shot must call soundboard.play('shot')."""
        self.audio._audio_play_shot()
        self.audio.soundboard.play.assert_called_once_with("shot")

    def test_audio_play_enemy_hit_delegates(self) -> None:
        """_audio_play_enemy_hit must call soundboard.play('enemy_hit')."""
        self.audio._audio_play_enemy_hit()
        self.audio.soundboard.play.assert_called_once_with("enemy_hit")

    def test_audio_play_player_hit_delegates(self) -> None:
        """_audio_play_player_hit must call soundboard.play('player_hit')."""
        self.audio._audio_play_player_hit()
        self.audio.soundboard.play.assert_called_once_with("player_hit")

    def test_audio_play_intro_delegates(self) -> None:
        """_audio_play_intro must call soundboard.play_intro()."""
        self.audio._audio_play_intro()
        self.audio.soundboard.play_intro.assert_called_once()


# ---------------------------------------------------------------------------
# CollisionManager tests
# ---------------------------------------------------------------------------


class TestCollisionManager(unittest.TestCase):
    """Tests for CollisionManager in isolation."""

    def setUp(self) -> None:
        """Init pygame and set up wiring."""
        pygame.init()
        self.grid = _FakeSpatialGrid()
        self.score_added: list[int] = []
        self.player_hit_count = 0
        self.audio_enemy_count = 0
        self.audio_player_count = 0

        self.manager = CollisionManager(
            enemy_grid=self.grid,  # type: ignore[arg-type]
            on_enemy_hit=lambda pts: self.score_added.append(pts),
            on_player_hit=lambda: setattr(
                self, "player_hit_count", self.player_hit_count + 1
            ),
            on_audio_enemy_hit=lambda: setattr(
                self, "audio_enemy_count", self.audio_enemy_count + 1
            ),
            on_audio_player_hit=lambda: setattr(
                self, "audio_player_count", self.audio_player_count + 1
            ),
        )

    def tearDown(self) -> None:
        """Shut down pygame."""
        pygame.quit()

    def _make_player(self, x: float = 200, y: float = 200) -> Player:
        """Return a Player at (x, y) with no shield."""
        p = Player(x, y)
        p.invulnerable_timer = 0
        return p

    # -- player bullet hits enemy --

    def test_player_bullet_kills_enemy(self) -> None:
        """A player bullet overlapping an enemy should deactivate and score."""
        enemy = _FakeEnemy(300, 300)
        bullet = Bullet(enemy.x, enemy.y, (1, 0), is_player_bullet=True)
        effects: list = []

        remaining = self.manager.check([bullet], [enemy], None, effects)

        self.assertFalse(bullet.active)
        self.assertFalse(enemy.alive)
        self.assertNotIn(bullet, remaining)
        self.assertEqual(self.score_added, [100])
        self.assertEqual(self.audio_enemy_count, 1)

    def test_player_bullet_miss_leaves_enemy_alive(self) -> None:
        """A player bullet far from the enemy should not hit it."""
        enemy = _FakeEnemy(300, 300)
        bullet = Bullet(0, 0, (1, 0), is_player_bullet=True)
        # Make the fake grid return empty for remote bullets
        self.grid._objects = []
        effects: list = []

        self.manager.check([bullet], [enemy], None, effects)

        self.assertTrue(bullet.active)
        self.assertTrue(enemy.alive)
        self.assertEqual(self.score_added, [])

    # -- enemy bullet hits player --

    def test_enemy_bullet_damages_player(self) -> None:
        """An enemy bullet overlapping the player should deactivate and wound."""
        player = self._make_player(200, 200)
        bullet = Bullet(player.x, player.y, (1, 0), is_player_bullet=False)
        effects: list = []

        remaining = self.manager.check([bullet], [], player, effects)

        self.assertFalse(bullet.active)
        self.assertFalse(player.alive)
        self.assertNotIn(bullet, remaining)
        self.assertEqual(self.audio_player_count, 1)
        self.assertEqual(self.player_hit_count, 1)

    def test_enemy_bullet_misses_player(self) -> None:
        """An enemy bullet far from the player must not damage it."""
        player = self._make_player(200, 200)
        bullet = Bullet(999, 999, (1, 0), is_player_bullet=False)
        effects: list = []

        self.manager.check([bullet], [], player, effects)

        self.assertTrue(bullet.active)
        self.assertTrue(player.alive)
        self.assertEqual(self.player_hit_count, 0)

    # -- player body contact with enemy --

    def test_player_body_contact_damages_player(self) -> None:
        """Player standing on an enemy should take damage."""
        player = self._make_player(300, 300)
        enemy = _FakeEnemy(player.x, player.y)
        effects: list = []

        self.manager.check([], [enemy], player, effects)

        self.assertFalse(player.alive)
        self.assertEqual(self.audio_player_count, 1)

    def test_dead_enemy_does_not_harm_player(self) -> None:
        """A dead enemy's bounding box must not damage the player."""
        player = self._make_player(300, 300)
        enemy = _FakeEnemy(player.x, player.y, alive=False)
        effects: list = []

        self.manager.check([], [enemy], player, effects)

        self.assertTrue(player.alive)

    # -- no player edge case --

    def test_no_player_does_not_crash(self) -> None:
        """check() must run cleanly when player is None."""
        enemy = _FakeEnemy(300, 300)
        bullet = Bullet(enemy.x, enemy.y, (1, 0), is_player_bullet=True)
        effects: list = []

        remaining = self.manager.check([bullet], [enemy], None, effects)

        self.assertNotIn(bullet, remaining)

    # -- multiple bullets removed in one pass --

    def test_multiple_bullets_all_removed(self) -> None:
        """All bullets that hit in the same frame must be removed once."""
        enemy1 = _FakeEnemy(300, 300)
        enemy2 = _FakeEnemy(400, 400)
        b1 = Bullet(enemy1.x, enemy1.y, (1, 0), is_player_bullet=True)
        b2 = Bullet(enemy2.x, enemy2.y, (1, 0), is_player_bullet=True)
        effects: list = []

        remaining = self.manager.check([b1, b2], [enemy1, enemy2], None, effects)

        self.assertNotIn(b1, remaining)
        self.assertNotIn(b2, remaining)
        self.assertFalse(enemy1.alive)
        self.assertFalse(enemy2.alive)

    # -- spatial grid integration --

    def test_spatial_grid_rebuilt_each_call(self) -> None:
        """CollisionManager must call grid.update() on every check()."""
        update_calls: list = []
        original_update = self.grid.update

        def counting_update(objs: list) -> None:
            update_calls.append(len(objs))
            original_update(objs)

        self.grid.update = counting_update  # type: ignore[method-assign, assignment]

        enemy = _FakeEnemy(300, 300)
        self.manager.check([], [enemy], None, [])
        self.manager.check([], [], None, [])

        self.assertEqual(len(update_calls), 2)
        self.assertEqual(update_calls[0], 1)  # 1 alive enemy
        self.assertEqual(update_calls[1], 0)  # 0 alive enemies

    # -- _enemy_grid attribute (inherited from WizardOfWorGame)

    def test_game_exposes_enemy_grid(self) -> None:
        """WizardOfWorGame must expose _enemy_grid as a SpatialGrid instance."""
        from wizard_of_wor.game import WizardOfWorGame

        from games.shared.spatial_grid import SpatialGrid

        with patch("pygame.mixer.init"), patch("pygame.mixer.Sound"):
            game = WizardOfWorGame()

        self.assertIsInstance(game._enemy_grid, SpatialGrid)


# ---------------------------------------------------------------------------
# Integration: WizardOfWorGame still works with extracted components
# ---------------------------------------------------------------------------


class TestGameIntegration(unittest.TestCase):
    """Smoke tests confirming the refactored game still passes original checks."""

    def setUp(self) -> None:
        """Set up a headless game instance."""
        pygame.init()
        with patch("pygame.mixer.init"), patch("pygame.mixer.Sound"):
            from wizard_of_wor.game import WizardOfWorGame

            self.game = WizardOfWorGame()

    def tearDown(self) -> None:
        """Shut down pygame."""
        pygame.quit()

    def test_check_collisions_player_bullet_hits_enemy(self) -> None:
        """Player bullet on enemy deactivates bullet and scores points."""
        enemy = self.game.enemies[0]
        bullet = Bullet(enemy.x, enemy.y, (1, 0), is_player_bullet=True)
        self.game.bullets.append(bullet)
        initial_score = self.game.score

        self.game.check_collisions()

        self.assertFalse(bullet.active)
        self.assertFalse(enemy.alive)
        self.assertGreater(self.game.score, initial_score)

    def test_check_collisions_enemy_bullet_hits_player(self) -> None:
        """Enemy bullet on player kills the player."""
        self.game.player.invulnerable_timer = 0  # type: ignore[union-attr]
        bullet = Bullet(
            self.game.player.x,  # type: ignore[union-attr]
            self.game.player.y,  # type: ignore[union-attr]
            (1, 0),
            is_player_bullet=False,
        )
        self.game.bullets.append(bullet)

        self.game.check_collisions()

        self.assertFalse(bullet.active)
        self.assertFalse(self.game.player.alive)  # type: ignore[union-attr]

    def test_soundboard_accessible(self) -> None:
        """After refactor, game.soundboard must still exist."""
        self.assertIsNotNone(self.game.soundboard)
        # Use type name check to avoid module identity issues from sys.path
        self.assertEqual(type(self.game.soundboard).__name__, "SoundBoard")

    def test_render_mixin_methods_exist(self) -> None:
        """Key draw methods must be present (provided by RenderMixin)."""
        for method in ("draw", "draw_game", "draw_menu", "draw_ui", "draw_paused"):
            self.assertTrue(
                callable(getattr(self.game, method, None)),
                f"{method} not found on game",
            )

    def test_collision_manager_attribute_exists(self) -> None:
        """WizardOfWorGame must expose _collision_manager."""
        # Use type name to avoid module identity issues from conftest sys.path
        self.assertEqual(
            type(self.game._collision_manager).__name__, "CollisionManager"
        )

    def test_game_init_starts_playing(self) -> None:
        """Game should start in 'playing' state with enemies present."""
        self.assertEqual(self.game.state, "playing")
        self.assertGreater(len(self.game.enemies), 0)
        self.assertIsNotNone(self.game.player)

    def test_spawn_fallback_still_works(self) -> None:
        """_spawn_enemy fallback to corners must still function."""
        initial_count = len(self.game.enemies)
        with patch.object(
            self.game.dungeon,
            "get_random_spawn_position",
            return_value=(self.game.player.x, self.game.player.y),  # type: ignore[union-attr]
        ):
            self.game._spawn_enemy(Burwor)

        # A new enemy was added without raising
        self.assertEqual(len(self.game.enemies), initial_count + 1)
        last_enemy = self.game.enemies[-1]
        self.assertIsNotNone(last_enemy)
