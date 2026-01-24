from __future__ import annotations

from typing import Protocol, TypedDict, runtime_checkable


class EnemyData(TypedDict, total=False):
    color: tuple[int, int, int]
    health_mult: float
    speed_mult: float
    damage_mult: float
    scale: float
    visual_style: str


class WeaponData(TypedDict, total=False):
    name: str
    damage: int
    range: int
    ammo: int
    cooldown: int
    clip_size: int
    reload_time: int
    key: str
    automatic: bool
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
    x: float
    y: float


@runtime_checkable
class Map(Protocol):
    grid: list[list[int]]
    size: int

    @property
    def width(self) -> int:
        """Return the map width in tiles."""
        return 0

    @property
    def height(self) -> int:
        """Return the map height in tiles."""
        return 0

    def is_wall(self, x: float, y: float) -> bool:
        """Return True if the coordinate is a wall."""
        return False

    def get_wall_type(self, x: float, y: float) -> int:
        """Return the wall type at the coordinate."""
        return 0


class LevelTheme(TypedDict):
    floor: tuple[int, int, int]
    ceiling: tuple[int, int, int]
    walls: dict[int, tuple[int, int, int]]


@runtime_checkable
class Bot(Protocol):
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

    def take_damage(self, damage: int, is_headshot: bool = False) -> bool:
        """Apply damage and return True if the bot dies."""
        return False


@runtime_checkable
class WorldParticle(Protocol):
    x: float
    y: float
    z: float
    alive: bool
    size: float
    color: tuple[int, int, int]


@runtime_checkable
class Projectile(Protocol):
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
    x: float
    y: float
    angle: float
    pitch: float
    zoomed: bool
    is_moving: bool
