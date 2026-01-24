"""Base class for game UI renderers with common initialization and asset loading."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

try:
    import cv2

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class UIRendererBase:
    """Base class for UI renderers with common font and asset loading."""

    def __init__(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        """Initialize the UI renderer base.

        Args:
            screen: Pygame surface to render to
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Load Intro Images
        self.intro_images: dict[str, pygame.Surface] = {}
        self.intro_video: Any | None = None
        self._load_assets()

        # Fonts
        self._init_fonts()

        # Optimization: Shared surface for alpha effects
        size = (screen_width, screen_height)
        self.overlay_surface = pygame.Surface(size, pygame.SRCALPHA)

        # Menu Visual State
        self.title_drips: list[dict[str, Any]] = []

    def _init_fonts(self) -> None:
        """Initialize fonts with fallback chain."""
        try:
            self.title_font = pygame.font.SysFont("impact", 100)
            self.font = pygame.font.SysFont("franklingothicmedium", 40)
            self.small_font = pygame.font.SysFont("franklingothicmedium", 28)
            self.tiny_font = pygame.font.SysFont("consolas", 20)
            self.subtitle_font = pygame.font.SysFont("georgia", 36)
            self.chiller_font = pygame.font.SysFont("chiller", 70)
        except Exception:  # noqa: BLE001
            self.title_font = pygame.font.Font(None, 80)
            self.font = pygame.font.Font(None, 48)
            self.small_font = pygame.font.Font(None, 32)
            self.tiny_font = pygame.font.Font(None, 24)
            self.subtitle_font = pygame.font.Font(None, 40)
            self.chiller_font = self.title_font

    def _get_base_dir(self) -> Path:
        """Get the base directory for the game.

        Subclasses can override this if needed.
        """
        return Path(__file__).resolve().parent.parent / self._get_game_name()

    def _get_game_name(self) -> str:
        """Get the game name from the class module path.

        Subclasses can override this if needed.
        """
        # Extract game name from module path
        # (e.g., 'games.Duum.src.ui_renderer' -> 'Duum')
        module_parts = self.__class__.__module__.split(".")
        if len(module_parts) >= 2 and module_parts[0] == "games":
            return module_parts[1]
        return "unknown"

    def _load_assets(self) -> None:
        """Load images and video assets."""
        try:
            base_dir = self._get_base_dir()
            self.assets_dir = str(base_dir / "assets")
            pics_dir = str(base_dir / "pics")

            # Willy Wonk image
            willy_path = os.path.join(pics_dir, "WillyWonk.JPG")
            if os.path.exists(willy_path):
                img = pygame.image.load(willy_path)
                img = pygame.transform.rotate(img, -90)
                scale = min(500 / img.get_height(), 800 / img.get_width())
                if scale < 1:
                    new_size = (
                        int(img.get_width() * scale),
                        int(img.get_height() * scale),
                    )
                    img = pygame.transform.scale(img, new_size)
                self.intro_images["willy"] = img

            # Setup Video
            video_path = os.path.join(pics_dir, "DeadFishSwimming.mp4")
            if HAS_CV2 and os.path.exists(video_path):
                self.intro_video = cv2.VideoCapture(video_path)

            # Fallback Image
            deadfish_path = os.path.join(pics_dir, "DeadFishSwimming_0.JPG")
            if os.path.exists(deadfish_path):
                img = pygame.image.load(deadfish_path)
                scale = min(500 / img.get_height(), 800 / img.get_width())
                if scale < 1:
                    new_size = (
                        int(img.get_width() * scale),
                        int(img.get_height() * scale),
                    )
                    img = pygame.transform.scale(img, new_size)
                self.intro_images["deadfish"] = img

        except Exception:
            logger.exception("Failed to load assets")

    def update_blood_drips(self, rect: pygame.Rect) -> None:
        """Update blood drip animations from title text.

        Args:
            rect: Rectangle of the title text to drip from
        """
        import random

        # Spawn new drips occasionally
        if random.random() < 0.05:
            x = rect.left + random.randint(0, rect.width)
            y = rect.bottom
            self.title_drips.append(
                {
                    "x": x,
                    "y": y,
                    "speed": random.uniform(1, 3),
                    "length": random.randint(10, 30),
                }
            )

        # Update existing drips
        for drip in self.title_drips[:]:
            drip["y"] += drip["speed"]
            # Remove drips that fall off screen
            if drip["y"] > self.screen_height:
                self.title_drips.remove(drip)

    def _draw_blood_drips(self, drips: list[dict[str, Any]]) -> None:
        """Draw blood drip effects.

        Args:
            drips: List of drip dictionaries with x, y, length properties
        """
        for drip in drips:
            # Draw drip as a vertical line with gradient
            start_y = int(drip["y"])
            end_y = int(drip["y"] + drip["length"])
            x = int(drip["x"])

            # Simple red line for drip
            if start_y < self.screen_height:
                pygame.draw.line(self.screen, (139, 0, 0), (x, start_y), (x, end_y), 2)
