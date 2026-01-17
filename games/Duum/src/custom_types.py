from __future__ import annotations

from typing import TypedDict

from games.shared.interfaces import EnemyData, LevelTheme, Portal, WeaponData


class DamageText(TypedDict):
    x: float
    y: float
    text: str
    color: tuple[int, int, int]
    timer: int
    vy: float


__all__ = ["DamageText", "EnemyData", "LevelTheme", "Portal", "WeaponData"]
