"""Base class for combat managers.

Encapsulates hit detection, damage application, kill tracking,
and explosion logic that was previously duplicated across game.py files.

Subclasses override constants and game-specific behavior as needed.
"""

from __future__ import annotations

import logging
import math
import random
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from games.shared.constants import COMBO_TIMER_FRAMES

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class CombatManagerBase:
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

        # Optional callback invoked after each kill: on_kill(bot)
        self._on_kill = on_kill

        # Kill tracking state -- the game reads these back
        self.kills = 0
        self.kill_combo_count = 0
        self.kill_combo_timer = 0
        self.last_death_pos: tuple[float, float] | None = None

    # ------------------------------------------------------------------
    # Kill handling
    # ------------------------------------------------------------------

    def handle_kill(self, bot: Any) -> None:
        """Record a kill and update combo state.

        Args:
            bot: The bot that was killed.
        """
        self.kills += 1
        self.kill_combo_count += 1
        self.kill_combo_timer = COMBO_TIMER_FRAMES
        self.last_death_pos = (bot.x, bot.y)
        with suppress(Exception):
            self.sound_manager.play_sound("scream")
        if self._on_kill is not None:
            self._on_kill(bot)

    # ------------------------------------------------------------------
    # Hitscan shot detection
    # ------------------------------------------------------------------

    def check_shot_hit(
        self,
        player: Any,
        raycaster: Any,
        bots: list[Any],
        damage_texts: list[dict[str, Any]],
        show_damage: bool = True,
        is_secondary: bool = False,
        angle_offset: float = 0.0,
        is_laser: bool = False,
    ) -> list[dict[str, Any]]:
        """Check if a hitscan shot hit any bot.

        Returns the updated damage_texts list.  The caller owns the list;
        this method only appends to it.

        Args:
            player: The player object (must have x, y, angle, zoomed, etc.).
            raycaster: The Raycaster instance for ray casting.
            bots: List of bot objects to check against.
            damage_texts: Mutable list of floating damage text dicts.
            show_damage: Whether to show damage numbers.
            is_secondary: Whether this is a secondary fire.
            angle_offset: Angle offset for spread weapons.
            is_laser: Whether this is a laser beam.

        Returns:
            The (possibly modified) damage_texts list.
        """
        try:
            weapon_range = player.get_current_weapon_range()
            if is_secondary:
                weapon_range = 100

            weapon_damage = player.get_current_weapon_damage()

            # Aim Logic
            spread_zoom = getattr(self.C, "SPREAD_ZOOM", 0.01)
            spread_base = getattr(self.C, "SPREAD_BASE", 0.04)
            current_spread = spread_zoom if player.zoomed else spread_base
            if angle_offset == 0.0:
                spread_offset = random.uniform(-current_spread, current_spread)
                aim_angle = player.angle + spread_offset
            else:
                aim_angle = player.angle + angle_offset

            aim_angle %= 2 * math.pi

            # Cast ray to find wall distance
            wall_dist, _, _, _, _ = raycaster.cast_ray(player.x, player.y, aim_angle)

            if wall_dist > weapon_range:
                wall_dist = float(weapon_range)

            closest_bot = None
            closest_dist = float("inf")
            is_headshot = False

            wall_dist_sq = wall_dist * wall_dist
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

                if angle_diff < 0.15:
                    if distance < closest_dist:
                        closest_bot = bot
                        closest_dist = distance
                        is_headshot = angle_diff < headshot_threshold

            if is_secondary:
                self._handle_secondary_hit(
                    player, closest_bot, closest_dist, wall_dist, damage_texts
                )
                return damage_texts

            if is_laser:
                self.particle_system.add_laser(
                    start=(self.C.SCREEN_WIDTH - 200, self.C.SCREEN_HEIGHT - 180),
                    end=(self.C.SCREEN_WIDTH // 2, self.C.SCREEN_HEIGHT // 2),
                    color=(255, 0, 0),
                    timer=5,
                    width=3,
                )

            if closest_bot:
                self._apply_hit_damage(
                    player,
                    closest_bot,
                    closest_dist,
                    weapon_range,
                    weapon_damage,
                    is_headshot,
                    damage_texts,
                    show_damage,
                )

            # Visual traces
            self._add_shot_visuals(
                player, aim_angle, closest_bot, closest_dist, wall_dist
            )

        except Exception:
            logger.exception("Error in check_shot_hit")

        return damage_texts

    def _handle_secondary_hit(
        self,
        player: Any,
        closest_bot: Any | None,
        closest_dist: float,
        wall_dist: float,
        damage_texts: list[dict[str, Any]],
    ) -> None:
        """Handle secondary fire (laser explosion at impact)."""
        impact_dist = wall_dist
        if closest_bot and closest_dist < wall_dist:
            impact_dist = closest_dist

        ray_angle = player.angle
        impact_x = player.x + math.cos(ray_angle) * impact_dist
        impact_y = player.y + math.sin(ray_angle) * impact_dist

        try:
            self.explode_laser(impact_x, impact_y, damage_texts)
        except Exception:
            logger.exception("Error in explode_laser")

        laser_duration = getattr(self.C, "LASER_DURATION", 10)
        laser_width = getattr(self.C, "LASER_WIDTH", 5)
        self.particle_system.add_laser(
            start=(self.C.SCREEN_WIDTH - 200, self.C.SCREEN_HEIGHT - 180),
            end=(self.C.SCREEN_WIDTH // 2, self.C.SCREEN_HEIGHT // 2),
            color=(0, 255, 255),
            timer=laser_duration,
            width=laser_width,
        )

    def _apply_hit_damage(
        self,
        player: Any,
        bot: Any,
        distance: float,
        weapon_range: float,
        base_damage: int,
        is_headshot: bool,
        damage_texts: list[dict[str, Any]],
        show_damage: bool,
    ) -> None:
        """Apply damage to a bot that was hit."""
        range_factor = max(0.3, 1.0 - (distance / weapon_range))

        dx = bot.x - player.x
        dy = bot.y - player.y
        bot_angle = math.atan2(dy, dx)
        if bot_angle < 0:
            bot_angle += 2 * math.pi

        angle_diff = abs(bot_angle - player.angle)
        if angle_diff > math.pi:
            angle_diff = 2 * math.pi - angle_diff

        accuracy_factor = max(0.5, 1.0 - (angle_diff / 0.15))
        final_damage = int(base_damage * range_factor * accuracy_factor)

        bot.take_damage(final_damage, is_headshot=is_headshot)

        if show_damage:
            damage_color = getattr(self.C, "DAMAGE_TEXT_COLOR", (255, 255, 255))
            damage_texts.append(
                {
                    "x": self.C.SCREEN_WIDTH // 2 + random.randint(-20, 20),
                    "y": self.C.SCREEN_HEIGHT // 2 - 50,
                    "text": str(final_damage) + ("!" if is_headshot else ""),
                    "color": self.C.RED if is_headshot else damage_color,
                    "timer": 60,
                    "vy": -1.0,
                }
            )

        self.particle_system.add_explosion(
            self.C.SCREEN_WIDTH // 2, self.C.SCREEN_HEIGHT // 2, count=5
        )

        blood_color = getattr(self.C, "BLUE_BLOOD", (0, 0, 200))
        particle_lifetime = getattr(self.C, "PARTICLE_LIFETIME", 30)
        for _ in range(10):
            self.particle_system.add_particle(
                x=self.C.SCREEN_WIDTH // 2,
                y=self.C.SCREEN_HEIGHT // 2,
                dx=random.uniform(-5, 5),
                dy=random.uniform(-5, 5),
                color=blood_color,
                timer=particle_lifetime,
                size=random.randint(2, 5),
            )

        if not bot.alive:
            self.handle_kill(bot)

    def _add_shot_visuals(
        self,
        player: Any,
        aim_angle: float,
        closest_bot: Any | None,
        closest_dist: float,
        wall_dist: float,
    ) -> None:
        """Add tracer and impact visual effects."""
        fov = getattr(self.C, "FOV", 1.0)
        angle_diff = aim_angle - player.angle
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

        screen_hit_x = (0.5 - angle_diff / fov) * self.C.SCREEN_WIDTH
        screen_hit_y = self.C.SCREEN_HEIGHT // 2 + getattr(player, "pitch", 0)

        weapon_start_x = self.C.SCREEN_WIDTH * 0.6
        weapon_start_y = self.C.SCREEN_HEIGHT

        self.particle_system.add_trace(
            start=(weapon_start_x, weapon_start_y),
            end=(screen_hit_x, screen_hit_y),
            color=(255, 255, 100),
            timer=5,
            width=1,
        )

        if not closest_bot:
            hit_world_x = player.x + math.cos(aim_angle) * wall_dist
            hit_world_y = player.y + math.sin(aim_angle) * wall_dist

            self.particle_system.add_world_explosion(
                hit_world_x,
                hit_world_y,
                0.5,
                count=10,
                color=(255, 200, 100),
                speed=0.1,
            )

            for _ in range(5):
                self.particle_system.add_particle(
                    x=screen_hit_x,
                    y=screen_hit_y,
                    dx=random.uniform(-3, 3),
                    dy=random.uniform(-3, 3),
                    color=(255, 200, 100),
                    timer=20,
                    size=random.randint(1, 3),
                )

    # ------------------------------------------------------------------
    # Explosion helpers
    # ------------------------------------------------------------------

    def handle_bomb_explosion(
        self,
        player: Any,
        bots: list[Any],
        damage_texts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Handle bomb explosion centered on the player.

        Returns the updated damage_texts list.
        """
        sw2 = self.C.SCREEN_WIDTH // 2
        sh2 = self.C.SCREEN_HEIGHT // 2

        self.particle_system.add_particle(
            x=sw2,
            y=sh2,
            dx=0,
            dy=0,
            color=self.C.WHITE,
            timer=40,
            size=3000,
        )

        # 3D explosion at player pos
        self.particle_system.add_world_explosion(
            player.x,
            player.y,
            0.5,
            count=100,
            color=self.C.ORANGE,
            speed=0.5,
        )

        for _ in range(300):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5, 25)
            color = random.choice(
                [
                    self.C.ORANGE,
                    self.C.RED,
                    self.C.YELLOW,
                    getattr(self.C, "DARK_RED", (139, 0, 0)),
                    (50, 50, 50),
                ]
            )
            self.particle_system.add_particle(
                x=sw2,
                y=sh2,
                dx=math.cos(angle) * speed,
                dy=math.sin(angle) * speed,
                color=color,
                timer=random.randint(40, 100),
                size=random.randint(5, 25),
            )

        bomb_radius = getattr(self.C, "BOMB_RADIUS", 10.0)
        for bot in bots:
            if not bot.alive:
                continue
            dx = bot.x - player.x
            dy = bot.y - player.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < bomb_radius:
                if bot.take_damage(1000):
                    self.handle_kill(bot)

                if dist < 5.0:
                    self.particle_system.add_explosion(sw2, sh2, count=3)

        try:
            self.sound_manager.play_sound("bomb")
        except Exception:
            logger.exception("Bomb Audio Failed")

        damage_texts.append(
            {
                "x": sw2,
                "y": sh2 - 100,
                "text": "BOMB DROPPED!",
                "color": self.C.ORANGE,
                "timer": 120,
                "vy": -0.5,
            }
        )
        return damage_texts

    def explode_laser(
        self,
        impact_x: float,
        impact_y: float,
        damage_texts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Trigger a laser AOE explosion at an impact point."""
        try:
            self.sound_manager.play_sound("boom_real")
        except Exception:
            logger.exception("Boom sound failed")

        try:
            self.particle_system.add_world_explosion(
                impact_x,
                impact_y,
                0.5,
                count=80,
                color=(0, 255, 255),
                speed=0.4,
            )

            sw2 = self.C.SCREEN_WIDTH // 2
            sh2 = self.C.SCREEN_HEIGHT // 2
            laser_radius = getattr(self.C, "LASER_AOE_RADIUS", 5.0)

            hits = 0
            for bot in self.entity_manager.bots:
                if not getattr(bot, "alive", False):
                    continue
                dist = math.sqrt((bot.x - impact_x) ** 2 + (bot.y - impact_y) ** 2)
                if dist < laser_radius:
                    killed = bot.take_damage(500)
                    hits += 1

                    if killed:
                        self.handle_kill(bot)

                    for _ in range(10):
                        self.particle_system.add_particle(
                            x=sw2,
                            y=sh2,
                            dx=random.uniform(-10, 10),
                            dy=random.uniform(-10, 10),
                            color=(
                                random.randint(200, 255),
                                0,
                                random.randint(200, 255),
                            ),
                            timer=40,
                            size=random.randint(4, 8),
                        )

            if hits > 0:
                damage_texts.append(
                    {
                        "x": sw2,
                        "y": sh2 - 80,
                        "text": "LASER ANNIHILATION!",
                        "color": (255, 0, 255),
                        "timer": 60,
                        "vy": -2,
                    }
                )
        except Exception:
            logger.exception("Critical Laser Error")

        return damage_texts

    def explode_generic(
        self,
        projectile: Any,
        radius: float,
        weapon_type: str,
        player: Any,
        damage_flash_timer: int,
    ) -> int:
        """Generic AOE explosion around a projectile impact.

        Returns the updated damage_flash_timer value.
        """
        dist_to_player = math.sqrt(
            (projectile.x - player.x) ** 2 + (projectile.y - player.y) ** 2
        )
        if dist_to_player < 15:
            damage_flash_timer = 15

        sw2 = self.C.SCREEN_WIDTH // 2
        sh2 = self.C.SCREEN_HEIGHT // 2

        color = self.C.CYAN if weapon_type == "plasma" else self.C.ORANGE
        self.particle_system.add_world_explosion(
            projectile.x,
            projectile.y,
            getattr(projectile, "z", 0.5),
            count=50,
            color=color,
            speed=0.3,
        )

        if dist_to_player < 20:
            count = 5 if weapon_type == "rocket" else 3
            self.particle_system.add_explosion(sw2, sh2, count=count)

            for _ in range(20):
                self.particle_system.add_particle(
                    x=sw2,
                    y=sh2,
                    dx=random.uniform(-10, 10),
                    dy=random.uniform(-10, 10),
                    color=color,
                    timer=40,
                    size=random.randint(4, 8),
                )

        try:
            self.sound_manager.play_sound(
                "boom_real" if weapon_type == "rocket" else "shoot_plasma"
            )
        except Exception:
            pass

        for bot in self.entity_manager.bots:
            if not bot.alive:
                continue
            dx = bot.x - projectile.x
            dy = bot.y - projectile.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < radius:
                damage_factor = 1.0 - (dist / radius)
                damage = int(projectile.damage * damage_factor)

                if bot.take_damage(damage):
                    self.handle_kill(bot)

        return damage_flash_timer
