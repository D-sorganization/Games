import logging
import os
import random

import pygame

logger = logging.getLogger(__name__)


def _draw_title_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    width: int,
    height: int,
) -> None:
    """Render the 3-D shadow + outline + main title text onto *surface*."""
    YELLOW = (255, 255, 0)
    BLUE = (0, 100, 255)

    for off in range(8, 0, -1):
        color_val = max(20, 100 - off * 10)
        shadow_color = (0, 0, color_val)
        render = font.render(text, True, shadow_color)
        rect = render.get_rect(center=(width // 2 + off, height // 2 + off))
        surface.blit(render, rect)

    for offx in [-2, 0, 2]:
        for offy in [-2, 0, 2]:
            if offx == 0 and offy == 0:
                continue
            render = font.render(text, True, BLUE)
            rect = render.get_rect(center=(width // 2 + offx, height // 2 + offy))
            surface.blit(render, rect)

    render = font.render(text, True, YELLOW)
    rect = render.get_rect(center=(width // 2, height // 2))
    surface.blit(render, rect)


def create_title_image() -> None:
    """Create a title image for Wizard of Wor game."""
    pygame.init()

    width = 600
    height = 200
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    try:
        font = pygame.font.SysFont("arial", 72, bold=True)
    except (pygame.error, OSError):
        font = pygame.font.Font(None, 72)

    _draw_title_text(surface, font, "WIZARD OF WOR", width, height)

    for _ in range(20):
        x = random.randint(50, 550)
        y = random.randint(50, 150)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 2)

    path = os.path.join(os.path.dirname(__file__), "title.png")
    pygame.image.save(surface, path)
    logger.info("Created %s", path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    create_title_image()
