"""Tests for FPSGameBase shared methods."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from games.shared.fps_game_base import FPSGameBase


def _make_constants():
    """Create a minimal constants module for testing."""
    return SimpleNamespace(
        SCREEN_WIDTH=800,
        SCREEN_HEIGHT=600,
        WHITE=(255, 255, 255),
        RED=(255, 0, 0),
        GREEN=(0, 255, 0),
        YELLOW=(255, 255, 0),
        CYAN=(0, 255, 255),
        SPAWN_SAFETY_MARGIN=5,
        DEFAULT_PLAYER_SPAWN=(5.5, 5.5, 0.0),
    )


def _make_game():
    """Create an FPSGameBase instance with minimal state for testing."""
    game = FPSGameBase()
    game.C = _make_constants()
    game.render_scale = 2
    game.raycaster = None
    game.damage_texts = []
    game.unlocked_weapons = {"pistol", "rifle"}
    game.player = None
    game.game_map = None
    game.selected_map_size = 40
    game.portal = None
    game.last_death_pos = None
    game.entity_manager = MagicMock()
    game.entity_manager.bots = []
    game.entity_manager.projectiles = []
    return game


class TestProperties:
    def test_bots_property(self):
        game = _make_game()
        game.entity_manager.bots = ["bot1", "bot2"]
        assert game.bots == ["bot1", "bot2"]

    def test_projectiles_property(self):
        game = _make_game()
        game.entity_manager.projectiles = ["proj1"]
        assert game.projectiles == ["proj1"]


class TestAddMessage:
    def test_adds_damage_text(self):
        game = _make_game()
        game.add_message("TEST", (255, 0, 0))
        assert len(game.damage_texts) == 1
        msg = game.damage_texts[0]
        assert msg["text"] == "TEST"
        assert msg["color"] == (255, 0, 0)
        assert msg["timer"] == 60

    def test_position_is_centered(self):
        game = _make_game()
        game.add_message("HI", (0, 0, 0))
        msg = game.damage_texts[0]
        assert msg["x"] == 400  # 800 // 2
        assert msg["y"] == 250  # 600 // 2 - 50


class TestCycleRenderScale:
    def test_cycles_through_scales(self):
        game = _make_game()
        game.render_scale = 2
        game.cycle_render_scale()
        assert game.render_scale == 4

    def test_wraps_around(self):
        game = _make_game()
        game.render_scale = 8
        game.cycle_render_scale()
        assert game.render_scale == 1

    def test_invalid_scale_resets_to_2(self):
        game = _make_game()
        game.render_scale = 99
        game.cycle_render_scale()
        assert game.render_scale == 2

    def test_updates_raycaster(self):
        game = _make_game()
        game.raycaster = MagicMock()
        game.render_scale = 1
        game.cycle_render_scale()
        game.raycaster.set_render_scale.assert_called_once_with(2)

    def test_adds_quality_message(self):
        game = _make_game()
        game.render_scale = 1
        game.cycle_render_scale()
        assert any("QUALITY" in t["text"] for t in game.damage_texts)


class TestSwitchWeaponWithMessage:
    def test_switch_unlocked_weapon(self):
        game = _make_game()
        game.player = MagicMock()
        game.player.current_weapon = "pistol"
        game.switch_weapon_with_message("rifle")
        game.player.switch_weapon.assert_called_once_with("rifle")

    def test_switch_locked_weapon_shows_locked(self):
        game = _make_game()
        game.player = MagicMock()
        game.switch_weapon_with_message("plasma")
        game.player.switch_weapon.assert_not_called()
        assert any("LOCKED" in t["text"] for t in game.damage_texts)

    def test_switch_same_weapon_no_op(self):
        game = _make_game()
        game.player = MagicMock()
        game.player.current_weapon = "pistol"
        game.switch_weapon_with_message("pistol")
        game.player.switch_weapon.assert_not_called()


class TestSpawnPortal:
    def test_uses_last_death_pos(self):
        game = _make_game()
        game.last_death_pos = (10.0, 20.0)
        game.spawn_portal()
        assert game.portal == {"x": 10.0, "y": 20.0}

    def test_fallback_near_player(self):
        game = _make_game()
        game.player = MagicMock()
        game.player.x = 5.0
        game.player.y = 5.0
        mock_map = MagicMock()
        mock_map.is_wall.return_value = False
        game.game_map = mock_map
        game.spawn_portal()
        assert game.portal is not None
        assert "x" in game.portal
        assert "y" in game.portal

    def test_spawn_portal_no_map(self):
        game = _make_game()
        game.player = MagicMock()
        game.player.x = 5.0
        game.player.y = 5.0
        game.game_map = None
        game.spawn_portal()
        assert game.portal is None

    def test_spawn_portal_all_walls(self):
        game = _make_game()
        game.player = MagicMock()
        game.player.x = 5.0
        game.player.y = 5.0
        mock_map = MagicMock()
        mock_map.is_wall.return_value = True
        game.game_map = mock_map
        game.spawn_portal()
        assert game.portal is None


class TestFindSafeSpawn:
    def test_returns_base_when_no_map(self):
        game = _make_game()
        result = game.find_safe_spawn(10.0, 20.0, 1.5)
        assert result == (10.0, 20.0, 1.5)

    def test_finds_non_wall_position(self):
        game = _make_game()
        mock_map = MagicMock()
        mock_map.size = 40
        mock_map.is_wall.return_value = False
        game.game_map = mock_map
        result = game.find_safe_spawn(20.0, 20.0, 0.0)
        assert result == (20.0, 20.0, 0.0)  # First attempt succeeds

    def test_expands_search_radius(self):
        game = _make_game()
        mock_map = MagicMock()
        mock_map.size = 40
        call_count = [0]

        def is_wall(x, y):
            call_count[0] += 1
            return call_count[0] < 10  # First 9 are walls

        mock_map.is_wall.side_effect = is_wall
        game.game_map = mock_map
        result = game.find_safe_spawn(20.0, 20.0, 0.0)
        assert len(result) == 3  # Returns a valid tuple

    def test_finds_safe_spawn_out_of_bounds_and_exhausts(self):
        game = _make_game()
        mock_map = MagicMock()
        mock_map.size = 10
        mock_map.is_wall.return_value = True
        game.game_map = mock_map
        result = game.find_safe_spawn(5.0, 5.0, 0.0)
        assert result == (5.0, 5.0, 0.0)


class TestGetBestSpawnPoint:
    def test_fallback_when_no_map(self):
        game = _make_game()
        result = game._get_best_spawn_point()
        assert result == (5.5, 5.5, 0.0)

    def test_uses_corner_positions(self):
        game = _make_game()
        mock_map = MagicMock()
        mock_map.size = 40
        mock_map.height = 40
        mock_map.width = 40
        mock_map.is_wall.return_value = False
        game.game_map = mock_map
        result = game._get_best_spawn_point()
        assert len(result) == 3

    def test_get_best_spawn_point_corners_are_walls_but_center_free(self):
        game = _make_game()
        mock_map = MagicMock()
        mock_map.size = 40
        mock_map.height = 40
        mock_map.width = 40

        def is_wall(x, y):
            if int(x) == 20 and int(y) == 2:
                return False
            return True

        mock_map.is_wall.side_effect = is_wall
        game.game_map = mock_map
        result = game._get_best_spawn_point()
        assert result == (20.5, 2.5, 0.0)

    def test_get_best_spawn_point_all_walls(self):
        game = _make_game()
        mock_map = MagicMock()
        mock_map.size = 40
        mock_map.height = 40
        mock_map.width = 40
        mock_map.is_wall.return_value = True
        game.game_map = mock_map
        result = game._get_best_spawn_point()
        assert result == (5.5, 5.5, 0.0)


class TestRespawnPlayer:
    def test_resets_player_state(self):
        game = _make_game()
        mock_map = MagicMock()
        mock_map.size = 40
        mock_map.height = 40
        mock_map.width = 40
        mock_map.is_wall.return_value = False
        game.game_map = mock_map
        game.player = MagicMock()
        game.player.alive = False
        game.player.health = 0
        game.respawn_player()
        assert game.player.alive is True
        assert game.player.health == 100
        assert game.player.shield_active is False

    def test_shows_respawned_message(self):
        game = _make_game()
        mock_map = MagicMock()
        mock_map.size = 40
        mock_map.height = 40
        mock_map.width = 40
        mock_map.is_wall.return_value = False
        game.game_map = mock_map
        game.player = MagicMock()
        game.respawn_player()
        assert any("RESPAWNED" in t["text"] for t in game.damage_texts)


class TestInitFPSGame:
    """Tests for shared FPS init helper."""

    def test_init_fps_game_sets_common_state(self) -> None:
        class InitGame(FPSGameBase):
            def _wire_event_bus(self) -> None:
                self._event_bus_wired = True

        class Constants(SimpleNamespace):
            SCREEN_WIDTH = 800
            SCREEN_HEIGHT = 600
            SPAWN_SAFETY_MARGIN = 2
            DEFAULT_PLAYER_SPAWN = (5.5, 5.5, 0.0)
            WHITE = (255, 255, 255)
            CYAN = (0, 255, 255)
            RED = (255, 0, 0)
            YELLOW = (255, 255, 0)
            BLACK = (0, 0, 0)
            PLAYER_HEALTH = 100
            DEFAULT_MAP_SIZE = 40
            DEFAULT_RENDER_SCALE = 2
            DEFAULT_DIFFICULTY = "NORMAL"
            DEFAULT_LIVES = 3
            DEFAULT_START_LEVEL = 1

        fake_event_bus = MagicMock()
        fake_sound_manager = MagicMock()
        fake_screen = MagicMock()
        fake_clock = MagicMock()
        fake_renderer = MagicMock()
        fake_ui_renderer = MagicMock()
        fake_joystick = MagicMock()
        fake_input_manager = MagicMock()
        fake_entity_manager = MagicMock()
        fake_particle_system = MagicMock()

        with (
            patch(
                "games.shared.fps_game_base.pygame.display.set_mode",
                return_value=fake_screen,
            ),
            patch(
                "games.shared.fps_game_base.pygame.display.set_caption",
            ) as mock_set_caption,
            patch(
                "games.shared.fps_game_base.pygame.time.Clock",
                return_value=fake_clock,
            ),
            patch(
                "games.shared.fps_game_base.pygame.joystick",
                new=MagicMock(
                    get_count=MagicMock(return_value=1),
                    Joystick=MagicMock(return_value=fake_joystick),
                ),
            ),
            patch(
                "games.shared.fps_game_base.EventBus",
                return_value=fake_event_bus,
            ),
        ):
            game = InitGame()
            game.init_fps_game(
                Constants,
                caption="Test FPS",
                sound_manager=fake_sound_manager,
                sound_manager_factory=MagicMock(return_value=fake_sound_manager),
                input_manager=fake_input_manager,
                entity_manager=fake_entity_manager,
                particle_system=fake_particle_system,
                unlocked_weapons={"pistol", "rifle"},
                render_cls=lambda _screen: fake_renderer,
                ui_render_cls=lambda _screen: fake_ui_renderer,
            )

        mock_set_caption.assert_called_once_with("Test FPS")
        assert game.C is Constants
        assert game.screen is fake_screen
        assert game.clock is fake_clock
        assert game.running is True
        assert game.render_scale == Constants.DEFAULT_RENDER_SCALE
        assert game.selected_map_size == Constants.DEFAULT_MAP_SIZE
        assert game.health == Constants.PLAYER_HEALTH
        assert game.unlocked_weapons == {"pistol", "rifle"}
        assert game.sound_manager is fake_sound_manager
        assert game.input_manager is fake_input_manager
        assert game.entity_manager is fake_entity_manager
        assert game.particle_system is fake_particle_system
        assert game.event_bus is fake_event_bus
        assert game._event_bus_wired is True
        assert game.visited_cells == set()
        assert game.show_minimap is True
        assert game.joystick is fake_joystick
