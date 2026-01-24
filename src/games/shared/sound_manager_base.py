"""Base class for game sound managers with singleton pattern."""

from __future__ import annotations

import contextlib
import logging
from pathlib import Path

import pygame

logger = logging.getLogger(__name__)


class SoundManagerBase:
    """Base class for managing sound effects and music with singleton pattern."""

    _instance: SoundManagerBase | None = None
    initialized: bool

    # Subclasses should override this with their sound file mappings
    SOUND_FILES: dict[str, str] = {}

    def __new__(cls) -> SoundManagerBase:  # noqa: PYI034
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        assert cls._instance is not None
        return cls._instance

    def __init__(self) -> None:
        """Initialize SoundManager."""
        if self.initialized:
            return

        # Re-initialize mixer with lower buffer to reduce latency
        with contextlib.suppress(Exception):
            pygame.mixer.quit()
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)

        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.music_channel = None
        self.sound_enabled = True
        self.current_music: str | None = None

        # Load assets
        self.load_assets()
        self.initialized = True

    def load_assets(self) -> None:
        """Load all sound files from the game's assets directory."""
        base_dir = Path(__file__).resolve().parent.parent.parent / self.get_game_name()
        sound_dir = base_dir / "assets" / "sounds"

        for name, filename in self.SOUND_FILES.items():
            path = sound_dir / filename
            if path.exists():
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                    # Lower volume for ambient to be background
                    if "music" in name or name == "ambient":
                        self.sounds[name].set_volume(0.5)
                except Exception:
                    msg = "Failed to load sound %s (probably codec issue?)"
                    logger.exception(msg, filename)
            else:
                msg = "Sound file not found: %s (Current Dir: %s)"
                logger.warning(msg, path, Path.cwd())

    def get_game_name(self) -> str:
        """Get the game name from the class module path.

        Subclasses can override this if needed.
        """
        # Extract game name from module path
        # (e.g., 'src.games.Duum.src.sound' -> 'Duum')
        module_parts = self.__class__.__module__.split(".")
        if (
            len(module_parts) >= 3
            and module_parts[0] == "src"
            and module_parts[1] == "games"
        ):
            return module_parts[2]
        return "unknown"

    def play_sound(self, name: str) -> None:
        """Play a sound effect."""
        if not self.sound_enabled:
            return

        if name in self.sounds:
            try:
                self.sounds[name].play()
            except BaseException:
                logger.exception("Sound play failed for %s", name)

    def start_music(self, name: str = "music_loop") -> None:
        """Start ambient music loop."""
        if not self.sound_enabled:
            return

        self.stop_music()

        if name in self.sounds:
            # -1 means loop indefinitely
            self.sounds[name].play(loops=-1)
            self.current_music = name

    def stop_music(self) -> None:
        """Stop music."""
        if (
            hasattr(self, "current_music")
            and self.current_music
            and self.current_music in self.sounds
        ):
            self.sounds[self.current_music].stop()

        # Fallback
        if "ambient" in self.sounds:
            self.sounds["ambient"].stop()

    def pause_all(self) -> None:
        """Pause all sounds and music."""
        if self.sound_enabled:
            pygame.mixer.pause()

    def unpause_all(self) -> None:
        """Unpause all sounds and music."""
        if self.sound_enabled:
            pygame.mixer.unpause()
