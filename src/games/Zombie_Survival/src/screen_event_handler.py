"""Per-screen event handlers for Zombie Survival.

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

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .game import Game


class ScreenEventHandler:
    """Handles per-screen event dispatching for all GameState screens.

    Instantiated once by Game and called from the main loop.
    """

    def __init__(self, game: Game) -> None:
        self._game = game

    # ------------------------------------------------------------------
    # Screen handlers
    # ------------------------------------------------------------------

    def handle_intro_events(self) -> None:
        """Handle intro screen events."""
        game = self._game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if game.ui_renderer.intro_video:
                    game.ui_renderer.intro_video.release()
                    game.ui_renderer.intro_video = None
                game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_ESCAPE):
                    if game.ui_renderer.intro_video:
                        game.ui_renderer.intro_video.release()
                        game.ui_renderer.intro_video = None
                    game.state = GameState.MENU
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game.ui_renderer.intro_video:
                    game.ui_renderer.intro_video.release()
                    game.ui_renderer.intro_video = None
                game.state = GameState.MENU

    def handle_menu_events(self) -> None:
        """Handle main menu events."""
        game = self._game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    game.state = GameState.MAP_SELECT
                elif event.key == pygame.K_ESCAPE:
                    game.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                game.state = GameState.MAP_SELECT

    def handle_map_select_events(self) -> None:
        """Handle map selection events."""
        game = self._game
        game.ui_renderer.start_button.update(pygame.mouse.get_pos())
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game.state = GameState.MENU
                elif event.key == pygame.K_RETURN:
                    game.start_game()
                    game.state = GameState.PLAYING
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game.ui_renderer.start_button.is_clicked(event.pos):
                    game.start_game()
                    game.state = GameState.PLAYING
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                self._handle_map_select_row_click(event.pos[1])

    def _handle_map_select_row_click(self, my: int) -> None:
        """Cycle the setting for the clicked row in the map-select screen."""
        game = self._game
        if 200 <= my < 200 + 4 * 80:
            row = (my - 200) // 80
            if row == 0:
                sizes = C.MAP_SIZES
                try:
                    idx = sizes.index(game.selected_map_size)
                    game.selected_map_size = sizes[(idx + 1) % len(sizes)]
                except ValueError:
                    game.selected_map_size = 40
            elif row == 1:
                diffs = list(C.DIFFICULTIES.keys())
                try:
                    idx = diffs.index(game.selected_difficulty)
                    game.selected_difficulty = diffs[(idx + 1) % len(diffs)]
                except ValueError:
                    game.selected_difficulty = "NORMAL"
            elif row == 2:
                game.selected_start_level = (game.selected_start_level % 5) + 1
            elif row == 3:
                game.selected_lives = (game.selected_lives % 5) + 1

    def handle_level_complete_events(self) -> None:
        """Handle input events during the level complete screen."""
        game = self._game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game.level += 1
                    game.start_level()
                    game.state = GameState.PLAYING
                elif event.key == pygame.K_ESCAPE:
                    game.state = GameState.MENU

    def handle_game_over_events(self) -> None:
        """Handle input events during the game over screen."""
        game = self._game
        # Sequence Sound Logic
        game.game_over_timer += 1
        if game.game_over_timer == 120:
            game.sound_manager.play_sound("game_over2")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game.start_game()
                    game.state = GameState.PLAYING
                elif event.key == pygame.K_ESCAPE:
                    game.state = GameState.MENU

    def handle_key_config_events(self) -> None:
        """Handle input events in Key Config menu."""
        game = self._game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN:
                if game.binding_action:
                    if event.key != pygame.K_ESCAPE:
                        game.input_manager.bind_key(game.binding_action, event.key)
                    game.binding_action = None
                elif event.key == pygame.K_ESCAPE:
                    game.state = GameState.PLAYING if game.paused else GameState.MENU
            elif event.type == pygame.MOUSEBUTTONDOWN and not game.binding_action:
                self._handle_key_config_mouse_click(event.pos)

    def _handle_key_config_mouse_click(self, pos: tuple[int, int]) -> None:
        """Handle a mouse click in the key-config screen."""
        game = self._game
        mx, my = pos
        bindings = game.input_manager.bindings
        actions = sorted(bindings.keys())
        start_y = 120
        col_1_x = C.SCREEN_WIDTH // 4
        col_2_x = C.SCREEN_WIDTH * 3 // 4
        limit = 12

        for i, action in enumerate(actions):
            col = 0 if i < limit else 1
            idx = i if i < limit else i - limit
            x = col_1_x if col == 0 else col_2_x
            y = start_y + idx * 40

            rect = pygame.Rect(x - 150, y, 300, 30)
            if rect.collidepoint(mx, my):
                game.binding_action = action
                return

        center_x = C.SCREEN_WIDTH // 2 - 50
        top_y = C.SCREEN_HEIGHT - 80
        back_rect = pygame.Rect(center_x, top_y, 100, 40)
        if back_rect.collidepoint(mx, my):
            game.state = GameState.PLAYING if game.paused else GameState.MENU

    def update_intro_logic(self, elapsed: int) -> None:
        """Update intro sequence logic and transitions.

        Args:
            elapsed: Elapsed time in milliseconds since intro started.
        """
        game = self._game
        duration = 0
        if game.intro_phase == 0:
            duration = 3000
        elif game.intro_phase == 1:
            duration = 3000
        elif game.intro_phase == 2:
            self._update_intro_phase2(elapsed)
            return

        if game.intro_phase < 2:
            if game.intro_phase == 1 and elapsed < 50:
                if not hasattr(game, "water_played"):
                    game.sound_manager.play_sound("water")
                    game.water_played = True

            if elapsed > duration:
                game.intro_phase += 1
                game.intro_start_time = 0
                if game.intro_phase == 2 and game.ui_renderer.intro_video:
                    game.ui_renderer.intro_video.release()
                    game.ui_renderer.intro_video = None

    def _update_intro_phase2(self, elapsed: int) -> None:
        """Advance the slide-show portion of the intro (phase 2)."""
        game = self._game
        slides_durations = [8000, 10000, 4000, 4000]
        if game.intro_step < len(slides_durations):
            duration = slides_durations[game.intro_step]

            if game.intro_step == 0 and elapsed < 50:
                if not hasattr(game, "laugh_played"):
                    game.sound_manager.play_sound("laugh")
                    game.laugh_played = True

            if elapsed > duration:
                game.intro_step += 1
                game.intro_start_time = 0
                if hasattr(game, "laugh_played"):
                    del game._laugh_played
        else:
            game.state = GameState.MENU

    def handle_playing_state(self) -> None:
        """Handle the PLAYING state: events, pause audio, update, render."""
        game = self._game
        game.handle_game_events()
        if game.paused:
            beat_delay = PAUSE_HEARTBEAT_DELAY
            game.heartbeat_timer -= 1
            if game.heartbeat_timer <= 0:
                game.sound_manager.play_sound("heartbeat")
                game.sound_manager.play_sound("breath")
                game.heartbeat_timer = beat_delay

            if game.player and game.player_health < 50:
                game.groan_timer -= 1
                if game.groan_timer <= 0:
                    game.sound_manager.play_sound("groan")
                    game.groan_timer = GROAN_TIMER_DELAY
        else:
            game.update_game()
        game.renderer.render_game(game)
        if not game.paused and game.damage_flash_timer > 0:
            game.damage_flash_timer -= 1
