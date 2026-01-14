import logging
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Any

import pygame

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("GameLauncher")

# Constants
WIDTH, HEIGHT = 1000, 700
BG_COLOR = (20, 20, 25)
TEXT_COLOR = (240, 240, 240)
TEXT_MUTED = (150, 150, 150)
HIGHLIGHT_COLOR = (60, 60, 80)
ACCENT_COLOR = (0, 200, 255)
ICON_SIZE = (128, 128)
GRID_COLS = 3
ITEM_WIDTH = 250
ITEM_HEIGHT = 200

# Base Dir
BASE_DIR = Path(__file__).resolve().parent
GAMES_DIR = BASE_DIR / "games"
ASSETS_DIR = BASE_DIR / "launcher_assets"

# Game Definitions
GAMES: list[dict[str, Any]] = [
    {
        "name": "Force Field",
        "description": "Defend the core from endless waves of enemies.",
        "icon": "force_field_icon.png",
        "type": "python",
        "path": GAMES_DIR / "Force_Field" / "force_field.py",
        "cwd": GAMES_DIR / "Force_Field",
        "description": (
            "A robust FPS with custom raycasting, 3D environments, and bot AI."
        ),
    },
    {
        "name": "Peanut Butter Panic",
        "description": "Protect your sandwiches from swarms of enemies!",
        "icon": "peanut_butter_panic_icon.png",
        "type": "module",
        "module_name": "peanut_butter_panic.game",
        "cwd": GAMES_DIR / "Peanut_Butter_Panic",
        "description": "A quirky arcade-style game where you panic over peanut butter.",
    },
    {
        "name": "Tetris",
        "description": "The classic tile-matching puzzle game.",
        "icon": "tetris_icon.png",
        "type": "python",
        "path": GAMES_DIR / "Tetris" / "tetris.py",
        "cwd": GAMES_DIR / "Tetris",
        "description": (
            "Modern puzzle game with hold mechanics, combos, and particle effects."
        ),
    },
    {
        "name": "Wizard of Wor",
        "description": "Battle monsters in this classic arcade maze shooter.",
        "icon": "wizard_of_wor_icon.png",
        "type": "python",
        "path": GAMES_DIR / "Wizard_of_Wor" / "wizard_of_wor" / "game.py",
        "cwd": GAMES_DIR / "Wizard_of_Wor" / "wizard_of_wor",
        "description": (
            "Classic arcade shooter remake. Battle monsters in a maze (1-2 Players)."
        ),
    },
    {
        "name": "Duum",
        "description": "A 3D raycasting shooter engine demo.",
        "icon": "doom_icon.png",
        "type": "python",
        "path": GAMES_DIR / "Duum" / "duum.py",
        "cwd": GAMES_DIR / "Duum",
        "description": (
            "High-octane FPS reimagining with projectile weapons and hordes of enemies."
        ),
    },
    {
        "name": "Zombie Games (Web)",
        "description": "A collection of web-based zombie survival games.",
        "icon": "zombie_games_icon.png",
        "type": "web",
        "path": GAMES_DIR / "Zombie_Games" / "Zombie_Game_v5" / "index.html",
        "description": "A collection of web-based 3D survival shooters.",
    },
]


