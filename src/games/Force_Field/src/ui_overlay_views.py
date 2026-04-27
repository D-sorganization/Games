from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .game import Game
    from .ui_renderer import UIRenderer


def render_pause_menu(renderer: UIRenderer, game: Game) -> None:
    """Render the pause menu overlay."""
    _draw_pause_overlay_background(renderer)
    if game.cheat_mode_active:
        _draw_cheat_input(renderer, game)
        return
    _draw_pause_menu_items(renderer)
    _draw_speed_slider(renderer, game)


def _draw_pause_overlay_background(renderer: UIRenderer) -> None:
    """Draw the translucent black overlay and PAUSED title."""
    overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    renderer.screen.blit(overlay, (0, 0))
    title = renderer.title_font.render("PAUSED", True, C.RED)
    renderer.screen.blit(title, title.get_rect(center=(C.SCREEN_WIDTH // 2, 150)))


def _draw_cheat_input(renderer: UIRenderer, game: Game) -> None:
    """Draw the cheat-code input prompt in place of the normal menu."""
    cheats_surf = renderer.subtitle_font.render("ENTER CHEAT CODE:", True, C.CYAN)
    cx = C.SCREEN_WIDTH // 2
    renderer.screen.blit(cheats_surf, cheats_surf.get_rect(center=(cx, 350)))

    input_surf = renderer.font.render(game.current_cheat_input + "_", True, C.WHITE)
    input_rect = input_surf.get_rect(center=(C.SCREEN_WIDTH // 2, 400))
    bg = input_rect.copy()
    bg.width = max(300, input_rect.width + 80)
    bg.height = input_rect.height + 30
    bg.center = input_rect.center
    pygame.draw.rect(renderer.screen, C.DARK_GRAY, bg)
    pygame.draw.rect(renderer.screen, C.CYAN, bg, 2)
    renderer.screen.blit(input_surf, input_rect)

    hint = renderer.tiny_font.render(
        "PRESS ENTER TO SUBMIT, ESC TO CANCEL", True, C.GRAY
    )
    renderer.screen.blit(hint, hint.get_rect(center=(cx, 450)))


def _draw_pause_menu_items(renderer: UIRenderer) -> None:
    """Draw the clickable menu item boxes with hover highlight."""
    menu_items = ["RESUME", "SAVE GAME", "ENTER CHEAT", "CONTROLS", "QUIT TO MENU"]
    mouse_pos = pygame.mouse.get_pos()
    max_text_width = max(
        renderer.subtitle_font.render(item, True, C.WHITE).get_width()
        for item in menu_items
    )
    box_width = max_text_width + 60
    box_height = 50
    for index, item in enumerate(menu_items):
        rect = pygame.Rect(
            C.SCREEN_WIDTH // 2 - box_width // 2,
            350 + index * 60,
            box_width,
            box_height,
        )
        color = C.WHITE
        if rect.collidepoint(mouse_pos):
            color = C.YELLOW
            pygame.draw.rect(renderer.screen, (50, 0, 0), rect)
            pygame.draw.rect(renderer.screen, C.RED, rect, 2)
        text = renderer.subtitle_font.render(item, True, color)
        renderer.screen.blit(text, text.get_rect(center=rect.center))


def _draw_speed_slider(renderer: UIRenderer, game: Game) -> None:
    """Draw the movement-speed slider below the menu items."""
    slider_y = 350 + 5 * 60 + 30  # 5 == len(menu_items)
    label = renderer.font.render("Movement Speed:", True, C.WHITE)
    renderer.screen.blit(label, label.get_rect(center=(C.SCREEN_WIDTH // 2, slider_y)))

    bar_y = slider_y + 30
    bar_w, bar_h = 200, 10
    bar_x = C.SCREEN_WIDTH // 2 - bar_w // 2
    bar_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
    pygame.draw.rect(renderer.screen, C.DARK_GRAY, bar_rect)
    pygame.draw.rect(renderer.screen, C.WHITE, bar_rect, 2)

    ratio = (game.movement_speed_multiplier - 0.5) / 1.5
    handle_rect = pygame.Rect(bar_x + int(ratio * bar_w) - 5, bar_y - 5, 10, bar_h + 10)
    pygame.draw.rect(renderer.screen, C.CYAN, handle_rect)

    speed_surf = renderer.font.render(
        f"{game.movement_speed_multiplier:.1f}x", True, C.CYAN
    )
    cx = C.SCREEN_WIDTH // 2
    renderer.screen.blit(speed_surf, speed_surf.get_rect(center=(cx, bar_y + 25)))


def render_key_config(renderer: UIRenderer, game: Any) -> None:
    """Render the key-configuration screen."""
    renderer.screen.fill(C.BLACK)

    title = renderer.title_font.render("CONTROLS", True, C.RED)
    renderer.screen.blit(title, title.get_rect(center=(C.SCREEN_WIDTH // 2, 50)))

    _render_binding_rows(renderer, game)

    back_text = renderer.subtitle_font.render("BACK", True, C.WHITE)
    back_rect = back_text.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 60))
    renderer.screen.blit(back_text, back_rect)
    if back_rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(renderer.screen, C.RED, back_rect, 2)

    pygame.display.flip()


def _render_binding_rows(renderer: UIRenderer, game: Any) -> None:
    """Render each key-binding row in two columns."""
    bindings = game.input_manager.bindings
    start_y = 120
    column_one_x = C.SCREEN_WIDTH // 4
    column_two_x = C.SCREEN_WIDTH * 3 // 4
    actions = sorted(bindings.keys())
    column_limit = 12

    for index, action in enumerate(actions):
        column = 0 if index < column_limit else 1
        row_index = index if index < column_limit else index - column_limit
        x_pos = column_one_x if column == 0 else column_two_x
        y_pos = start_y + row_index * 40

        action_name = action.replace("_", " ").upper()
        color = C.YELLOW if game.binding_action == action else C.WHITE
        key_text = (
            "PRESS ANY KEY..."
            if game.binding_action == action
            else game.input_manager.get_key_name(action)
        )

        name_surface = renderer.tiny_font.render(f"{action_name}:", True, C.GRAY)
        key_surface = renderer.tiny_font.render(key_text, True, color)

        renderer.screen.blit(name_surface, (x_pos - 150, y_pos))
        renderer.screen.blit(key_surface, (x_pos + 20, y_pos))
