"""Ambient-effect management for Duum."""

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
    """Owns fog reveal, ambient cues, and combo-announcement timing."""

    def __init__(self, game: Game) -> None:
        self._game = game

    @property
    def game(self) -> Game:
        """Return the owned game object."""
        return self._game

    @property
    def player(self):
        game = self._game
        if game.player is None:
            raise ValueError("DbC Blocked: Precondition failed.")
        return game.player

    @property
    def sound_manager(self):
        return self._game.sound_manager

    @property
    def combat_manager(self):
        return self._game.combat_manager

    @property
    def visited_cells(self):
        return self._game.visited_cells

    @property
    def bots(self):
        return self._game.bots

    def update_fog_reveal(self) -> None:
        """Expand the visited-cell set around the player position."""
        player = self.player
        cx, cy = int(player.x), int(player.y)
        reveal_radius = FOG_REVEAL_RADIUS
        for row_offset in range(-reveal_radius, reveal_radius + 1):
            for col_offset in range(-reveal_radius, reveal_radius + 1):
                if (
                    row_offset * row_offset + col_offset * col_offset
                    <= reveal_radius * reveal_radius
                ):
                    self.visited_cells.add((cx + col_offset, cy + row_offset))

    def update_atmosphere(self) -> None:
        """Update ambient sound timers from nearby live enemies."""
        game = self._game
        player = self.player

        min_dist_sq = float("inf")
        for bot in self.bots:
            if bot.alive:
                dx = bot.x - player.x
                dy = bot.y - player.y
                dist_sq = dx * dx + dy * dy
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq

        min_dist = (
            math.sqrt(min_dist_sq) if min_dist_sq != float("inf") else float("inf")
        )

        if min_dist < 15:
            game.beast_timer -= 1
            if game.beast_timer <= 0:
                self.sound_manager.play_sound("beast")
                game.beast_timer = random.randint(BEAST_TIMER_MIN, BEAST_TIMER_MAX)

        if min_dist < 20:
            beat_delay = int(min(1.5, max(0.4, min_dist / 10.0)) * C.FPS)  # type: ignore[attr-defined]
            game.heartbeat_timer -= 1
            if game.heartbeat_timer <= 0:
                self.sound_manager.play_sound("heartbeat")
                self.sound_manager.play_sound("breath")
                game.heartbeat_timer = beat_delay

        if player.health < 50:
            game.groan_timer -= 1
            if game.groan_timer <= 0:
                self.sound_manager.play_sound("groan")
                game.groan_timer = GROAN_TIMER_DELAY

    def check_kill_combo(self) -> None:
        """Resolve pending combo expiry and keep combat state synchronized."""
        game = self._game
        if game.kill_combo_timer > 0:
            game.kill_combo_timer -= 1
            if game.kill_combo_timer <= 0:
                if game.kill_combo_count >= 3:
                    phrase = random.choice(
                        ["phrase_cool", "phrase_awesome", "phrase_brutal"]
                    )
                    self.sound_manager.play_sound(phrase)
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
                game.kill_combo_count = 0

        self.combat_manager.kill_combo_timer = game.kill_combo_timer
        self.combat_manager.kill_combo_count = game.kill_combo_count
