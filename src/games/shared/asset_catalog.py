"""Shared asset loading with caching for game resources.

Provides centralized path resolution and cached loading for
images, sounds, and data files across all games.

Usage:
    from games.shared.asset_catalog import AssetCatalog

    catalog = AssetCatalog("/path/to/game")
    data = catalog.load_json("levels/level1.json")
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from games.shared.contracts import validate_not_none

logger = logging.getLogger(__name__)


class AssetCatalog:
    """Centralized asset loader with path resolution and caching."""

    def __init__(self, base_dir: str | Path) -> None:
        validate_not_none(base_dir, "base_dir")
        self._base = Path(base_dir)
        self._assets_dir = self._base / "assets"
        self._cache: dict[str, Any] = {}

    @property
    def base_dir(self) -> Path:
        """The base directory for this catalog."""
        return self._base

    @property
    def assets_dir(self) -> Path:
        """The assets subdirectory."""
        return self._assets_dir

    def resolve_path(self, *parts: str) -> Path:
        """Resolve a path relative to the assets directory."""
        return self._assets_dir.joinpath(*parts)

    def exists(self, *parts: str) -> bool:
        """Check if an asset file exists."""
        return self.resolve_path(*parts).exists()

    def load_json(self, filename: str) -> dict[str, Any] | None:
        """Load a JSON data file with caching."""
        key = f"json:{filename}"
        if key in self._cache:
            return self._cache[key]

        path = self.resolve_path("data", filename)
        if not path.exists():
            path = self.resolve_path(filename)

        if not path.exists():
            logger.warning("JSON not found: %s", path)
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._cache[key] = data
            return data
        except (OSError, json.JSONDecodeError):
            logger.exception("Failed to load JSON: %s", path)
            return None

    def load_text(self, filename: str) -> str | None:
        """Load a text file with caching."""
        key = f"text:{filename}"
        if key in self._cache:
            return self._cache[key]

        path = self.resolve_path(filename)
        if not path.exists():
            logger.warning("Text file not found: %s", path)
            return None

        try:
            text = path.read_text(encoding="utf-8")
            self._cache[key] = text
            return text
        except OSError:
            logger.exception("Failed to load text: %s", path)
            return None

    def load_sound(self, filename: str, volume: float = 1.0) -> Any:
        """Load a sound file with caching. Returns pygame.mixer.Sound or None."""
        key = f"sound:{filename}"
        if key in self._cache:
            return self._cache[key]

        path = self.resolve_path("sounds", filename)
        if not path.exists():
            logger.warning("Sound not found: %s", path)
            return None

        try:
            import pygame

            sound = pygame.mixer.Sound(str(path))
            sound.set_volume(volume)
            self._cache[key] = sound
            return sound
        except Exception:
            logger.exception("Failed to load sound: %s", path)
            return None

    def load_image(self, filename: str, alpha: bool = True) -> Any:
        """Load an image file with caching. Returns pygame.Surface or None."""
        key = f"image:{filename}:{alpha}"
        if key in self._cache:
            return self._cache[key]

        path = self.resolve_path("images", filename)
        if not path.exists():
            logger.warning("Image not found: %s", path)
            return None

        try:
            import pygame

            surface = pygame.image.load(str(path))
            surface = surface.convert_alpha() if alpha else surface.convert()
            self._cache[key] = surface
            return surface
        except Exception:
            logger.exception("Failed to load image: %s", path)
            return None

    def clear_cache(self) -> None:
        """Clear all cached assets."""
        self._cache.clear()

    @property
    def cache_size(self) -> int:
        """Number of cached assets."""
        return len(self._cache)
