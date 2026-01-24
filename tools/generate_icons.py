from pathlib import Path

import pygame

# Initialize Pygame
pygame.init()

# Constants
ICON_SIZE = (512, 512)
OUTPUT_DIR = Path(__file__).parent.parent / "launcher_assets"
OUTPUT_DIR.mkdir(exist_ok=True)

COLORS = {
    "neon_blue": (0, 255, 255),
    "neon_purple": (180, 0, 255),
    "black": (0, 0, 0),
    "red": (200, 0, 0),
    "dark_red": (100, 0, 0),
    "green": (0, 200, 0),
    "dark_green": (0, 100, 0),
    "brown": (139, 69, 19),
    "orange": (255, 140, 0),
    "dark_blue": (0, 0, 139),
    "yellow": (255, 255, 0),
}


def save_icon(surface: pygame.Surface, name: str) -> None:
    """Write a generated icon to disk."""
    path = OUTPUT_DIR / f"{name}.png"
    pygame.image.save(surface, str(path))
    print(f"Saved {path}")


def create_force_field_icon() -> None:
    """Generate the Force Field icon asset."""
    surf = pygame.Surface(ICON_SIZE)
    surf.fill(COLORS["black"])

    center = (256, 256)
    # Outer glow
    pygame.draw.circle(surf, COLORS["neon_blue"], center, 200, 10)
    # Inner field
    s = pygame.Surface(ICON_SIZE, pygame.SRCALPHA)
    pygame.draw.circle(s, (*COLORS["neon_purple"], 100), center, 180)
    surf.blit(s, (0, 0))
    # Core
    pygame.draw.circle(surf, (255, 255, 255), center, 50)
    pygame.draw.circle(surf, COLORS["neon_blue"], center, 50, 5)

    save_icon(surf, "force_field_icon")


def create_doom_icon() -> None:
    """Generate the Duum icon asset."""
    surf = pygame.Surface(ICON_SIZE)
    surf.fill(COLORS["black"])

    # Red background (hellish)
    rect = pygame.Rect(50, 50, 412, 412)
    pygame.draw.rect(surf, COLORS["dark_red"], rect)

    # Crosshair
    center = (256, 256)
    pygame.draw.circle(surf, (0, 0, 0), center, 100, 20)
    pygame.draw.line(surf, (0, 0, 0), (256, 100), (256, 412), 20)
    pygame.draw.line(surf, (0, 0, 0), (100, 256), (412, 256), 20)

    save_icon(surf, "doom_icon")


def create_peanut_butter_panic_icon() -> None:
    """Generate the Peanut Butter Panic icon asset."""
    surf = pygame.Surface(ICON_SIZE)
    surf.fill((255, 228, 196))  # Bisque background

    # Jar shape
    jar_rect = pygame.Rect(156, 156, 200, 250)
    pygame.draw.rect(surf, COLORS["brown"], jar_rect, border_radius=20)

    # Label
    pygame.draw.rect(surf, COLORS["orange"], (156, 220, 200, 100))

    # Exclamation mark
    font = pygame.font.SysFont("Arial", 150, bold=True)
    text = font.render("!", True, COLORS["black"])
    text_rect = text.get_rect(center=(256, 270))
    surf.blit(text, text_rect)

    save_icon(surf, "peanut_butter_panic_icon")


def create_tetris_icon() -> None:
    """Generate the Tetris icon asset."""
    surf = pygame.Surface(ICON_SIZE)
    surf.fill(COLORS["black"])

    # Blocks
    block_size = 80
    start_x = 136
    start_y = 100

    # T shape
    colors = [
        COLORS["neon_purple"],
        COLORS["neon_blue"],
        COLORS["orange"],
        COLORS["green"],
    ]
    positions = [(1, 0), (0, 1), (1, 1), (2, 1)]  # T top  # T bottom

    for i, (gx, gy) in enumerate(positions):
        rect = pygame.Rect(
            start_x + gx * block_size,
            start_y + gy * block_size,
            block_size - 2,
            block_size - 2,
        )
        pygame.draw.rect(surf, colors[i % len(colors)], rect)

    save_icon(surf, "tetris_icon")


def create_wizard_of_wor_icon() -> None:
    """Generate the Wizard of Wor icon asset."""
    surf = pygame.Surface(ICON_SIZE)
    surf.fill(COLORS["dark_blue"])

    # Star/Spark
    points = [
        (256, 50),
        (300, 200),
        (462, 256),
        (300, 312),
        (256, 462),
        (212, 312),
        (50, 256),
        (212, 200),
    ]
    pygame.draw.polygon(surf, COLORS["yellow"], points)

    save_icon(surf, "wizard_of_wor_icon")


def create_zombie_games_icon() -> None:
    """Generate the Zombie Survival icon asset."""
    surf = pygame.Surface(ICON_SIZE)
    surf.fill(COLORS["black"])

    # Green ground/fog
    pygame.draw.rect(surf, COLORS["dark_green"], (0, 300, 512, 212))

    # Tombstone shape
    pygame.draw.rect(
        surf,
        (100, 100, 100),
        (200, 150, 112, 200),
        border_top_left_radius=50,
        border_top_right_radius=50,
    )

    # Hand reaching out
    pygame.draw.line(surf, (0, 255, 0), (256, 400), (256, 300), 10)
    pygame.draw.circle(surf, (0, 255, 0), (256, 300), 20)

    save_icon(surf, "zombie_games_icon")


if __name__ == "__main__":
    create_force_field_icon()
    create_doom_icon()
    create_peanut_butter_panic_icon()
    create_tetris_icon()
    create_wizard_of_wor_icon()
    create_zombie_games_icon()
    pygame.quit()
