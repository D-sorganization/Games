"""Force Field-specific spawn manager."""

from __future__ import annotations

from typing import Any

from games.shared.spawn_manager import SpawnManagerBase

from . import constants as C  # noqa: N812
from .bot import Bot


class FFSpawnManager(SpawnManagerBase):
    """Spawn manager configured for Force Field."""

    SPAWN_EXCLUSIONS = [
        "boss",
        "demon",
        "ball",
        "beast",
        "health_pack",
        "ammo_box",
        "bomb_item",
        "pickup_rocket",
        "pickup_flamethrower",
        "pickup_pulse",
        "pickup_freezer",
    ]

    BOSS_OPTIONS = ["ball", "beast"]
    WEAPON_PICKUPS = [
        "pickup_rifle",
        "pickup_shotgun",
        "pickup_plasma",
        "pickup_minigun",
        "pickup_flamethrower",
        "pickup_pulse",
        "pickup_freezer",
    ]

    def __init__(self, entity_manager: Any) -> None:
        super().__init__(entity_manager, C)

    def _make_bot(
        self,
        x: float,
        y: float,
        level: int,
        enemy_type: str,
        difficulty: str = "NORMAL",
    ) -> Bot:
        return Bot(x, y, level, enemy_type, difficulty=difficulty)
