import os
import random

import pygame


def create_title_image() -> None:
    """Create a title image for Wizard of Wor game."""
    pygame.init()

    # Create the surface (600x200 should be enough for the logo)
    width = 600
    height = 200
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    # Colors
    YELLOW = (255, 255, 0)
    BLUE = (0, 100, 255)

    # Try to find a bold font, fallback to default
    try:
        font = pygame.font.SysFont("arial", 72, bold=True)
    except Exception:  # Catch specific exception instead of bare except
        font = pygame.font.Font(None, 72)

    text = "WIZARD OF WOR"

    # Draw glow/shadow/3D effect
    # Deep shadow
    for off in range(8, 0, -1):
        color_val = max(20, 100 - off * 10)
        shadow_color = (0, 0, color_val)  # Dark Blue/Black fade
        render = font.render(text, True, shadow_color)
        rect = render.get_rect(center=(width // 2 + off, height // 2 + off))
        surface.blit(render, rect)

    # Blue outline
    for offx in [-2, 0, 2]:
        for offy in [-2, 0, 2]:
            if offx == 0 and offy == 0:
                continue
            render = font.render(text, True, BLUE)
            rect = render.get_rect(center=(width // 2 + offx, height // 2 + offy))
            surface.blit(render, rect)

    # Main text
    render = font.render(text, True, YELLOW)
    rect = render.get_rect(center=(width // 2, height // 2))
    surface.blit(render, rect)

    # Add some "sparkles"
    for _ in range(20):
        x = random.randint(50, 550)
        y = random.randint(50, 150)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 2)

    # Save
    path = os.path.join(os.path.dirname(__file__), "title.png")
    pygame.image.save(surface, path)
    print(f"Created {path}")


if __name__ == "__main__":
    create_title_image()
