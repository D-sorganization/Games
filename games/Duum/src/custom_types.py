from __future__ import annotations

from typing import TypedDict


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


class EnemyData(TypedDict, total=False):
    color: tuple[int, int, int]
    health_mult: float
    speed_mult: float
    damage_mult: float
    scale: float
    visual_style: str


class LevelTheme(TypedDict):
    floor: tuple[int, int, int]
    ceiling: tuple[int, int, int]
    walls: dict[int, tuple[int, int, int]]
