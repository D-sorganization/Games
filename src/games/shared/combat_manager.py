"""Base class for combat managers.

Encapsulates hit detection, kill tracking, and hitscan shot logic.
Explosion helpers live in combat_explosions.py (_CombatExplosionsMixin).
Shot visual helpers live in combat_visuals.py (_CombatVisualsMixin).

Subclasses override constants and game-specific behavior as needed.
"""

from __future__ import annotations

import logging
import math
import random
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from games.shared.combat_explosions import _CombatExplosionsMixin
from games.shared.combat_visuals import _CombatVisualsMixin
from games.shared.constants import COMBO_TIMER_FRAMES

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ShotResolutionRequest:
    """Input contract for resolving one hitscan shot."""

    player: Any
    raycaster: Any
    bots: Sequence[Any]
    damage_texts: list[dict[str, Any]]
    show_damage: bool = True
    is_secondary: bool = False
    angle_offset: float = 0.0
    is_laser: bool = False


@dataclass(slots=True)
class ShotResolutionResult:
    """Resolved hit target and aim geometry for one hitscan shot."""

    aim_angle: float
    wall_distance: float
    closest_bot: Any | None
    closest_distance: float
    is_headshot: bool


class CombatManagerBase(_CombatExplosionsMixin, _CombatVisualsMixin):
    """Manages hit detection, damage calculation, and explosions.

    Dependencies are injected via the constructor -- the manager never
    holds a reference back to the Game object.

    Args:
        entity_manager: The EntityManager that owns bot/projectile lists.
        particle_system: The ParticleSystem for visual effects.
        sound_manager: The SoundManager for audio feedback.
        constants: The game-specific constants module (C).
    """

    def __init__(
        self,
        entity_manager: Any,
        particle_system: Any,
        sound_manager: Any,
        constants: Any,
        on_kill: Any | None = None,
    ) -> None:
        self.entity_manager = entity_manager
        self.particle_system = particle_system
        self.sound_manager = sound_manager
        self.C = constants
        self._on_kill = on_kill
        self.kills = 0
        self.kill_combo_count = 0
        self.kill_combo_timer = 0
        self.last_death_pos: tuple[float, float] | None = None

    def handle_kill(self, bot: Any) -> None:
        """Record a kill and update combo state."""
        self.kills += 1
        self.kill_combo_count += 1
        self.kill_combo_timer = COMBO_TIMER_FRAMES
        self.last_death_pos = (bot.x, bot.y)
        with suppress(Exception):
            self.sound_manager.play_sound("scream")
        if self._on_kill is not None:
            self._on_kill(bot)

    def check_shot_hit(self, request: ShotResolutionRequest) -> list[dict[str, Any]]:
        """Resolve a hitscan shot and apply the shared side effects."""
        try:
            resolution = self.resolve_shot_target(request)
            weapon_range = self._get_weapon_range(request.player, request.is_secondary)

            if request.is_secondary:
                self._handle_secondary_hit(
                    request.player,
                    resolution.closest_bot,
                    resolution.closest_distance,
                    resolution.wall_distance,
                    request.damage_texts,
                )
                return request.damage_texts

            if request.is_laser:
                self.particle_system.add_laser(
                    start=(self.C.SCREEN_WIDTH - 200, self.C.SCREEN_HEIGHT - 180),
                    end=(self.C.SCREEN_WIDTH // 2, self.C.SCREEN_HEIGHT // 2),
                    color=(255, 0, 0),
                    timer=5,
                    width=3,
                )

            if resolution.closest_bot:
                self._apply_hit_damage(
                    request.player,
                    resolution.closest_bot,
                    resolution.closest_distance,
                    weapon_range,
                    request.player.get_current_weapon_damage(),
                    resolution.is_headshot,
                    request.damage_texts,
                    request.show_damage,
                )

            self._add_shot_visuals(
                request.player,
                resolution.aim_angle,
                resolution.closest_bot,
                resolution.closest_distance,
                resolution.wall_distance,
            )
        except (ValueError, AttributeError, ZeroDivisionError):
            logger.exception("Error in check_shot_hit")

        return request.damage_texts

    def resolve_shot_target(
        self, request: ShotResolutionRequest
    ) -> ShotResolutionResult:
        """Resolve hit geometry without side effects."""
        weapon_range = self._get_weapon_range(request.player, request.is_secondary)
        aim_angle = self._resolve_aim_angle(request.player, request.angle_offset)
        wall_distance = self._resolve_wall_distance(
            request.player, request.raycaster, aim_angle, weapon_range
        )
        closest_bot, closest_distance, is_headshot = self._find_closest_target(
            request.player,
            request.bots,
            aim_angle,
            wall_distance,
        )
        return ShotResolutionResult(
            aim_angle=aim_angle,
            wall_distance=wall_distance,
            closest_bot=closest_bot,
            closest_distance=closest_distance,
            is_headshot=is_headshot,
        )

    def _get_weapon_range(self, player: Any, is_secondary: bool) -> float:
        """Return the range to use for the current shot mode."""
        if is_secondary:
            return 100.0
        return float(player.get_current_weapon_range())

    def _resolve_aim_angle(self, player: Any, angle_offset: float) -> float:
        """Return the normalized aim angle for a shot."""
        spread_zoom = getattr(self.C, "SPREAD_ZOOM", 0.01)
        spread_base = getattr(self.C, "SPREAD_BASE", 0.04)
        current_spread = spread_zoom if player.zoomed else spread_base
        if angle_offset == 0.0:
            angle = player.angle + random.uniform(-current_spread, current_spread)
        else:
            angle = player.angle + angle_offset
        return angle % (2 * math.pi)

    def _resolve_wall_distance(
        self,
        player: Any,
        raycaster: Any,
        aim_angle: float,
        weapon_range: float,
    ) -> float:
        """Return the distance to the blocking wall, clamped by weapon range."""
        wall_dist, _, _, _, _ = raycaster.cast_ray(player.x, player.y, aim_angle)
        return min(float(wall_dist), weapon_range)

    def _find_closest_target(
        self,
        player: Any,
        bots: Sequence[Any],
        aim_angle: float,
        wall_distance: float,
    ) -> tuple[Any | None, float, bool]:
        """Return the nearest hittable bot intersecting the resolved shot."""
        closest_bot = None
        closest_dist = float("inf")
        is_headshot = False
        wall_dist_sq = wall_distance * wall_distance
        headshot_threshold = getattr(self.C, "HEADSHOT_THRESHOLD", 0.05)

        for bot in bots:
            if not bot.alive:
                continue
            dx = bot.x - player.x
            dy = bot.y - player.y
            dist_sq = dx * dx + dy * dy
            if dist_sq > wall_dist_sq:
                continue
            distance = math.sqrt(dist_sq)
            bot_angle = math.atan2(dy, dx)
            if bot_angle < 0:
                bot_angle += 2 * math.pi
            angle_diff = abs(bot_angle - aim_angle)
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff
            if angle_diff < 0.15 and distance < closest_dist:
                closest_bot = bot
                closest_dist = distance
                is_headshot = angle_diff < headshot_threshold

        return closest_bot, closest_dist, is_headshot
