from __future__ import annotations

from typing import Protocol, TypedDict, runtime_checkable


class EnemyData(TypedDict, total=False):
    """Configuration data for an enemy type, controlling stats and appearance."""

    color: tuple[int, int, int]
    health_mult: float
    speed_mult: float
    damage_mult: float
    scale: float
    visual_style: str


class WeaponData(TypedDict, total=False):
    """Configuration data for a weapon, covering damage, ammo, and fire mode."""

    name: str
    damage: int
    range: int
    ammo: int
    cooldown: int
    clip_size: int
    reload_time: int
    key: str
    automatic: bool
    fire_mode: str  # "hitscan", "projectile", "spread", "beam", "burst"
    spin_up_time: int
    heat_per_shot: float
    max_heat: float
    cooling_rate: float
    overheat_penalty: int
    projectile_speed: float
    projectile_color: tuple[int, int, int]
    beam_color: tuple[int, int, int]
    beam_width: int
    aoe_radius: float
    pellets: int
    spread: float


class Portal(TypedDict):
    """World position of a level portal or teleporter."""

    x: float
    y: float


@runtime_checkable
class Map(Protocol):
    """Protocol for tile-based game maps supporting wall queries."""

    grid: list[list[int]]
    size: int

    @property
    def width(self) -> int: ...  # pragma: no cover

    @property
    def height(self) -> int: ...  # pragma: no cover

    def is_wall(self, x: float, y: float) -> bool: ...  # pragma: no cover
    def get_wall_type(self, x: float, y: float) -> int: ...  # pragma: no cover


class LevelTheme(TypedDict):
    """Color palette for a level's floor, ceiling, and wall types."""

    floor: tuple[int, int, int]
    ceiling: tuple[int, int, int]
    walls: dict[int, tuple[int, int, int]]


@runtime_checkable
class Bot(Protocol):
    """Protocol for enemy bots with position, state, and damage interface."""

    x: float
    y: float
    z: float = 0.0
    alive: bool
    removed: bool
    dead: bool
    death_timer: float
    disintegrate_timer: float
    enemy_type: str
    type_data: EnemyData
    walk_animation: float
    shoot_animation: float
    frozen: bool
    mouth_open: bool

    def take_damage(
        self, damage: int, is_headshot: bool = False
    ) -> bool: ...  # pragma: no cover


@runtime_checkable
class WorldParticle(Protocol):
    """Protocol for 3D particles positioned in world space."""

    x: float
    y: float
    z: float
    alive: bool
    size: float
    color: tuple[int, int, int]


@runtime_checkable
class Projectile(Protocol):
    """Protocol for in-flight projectiles with position, damage, and weapon metadata."""

    x: float
    y: float
    z: float
    alive: bool
    size: float
    color: tuple[int, int, int]
    weapon_type: str
    damage: int


@runtime_checkable
class Player(Protocol):
    """Protocol for the player character, exposing position, orientation, and state."""

    x: float
    y: float
    angle: float
    pitch: float
    zoomed: bool
    is_moving: bool
