"""Base class for game UI renderers with common initialization and asset loading."""

from __future__ import annotations

import logging
import math
import os
import random
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pygame

from games.shared.contracts import (
    validate_non_negative,
    validate_not_none,
    validate_positive,
)

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

    # Intro branding. Defaults cover the "Upstream Drift" titled games;
    # subclasses override these class attributes for their own title card.
    INTRO_TITLE = "UPSTREAM DRIFT"
    INTRO_SUBTITLE = "in association with"
    INTRO_SUBTITLE_COLOR = (0, 255, 255)
    INTRO_BG_COLOR = (0, 0, 0)
    INTRO_PRODUCTION_TEXT = "A Willy Wonk Production"
    INTRO_PRODUCTION_COLOR = (255, 182, 193)
    INTRO_PRODUCTION_BORDER_COLOR = (255, 192, 203)
    # Phase-1 still images tried in priority order (video frame is preferred).
    DEADFISH_IMAGE_FILES = ("DeadFishSwimming_0.JPG", "Deadfish.gif")

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
            self._load_willy_image(pics_dir)
            self._load_intro_video(pics_dir)
            self._load_deadfish_image(pics_dir)
        except (pygame.error, FileNotFoundError, OSError, TypeError):
            logger.exception("Failed to load assets")

    def _load_and_scale_image(
        self,
        path: str,
        *,
        rotate: int = 0,
        max_height: int = 500,
        max_width: int = 800,
    ) -> pygame.Surface:
        """Load an image, optionally rotate it, and downscale it to fit a box.

        Args:
            path: Filesystem path to the image to load.
            rotate: Degrees to rotate the image after loading (0 skips rotation).
            max_height: Maximum height in pixels; must be positive.
            max_width: Maximum width in pixels; must be positive.

        Returns:
            The loaded surface, rotated and/or scaled down as needed.
        """
        validate_not_none(path, "path")
        validate_positive(max_height, "max_height")
        validate_positive(max_width, "max_width")
        img = pygame.image.load(path)
        if rotate:
            img = pygame.transform.rotate(img, rotate)
        scale = min(max_height / img.get_height(), max_width / img.get_width())
        if scale < 1:
            img = pygame.transform.scale(
                img, (int(img.get_width() * scale), int(img.get_height() * scale))
            )
        return img

    def _load_willy_image(self, pics_dir: str) -> None:
        """Load and rotate the WillyWonk intro image when it is present."""
        willy_path = os.path.join(pics_dir, "WillyWonk.JPG")
        if not os.path.exists(willy_path):
            return
        self.intro_images["willy"] = self._load_and_scale_image(willy_path, rotate=-90)

    def _load_intro_video(self, pics_dir: str) -> None:
        """Load the DeadFishSwimming video if cv2 is available."""
        video_path = os.path.join(pics_dir, "DeadFishSwimming.mp4")
        if HAS_CV2 and os.path.exists(video_path):
            self.intro_video = cv2.VideoCapture(video_path)

    def _load_deadfish_image(self, pics_dir: str) -> None:
        """Load the first available dead-fish still as the video fallback.

        The original asset name (``DeadFishSwimming_0.JPG``) is tried first for
        backwards compatibility, then the ``Deadfish.gif`` that ships in each
        game's ``pics`` directory.
        """
        for filename in self.DEADFISH_IMAGE_FILES:
            path = os.path.join(pics_dir, filename)
            if os.path.exists(path):
                self.intro_images["deadfish"] = self._load_and_scale_image(path)
                return

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

    def release_intro_video(self) -> None:
        """Release the intro video capture and clear the reference."""
        if self.intro_video is not None:
            self.intro_video.release()
            self.intro_video = None

    def render_intro(self, intro_phase: int, intro_step: int, elapsed: int) -> None:
        """Render the active intro phase to the screen.

        Args:
            intro_phase: Active phase (0 = production card, 1 = title + media,
                2 = story slides).
            intro_step: Index of the active phase-2 story slide.
            elapsed: Milliseconds elapsed within the current phase.
        """
        validate_non_negative(intro_phase, "intro_phase")
        validate_non_negative(intro_step, "intro_step")
        validate_non_negative(elapsed, "elapsed")
        self.screen.fill(self.INTRO_BG_COLOR)
        if intro_phase == 0:
            self._render_intro_phase0()
        elif intro_phase == 1:
            self._render_intro_phase1(elapsed)
        elif intro_phase == 2:
            self._render_intro_slide(intro_step, elapsed)
        pygame.display.flip()

    def _render_intro_phase0(self) -> None:
        """Render the production-card intro phase."""
        text = self.subtitle_font.render(
            self.INTRO_PRODUCTION_TEXT, True, self.INTRO_PRODUCTION_COLOR
        )
        self.screen.blit(text, text.get_rect(center=(self.screen_width // 2, 100)))
        if "willy" in self.intro_images:
            img = self.intro_images["willy"]
            rect = img.get_rect(
                center=(self.screen_width // 2, self.screen_height // 2 + 30)
            )
            self.screen.blit(img, rect)
            pygame.draw.rect(
                self.screen,
                self.INTRO_PRODUCTION_BORDER_COLOR,
                rect,
                4,
                border_radius=10,
            )

    def _render_intro_phase1(self, elapsed: int) -> None:
        """Render the pulsing title and dead-fish media for intro phase 1."""
        title_font = pygame.font.SysFont("impact", 70)
        pulse = abs(math.sin(elapsed * 0.003))
        title_color = (0, int(150 + 100 * pulse), int(200 + 55 * pulse))
        title = title_font.render(self.INTRO_TITLE, True, title_color)
        self.screen.blit(
            title,
            title.get_rect(
                center=(self.screen_width // 2, self.screen_height // 2 - 180)
            ),
        )
        subtitle = self.tiny_font.render(
            self.INTRO_SUBTITLE, True, self.INTRO_SUBTITLE_COLOR
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(
                center=(self.screen_width // 2, self.screen_height // 2 - 230)
            ),
        )
        self._render_intro_phase1_media()

    def _render_intro_phase1_media(self) -> None:
        """Render the dead-fish video frame, falling back to the still image."""
        if self.intro_video and self.intro_video.isOpened():
            ret, frame = self.intro_video.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = frame.swapaxes(0, 1)
                surf = pygame.surfarray.make_surface(frame)
                scale = 400 / surf.get_height()
                surf = pygame.transform.scale(
                    surf,
                    (int(surf.get_width() * scale), int(surf.get_height() * scale)),
                )
                self.screen.blit(
                    surf,
                    surf.get_rect(
                        center=(self.screen_width // 2, self.screen_height // 2 + 50)
                    ),
                )
            else:
                self.intro_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        elif "deadfish" in self.intro_images:
            img = self.intro_images["deadfish"]
            self.screen.blit(
                img,
                img.get_rect(
                    center=(self.screen_width // 2, self.screen_height // 2 + 50)
                ),
            )

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
