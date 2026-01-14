from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .interfaces import LevelTheme


@dataclass
class RaycasterConfig:
    SCREEN_WIDTH: int
    SCREEN_HEIGHT: int
    FOV: float
    HALF_FOV: float
    ZOOM_FOV_MULT: float = 0.5
    DEFAULT_RENDER_SCALE: int = 1
    MAX_DEPTH: float = 20.0
    FOG_START: float = 0.6
    FOG_COLOR: tuple[int, int, int] = (0, 0, 0)
    LEVEL_THEMES: Sequence[LevelTheme] | None = None
    WALL_COLORS: dict[int, tuple[int, int, int]] | None = None
    DARK_GRAY: tuple[int, int, int] = (40, 40, 40)
    BLACK: tuple[int, int, int] = (0, 0, 0)
    CYAN: tuple[int, int, int] = (0, 255, 255)
    RED: tuple[int, int, int] = (255, 0, 0)
    GREEN: tuple[int, int, int] = (0, 255, 0)
    GRAY: tuple[int, int, int] = (128, 128, 128)
    ENEMY_TYPES: dict[str, Any] | None = None
    WHITE: tuple[int, int, int] = (255, 255, 255)
    YELLOW: tuple[int, int, int] = (255, 255, 0)
