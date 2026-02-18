"""Base class for FPS raycaster games (Duum, Force_Field, Zombie_Survival).

Consolidates identical methods shared across FPS games to eliminate
code duplication. Each game subclass passes its own constants module
via __init__ and overrides game-specific behavior.

Usage:
    from games.shared.fps_game_base import FPSGameBase
    from . import constants as C

    class Game(FPSGameBase):
        def __init__(self):
            super().__init__(C)
            # game-specific init...
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class FPSGameBase:
    """Base class for FPS raycaster games.

    Subclasses must set up the following attributes before calling
    any base methods:
        - self.C: constants module
        - self.render_scale: int
        - self.raycaster: Raycaster | None
        - self.damage_texts: list[dict]
        - self.unlocked_weapons: set[str]
        - self.player: Player | None
        - self.game_map: Map | None
        - self.selected_map_size: int
        - self.portal: dict | None
        - self.last_death_pos: tuple | None
        - self.entity_manager: EntityManager
    """

    # --- Properties ---

    @property
    def bots(self) -> list[Any]:
        """Get list of active bots."""
        return self.entity_manager.bots

    @property
    def projectiles(self) -> list[Any]:
        """Get list of active projectiles."""
        return self.entity_manager.projectiles

    # --- Identical methods extracted from all 3 FPS games ---

    def cycle_render_scale(self) -> None:
        """Cycle through render scales."""
        scales = [1, 2, 4, 8]
        try:
            idx = scales.index(self.render_scale)
            self.render_scale = scales[(idx + 1) % len(scales)]
        except ValueError:
            self.render_scale = 2

        if self.raycaster:
            self.raycaster.set_render_scale(self.render_scale)

        scale_names = {1: "ULTRA", 2: "HIGH", 4: "MEDIUM", 8: "LOW"}
        msg = f"QUALITY: {scale_names.get(self.render_scale, 'CUSTOM')}"
        self.add_message(msg, self.C.WHITE)

    def add_message(self, text: str, color: tuple[int, int, int]) -> None:
        """Add a temporary message to the center of the screen."""
        self.damage_texts.append(
            {
                "x": self.C.SCREEN_WIDTH // 2,
                "y": self.C.SCREEN_HEIGHT // 2 - 50,
                "text": text,
                "color": color,
                "timer": 60,
                "vy": -0.5,
            }
        )

    def switch_weapon_with_message(self, weapon_name: str) -> None:
        """Switch weapon and show a message if successful."""
        if weapon_name not in self.unlocked_weapons:
            self.add_message("WEAPON LOCKED", self.C.RED)
            return

        assert self.player is not None
        if self.player.current_weapon != weapon_name:
            self.player.switch_weapon(weapon_name)
            self.add_message(f"SWITCHED TO {weapon_name.upper()}", self.C.YELLOW)

    def spawn_portal(self) -> None:
        """Spawn exit portal at last death position or near player."""
        if self.last_death_pos:
            self.portal = {
                "x": self.last_death_pos[0],
                "y": self.last_death_pos[1],
            }
            return

        assert self.player is not None
        if self.game_map:
            for r in range(2, 10):
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    tx = int(self.player.x + math.cos(rad) * r)
                    ty = int(self.player.y + math.sin(rad) * r)
                    if not self.game_map.is_wall(tx, ty):
                        self.portal = {"x": tx + 0.5, "y": ty + 0.5}
                        return

    def find_safe_spawn(
        self,
        base_x: float,
        base_y: float,
        angle: float,
    ) -> tuple[float, float, float]:
        """Find a safe spawn position near the base coordinates."""
        game_map = self.game_map
        map_size = game_map.size if game_map else self.selected_map_size
        if not game_map:
            return (base_x, base_y, angle)

        for attempt in range(10):
            radius = attempt * 2
            for angle_offset in [
                0,
                math.pi / 4,
                math.pi / 2,
                3 * math.pi / 4,
                math.pi,
                5 * math.pi / 4,
                3 * math.pi / 2,
                7 * math.pi / 4,
            ]:
                test_x = base_x + math.cos(angle_offset) * radius
                test_y = base_y + math.sin(angle_offset) * radius

                in_x = test_x >= 2 and test_x < map_size - 2
                in_y = test_y >= 2 and test_y < map_size - 2
                if not (in_x and in_y):
                    continue

                if not game_map.is_wall(test_x, test_y):
                    return (test_x, test_y, angle)

        return (base_x, base_y, angle)

    def get_corner_positions(self) -> list[tuple[float, float, float]]:
        """Get spawn positions for four corners (x, y, angle)."""
        offset = 5
        map_size = self.game_map.size if self.game_map else self.selected_map_size

        building4_start = int(map_size * 0.75)
        bottom_right_offset = map_size - building4_start + self.C.SPAWN_SAFETY_MARGIN

        corners = [
            (offset, offset, math.pi / 4),
            (offset, map_size - offset, 7 * math.pi / 4),
            (map_size - offset, offset, 3 * math.pi / 4),
            (
                map_size - bottom_right_offset,
                map_size - bottom_right_offset,
                5 * math.pi / 4,
            ),
        ]

        safe_corners = []
        for x, y, angle in corners:
            safe_corners.append(self.find_safe_spawn(x, y, angle))

        return safe_corners

    def _get_best_spawn_point(self) -> tuple[float, float, float]:
        """Find a valid spawn point."""
        corners = self.get_corner_positions()
        random.shuffle(corners)

        game_map = self.game_map
        if not game_map:
            return self.C.DEFAULT_PLAYER_SPAWN

        for pos in corners:
            if not game_map.is_wall(pos[0], pos[1]):
                return pos

        for y in range(game_map.height):
            for x in range(game_map.width):
                if not game_map.is_wall(x, y):
                    return (x + 0.5, y + 0.5, 0.0)

        return self.C.DEFAULT_PLAYER_SPAWN

    def respawn_player(self) -> None:
        """Respawn player after death if lives remain."""
        assert self.game_map is not None
        assert self.player is not None

        player_pos = self._get_best_spawn_point()

        self.player.x = player_pos[0]
        self.player.y = player_pos[1]
        self.player.angle = player_pos[2]
        self.player.health = 100
        self.player.alive = True
        self.player.shield_active = False

        self.damage_texts.append(
            {
                "x": self.C.SCREEN_WIDTH // 2,
                "y": self.C.SCREEN_HEIGHT // 2,
                "text": "RESPAWNED",
                "color": self.C.GREEN,
                "timer": 120,
                "vy": -0.5,
            }
        )
