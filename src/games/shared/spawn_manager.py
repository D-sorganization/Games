"""Base class for spawn managers.

Encapsulates enemy spawning, position validation, and level scaling
logic that was previously duplicated across game.py files.

Subclasses override constants and Bot construction as needed.
"""

from __future__ import annotations

import logging
import random
from typing import Any

logger = logging.getLogger(__name__)


class SpawnManagerBase:
    """Manages enemy, boss, pickup, and item spawning for FPS games.

    Dependencies are injected via the constructor -- the manager never
    holds a reference back to the Game object.

    Args:
        entity_manager: The EntityManager that owns bot/projectile lists.
        constants: The game-specific constants module (C).
    """

    # Subclasses should set these to control spawn behavior.
    # They can also be overridden per-instance via constructor kwargs.
    SPAWN_EXCLUSIONS: list[str] = [
        "boss",
        "demon",
        "ball",
        "beast",
        "health_pack",
        "ammo_box",
        "bomb_item",
    ]

    BOSS_OPTIONS: list[str] = ["ball", "beast"]

    WEAPON_PICKUPS: list[str] = [
        "pickup_rifle",
        "pickup_shotgun",
        "pickup_plasma",
        "pickup_minigun",
    ]

    PICKUP_CHANCE: float = 0.4
    ITEM_COUNT: int = 8

    def __init__(
        self,
        entity_manager: Any,
        constants: Any,
    ) -> None:
        self.entity_manager = entity_manager
        self.C = constants

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def spawn_all(
        self,
        player_pos: tuple[float, float, float],
        game_map: Any,
        level: int,
        difficulty: str,
    ) -> None:
        """Spawn all entities for a new level.

        Args:
            player_pos: (x, y, angle) of the player spawn.
            game_map: The Map instance.
            level: Current game level (1-based).
            difficulty: Difficulty key (e.g. "NORMAL").
        """
        self.spawn_enemies(player_pos, game_map, level, difficulty)
        self.spawn_boss(player_pos, game_map, level, difficulty)
        self.spawn_pickups(game_map, level)
        self.spawn_items(game_map, level)

    # ------------------------------------------------------------------
    # Spawning methods (override in subclasses for game-specific logic)
    # ------------------------------------------------------------------

    def _make_bot(
        self,
        x: float,
        y: float,
        level: int,
        enemy_type: str,
        difficulty: str = "NORMAL",
    ) -> Any:
        """Create a Bot instance.  Subclasses must override this."""
        raise NotImplementedError("Subclasses must implement _make_bot")

    def _get_num_enemies(self, level: int, difficulty: str) -> int:
        """Calculate number of enemies to spawn for a level."""
        score_mult = self.C.DIFFICULTIES[difficulty]["score_mult"]
        return int(min(50, 5 + level * 2 * score_mult))

    def _get_enemy_type(self) -> str:
        """Choose a random valid enemy type (excluding bosses/items)."""
        keys = list(self.C.ENEMY_TYPES.keys())
        enemy_type = random.choice(keys)
        while self._is_excluded(enemy_type):
            enemy_type = random.choice(keys)
        return enemy_type

    def _is_excluded(self, enemy_type: str) -> bool:
        """Check if an enemy type should be excluded from regular spawning."""
        if enemy_type in self.SPAWN_EXCLUSIONS:
            return True
        if enemy_type.startswith("pickup"):
            return True
        return False

    def spawn_enemies(
        self,
        player_pos: tuple[float, float, float],
        game_map: Any,
        level: int,
        difficulty: str,
    ) -> None:
        """Spawn regular enemies for the level."""
        num_enemies = self._get_num_enemies(level, difficulty)
        safe_radius_sq = getattr(self.C, "SPAWN_SAFE_ZONE_RADIUS", 15.0) ** 2

        for _ in range(num_enemies):
            placed = False
            for attempt in range(50):
                bx = random.randint(2, game_map.size - 2)
                by = random.randint(2, game_map.size - 2)

                # Relax distance check on later attempts
                min_dist_sq = safe_radius_sq if attempt < 40 else safe_radius_sq * 0.25
                dist_sq = (bx - player_pos[0]) ** 2 + (by - player_pos[1]) ** 2

                if dist_sq < min_dist_sq and attempt < 49:
                    continue

                if not game_map.is_wall(bx, by):
                    enemy_type = self._get_enemy_type()
                    self.entity_manager.add_bot(
                        self._make_bot(
                            bx + 0.5, by + 0.5, level, enemy_type, difficulty
                        )
                    )
                    placed = True
                    break

            if not placed:
                logger.warning("Failed to spawn enemy after 50 attempts.")

    def spawn_boss(
        self,
        player_pos: tuple[float, float, float],
        game_map: Any,
        level: int,
        difficulty: str,
    ) -> None:
        """Spawn a boss enemy far from the player."""
        boss_type = random.choice(self.BOSS_OPTIONS)
        min_boss_dist = getattr(self.C, "MIN_BOSS_DISTANCE", 15.0)

        upper_bound = max(2, game_map.size - 3)
        for attempt in range(100):
            cx = random.randint(2, upper_bound)
            cy = random.randint(2, upper_bound)

            min_boss_dist_sq = (
                min_boss_dist**2 if attempt < 70 else (min_boss_dist * 0.7) ** 2
            )
            dist_sq = (cx - player_pos[0]) ** 2 + (cy - player_pos[1]) ** 2

            if not game_map.is_wall(cx, cy) and dist_sq > min_boss_dist_sq:
                self.entity_manager.add_bot(
                    self._make_bot(cx + 0.5, cy + 0.5, level, boss_type, difficulty)
                )
                break

    def spawn_pickups(self, game_map: Any, level: int) -> None:
        """Spawn weapon pickups on the map."""
        for w_pickup in self.WEAPON_PICKUPS:
            if random.random() < self.PICKUP_CHANCE:
                rx = random.randint(5, game_map.size - 5)
                ry = random.randint(5, game_map.size - 5)
                if not game_map.is_wall(rx, ry):
                    self.entity_manager.add_bot(
                        self._make_bot(rx + 0.5, ry + 0.5, level, w_pickup)
                    )

    def spawn_items(self, game_map: Any, level: int) -> None:
        """Spawn health packs, ammo boxes, and bombs."""
        for _ in range(self.ITEM_COUNT):
            rx = random.randint(5, game_map.size - 5)
            ry = random.randint(5, game_map.size - 5)
            if not game_map.is_wall(rx, ry):
                choice = random.random()
                if choice < 0.2:
                    item_type = "bomb_item"
                elif choice < 0.7:
                    item_type = "ammo_box"
                else:
                    item_type = "health_pack"
                self.entity_manager.add_bot(
                    self._make_bot(rx + 0.5, ry + 0.5, level, item_type)
                )
