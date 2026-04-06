"""Combat-side gameplay actions extracted from the Force Field orchestrator."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

from games.shared.constants import COMBO_TIMER_FRAMES

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .bot import Bot
    from .game import Game
    from .player import Player


MELEE_RANGE = 3.0
MELEE_DAMAGE = 75
MELEE_ARC = math.pi / 3
SWEEP_ARC_HALF_WIDTH = math.pi / 4
SWEEP_LAYERS = 3
SWEEP_SEGMENTS = 30
SWEEP_SPARK_COUNT = 15
BOT_PARTICLE_COUNT = 5


def execute_melee_attack(game: Game) -> None:
    """Apply the player's melee attack to nearby bots and trigger FX."""
    player = _require_player(game)

    create_melee_sweep_effect(game)
    _play_melee_sound(game)

    hits = 0
    for bot in game.bots:
        if not bot.alive or not _bot_in_melee_arc(player, bot):
            continue
        if bot.take_damage(MELEE_DAMAGE):
            _record_melee_kill(game, bot)
        hits += 1
        _spawn_bot_hit_particles(game, bot)

    if hits == 1:
        game.add_message("CRITICAL HIT!", C.RED)
    elif hits > 1:
        game.add_message(f"COMBO x{hits}!", C.RED)


def create_melee_sweep_effect(game: Game) -> None:
    """Create the sweeping slash particles for the melee attack."""
    player = _require_player(game)
    _add_sweep_layers(game, player.angle)
    _add_center_burst(game)


def _play_melee_sound(game: Game) -> None:
    """Fire and forget the melee shotgun audio cue."""
    try:
        game.sound_manager.play_sound("shoot_shotgun")
    except (pygame.error, OSError):
        return


def _bot_in_melee_arc(player: Player, bot: Bot) -> bool:
    """Return whether a bot falls inside the melee cone."""
    dx = bot.x - player.x
    dy = bot.y - player.y
    if math.hypot(dx, dy) > MELEE_RANGE:
        return False
    bot_angle = math.atan2(dy, dx)
    angle_diff = abs(bot_angle - player.angle)
    while angle_diff > math.pi:
        angle_diff -= 2 * math.pi
    return abs(angle_diff) <= MELEE_ARC / 2


def _record_melee_kill(game: Game, bot: Bot) -> None:
    """Synchronize kill/combo state and emit the kill event."""
    game.sound_manager.play_sound("scream")
    game.kills += 1
    game.kill_combo_count += 1
    game.kill_combo_timer = COMBO_TIMER_FRAMES
    game.last_death_pos = (bot.x, bot.y)
    game.event_bus.emit("bot_killed", x=bot.x, y=bot.y)


def _spawn_bot_hit_particles(game: Game, bot: Bot) -> None:
    """Spawn blood particles at the impacted bot location."""
    for _ in range(BOT_PARTICLE_COUNT):
        game.particle_system.add_particle(
            x=bot.x * 64 + 32,
            y=bot.y * 64 + 32,
            dx=random.uniform(-3, 3),
            dy=random.uniform(-3, 3),
            color=(200, 0, 0),
            timer=30,
            size=random.randint(2, 4),
        )


def _add_sweep_layers(game: Game, player_angle: float) -> None:
    """Render the layered melee arc across the center of the screen."""
    arc_start = player_angle - SWEEP_ARC_HALF_WIDTH
    arc_end = player_angle + SWEEP_ARC_HALF_WIDTH
    for layer in range(SWEEP_LAYERS):
        layer_distance = 80 + layer * 40
        for index in range(SWEEP_SEGMENTS):
            angle = arc_start + (index / (SWEEP_SEGMENTS - 1)) * (arc_end - arc_start)
            distance = layer_distance + random.randint(-20, 20)
            x = C.SCREEN_WIDTH // 2 + math.cos(angle) * distance
            y = C.SCREEN_HEIGHT // 2 + math.sin(angle) * distance
            game.particle_system.add_particle(
                x=x,
                y=y,
                dx=math.cos(angle) * 8,
                dy=math.sin(angle) * 8,
                color=_layer_color(layer),
                timer=20 - layer * 5,
                size=4 + layer,
                gravity=0.05,
                fade_color=(100, 0, 0),
            )


def _add_center_burst(game: Game) -> None:
    """Add the central slash burst so melee impacts read clearly."""
    for _ in range(SWEEP_SPARK_COUNT):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3, 12)
        game.particle_system.add_particle(
            x=C.SCREEN_WIDTH // 2,
            y=C.SCREEN_HEIGHT // 2,
            dx=math.cos(angle) * speed,
            dy=math.sin(angle) * speed,
            color=(255, 255, 255),
            timer=25,
            size=random.randint(2, 6),
            gravity=0.1,
            fade_color=(255, 100, 0),
        )


def _layer_color(layer: int) -> tuple[int, int, int]:
    """Return the color used for the given sweep layer."""
    if layer == 0:
        return (255, 255, 200)
    if layer == 1:
        return (255, 150, 0)
    return (255, 50, 0)


def _require_player(game: Game) -> Player:
    """Return the current player or raise when combat state is incomplete."""
    if game.player is None:
        raise ValueError("DbC Blocked: Precondition failed.")
    return game.player
