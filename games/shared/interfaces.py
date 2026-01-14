from __future__ import annotations
from typing import Protocol, Any, runtime_checkable

@runtime_checkable
class Map(Protocol):
    grid: list[list[int]]
    width: int
    height: int
    size: int
    def is_wall(self, x: float, y: float) -> bool: ...
    def get_wall_type(self, x: float, y: float) -> int: ...

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
    type_data: dict[str, Any]
    walk_animation: float
    shoot_animation: float
    frozen: bool
    def take_damage(self, damage: int, is_headshot: bool = False) -> bool: ...

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
