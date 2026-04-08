from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

import pygame

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .game import Game
    from .ui_renderer import UIRenderer


def render_menu(renderer: UIRenderer) -> None:
    """Render the Zombie Survival main menu."""
    renderer.screen.fill(C.BLACK)

    title = renderer.title_font.render("ZOMBIE SURVIVAL", True, C.RED)
    title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 100))

    subtitle = renderer.subtitle_font.render("UNDEAD NIGHTMARE", True, C.WHITE)
    subtitle_rect = subtitle.get_rect(center=(C.SCREEN_WIDTH // 2, 160))

    renderer.screen.blit(title, title_rect)
    renderer.screen.blit(subtitle, subtitle_rect)

    update_blood_drips(renderer, title_rect)
    draw_blood_drips(renderer, renderer.title_drips)

    if (pygame.time.get_ticks() // 500) % 2 == 0:
        prompt = renderer.font.render("CLICK TO BEGIN", True, C.GRAY)
        prompt_rect = prompt.get_rect(
            center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 150)
        )
        renderer.screen.blit(prompt, prompt_rect)

    credit = renderer.tiny_font.render("A Jasper Production", True, C.DARK_GRAY)
    credit_rect = credit.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 50))
    renderer.screen.blit(credit, credit_rect)
    pygame.display.flip()


def update_blood_drips(renderer: UIRenderer, rect: pygame.Rect) -> None:
    """Spawn and update menu blood drips."""
    if random.random() < 0.3:
        x = random.randint(rect.left, rect.right)
        renderer.title_drips.append(
            {
                "x": x,
                "y": rect.top,
                "start_y": rect.top,
                "speed": random.uniform(0.5, 2.0),
                "size": random.randint(2, 4),
                "color": (random.randint(180, 255), 0, 0),
            }
        )

    for drip in renderer.title_drips:
        drip["y"] += drip["speed"]
        drip["speed"] *= 1.02
    renderer.title_drips = [
        drip for drip in renderer.title_drips if drip["y"] <= C.SCREEN_HEIGHT
    ]


def draw_blood_drips(renderer: UIRenderer, drips: list[dict[str, Any]]) -> None:
    """Draw decorative menu blood drips."""
    for drip in drips:
        pygame.draw.line(
            renderer.screen,
            drip["color"],
            (drip["x"], drip["start_y"]),
            (drip["x"], drip["y"]),
            drip["size"],
        )
        pygame.draw.circle(
            renderer.screen,
            drip["color"],
            (drip["x"], int(drip["y"])),
            drip["size"] + 1,
        )


def render_map_select(renderer: UIRenderer, game: Game) -> None:
    """Render the Zombie Survival map-selection screen."""
    renderer.screen.fill(C.BLACK)

    title = renderer.subtitle_font.render("MISSION SETUP", True, C.RED)
    for off_x, off_y in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        shadow = renderer.subtitle_font.render("MISSION SETUP", True, (50, 0, 0))
        shadow_rect = shadow.get_rect(center=(C.SCREEN_WIDTH // 2 + off_x, 100 + off_y))
        renderer.screen.blit(shadow, shadow_rect)

    title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 100))
    renderer.screen.blit(title, title_rect)

    mouse_pos = pygame.mouse.get_pos()
    start_y = 200
    line_height = 80
    settings = [
        ("Map Size", str(game.selected_map_size)),
        ("Difficulty", game.selected_difficulty),
        ("Start Level", str(game.selected_start_level)),
        ("Lives", str(game.selected_lives)),
    ]

    for index, (label, value) in enumerate(settings):
        y_pos = start_y + index * line_height
        color = C.YELLOW if abs(mouse_pos[1] - y_pos) < 20 else C.WHITE

        label_surface = renderer.subtitle_font.render(f"{label}:", True, C.GRAY)
        label_rect = label_surface.get_rect(
            right=C.SCREEN_WIDTH // 2 - 20,
            centery=y_pos,
        )

        value_surface = renderer.subtitle_font.render(value, True, color)
        value_rect = value_surface.get_rect(
            left=C.SCREEN_WIDTH // 2 + 20,
            centery=y_pos,
        )

        renderer.screen.blit(label_surface, label_rect)
        renderer.screen.blit(value_surface, value_rect)

    renderer.start_button.draw(renderer.screen, renderer.font)

    instructions = [
        "",
        "",
        "WASD: Move | Shift: Sprint | Mouse: Look | 1-4: Weapons",
        "Ctrl: Shoot | Z: Zoom | F: Bomb | Space: Shield",
    ]
    y_pos = C.SCREEN_HEIGHT - 260
    for line in instructions:
        text = renderer.tiny_font.render(line, True, C.RED)
        text_rect = text.get_rect(center=(C.SCREEN_WIDTH // 2, y_pos))
        renderer.screen.blit(text, text_rect)
        y_pos += 30

    pygame.display.flip()
