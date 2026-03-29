"""Typed dataclasses for shared FPS game state.

Replaces ad-hoc dict literals with structured, self-documenting types
used across Duum, Force Field, and Zombie Survival.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IntroState:
    """State tracking for the multi-phase intro sequence."""

    phase: int = 0
    step: int = 0
    timer: int = 0
    start_time: int = 0
    laugh_played: bool = False
    water_played: bool = False


@dataclass
class GameplayState:
    """Core gameplay tracking shared across FPS games."""

    level: int = 1
    kills: int = 0
    lives: int = 3
    health: int = 100
    level_start_time: int = 0
    level_times: list[float] = field(default_factory=list)
    paused: bool = False
    pause_start_time: int = 0
    total_paused_time: int = 0
    show_damage: bool = True
    game_over_timer: int = 0


@dataclass
class ComboState:
    """Kill-combo and atmospheric timer tracking."""

    kill_combo_count: int = 0
    kill_combo_timer: int = 0
    heartbeat_timer: int = 0
    breath_timer: int = 0
    groan_timer: int = 0
    beast_timer: int = 0


@dataclass
class VisualEffectState:
    """Visual effect timers owned by the game loop."""

    damage_flash_timer: int = 0
    screen_shake: float = 0.0
    flash_intensity: float = 0.0


@dataclass
class DamageText:
    """Floating damage-number overlay drawn above a world position."""

    x: float
    y: float
    text: str
    color: tuple[int, int, int]
    timer: int
    vy: float = -0.5

    def to_dict(self) -> dict[str, object]:
        """Convert to dict for backward compatibility with dict-based consumers."""
        return {
            "x": self.x,
            "y": self.y,
            "text": self.text,
            "color": self.color,
            "timer": self.timer,
            "vy": self.vy,
        }