def main() -> None:
    """
    Main entry point for the Game Launcher.
    Initializes Pygame, loads assets, and handles the main event loop.
    """
    pygame.display.init()
    pygame.font.init()
    pygame.display.set_caption("Game Launcher")

    # Set window icon
    icon_path = ASSETS_DIR / "force_field_icon.png"
    if icon_path.exists():
        pygame.display.set_icon(pygame.image.load(str(icon_path)))

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    font = pygame.font.SysFont("Segoe UI", 24)
    title_font = pygame.font.SysFont("Segoe UI", 48, bold=True)
    helper_font = pygame.font.SysFont("Segoe UI", 18)
    desc_font = pygame.font.SysFont("Segoe UI", 20, italic=True)

    # Load Icons
    for game in GAMES:
        icon_path = ASSETS_DIR / game["icon"]
        if icon_path.exists():
            img = pygame.image.load(str(icon_path))
            img = pygame.transform.smoothscale(img, ICON_SIZE)
            game["img"] = img
        else:
            # Fallback
            surf = pygame.Surface(ICON_SIZE)
            surf.fill((100, 100, 100))
            game["img"] = surf

    def draw_text(
        surf: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        pos: tuple[int, int],
        center: bool = False,
    ) -> None:
        """Helper to draw text on a surface."""
        t = font.render(text, True, color)
        if center:
            rect = t.get_rect(center=pos)
            surf.blit(t, rect)
        else:
            surf.blit(t, pos)

    def launch_game(game: dict[str, Any]) -> None:
        """Launches the selected game based on its type configuration."""
        logger.info(f"Launching {game['name']}...")
        if game["type"] == "python":
            try:
                # Use sys.executable to ensure we use the same python interpreter
                subprocess.Popen(
                    [sys.executable, str(game["path"])], cwd=str(game["cwd"])
                )
            except Exception as e:
                logger.error(f"Error launching {game['name']}: {e}")
        elif game["type"] == "module":
            try:
                subprocess.Popen(
                    [sys.executable, "-m", game["module_name"]], cwd=str(game["cwd"])
                )
            except Exception as e:
                logger.error(f"Error launching {game['name']}: {e}")
        elif game["type"] == "web":
            webbrowser.open(str(game["path"]))

    running = True
    clock = pygame.time.Clock()
    last_launch_time = 0.0
    selected_index = -1
    using_keyboard = False

    # Pre-calculate rects for consistent hit testing
    game_rects = []
    start_x = (WIDTH - (GRID_COLS * ITEM_WIDTH)) // 2
    start_y = 150
    for i in range(len(GAMES)):
        row = i // GRID_COLS
        col = i % GRID_COLS
        x = start_x + col * ITEM_WIDTH
        y = start_y + row * ITEM_HEIGHT
        game_rects.append(
            pygame.Rect(x + 10, y + 10, ITEM_WIDTH - 20, ITEM_HEIGHT - 20)
        )

    while running:
        mx, my = pygame.mouse.get_pos()
        hovered_any = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                if event.rel != (0, 0):
                    using_keyboard = False
                    if not pygame.mouse.get_visible():
                        pygame.mouse.set_visible(True)
            elif event.type == pygame.KEYDOWN:
                using_keyboard = True
                if pygame.mouse.get_visible():
                    pygame.mouse.set_visible(False)

                if event.key == pygame.K_ESCAPE:
                    running = False
                elif selected_index == -1:
                    selected_index = 0
                else:
                    if event.key == pygame.K_RIGHT:
                        selected_index = (selected_index + 1) % len(GAMES)
                    elif event.key == pygame.K_LEFT:
                        selected_index = (selected_index - 1) % len(GAMES)
                    elif event.key == pygame.K_DOWN:
                        new_idx = selected_index + GRID_COLS
                        if new_idx < len(GAMES):
                            selected_index = new_idx
                    elif event.key == pygame.K_UP:
                        new_idx = selected_index - GRID_COLS
                        if new_idx >= 0:
                            selected_index = new_idx
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        now = time.time()
                        if now - last_launch_time > 1.0:
                            last_launch_time = now
                            launch_game(GAMES[selected_index])

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for i, rect in enumerate(game_rects):
                        if rect.collidepoint(mx, my):
                            now = time.time()
                            if now - last_launch_time > 1.0:
                                last_launch_time = now
                                launch_game(GAMES[i])

        # Draw
        screen.fill(BG_COLOR)

        # Title
        draw_text(
            screen,
            "Game Launcher",
            title_font,
            ACCENT_COLOR,
            (WIDTH // 2, 60),
            center=True,
        )

        # Helper Text
        draw_text(
            screen,
            "Use Arrow Keys to Select • Enter to Start • Esc to Quit",
            helper_font,
            TEXT_MUTED,
            (WIDTH // 2, HEIGHT - 30),
            center=True,
        )

        # Description Text (if selected)
        if selected_index != -1 and selected_index < len(GAMES):
            desc = GAMES[selected_index].get("description", "")
            if desc:
                draw_text(
                    screen,
                    desc,
                    desc_font,
                    TEXT_COLOR,
                    (WIDTH // 2, HEIGHT - 70),
                    center=True,
                )

        for i, game in enumerate(GAMES):
            rect = game_rects[i]
            # is_selected is handled by is_highlighted logic below

            is_highlighted = False
            if using_keyboard:
                if i == selected_index:
                    is_highlighted = True
            else:
                if rect.collidepoint(mx, my):
                    is_highlighted = True
                    selected_index = i
                    hovered_any = True

            draw_rect = rect.copy()
            if is_highlighted:
                draw_rect.y -= 6

            bg = HIGHLIGHT_COLOR if is_highlighted else (30, 30, 35)
            pygame.draw.rect(screen, bg, draw_rect, border_radius=15)

            if is_highlighted:
                pygame.draw.rect(
                    screen, ACCENT_COLOR, draw_rect, width=2, border_radius=15
                )

            # Position variables needed for icon/text
            # Use draw_rect to ensure content moves with the background
            x = draw_rect.x - 10
            y = draw_rect.y - 10

            # Icon
            if "img" in game:
                game_img = game["img"]
                if isinstance(game_img, pygame.Surface):
                    icon_x = x + (ITEM_WIDTH - ICON_SIZE[0]) // 2
                    icon_y = y + 20
                    screen.blit(game_img, (icon_x, icon_y))

            # Name
            colors = ACCENT_COLOR if is_highlighted else TEXT_COLOR
            draw_text(
                screen,
                str(game["name"]),
                font,
                colors,
                (x + ITEM_WIDTH // 2, y + ICON_SIZE[1] + 30),
                center=True,
            )

        # Update Cursor
        if hovered_any:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
