"""State- and screen-level flow handlers for Force Field."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from games.shared.constants import GameState

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .game import Game


MAP_SELECT_TOP = 200
MAP_SELECT_ROW_HEIGHT = 80
MAP_SELECT_ROWS = 4
KEY_CONFIG_START_Y = 120
KEY_CONFIG_ROW_HEIGHT = 40
KEY_CONFIG_COLUMN_LIMIT = 12
KEY_CONFIG_BIND_WIDTH = 300
KEY_CONFIG_BIND_HEIGHT = 30
BACK_BUTTON_WIDTH = 100
BACK_BUTTON_HEIGHT = 40
BACK_BUTTON_BOTTOM_OFFSET = 80
INTRO_PHASE_DURATION_MS = 3000
INTRO_SLIDE_DURATIONS_MS = (8000, 10000, 4000, 4000)


def handle_intro_events(game: Game) -> None:
    """Handle intro-state input and exit conditions."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game.ui_renderer.release_intro_video()
            game.running = False
        elif event.type == pygame.KEYDOWN and event.key in (
            pygame.K_SPACE,
            pygame.K_ESCAPE,
        ):
            game.ui_renderer.release_intro_video()
            game.state = GameState.MENU
        elif event.type == pygame.MOUSEBUTTONDOWN:
            game.ui_renderer.release_intro_video()
            game.state = GameState.MENU


def handle_menu_events(game: Game) -> None:
    """Handle input on the main menu screen."""
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


def handle_map_select_events(game: Game) -> None:
    """Handle selection changes and launch actions on the setup screen."""
    game.ui_renderer.update_start_button(pygame.mouse.get_pos())
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game.state = GameState.MENU
            elif event.key == pygame.K_RETURN:
                _start_selected_game(game)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game.ui_renderer.is_start_button_clicked(event.pos):
                _start_selected_game(game)
            _cycle_map_select_option(game, event.pos[1])


def handle_level_complete_events(game: Game) -> None:
    """Handle input on the level-complete screen."""
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


def handle_game_over_events(game: Game) -> None:
    """Handle restart and exit actions after the player dies."""
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


def handle_key_config_events(game: Game) -> None:
    """Handle key-binding selection and reassignment input."""
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
            if _select_key_binding(game, event.pos):
                return
            if _clicks_back_button(event.pos):
                game.state = GameState.PLAYING if game.paused else GameState.MENU


def update_intro_logic(game: Game, elapsed: int) -> None:
    """Advance the intro sequence and perform its timed transitions."""
    if game.intro_phase == 2:
        _update_intro_slides(game, elapsed)
        return
    if (
        game.intro_phase == 1
        and elapsed < 50
        and not getattr(game, "water_played", False)
    ):
        game.sound_manager.play_sound("water")
        game.water_played = True
    if elapsed <= INTRO_PHASE_DURATION_MS:
        return
    game.intro_phase += 1
    game.intro_start_time = 0
    if game.intro_phase == 2:
        game.ui_renderer.release_intro_video()


def _start_selected_game(game: Game) -> None:
    """Enter gameplay from the map-selection screen."""
    game.start_game()
    game.state = GameState.PLAYING
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)


def _cycle_map_select_option(game: Game, mouse_y: int) -> None:
    """Cycle the selected map option based on the clicked row."""
    row = _map_select_row(mouse_y)
    if row is None:
        return
    if row == 0:
        _cycle_map_size(game)
    elif row == 1:
        _cycle_difficulty(game)
    elif row == 2:
        game.selected_start_level = (game.selected_start_level % 5) + 1
    elif row == 3:
        game.selected_lives = (game.selected_lives % 5) + 1


def _map_select_row(mouse_y: int) -> int | None:
    """Return the clicked option row, or ``None`` when outside the menu."""
    if not (
        MAP_SELECT_TOP
        <= mouse_y
        < MAP_SELECT_TOP + MAP_SELECT_ROWS * MAP_SELECT_ROW_HEIGHT
    ):
        return None
    return (mouse_y - MAP_SELECT_TOP) // MAP_SELECT_ROW_HEIGHT


def _cycle_map_size(game: Game) -> None:
    """Advance the selected map size through the supported options."""
    try:
        current_index = C.MAP_SIZES.index(game.selected_map_size)
        game.selected_map_size = C.MAP_SIZES[(current_index + 1) % len(C.MAP_SIZES)]
    except ValueError:
        game.selected_map_size = 40


def _cycle_difficulty(game: Game) -> None:
    """Advance the selected difficulty through the configured options."""
    difficulties = list(C.DIFFICULTIES.keys())
    try:
        current_index = difficulties.index(game.selected_difficulty)
        game.selected_difficulty = difficulties[(current_index + 1) % len(difficulties)]
    except ValueError:
        game.selected_difficulty = "NORMAL"


def _select_key_binding(game: Game, mouse_pos: tuple[int, int]) -> bool:
    """Select a key binding slot when the user clicks its row."""
    for action, rect in _binding_rects(game.input_manager.bindings).items():
        if rect.collidepoint(mouse_pos):
            game.binding_action = action
            return True
    return False


def _binding_rects(bindings: dict[str, int]) -> dict[str, pygame.Rect]:
    """Build the click targets for each key-binding row."""
    column_x = (C.SCREEN_WIDTH // 4, C.SCREEN_WIDTH * 3 // 4)
    rects: dict[str, pygame.Rect] = {}
    for index, action in enumerate(sorted(bindings.keys())):
        column = 0 if index < KEY_CONFIG_COLUMN_LIMIT else 1
        row = (
            index
            if index < KEY_CONFIG_COLUMN_LIMIT
            else index - KEY_CONFIG_COLUMN_LIMIT
        )
        rects[action] = pygame.Rect(
            column_x[column] - 150,
            KEY_CONFIG_START_Y + row * KEY_CONFIG_ROW_HEIGHT,
            KEY_CONFIG_BIND_WIDTH,
            KEY_CONFIG_BIND_HEIGHT,
        )
    return rects


def _clicks_back_button(mouse_pos: tuple[int, int]) -> bool:
    """Return whether the back button was clicked."""
    center_x = C.SCREEN_WIDTH // 2 - 50
    top_y = C.SCREEN_HEIGHT - BACK_BUTTON_BOTTOM_OFFSET
    return pygame.Rect(
        center_x,
        top_y,
        BACK_BUTTON_WIDTH,
        BACK_BUTTON_HEIGHT,
    ).collidepoint(mouse_pos)


def _update_intro_slides(game: Game, elapsed: int) -> None:
    """Advance the phase-2 intro slideshow and its one-shot audio cues."""
    if game.intro_step >= len(INTRO_SLIDE_DURATIONS_MS):
        game.state = GameState.MENU
        return
    duration = INTRO_SLIDE_DURATIONS_MS[game.intro_step]
    if (
        game.intro_step == 0
        and elapsed < 50
        and not getattr(game, "laugh_played", False)
    ):
        game.sound_manager.play_sound("laugh")
        game.laugh_played = True
    if elapsed <= duration:
        return
    game.intro_step += 1
    game.intro_start_time = 0
    if hasattr(game, "laugh_played"):
        del game.laugh_played
