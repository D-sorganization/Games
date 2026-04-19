"""Weapon firing system for Duum.

Extracted from game.py to keep that file within the repository's size budget.
Provides WeaponSystem, a focused helper that owns fire-mode dispatch, hitscan
checks, projectile spawning, and explosion delegation.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, cast

from games.shared.combat_manager import ShotResolutionRequest
from games.shared.constants import MINIGUN_BULLETS_PER_SHOT, MINIGUN_SPREAD

from . import constants as C  # noqa: N812
from .projectile import Projectile

if TYPE_CHECKING:
    from .game import Game
    from .player import Player


class WeaponSystem:
    """Handle weapon firing and combat delegation on behalf of Game."""

    _FIRE_DISPATCH: dict[str, str] = {
        "hitscan": "_fire_hitscan",
        "projectile": "_fire_projectile",
        "spread": "_fire_spread",
        "beam": "_fire_beam",
        "burst": "_fire_burst",
    }

    def __init__(self, game: Game) -> None:
        """Store a back-reference to the owning game."""
        self._game = game

    def fire_weapon(self, is_secondary: bool = False) -> None:
        """Handle weapon firing via data-driven dispatch."""
        game = self._game
        if not (game.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        player = cast("Player", game.player)
        weapon_name = player.current_weapon
        weapon_data = C.WEAPONS[weapon_name]

        game.sound_manager.play_sound(f"shoot_{weapon_name}")
        game.flash_intensity = 0.8

        if is_secondary:
            self.check_shot_hit(is_secondary=True)
            return

        fire_mode = weapon_data.get("fire_mode", "hitscan")
        handler = getattr(self, self._FIRE_DISPATCH[fire_mode])
        handler(weapon_data, weapon_name)

    def check_shot_hit(
        self,
        is_secondary: bool = False,
        angle_offset: float = 0.0,
        is_laser: bool = False,
    ) -> None:
        """Delegate hitscan hit detection to the combat manager."""
        game = self._game
        if not (game.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        if not (game.raycaster is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        player = cast("Player", game.player)
        game.damage_texts = game.combat_manager.check_shot_hit(
            ShotResolutionRequest(
                player=player,
                raycaster=game.raycaster,
                bots=game.bots,
                damage_texts=game.damage_texts,
                show_damage=game.show_damage,
                is_secondary=is_secondary,
                angle_offset=angle_offset,
                is_laser=is_laser,
            )
        )
        game.sync_combat_state()

    def handle_bomb_explosion(self) -> None:
        """Delegate bomb explosion to the combat manager."""
        game = self._game
        if not (game.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        player = cast("Player", game.player)
        game.damage_texts = game.combat_manager.handle_bomb_explosion(
            player=player,
            bots=game.bots,
            damage_texts=game.damage_texts,
        )
        game.sync_combat_state()

    def explode_laser(self, impact_x: float, impact_y: float) -> None:
        """Delegate laser explosion to the combat manager."""
        game = self._game
        game.damage_texts = game.combat_manager.explode_laser(
            impact_x, impact_y, game.damage_texts
        )
        game.sync_combat_state()

    def explode_plasma(self, projectile: Projectile) -> None:
        """Delegate plasma explosion to the combat manager."""
        game = self._game
        if not (game.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        player = cast("Player", game.player)
        game.damage_flash_timer = game.combat_manager.explode_generic(
            projectile,
            C.PLASMA_AOE_RADIUS,
            "plasma",
            player,
            game.damage_flash_timer,
        )
        game.sync_combat_state()

    def explode_rocket(self, projectile: Projectile) -> None:
        """Delegate rocket explosion to the combat manager."""
        game = self._game
        if not (game.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        player = cast("Player", game.player)
        radius = float(C.WEAPONS["rocket"].get("aoe_radius", 6.0))
        game.damage_flash_timer = game.combat_manager.explode_generic(
            projectile,
            radius,
            "rocket",
            player,
            game.damage_flash_timer,
        )
        game.sync_combat_state()

    def _fire_hitscan(self, weapon_data: dict[str, Any], weapon_name: str) -> None:
        """Fire a single hitscan ray."""
        self.check_shot_hit(is_secondary=False)

    def _fire_projectile(self, weapon_data: dict[str, Any], weapon_name: str) -> None:
        """Spawn a projectile based on weapon data."""
        game = self._game
        if not (game.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        player = cast("Player", game.player)
        size_map = {"plasma": 0.225, "rocket": 0.3}
        projectile = Projectile(
            player.x,
            player.y,
            player.angle,
            speed=float(weapon_data.get("projectile_speed", 0.5)),
            damage=player.get_current_weapon_damage(),
            is_player=True,
            color=weapon_data.get("projectile_color", (0, 255, 255)),
            size=size_map.get(weapon_name, 0.3),
            weapon_type=weapon_name,
        )
        game.entity_manager.add_projectile(projectile)

    def _fire_spread(self, weapon_data: dict[str, Any], weapon_name: str) -> None:
        """Fire multiple pellets with spread."""
        pellets = int(weapon_data.get("pellets", 8))
        spread = float(weapon_data.get("spread", 0.15))
        for _ in range(pellets):
            angle_off = random.uniform(-spread, spread)
            self.check_shot_hit(angle_offset=angle_off)

    def _fire_beam(self, weapon_data: dict[str, Any], weapon_name: str) -> None:
        """Fire a hitscan beam with visual trail."""
        self.check_shot_hit(is_secondary=False, is_laser=True)

    def _fire_burst(self, weapon_data: dict[str, Any], weapon_name: str) -> None:
        """Fire a burst of fast projectiles."""
        game = self._game
        if not (game.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        player = cast("Player", game.player)
        damage = player.get_current_weapon_damage()
        for _ in range(MINIGUN_BULLETS_PER_SHOT):
            angle_off = random.uniform(-MINIGUN_SPREAD, MINIGUN_SPREAD)
            final_angle = player.angle + angle_off
            projectile = Projectile(
                player.x,
                player.y,
                final_angle,
                damage,
                speed=2.0,
                is_player=True,
                color=(255, 255, 0),
                size=0.1,
                weapon_type="minigun",
            )
            game.entity_manager.add_projectile(projectile)

        game.particle_system.add_explosion(
            C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2, count=8, color=(255, 255, 0)
        )
