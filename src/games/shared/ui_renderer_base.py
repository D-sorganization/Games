"""Base class for game UI renderers with common initialization and asset loading."""

from __future__ import annotations

import logging
import math
import os
import random
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pygame

from games.shared.contracts import validate_not_none, validate_positive

try:
    import cv2

    HAS_CV2 = True
except ImportError:  # pragma: no cover
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
        validate_not_none(screen, "screen")
        validate_positive(screen_width, "screen_width")
        validate_positive(screen_height, "screen_height")
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
        except (pygame.error, OSError):
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

        except (pygame.error, FileNotFoundError, OSError, TypeError):
            logger.exception("Failed to load assets")

    def update_blood_drips(self, rect: pygame.Rect) -> None:
        """Update blood drip animations from title text.

        Args:
            rect: Rectangle of the title text to drip from
        """
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
        for drip in self.title_drips:
            drip["y"] += drip["speed"]
        self.title_drips = [d for d in self.title_drips if d["y"] <= self.screen_height]

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

    def render_subtitle_text(
        self, text: str, antialias: bool, color: tuple[int, int, int]
    ) -> pygame.Surface:
        """Render text using the subtitle font.

        Encapsulates font access so callers don't need to reach
        through to self.subtitle_font directly (Law of Demeter).
        """
        return self.subtitle_font.render(text, antialias, color)

    # ------------------------------------------------------------------
    # Intro slide rendering (DRY: extracted from per-game ui_renderers)
    # ------------------------------------------------------------------

    def _get_intro_slides(self) -> list[dict[str, Any]]:
        """Return the intro slide data for this game.

        Subclasses should override this to provide game-specific slide content.
        Default returns an empty list (no intro).
        """
        return []

    def _get_game_title(self) -> str:
        """Return the game title used for title-slide effects.

        Subclasses should override to return their title string
        (e.g. 'DUUM', 'FORCE FIELD', 'ZOMBIE SURVIVAL').
        """
        return ""

    def _get_subtitle_color(self) -> tuple[int, int, int]:
        """Return the color used for subtitle text on static slides.

        Defaults to red (200, 0, 0). Subclasses can override.
        """
        return (200, 0, 0)

    def _get_constants_module(self) -> Any:
        """Return the game's constants module (provides SCREEN_WIDTH, etc.).

        Subclasses must override this.
        """
        raise NotImplementedError  # pragma: no cover

    def _render_intro_slide(self, step: int, elapsed: int) -> None:
        """Render intro slides using data from _get_intro_slides().

        Args:
            step: Current slide index.
            elapsed: Milliseconds elapsed in the current slide.
        """
        slides = self._get_intro_slides()
        C = self._get_constants_module()
        game_title = self._get_game_title()
        sub_color = self._get_subtitle_color()

        if step >= len(slides):
            return

        slide = slides[step]
        duration = int(cast("int", slide["duration"]))

        if slide["type"] == "distortion":
            self._render_distortion_slide(slide, C)
        elif slide["type"] == "story":
            self._render_story_slide(slide, duration, elapsed, C)
        elif slide["type"] == "static":
            self._render_static_slide(
                slide, duration, elapsed, C, game_title, sub_color
            )

    def _render_distortion_slide(self, slide: dict[str, Any], C: Any) -> None:
        """Render a distortion-type intro slide with jittering characters."""
        font = self.chiller_font
        lines = [str(slide["text"])]
        if "text2" in slide:
            lines.append(str(slide["text2"]))

        start_y = C.SCREEN_HEIGHT // 2 - (len(lines) * 80) // 2
        for i, text in enumerate(lines):
            total_w = sum(font.size(c)[0] for c in text)
            start_x = (C.SCREEN_WIDTH - total_w) // 2
            y = start_y + i * 100
            x_off = 0
            for idx, char in enumerate(text):
                tf = pygame.time.get_ticks() * 0.003 + idx * 0.2
                jx = math.sin(tf * 2.0) * 2
                jy = math.cos(tf * 1.5) * 4
                c_val = int(120 + 135 * abs(math.sin(tf * 0.8)))

                self.screen.blit(
                    font.render(char, True, (50, 0, 0)),
                    (start_x + x_off + jx + 2, y + jy + 2),
                )
                self.screen.blit(
                    font.render(char, True, (c_val, 0, 0)),
                    (start_x + x_off + jx, y + jy),
                )
                x_off += font.size(char)[0]

    def _render_story_slide(
        self,
        slide: dict[str, Any],
        duration: int,
        elapsed: int,
        C: Any,
    ) -> None:
        """Render a story-type intro slide with sequentially revealed lines."""
        lines = cast("list[str]", slide["lines"])
        show_count = int((elapsed / duration) * (len(lines) + 1))
        show_count = min(show_count, len(lines))
        y = C.SCREEN_HEIGHT // 2 - (len(lines) * 50) // 2
        for i in range(show_count):
            s = self.subtitle_font.render(lines[i], True, C.RED)
            self.screen.blit(s, s.get_rect(center=(C.SCREEN_WIDTH // 2, y)))
            y += 50

    def _render_static_slide(
        self,
        slide: dict[str, Any],
        duration: int,
        elapsed: int,
        C: Any,
        game_title: str,
        sub_color: tuple[int, int, int],
    ) -> None:
        """Render a static-type intro slide with optional title fade and blood drips."""
        color = cast("tuple[int, int, int]", slide.get("color", C.WHITE))
        if slide["text"] == game_title:
            fade = min(1.0, elapsed / duration)
            r = 255
            g = int(255 + (0 - 255) * fade)
            b = int(255 + (0 - 255) * fade)
            color = (r, g, b)

        txt = self.title_font.render(str(slide["text"]), True, color)
        rect = txt.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2))
        if slide["text"] == game_title:
            rect.centery = 100  # Match Main Menu title position
        self.screen.blit(txt, rect)

        if (
            slide["text"] == game_title
            and color[0] > 250
            and color[1] < 10
            and color[2] < 10
        ):
            self.update_blood_drips(rect)
            self._draw_blood_drips(self.title_drips)

        if "sub" in slide:
            sub = self.subtitle_font.render(str(slide["sub"]), True, sub_color)
            self.screen.blit(
                sub,
                sub.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 60)),
            )
