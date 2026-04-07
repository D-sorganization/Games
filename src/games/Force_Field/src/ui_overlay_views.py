from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .game import Game
    from .ui_renderer import UIRenderer


def render_pause_menu(renderer: UIRenderer, game: Game) -> None:
    """Render the pause menu overlay."""
    overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    renderer.screen.blit(overlay, (0, 0))

    title = renderer.title_font.render("PAUSED", True, C.RED)
    title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 150))
    renderer.screen.blit(title, title_rect)

    if game.cheat_mode_active:
        cheats_surface = renderer.subtitle_font.render(
            "ENTER CHEAT CODE:",
            True,
            C.CYAN,
        )
        cheats_rect = cheats_surface.get_rect(center=(C.SCREEN_WIDTH // 2, 350))
        renderer.screen.blit(cheats_surface, cheats_rect)

        input_text = game.current_cheat_input + "_"
        input_surface = renderer.font.render(input_text, True, C.WHITE)
        input_rect = input_surface.get_rect(center=(C.SCREEN_WIDTH // 2, 400))

        background_rect = input_rect.copy()
        background_rect.width = max(300, input_rect.width + 80)
        background_rect.height = input_rect.height + 30
        background_rect.center = input_rect.center

        pygame.draw.rect(renderer.screen, C.DARK_GRAY, background_rect)
        pygame.draw.rect(renderer.screen, C.CYAN, background_rect, 2)

        renderer.screen.blit(input_surface, input_rect)

        hint = renderer.tiny_font.render(
            "PRESS ENTER TO SUBMIT, ESC TO CANCEL",
            True,
            C.GRAY,
        )
        hint_rect = hint.get_rect(center=(C.SCREEN_WIDTH // 2, 450))
        renderer.screen.blit(hint, hint_rect)
        return

    menu_items = ["RESUME", "SAVE GAME", "ENTER CHEAT", "CONTROLS", "QUIT TO MENU"]
    mouse_pos = pygame.mouse.get_pos()
    max_text_width = 0
    for item in menu_items:
        text_surface = renderer.subtitle_font.render(item, True, C.WHITE)
        max_text_width = max(max_text_width, text_surface.get_width())

    box_width = max_text_width + 60
    box_height = 50

    for index, item in enumerate(menu_items):
        color = C.WHITE
        rect = pygame.Rect(
            C.SCREEN_WIDTH // 2 - box_width // 2,
            350 + index * 60,
            box_width,
            box_height,
        )
        if rect.collidepoint(mouse_pos):
            color = C.YELLOW
            pygame.draw.rect(renderer.screen, (50, 0, 0), rect)
            pygame.draw.rect(renderer.screen, C.RED, rect, 2)

        text = renderer.subtitle_font.render(item, True, color)
        text_rect = text.get_rect(center=rect.center)
        renderer.screen.blit(text, text_rect)

    slider_y = 350 + len(menu_items) * 60 + 30
    slider_label = renderer.font.render("Movement Speed:", True, C.WHITE)
    label_rect = slider_label.get_rect(center=(C.SCREEN_WIDTH // 2, slider_y))
    renderer.screen.blit(slider_label, label_rect)

    slider_bar_y = slider_y + 30
    slider_width = 200
    slider_height = 10
    slider_x = C.SCREEN_WIDTH // 2 - slider_width // 2
    slider_background_rect = pygame.Rect(
        slider_x, slider_bar_y, slider_width, slider_height
    )
    pygame.draw.rect(renderer.screen, C.DARK_GRAY, slider_background_rect)
    pygame.draw.rect(renderer.screen, C.WHITE, slider_background_rect, 2)

    speed_ratio = (game.movement_speed_multiplier - 0.5) / 1.5
    handle_x = slider_x + int(speed_ratio * slider_width)
    handle_rect = pygame.Rect(handle_x - 5, slider_bar_y - 5, 10, slider_height + 10)
    pygame.draw.rect(renderer.screen, C.CYAN, handle_rect)

    speed_text = f"{game.movement_speed_multiplier:.1f}x"
    speed_surface = renderer.font.render(speed_text, True, C.CYAN)
    speed_rect = speed_surface.get_rect(center=(C.SCREEN_WIDTH // 2, slider_bar_y + 25))
    renderer.screen.blit(speed_surface, speed_rect)


def render_key_config(renderer: UIRenderer, game: Any) -> None:
    """Render the key-configuration screen."""
    renderer.screen.fill(C.BLACK)

    title = renderer.title_font.render("CONTROLS", True, C.RED)
    renderer.screen.blit(title, title.get_rect(center=(C.SCREEN_WIDTH // 2, 50)))

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

    back_text = renderer.subtitle_font.render("BACK", True, C.WHITE)
    back_rect = back_text.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 60))
    renderer.screen.blit(back_text, back_rect)
    if back_rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(renderer.screen, C.RED, back_rect, 2)

    pygame.display.flip()
