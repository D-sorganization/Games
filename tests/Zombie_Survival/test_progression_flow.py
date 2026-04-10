"""Focused tests for the extracted Zombie Survival progression helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pygame

from games.shared.constants import GameState


class _GameStub(SimpleNamespace):
    """Small game-like stub with the properties progression helpers expect."""

    @property
    def player_current_weapon(self) -> str:
        if self.player is None:
            return "pistol"
        return self.player.current_weapon

    @player_current_weapon.setter
    def player_current_weapon(self, value: str) -> None:
        if self.player is not None:
            self.player.current_weapon = value

    @property
    def player_alive(self) -> bool:
        return bool(self.player and self.player.alive)

    @property
    def player_x(self) -> float:
        return self.player.x if self.player else 0.0

    @property
    def player_y(self) -> float:
        return self.player.y if self.player else 0.0


def test_start_game_resets_session_and_initializes_map(monkeypatch) -> None:
    """Full game restarts should reset shared state and build the world shell."""
    from games.Zombie_Survival.src import progression_flow

    start_level = MagicMock()

    class FakeMap:
        def __init__(self, size: int) -> None:
            self.size = size

    class FakeRaycaster:
        def __init__(self, game_map: FakeMap, config: object) -> None:
            self.game_map = game_map
            self.config = config

    mouse_visible = MagicMock()
    event_grab = MagicMock()
    monkeypatch.setattr(progression_flow, "Map", FakeMap)
    monkeypatch.setattr(progression_flow, "Raycaster", FakeRaycaster)
    monkeypatch.setattr(progression_flow, "start_level", start_level)
    monkeypatch.setattr(pygame.mouse, "set_visible", mouse_visible)
    monkeypatch.setattr(pygame.event, "set_grab", event_grab)

    game = _GameStub(
        selected_start_level=3,
        selected_lives=4,
        selected_map_size=42,
        render_scale=2,
        kills=99,
        level_times=[1.0],
        paused=True,
        particle_system=SimpleNamespace(particles=[1, 2]),
        damage_texts=[{"text": "old"}],
        entity_manager=SimpleNamespace(reset=MagicMock()),
        unlocked_weapons={"rocket"},
        god_mode=True,
        cheat_mode_active=True,
        kill_combo_count=5,
        kill_combo_timer=9,
        heartbeat_timer=1,
        breath_timer=2,
        groan_timer=3,
        beast_timer=4,
        last_death_pos=(5.0, 7.0),
        portal={"x": 1.0, "y": 1.0},
    )

    progression_flow.start_game(game)

    assert game.level == 3
    assert game.lives == 4
    assert game.kills == 0
    assert game.level_times == []
    assert game.paused is False
    assert game.unlocked_weapons == {"pistol", "rifle"}
    assert game.god_mode is False
    assert game.cheat_mode_active is False
    assert game.last_death_pos is None
    assert isinstance(game.game_map, FakeMap)
    assert isinstance(game.raycaster, FakeRaycaster)
    game.entity_manager.reset.assert_called_once_with()
    start_level.assert_called_once_with(game)
    mouse_visible.assert_called_once_with(False)
    event_grab.assert_called_once_with(True)


def test_start_level_restores_previous_ammo_and_weapon(monkeypatch) -> None:
    """Level starts should preserve compatible player progression state."""
    from games.Zombie_Survival.src import progression_flow

    class FakePlayer:
        def __init__(self, x: float, y: float, angle: float) -> None:
            self.x = x
            self.y = y
            self.angle = angle
            self.ammo = {"pistol": 0, "rifle": 0}
            self.current_weapon = "pistol"
            self.god_mode = False

    mouse_visible = MagicMock()
    event_grab = MagicMock()
    monkeypatch.setattr(progression_flow, "Player", FakePlayer)
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 4321)
    monkeypatch.setattr(pygame.mouse, "set_visible", mouse_visible)
    monkeypatch.setattr(pygame.event, "set_grab", event_grab)
    monkeypatch.setattr(progression_flow.random, "choice", lambda tracks: tracks[0])

    old_player = SimpleNamespace(
        ammo={"pistol": 15, "rifle": 90},
        current_weapon="rifle",
    )
    entity_manager = SimpleNamespace(reset=MagicMock())
    spawn_manager = SimpleNamespace(spawn_all=MagicMock())
    sound_manager = SimpleNamespace(start_music=MagicMock())
    game = _GameStub(
        game_map=SimpleNamespace(),
        particle_system=SimpleNamespace(particles=["old"]),
        damage_texts=[{"text": "old"}],
        damage_flash_timer=10,
        visited_cells={(1, 1)},
        portal={"x": 1.0, "y": 1.0},
        _get_best_spawn_point=lambda: (10.5, 11.5, 0.75),
        player=old_player,
        unlocked_weapons={"pistol", "rifle"},
        god_mode=True,
        entity_manager=entity_manager,
        spawn_manager=spawn_manager,
        sound_manager=sound_manager,
        level=2,
        selected_difficulty="normal",
    )

    progression_flow.start_level(game)

    assert game.level_start_time == 4321
    assert game.total_paused_time == 0
    assert game.pause_start_time == 0
    assert game.damage_texts == []
    assert game.visited_cells == set()
    assert game.portal is None
    assert isinstance(game.player, FakePlayer)
    assert game.player.x == 10.5
    assert game.player.ammo == {"pistol": 15, "rifle": 90}
    assert game.player.current_weapon == "rifle"
    assert game.player.god_mode is True
    entity_manager.reset.assert_called_once_with()
    spawn_manager.spawn_all.assert_called_once_with(
        (10.5, 11.5, 0.75),
        game.game_map,
        2,
        "normal",
    )
    sound_manager.start_music.assert_called_once_with("music_loop")
    mouse_visible.assert_called_once_with(False)
    event_grab.assert_called_once_with(True)


def test_check_game_over_transitions_to_game_over(monkeypatch) -> None:
    """A final death should end the level and show the game-over screen."""
    from games.Zombie_Survival.src import progression_flow

    mouse_visible = MagicMock()
    event_grab = MagicMock()
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 3200)
    monkeypatch.setattr(pygame.mouse, "set_visible", mouse_visible)
    monkeypatch.setattr(pygame.event, "set_grab", event_grab)

    game = _GameStub(
        player=SimpleNamespace(alive=False),
        lives=1,
        level_start_time=1000,
        total_paused_time=200,
        level_times=[],
        state=GameState.PLAYING,
        game_over_timer=7,
        sound_manager=SimpleNamespace(play_sound=MagicMock()),
    )

    result = progression_flow.check_game_over(game)

    assert result is True
    assert game.level_times == [2.0]
    assert game.lives == 0
    assert game.state == GameState.GAME_OVER
    assert game.game_over_timer == 0
    game.sound_manager.play_sound.assert_called_once_with("game_over1")
    mouse_visible.assert_called_once_with(True)
    event_grab.assert_called_once_with(False)


def test_check_portal_completion_opens_and_completes_level(monkeypatch) -> None:
    """Clearing enemies and entering the portal should finish the level."""
    from games.Zombie_Survival.src import progression_flow

    mouse_visible = MagicMock()
    event_grab = MagicMock()
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 2100)
    monkeypatch.setattr(pygame.mouse, "set_visible", mouse_visible)
    monkeypatch.setattr(pygame.event, "set_grab", event_grab)

    game = _GameStub(
        entity_manager=SimpleNamespace(get_active_enemies=MagicMock(return_value=[])),
        portal=None,
        damage_texts=[],
        player=SimpleNamespace(x=5.0, y=5.0),
        level_start_time=1000,
        total_paused_time=100,
        level_times=[],
        state=GameState.PLAYING,
    )

    def spawn_portal() -> None:
        game.portal = {"x": 5.0, "y": 5.0}

    game.spawn_portal = MagicMock(side_effect=spawn_portal)

    result = progression_flow.check_portal_completion(game)

    assert result is True
    game.spawn_portal.assert_called_once_with()
    assert game.damage_texts[0]["text"] == "PORTAL OPENED!"
    assert game.level_times == [1.0]
    assert game.state == GameState.LEVEL_COMPLETE
    mouse_visible.assert_called_once_with(True)
    event_grab.assert_called_once_with(False)
