import socket
import subprocess
import sys
import threading
import webbrowser
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

import pygame

# Constants
WIDTH, HEIGHT = 1000, 700
BG_COLOR = (20, 20, 25)
TEXT_COLOR = (240, 240, 240)
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

# Server Globals
SERVER_PORT = 0
SERVER_THREAD: threading.Thread | None = None


def start_server() -> None:
    """Start a local HTTP server to serve web games."""
    global SERVER_PORT, SERVER_THREAD
    if SERVER_THREAD is not None:
        return

    class CORSRequestHandler(SimpleHTTPRequestHandler):
        def end_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            super().end_headers()

    # Find a free port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    SERVER_PORT = sock.getsockname()[1]
    sock.close()

    def run() -> None:
        handler = partial(CORSRequestHandler, directory=str(GAMES_DIR))
        # HTTPServer expects a callable that accepts (request, client_address, server)
        # partial(CORSRequestHandler, directory=...) works because
        # SimpleHTTPRequestHandler takes directory as kwarg.
        try:
            server = HTTPServer(("localhost", SERVER_PORT), handler)
            server.serve_forever()
        except Exception as e:
            print(f"Server error: {e}")

    SERVER_THREAD = threading.Thread(target=run, daemon=True)
    SERVER_THREAD.start()


# Game Definitions
GAMES: list[dict[str, Any]] = [
    {
        "name": "Force Field",
        "icon": "force_field_icon.png",
        "type": "python",
        "path": GAMES_DIR / "Force_Field" / "force_field.py",
        "cwd": GAMES_DIR / "Force_Field",
    },
    {
        "name": "Peanut Butter Panic",
        "icon": "peanut_butter_panic_icon.png",
        "type": "python",
        "path": GAMES_DIR / "Peanut_Butter_Panic" / "peanut_butter_panic" / "game.py",
        "cwd": GAMES_DIR / "Peanut_Butter_Panic",
    },
    {
        "name": "Tetris",
        "icon": "tetris_icon.png",
        "type": "python",
        "path": GAMES_DIR / "Tetris" / "tetris.py",
        "cwd": GAMES_DIR / "Tetris",
    },
    {
        "name": "Wizard of Wor",
        "icon": "wizard_of_wor_icon.png",
        "type": "python",
        "path": GAMES_DIR / "Wizard_of_Wor" / "wizard_of_wor" / "game.py",
        "cwd": GAMES_DIR / "Wizard_of_Wor" / "wizard_of_wor",
    },
    {
        "name": "Duum",
        "icon": "doom_icon.png",
        "type": "python",
        "path": GAMES_DIR / "Duum" / "duum.py",
        "cwd": GAMES_DIR / "Duum",
    },
    {
        "name": "Zombie Games (Web)",
        "icon": "zombie_games_icon.png",
        "type": "web",
        "path": GAMES_DIR / "Zombie_Games" / "Zombie_Game_v5" / "index.html",
    },
]


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Game Launcher")

    # Set window icon
    icon_path = ASSETS_DIR / "force_field_icon.png"
    if icon_path.exists():
        pygame.display.set_icon(pygame.image.load(str(icon_path)))

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    font = pygame.font.SysFont("Segoe UI", 24)
    title_font = pygame.font.SysFont("Segoe UI", 48, bold=True)

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
        t = font.render(text, True, color)
        if center:
            rect = t.get_rect(center=pos)
            surf.blit(t, rect)
        else:
            surf.blit(t, pos)

    last_launch_time = 0
    LAUNCH_COOLDOWN = 1000

    def launch_game(game: dict[str, Any]) -> None:
        nonlocal last_launch_time
        current_time = pygame.time.get_ticks()
        if current_time - last_launch_time < LAUNCH_COOLDOWN:
            print("Launch ignored (cooldown).")
            return
        last_launch_time = current_time

        print(f"Launching {game['name']}...")
        if game["type"] == "python":
            try:
                # Use sys.executable to ensure we use the same python interpreter
                subprocess.Popen(
                    [sys.executable, str(game["path"])], cwd=str(game["cwd"])
                )
            except Exception as e:
                print(f"Error launching {game['name']}: {e}")
        elif game["type"] == "web":
            path_obj = Path(game["path"])
            try:
                # Try to make path relative to GAMES_DIR
                rel_path = path_obj.relative_to(GAMES_DIR)
                start_server()
                # Wait briefly for server to start
                pygame.time.wait(100)
                url = f"http://localhost:{SERVER_PORT}/{rel_path.as_posix()}"
                print(f"Opening {url}")
                webbrowser.open(url)
            except ValueError:
                # If not in GAMES_DIR, open normally
                print(
                    "Path not relative to games dir, opening file directly: "
                    f"{game['path']}"
                )
                webbrowser.open(str(game["path"]))

    running = True
    clock = pygame.time.Clock()

    while running:
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Check clicks
                    start_x = (WIDTH - (GRID_COLS * ITEM_WIDTH)) // 2
                    start_y = 150

                    for i, game in enumerate(GAMES):
                        row = i // GRID_COLS
                        col = i % GRID_COLS
                        x = start_x + col * ITEM_WIDTH
                        y = start_y + row * ITEM_HEIGHT

                        rect = pygame.Rect(x, y, ITEM_WIDTH, ITEM_HEIGHT)
                        if rect.collidepoint(mx, my):
                            launch_game(game)

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

        # Grid
        start_x = (WIDTH - (GRID_COLS * ITEM_WIDTH)) // 2
        start_y = 150

        for i, game in enumerate(GAMES):
            row = i // GRID_COLS
            col = i % GRID_COLS
            x = start_x + col * ITEM_WIDTH
            y = start_y + row * ITEM_HEIGHT

            # Hover effect
            rect = pygame.Rect(x + 10, y + 10, ITEM_WIDTH - 20, ITEM_HEIGHT - 20)
            is_hovered = rect.collidepoint(mx, my)

            bg = HIGHLIGHT_COLOR if is_hovered else (30, 30, 35)
            pygame.draw.rect(screen, bg, rect, border_radius=15)

            # Icon
            if "img" in game:
                game_img = game["img"]
                if isinstance(game_img, pygame.Surface):
                    icon_x = x + (ITEM_WIDTH - ICON_SIZE[0]) // 2
                    icon_y = y + 20
                    screen.blit(game_img, (icon_x, icon_y))

            # Name
            colors = ACCENT_COLOR if is_hovered else TEXT_COLOR
            draw_text(
                screen,
                str(game["name"]),
                font,
                colors,
                (x + ITEM_WIDTH // 2, y + ICON_SIZE[1] + 30),
                center=True,
            )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
