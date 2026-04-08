from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .ui_renderer import UIRenderer


def render_pause_menu(renderer: UIRenderer) -> None:
    """Render the Zombie Survival pause menu overlay."""
    overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    renderer.screen.blit(overlay, (0, 0))

    title = renderer.title_font.render("PAUSED", True, C.RED)
    title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 150))
    renderer.screen.blit(title, title_rect)

    menu_items = ["RESUME", "SAVE GAME", "CONTROLS", "QUIT TO MENU"]
    mouse_pos = pygame.mouse.get_pos()

    for index, item in enumerate(menu_items):
        color = C.WHITE
        rect = pygame.Rect(C.SCREEN_WIDTH // 2 - 100, 350 + index * 60, 200, 50)
        if rect.collidepoint(mouse_pos):
            color = C.YELLOW
            pygame.draw.rect(renderer.screen, (50, 0, 0), rect)
            pygame.draw.rect(renderer.screen, C.RED, rect, 2)

        text = renderer.subtitle_font.render(item, True, color)
        text_rect = text.get_rect(center=rect.center)
        renderer.screen.blit(text, text_rect)


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
