"""Atmosphere and ambient-effect management for Zombie Survival.

Extracted from game.py to keep that file within the 1 000-line budget.
Owns fog-of-war reveal, proximity-based ambient sounds, and kill-combo
announcement logic.
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from games.shared.constants import (
    BEAST_TIMER_MAX,
    BEAST_TIMER_MIN,
    FOG_REVEAL_RADIUS,
    GROAN_TIMER_DELAY,
)

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .game import Game


class AtmosphereManager:
    """Manages ambient sounds, fog-of-war reveal, and kill-combo timing.

    Instantiated once by Game and updated every frame.
    """

    def __init__(self, game: Game) -> None:
        self._game = game

    def update_fog_reveal(self) -> None:
        """Expand the visited-cells fog-of-war set around the player."""
        game = self._game
        cx, cy = int(game.player_x), int(game.player_y)
        reveal_radius = FOG_REVEAL_RADIUS
        for r_i in range(-reveal_radius, reveal_radius + 1):
            for r_j in range(-reveal_radius, reveal_radius + 1):
                if r_i * r_i + r_j * r_j <= reveal_radius * reveal_radius:
                    game.visited_cells.add((cx + r_j, cy + r_i))

    def update_atmosphere(self) -> None:
        """Update proximity-based ambient sounds (heartbeat, beast, groan)."""
        game = self._game
        min_dist_sq = float("inf")
        for bot in game.bots:
            if bot.alive:
                dx = bot.x - game.player_x
                dy = bot.y - game.player_y
                d_sq = dx * dx + dy * dy
                if d_sq < min_dist_sq:
                    min_dist_sq = d_sq

        min_dist = (
            math.sqrt(min_dist_sq) if min_dist_sq != float("inf") else float("inf")
        )

        if min_dist < 15:
            game.beast_timer -= 1
            if game.beast_timer <= 0:
                game.sound_manager.play_sound("beast")
                game.beast_timer = random.randint(BEAST_TIMER_MIN, BEAST_TIMER_MAX)

        if min_dist < 20:
            beat_delay = int(min(1.5, max(0.4, min_dist / 10.0)) * C.FPS)
            game.heartbeat_timer -= 1
            if game.heartbeat_timer <= 0:
                game.sound_manager.play_sound("heartbeat")
                game.sound_manager.play_sound("breath")
                game.heartbeat_timer = beat_delay

        if game.player_health < 50:
            game.groan_timer -= 1
            if game.groan_timer <= 0:
                game.sound_manager.play_sound("groan")
                game.groan_timer = GROAN_TIMER_DELAY

    def check_kill_combo(self) -> None:
        """Tick the kill-combo timer and trigger combo announcement if earned."""
        game = self._game
        if game.kill_combo_timer > 0:  # type: ignore[has-type]
            game.kill_combo_timer = game.kill_combo_timer - 1  # type: ignore[has-type]
            if game.kill_combo_timer <= 0:  # type: ignore[has-type]
                if game.kill_combo_count >= 3:  # type: ignore[has-type]
                    phrases = ["phrase_cool", "phrase_awesome", "phrase_brutal"]
                    phrase = random.choice(phrases)
                    game.sound_manager.play_sound(phrase)
                    game.damage_texts.append(
                        {
                            "x": C.SCREEN_WIDTH // 2,
                            "y": C.SCREEN_HEIGHT // 2 - 150,
                            "text": phrase.replace("phrase_", "").upper() + "!",
                            "color": C.YELLOW,
                            "timer": 120,
                            "vy": -0.2,
                        }
                    )
                game.kill_combo_count = 0  # type: ignore[has-type]
