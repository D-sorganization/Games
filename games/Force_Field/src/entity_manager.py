from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING

from . import constants as C  # noqa: N812
from .projectile import Projectile

if TYPE_CHECKING:
    from .bot import Bot
    from .game import Game
    from .map import Map
    from .player import Player

logger = logging.getLogger(__name__)


class EntityManager:
    """Manages game entities (Bots and Projectiles)"""

    def __init__(self) -> None:
        """Initialize the entity manager."""
        self.bots: list[Bot] = []
        self.projectiles: list[Projectile] = []

        # Spatial partitioning for optimized collision detection
        self.spatial_grid: dict[tuple[int, int], list[Bot]] = defaultdict(list)
        self.grid_cell_size = 5

    def reset(self) -> None:
        """Clear all entities."""
        self.bots = []
        self.projectiles = []
        self.spatial_grid.clear()

    def add_bot(self, bot: Bot) -> None:
        """Add a bot to the manager."""
        self.bots.append(bot)

    def add_projectile(self, projectile: Projectile) -> None:
        """Add a projectile to the manager."""
        self.projectiles.append(projectile)

    def _update_spatial_grid(self) -> None:
        """Update the spatial grid with current bot positions."""
        self.spatial_grid.clear()
        for bot in self.bots:
            if bot.alive:
                # Calculate grid cell coordinates
                cell_x = int(bot.x // self.grid_cell_size)
                cell_y = int(bot.y // self.grid_cell_size)
                self.spatial_grid[(cell_x, cell_y)].append(bot)

    def get_nearby_bots(self, x: float, y: float, radius: float = 1.0) -> list[Bot]:
        """Get bots near a specific location using the spatial grid."""
        cell_x = int(x // self.grid_cell_size)
        cell_y = int(y // self.grid_cell_size)

        nearby_bots = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cell_bots = self.spatial_grid.get((cell_x + dx, cell_y + dy))
                if cell_bots:
                    nearby_bots.extend(cell_bots)
        return nearby_bots

    def update_bots(self, game_map: Map, player: Player, game: Game) -> None:
        """Update all bots."""
        self._update_spatial_grid()

        new_projectiles = []

        for bot in self.bots:
            nearby_bots = self.get_nearby_bots(bot.x, bot.y)
            projectile = bot.update(game_map, player, nearby_bots)
            if projectile:
                new_projectiles.append(projectile)
                game.sound_manager.play_sound("enemy_shoot")

        self.projectiles.extend(new_projectiles)
        self.cleanup_dead_bots()

    def update_projectiles(self, game_map: Map, player: Player, game: Game) -> None:
        """Update all projectiles."""
        for projectile in self.projectiles[:]:
            was_alive = projectile.alive
            projectile.update(game_map)

            if was_alive and not projectile.alive:
                w_type = getattr(projectile, "weapon_type", "normal")
                if w_type == "plasma":
                    game.combat_system.explode_plasma(projectile)
                elif w_type == "rocket":
                    game.combat_system.explode_rocket(projectile)
                elif w_type == "bomb":
                    game.combat_system.explode_bomb(projectile)

            if projectile.alive:
                if not projectile.is_player:
                    # Enemy projectile hitting player
                    dx = projectile.x - player.x
                    dy = projectile.y - player.y
                    dist_sq = dx * dx + dy * dy
                    if dist_sq < 0.25:
                        old_health = player.health
                        player.take_damage(projectile.damage)
                        if player.health < old_health:
                            game.damage_flash_timer = 10
                            game.sound_manager.play_sound("oww")
                        projectile.alive = False
                else:
                    # Player projectile hitting bots
                    potential_targets = self.get_nearby_bots(projectile.x, projectile.y)
                    for bot in potential_targets:
                        if not bot.alive:
                            continue
                        dx = projectile.x - bot.x
                        dy = projectile.y - bot.y
                        dist_sq = dx * dx + dy * dy
                        if dist_sq < 0.64:
                            if bot.take_damage(projectile.damage):
                                game.sound_manager.play_sound("scream")
                                game.kills += 1
                                game.kill_combo_count += 1
                                game.kill_combo_timer = 180
                                game.last_death_pos = (bot.x, bot.y)

                            game.particle_system.add_explosion(
                                C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2, count=5
                            )
                            projectile.alive = False
                            w_type = getattr(projectile, "weapon_type", "normal")
                            if w_type == "plasma":
                                game.combat_system.explode_plasma(projectile)
                            elif w_type == "rocket":
                                game.combat_system.explode_rocket(projectile)
                            break

        self.projectiles = [p for p in self.projectiles if p.alive]

    def cleanup_dead_bots(self) -> None:
        """Remove fully disintegrated bots."""
        self.bots = [b for b in self.bots if not b.removed]

    def get_active_enemies(self) -> list[Bot]:
        """Return list of alive enemies (excluding items)."""
        return [
            b
            for b in self.bots
            if b.alive and b.type_data.get("visual_style") != "item"
        ]

    def get_nearest_enemy_distance(self, x: float, y: float) -> float:
        """Get the distance to the nearest enemy."""
        min_dist_sq = float("inf")

        # Optimization: Only check nearby cells in spatial grid if possible?
        # For now, we can iterate all or optimize using spatial grid.
        # Since sound effect range is global/large, checking all active bots is robust,
        # but using spatial grid for neighbors is better if sound range is small.
        # However, the original code checked ALL bots.

        # If we just want "nearest" globally, we have to check all or do a BFS.
        # Iterating all active bots for correctness matches original logic.

        for bot in self.bots:
            if bot.alive:
                dx = bot.x - x
                dy = bot.y - y
                d_sq = dx * dx + dy * dy
                if d_sq < min_dist_sq:
                    min_dist_sq = d_sq

        return min_dist_sq**0.5 if min_dist_sq != float("inf") else float("inf")
