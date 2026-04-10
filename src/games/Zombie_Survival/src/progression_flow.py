"""Lifecycle and progression helpers for Zombie Survival."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from games.shared.config import RaycasterConfig
from games.shared.constants import PORTAL_RADIUS_SQ, GameState
from games.shared.raycaster import Raycaster

from . import constants as C  # noqa: N812
from .map import Map
from .player import Player

if TYPE_CHECKING:
    from .game import Game


def start_game(game: Game) -> None:
    """Reset the full game session and initialize the first level."""
    game.level = game.selected_start_level
    game.lives = game.selected_lives
    game.kills = 0
    game.level_times = []
    game.paused = False
    game.particle_system.particles = []
    game.damage_texts = []
    game.entity_manager.reset()

    game.unlocked_weapons = {"pistol", "rifle"}
    game.god_mode = False
    game.cheat_mode_active = False

    game.kill_combo_count = 0
    game.kill_combo_timer = 0
    game.heartbeat_timer = 0
    game.breath_timer = 0
    game.groan_timer = 0
    game.beast_timer = 0

    game.kills = 0
    game.kill_combo_count = 0
    game.kill_combo_timer = 0
    game.last_death_pos = None

    game.game_map = Map(game.selected_map_size)
    game.raycaster = Raycaster(game.game_map, _build_raycaster_config(game))
    game.portal = None

    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    start_level(game)


def start_level(game: Game) -> None:
    """Start a new level and respawn the player into a fresh world state."""
    if not (game.game_map is not None):
        raise ValueError("DbC Blocked: Precondition failed.")

    game.level_start_time = pygame.time.get_ticks()
    game.total_paused_time = 0
    game.pause_start_time = 0
    game.particle_system.particles = []
    game.damage_texts = []
    game.damage_flash_timer = 0
    game.visited_cells = set()
    game.portal = None

    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    player_pos = game._get_best_spawn_point()

    previous_ammo = None
    previous_weapon = "pistol"
    old_player = game.player
    if old_player:
        previous_ammo = old_player.ammo
        previous_weapon = old_player.current_weapon

    game.player = Player(player_pos[0], player_pos[1], player_pos[2])
    if previous_ammo:
        game.player.ammo = previous_ammo
        if previous_weapon in game.unlocked_weapons:
            game.player_current_weapon = previous_weapon
        else:
            game.player_current_weapon = "pistol"
    if game.player_current_weapon not in game.unlocked_weapons:
        game.player_current_weapon = "pistol"

    game.player.god_mode = game.god_mode

    game.entity_manager.reset()
    game.spawn_manager.spawn_all(
        player_pos,
        game.game_map,
        game.level,
        game.selected_difficulty,
    )

    music_tracks = [
        "music_loop",
        "music_drums",
        "music_wind",
        "music_horror",
        "music_piano",
        "music_action",
    ]
    if hasattr(game, "sound_manager"):
        game.sound_manager.start_music(random.choice(music_tracks))


def check_game_over(game: Game) -> bool:
    """Handle player death transitions and report whether the frame should stop."""
    if game.player_alive:
        return False

    if game.lives > 1:
        game.lives -= 1
        game.respawn_player()
        return True

    level_time = (
        pygame.time.get_ticks() - game.level_start_time - game.total_paused_time
    ) / 1000.0
    game.level_times.append(level_time)
    game.lives = 0
    game.state = GameState.GAME_OVER
    game.game_over_timer = 0
    game.sound_manager.play_sound("game_over1")
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)
    return True


def check_portal_completion(game: Game) -> bool:
    """Open the exit portal when the arena clears and handle level completion."""
    enemies_alive = game.entity_manager.get_active_enemies()
    if not enemies_alive and game.portal is None:
        game.spawn_portal()
        game.damage_texts.append(
            {
                "x": C.SCREEN_WIDTH // 2,
                "y": C.SCREEN_HEIGHT // 2,
                "text": "PORTAL OPENED!",
                "color": C.CYAN,
                "timer": 180,
                "vy": 0,
            }
        )

    if not game.portal:
        return False

    dx = game.portal["x"] - game.player_x
    dy = game.portal["y"] - game.player_y
    dist_sq = dx * dx + dy * dy
    if dist_sq >= PORTAL_RADIUS_SQ:
        return False

    level_time = (
        pygame.time.get_ticks() - game.level_start_time - game.total_paused_time
    ) / 1000.0
    game.level_times.append(level_time)
    game.state = GameState.LEVEL_COMPLETE
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)
    return True


def _build_raycaster_config(game: Game) -> RaycasterConfig:
    """Construct the raycaster config from the current game constants/state."""
    return RaycasterConfig(
        SCREEN_WIDTH=C.SCREEN_WIDTH,
        SCREEN_HEIGHT=C.SCREEN_HEIGHT,
        FOV=C.FOV,
        HALF_FOV=C.HALF_FOV,
        ZOOM_FOV_MULT=C.ZOOM_FOV_MULT,
        DEFAULT_RENDER_SCALE=game.render_scale,
        MAX_DEPTH=C.MAX_DEPTH,
        FOG_START=C.FOG_START,
        FOG_COLOR=C.FOG_COLOR,
        LEVEL_THEMES=C.LEVEL_THEMES,
        ENEMY_TYPES=C.ENEMY_TYPES,
    )
