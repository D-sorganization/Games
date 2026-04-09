"""Per-screen event handlers for Duum.

Extracted from game.py to keep that file within the 1 000-line budget.
Each method corresponds to one GameState and is called from the main
game loop.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from games.shared.constants import (
    GROAN_TIMER_DELAY,
    PAUSE_HEARTBEAT_DELAY,
    GameState,
)

if TYPE_CHECKING:
    from .game import Game


class ScreenEventHandler:
    """Handles per-screen event dispatching for all Duum GameState screens."""

    def __init__(self, game: Game) -> None:
        self._game = game

    def handle_intro_events(self) -> None:
        """Handle events during the intro sequence."""
        game = self._game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_SPACE):
                    game.state = GameState.MENU

    def handle_menu_events(self) -> None:
        """Handle events in the main menu."""
        game = self._game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                game.running = False

    def handle_key_config_events(self) -> None:
        """Handle events in the key configuration screen."""
        game = self._game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                game.state = GameState.MENU

    def handle_map_select_events(self) -> None:
        """Handle events in the map selection screen."""
        game = self._game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                game.state = GameState.MENU

    def handle_level_complete_events(self) -> None:
        """Handle events in the level-complete screen."""
        game = self._game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                    game.state = GameState.MENU

    def handle_game_over_events(self) -> None:
        """Handle events in the game-over screen."""
        game = self._game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                    game.state = GameState.MENU

    def update_intro_logic(self, elapsed: int) -> None:
        """Update intro sequence logic and transitions."""
        game = self._game
        duration = 0
        if game.intro_phase == 0:
            duration = 3000
        elif game.intro_phase == 1:
            duration = 3000
        elif game.intro_phase == 2:
            slides_durations = [8000, 10000, 4000, 4000]
            if game.intro_step < len(slides_durations):
                duration = slides_durations[game.intro_step]

                if game.intro_step == 0 and elapsed < 50:
                    if not game.laugh_played:
                        game.sound_manager.play_sound("laugh")
                        game.laugh_played = True

                if elapsed > duration:
                    game.intro_step += 1
                    game.intro_start_time = 0
                    game.laugh_played = False
            else:
                game.state = GameState.MENU
                return

        if game.intro_phase < 2:
            if game.intro_phase == 1 and elapsed < 50:
                if not game.water_played:
                    game.sound_manager.play_sound("water")
                    game.water_played = True

            if elapsed > duration:
                game.intro_phase += 1
                game.intro_start_time = 0
                if game.intro_phase == 2:
                    game.ui_renderer.release_intro_video()

    def handle_playing_state(self) -> None:
        """Handle the PLAYING state: events, pause audio, update, and render."""
        game = self._game
        game.handle_game_events()
        if game.paused:
            game.heartbeat_timer -= 1
            if game.heartbeat_timer <= 0:
                game.sound_manager.play_sound("heartbeat")
                game.sound_manager.play_sound("breath")
                game.heartbeat_timer = PAUSE_HEARTBEAT_DELAY

            if game.player and game.player.health < 50:
                game.groan_timer -= 1
                if game.groan_timer <= 0:
                    game.sound_manager.play_sound("groan")
                    game.groan_timer = GROAN_TIMER_DELAY
        else:
            game.update_game()

        game.renderer.render_game(game, game.flash_intensity)
        if not game.paused and game.damage_flash_timer > 0:
            game.damage_flash_timer -= 1
