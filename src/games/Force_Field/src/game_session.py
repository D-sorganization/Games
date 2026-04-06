"""Session lifecycle helpers for Force Field."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from games.shared.raycaster import Raycaster

from .map import Map
from .player import Player

if TYPE_CHECKING:
    from .game import Game


STARTER_WEAPONS = (
    "rifle",
    "shotgun",
    "minigun",
    "plasma",
    "laser",
    "rocket",
    "flamethrower",
    "pulse",
    "freezer",
)
LEVEL_MUSIC_TRACKS = (
    "music_loop",
    "music_drums",
    "music_wind",
    "music_horror",
    "music_piano",
    "music_action",
)


def start_game(game: Game) -> None:
    """Reset top-level run state and begin the selected starting level."""
    game.level = game.selected_start_level
    game.lives = game.selected_lives
    game.kills = 0
    game.level_times = []
    game.paused = False
    game.particle_system.particles = []
    game.damage_texts = []
    game.entity_manager.reset()
    game.unlocked_weapons = {"pistol", random.choice(STARTER_WEAPONS)}
    game.god_mode = False
    game.cheat_mode_active = False
    _reset_atmosphere(game)
    game.game_map = Map(game.selected_map_size)
    game.raycaster = Raycaster(game.game_map, game.raycaster_config)
    game.raycaster.set_render_scale(game.render_scale)
    game.last_death_pos = None
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    start_level(game)


def start_level(game: Game) -> None:
    """Start the current level while preserving the existing loadout."""
    if game.game_map is None:
        raise ValueError("DbC Blocked: Precondition failed.")
    _reset_level_state(game)
    player_pos = game._get_best_spawn_point()
    previous_ammo, previous_weapon = _previous_loadout(game)
    game.player = Player(player_pos[0], player_pos[1], player_pos[2])
    player = _require_player(game)
    _restore_player_loadout(game, previous_ammo, previous_weapon)
    _equip_starter_weapon(game)
    player.god_mode = game.god_mode
    game.entity_manager.reset()
    game.spawn_manager.spawn_all(
        player_pos,
        game.game_map,
        game.level,
        game.selected_difficulty,
    )
    if hasattr(game, "sound_manager"):
        game.sound_manager.start_music(random.choice(LEVEL_MUSIC_TRACKS))


def _reset_atmosphere(game: Game) -> None:
    """Reset combo and atmosphere timers for a new run."""
    game.kill_combo_count = 0
    game.kill_combo_timer = 0
    game.heartbeat_timer = 0
    game.breath_timer = 0
    game.groan_timer = 0
    game.beast_timer = 0


def _reset_level_state(game: Game) -> None:
    """Reset per-level transient state before spawning entities."""
    game.level_start_time = pygame.time.get_ticks()
    game.total_paused_time = 0
    game.pause_start_time = 0
    game.particle_system.particles = []
    game.damage_texts = []
    game.damage_flash_timer = 0
    game.screen_shake = 0.0
    game.visited_cells = set()
    game.portal = None
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)


def _previous_loadout(game: Game) -> tuple[dict[str, int] | None, str]:
    """Capture ammo and weapon selection from the current player, if any."""
    if game.player is None:
        return None, "pistol"
    return game.player.ammo, game.player.current_weapon


def _restore_player_loadout(
    game: Game,
    previous_ammo: dict[str, int] | None,
    previous_weapon: str,
) -> None:
    """Restore the previous ammo state and valid weapon selection."""
    player = _require_player(game)
    if previous_ammo is not None:
        player.ammo = previous_ammo
        if previous_weapon in game.unlocked_weapons:
            player.current_weapon = previous_weapon
        else:
            player.current_weapon = "pistol"
    if player.current_weapon not in game.unlocked_weapons:
        player.current_weapon = "pistol"


def _equip_starter_weapon(game: Game) -> None:
    """Equip the random starter weapon on the first level of a new run."""
    if game.level != 1:
        return
    player = _require_player(game)
    for weapon_name in game.unlocked_weapons:
        if weapon_name != "pistol":
            player.current_weapon = weapon_name
            return


def _require_player(game: Game) -> Player:
    """Return the current player or raise when level state is incomplete."""
    if game.player is None:
        raise ValueError("DbC Blocked: Precondition failed.")
    return game.player
