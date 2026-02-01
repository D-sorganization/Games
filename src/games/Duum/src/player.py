from __future__ import annotations

import math
from typing import TYPE_CHECKING

from games.shared.player_base import PlayerBase

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .bot import Bot
    from .map import Map


class Player(PlayerBase):
    """Player with position, rotation, and shooting capabilities"""

    # Explicitly re-annotate inherited attributes for mypy
    health: int

    def __init__(self, x: float, y: float, angle: float):
        """Initialize player"""
        super().__init__(x, y, angle, C.WEAPONS, C)

        # Head Bobbing (Distance based)
        self.bob_phase = 0.0
        self.walk_distance = 0.0

    def move(
        self,
        game_map: Map,
        bots: list[Bot],
        forward: bool = True,
        speed: float = C.PLAYER_SPEED,
    ) -> None:
        """Move player forward or backward"""
        if self.shield_active or self.zoomed:
            if self.zoomed:
                return
            if self.shield_active:
                speed *= 0.8

        dx = math.cos(self.angle) * speed * (1 if forward else -1)
        dy = math.sin(self.angle) * speed * (1 if forward else -1)

        from games.shared.utils import try_move_entity

        old_x, old_y = self.x, self.y
        try_move_entity(self, dx, dy, game_map, bots, radius=0.5)

        dist_moved = math.sqrt((self.x - old_x) ** 2 + (self.y - old_y) ** 2)
        if dist_moved > 0.001:
            self.is_moving = True
            self.walk_distance += dist_moved * 0.8
        else:
            self.is_moving = False

    def strafe(
        self,
        game_map: Map,
        bots: list[Bot],
        right: bool = True,
        speed: float = C.PLAYER_SPEED,
    ) -> None:
        """Strafe left or right"""
        if self.zoomed:
            return
        if self.shield_active:
            speed *= 0.8

        angle = self.angle + math.pi / 2 * (1 if right else -1)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed

        from games.shared.utils import try_move_entity

        old_x, old_y = self.x, self.y
        try_move_entity(self, dx, dy, game_map, bots, radius=0.5)

        dist_moved = math.sqrt((self.x - old_x) ** 2 + (self.y - old_y) ** 2)
        if dist_moved > 0.001:
            self.is_moving = True
            self.walk_distance += dist_moved * 0.8

    def take_damage(self, damage: int) -> None:
        """Take damage"""
        if self.shield_active or self.god_mode:
            return
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def update(self) -> None:
        """Update player state (timers, etc)"""
        self.update_timers()

        # Update Bobbing Phase
        if self.is_moving:
            self.bob_phase = self.walk_distance
        else:
            self.bob_phase = self.bob_phase * 0.9

        self.update_weapon_state()
