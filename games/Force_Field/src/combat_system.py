from __future__ import annotations

import logging
import math
import random
from typing import TYPE_CHECKING

from . import constants as C
from .projectile import Projectile

if TYPE_CHECKING:
    from .bot import Bot
    from .game import Game
    from .player import Player

logger = logging.getLogger(__name__)


class CombatSystem:
    """Handles weapon firing, hit detection, and damage application."""

    def __init__(self, game: Game):
        self.game = game

    @property
    def player(self) -> Player:
        if self.game.player is None:
            raise ValueError("Player is None")
        return self.game.player

    def fire_weapon(self, is_secondary: bool = False) -> None:
        """Handle weapon firing (Hitscan or Projectile)"""
        weapon = self.player.current_weapon

        # Recoil Effect
        recoil_amount = 2.0
        if self.player.zoomed:
            recoil_amount = 0.5
        elif weapon == "minigun":
            recoil_amount = 0.5
        elif weapon == "shotgun":
            recoil_amount = 4.0
        elif weapon == "rocket":
            recoil_amount = 5.0

        self.player.pitch += recoil_amount
        # Clamp pitch is handled in player update, but we can clamp here too if needed
        # or rely on player logic.

        # Sound
        sound_name = f"shoot_{weapon}"
        self.game.sound_manager.play_sound(sound_name)

        # Visuals & Logic
        if weapon == "plasma" and not is_secondary:
            self._fire_plasma()
            return

        if weapon == "rocket" and not is_secondary:
            self._fire_rocket()
            return

        if weapon == "flamethrower" and not is_secondary:
            self._fire_flamethrower()
            return

        if weapon == "minigun" and not is_secondary:
            self._fire_minigun()
            return

        if weapon == "laser" and not is_secondary:
            self.check_shot_hit(is_secondary=False, is_laser=True)
            return

        if weapon == "shotgun" and not is_secondary:
            pellets = int(C.WEAPONS["shotgun"].get("pellets", 8))
            spread = float(C.WEAPONS["shotgun"].get("spread", 0.15))
            for _ in range(pellets):
                angle_off = random.uniform(-spread, spread)
                self.check_shot_hit(angle_offset=angle_off)
        else:
            self.check_shot_hit(is_secondary=is_secondary)

    def _fire_plasma(self) -> None:
        p = Projectile(
            self.player.x,
            self.player.y,
            self.player.angle,
            speed=float(C.WEAPONS["plasma"].get("projectile_speed", 0.5)),
            damage=self.player.get_current_weapon_damage(),
            is_player=True,
            color=C.WEAPONS["plasma"].get("projectile_color", (0, 255, 255)),
            size=0.225,
            weapon_type="plasma",
        )
        self.game.entity_manager.add_projectile(p)

    def _fire_rocket(self) -> None:
        p = Projectile(
            self.player.x,
            self.player.y,
            self.player.angle,
            speed=float(C.WEAPONS["rocket"].get("projectile_speed", 0.3)),
            damage=self.player.get_current_weapon_damage(),
            is_player=True,
            color=C.WEAPONS["rocket"].get("projectile_color", (255, 100, 0)),
            size=0.6,
            weapon_type="rocket",
        )
        self.game.entity_manager.add_projectile(p)

    def _fire_flamethrower(self) -> None:
        damage = self.player.get_current_weapon_damage()
        # Spawn multiple flame particles
        for _ in range(2):
            angle_off = random.uniform(-0.15, 0.15)
            final_angle = self.player.angle + angle_off
            speed = float(C.WEAPONS["flamethrower"].get("projectile_speed", 0.35))

            # Add slight speed variation
            speed *= random.uniform(0.8, 1.2)

            p = Projectile(
                self.player.x,
                self.player.y,
                final_angle,
                damage,
                speed=speed,
                is_player=True,
                color=C.WEAPONS["flamethrower"].get("projectile_color", (255, 140, 0)),
                size=0.4,
                weapon_type="flamethrower",
            )
            self.game.entity_manager.add_projectile(p)

    def _fire_minigun(self) -> None:
        damage = self.player.get_current_weapon_damage()
        num_bullets = 3
        for _ in range(num_bullets):
            angle_off = random.uniform(-0.15, 0.15)
            final_angle = self.player.angle + angle_off

            p = Projectile(
                self.player.x,
                self.player.y,
                final_angle,
                damage,
                speed=2.0,
                is_player=True,
                color=(255, 255, 0),
                size=0.1,
                weapon_type="minigun",
            )
            self.game.entity_manager.add_projectile(p)

        self.game.particle_system.add_explosion(
            C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2, count=8, color=(255, 255, 0)
        )

    def check_shot_hit(
        self,
        is_secondary: bool = False,
        angle_offset: float = 0.0,
        is_laser: bool = False,
    ) -> None:
        """Check if player's shot hit a bot"""
        assert self.game.raycaster is not None

        weapon_range = self.player.get_current_weapon_range()
        if is_secondary:
            weapon_range = 100

        weapon_damage = self.player.get_current_weapon_damage()

        current_spread = C.SPREAD_ZOOM if self.player.zoomed else C.SPREAD_BASE
        if angle_offset == 0.0:
            spread_offset = random.uniform(-current_spread, current_spread)
            aim_angle = self.player.angle + spread_offset
        else:
            aim_angle = self.player.angle + angle_offset

        aim_angle %= 2 * math.pi

        wall_dist, _, _, _, _ = self.game.raycaster.cast_ray(
            self.player.x, self.player.y, aim_angle
        )

        if wall_dist > weapon_range:
            wall_dist = float(weapon_range)

        closest_bot = None
        closest_dist = float("inf")
        is_headshot = False

        wall_dist_sq = wall_dist * wall_dist

        for bot in self.game.bots:
            if not bot.alive:
                continue

            dx = bot.x - self.player.x
            dy = bot.y - self.player.y
            dist_sq = dx * dx + dy * dy

            if dist_sq > wall_dist_sq:
                continue

            distance = math.sqrt(dist_sq)

            bot_angle = math.atan2(dy, dx)
            angle = bot_angle if bot_angle >= 0 else bot_angle + 2 * math.pi
            bot_angle_norm = angle

            angle_diff = abs(bot_angle_norm - aim_angle)
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff

            if angle_diff < 0.15:
                if distance < closest_dist:
                    closest_bot = bot
                    closest_dist = distance
                    is_headshot = angle_diff < C.HEADSHOT_THRESHOLD

        if is_secondary:
            self._handle_secondary_hit(closest_bot, closest_dist, wall_dist)
            return

        if is_laser:
            self.game.particle_system.add_laser(
                start=(C.SCREEN_WIDTH - 200, C.SCREEN_HEIGHT - 180),
                end=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2),
                color=(255, 0, 0),
                timer=5,
                width=3,
            )

        if closest_bot:
            self._apply_damage(
                closest_bot, closest_dist, weapon_range, weapon_damage, is_headshot
            )

    def _handle_secondary_hit(
        self, closest_bot: Bot | None, closest_dist: float, wall_dist: float
    ) -> None:
        impact_dist = wall_dist
        if closest_bot and closest_dist < wall_dist:
            impact_dist = closest_dist

        ray_angle = self.player.angle
        impact_x = self.player.x + math.cos(ray_angle) * impact_dist
        impact_y = self.player.y + math.sin(ray_angle) * impact_dist

        try:
            self.explode_laser(impact_x, impact_y)
        except Exception:
            logger.exception("Error in explode_laser")

        self.game.particle_system.add_laser(
            start=(C.SCREEN_WIDTH - 200, C.SCREEN_HEIGHT - 180),
            end=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2),
            color=(0, 255, 255),
            timer=C.LASER_DURATION,
            width=C.LASER_WIDTH,
        )

    def _apply_damage(
        self,
        bot: Bot,
        distance: float,
        weapon_range: float,
        base_damage: int,
        is_headshot: bool,
    ) -> None:
        range_factor = max(0.3, 1.0 - (distance / weapon_range))

        # Re-calculate angle diff for accuracy factor
        dx = bot.x - self.player.x
        dy = bot.y - self.player.y
        bot_angle = math.atan2(dy, dx)
        angle = bot_angle if bot_angle >= 0 else bot_angle + 2 * math.pi

        angle_diff = abs(angle - self.player.angle)
        if angle_diff > math.pi:
            angle_diff = 2 * math.pi - angle_diff

        accuracy_factor = max(0.5, 1.0 - (angle_diff / 0.15))

        final_damage = int(base_damage * range_factor * accuracy_factor)

        bot.take_damage(final_damage, is_headshot=is_headshot)

        if self.game.show_damage:
            self.game.damage_texts.append(
                {
                    "x": C.SCREEN_WIDTH // 2 + random.randint(-20, 20),
                    "y": C.SCREEN_HEIGHT // 2 - 50,
                    "text": str(final_damage) + ("!" if is_headshot else ""),
                    "color": C.RED if is_headshot else C.DAMAGE_TEXT_COLOR,
                    "timer": 60,
                    "vy": -1.0,
                }
            )

        self.game.particle_system.add_explosion(
            C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2, count=5
        )

        # Improved Blood Feedback
        blood_color = (200, 0, 0)
        # For non-standard enemies (like robots/aliens), maybe different blood?
        if bot.enemy_type in ["ball", "minigunner"]: # Maybe robots?
             blood_color = (20, 20, 20) # Oil?
        elif bot.enemy_type == "demon":
             blood_color = (0, 200, 0) # Green slime

        for _ in range(15):
            speed = random.uniform(2, 8)
            angle = random.uniform(0, 2 * math.pi)
            self.game.particle_system.add_particle(
                x=C.SCREEN_WIDTH // 2,
                y=C.SCREEN_HEIGHT // 2,
                dx=math.cos(angle) * speed,
                dy=math.sin(angle) * speed,
                color=blood_color,
                timer=random.randint(20, 40),
                size=random.randint(3, 6),
                gravity=0.2, # Gravity for blood
            )

        if not bot.alive:
            self._handle_kill(bot)

    def _handle_kill(self, bot: Bot) -> None:
        self.game.kills += 1
        self.game.kill_combo_count += 1
        self.game.kill_combo_timer = 180
        self.game.last_death_pos = (bot.x, bot.y)
        self.game.sound_manager.play_sound("scream")

    def explode_bomb(self, projectile: Projectile) -> None:
        """Handle bomb explosion logic"""
        dist_to_player = math.sqrt(
            (projectile.x - self.player.x) ** 2 + (projectile.y - self.player.y) ** 2
        )

        try:
            self.game.sound_manager.play_sound("bomb")
        except Exception:
            logger.exception("Bomb Audio Failed")

        # Screen shake on bomb
        if dist_to_player < 30:
            shake = max(0, 30 - dist_to_player)
            self.game.screen_shake = shake

        if dist_to_player < 20:
            if dist_to_player < 10:
                self.game.particle_system.add_particle(
                    x=C.SCREEN_WIDTH // 2,
                    y=C.SCREEN_HEIGHT // 2,
                    dx=0,
                    dy=0,
                    color=C.WHITE,
                    timer=20,
                    size=3000,
                )

            explosion_center = (C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2)

            for _ in range(100):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(5, 20)
                color = random.choice([C.ORANGE, C.RED, C.YELLOW, (50, 50, 50)])
                self.game.particle_system.add_particle(
                    x=explosion_center[0],
                    y=explosion_center[1],
                    dx=math.cos(angle) * speed,
                    dy=math.sin(angle) * speed,
                    color=color,
                    timer=random.randint(40, 80),
                    size=random.randint(5, 15),
                )

        for bot in self.game.bots:
            if not bot.alive:
                continue
            dx = bot.x - projectile.x
            dy = bot.y - projectile.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < C.BOMB_RADIUS:
                damage_factor = 1.0 - (dist / C.BOMB_RADIUS)
                damage = int(1000 * damage_factor)

                if bot.take_damage(damage):
                    self._handle_kill(bot)

                if dist < 5.0 and dist_to_player < 20:
                    self.game.particle_system.add_explosion(
                        C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2, count=3
                    )

        self.game.damage_texts.append(
            {
                "x": C.SCREEN_WIDTH // 2,
                "y": C.SCREEN_HEIGHT // 2 - 100,
                "text": "BOOM!",
                "color": C.ORANGE,
                "timer": 90,
                "vy": -0.5,
            }
        )

    def explode_laser(self, impact_x: float, impact_y: float) -> None:
        """Trigger Massive Laser Explosion at Impact Point"""
        try:
            self.game.sound_manager.play_sound("boom_real")
        except Exception:
            logger.exception("Boom sound failed")

        self.game.screen_shake = 10.0

        hits = 0
        for bot in self.game.bots:
            if not hasattr(bot, "alive"):
                continue

            if bot.alive:
                dist = math.sqrt((bot.x - impact_x) ** 2 + (bot.y - impact_y) ** 2)
                if dist < C.LASER_AOE_RADIUS:
                    damage = 500
                    killed = bot.take_damage(damage)
                    hits += 1

                    if killed:
                        self._handle_kill(bot)

                    for _ in range(10):
                        self.game.particle_system.add_particle(
                            x=C.SCREEN_WIDTH // 2,
                            y=C.SCREEN_HEIGHT // 2,
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
            self.game.damage_texts.append(
                {
                    "x": C.SCREEN_WIDTH // 2,
                    "y": C.SCREEN_HEIGHT // 2 - 80,
                    "text": "LASER ANNIHILATION!",
                    "color": (255, 0, 255),
                    "timer": 60,
                    "vy": -2,
                }
            )

    def _explode_generic(
        self, projectile: Projectile, radius: float, weapon_type: str
    ) -> None:
        """Generic explosion logic"""
        dist_to_player = math.sqrt(
            (projectile.x - self.player.x) ** 2 + (projectile.y - self.player.y) ** 2
        )
        if dist_to_player < 15:
            self.game.damage_flash_timer = 15
            self.game.screen_shake = 15.0 - dist_to_player

        if dist_to_player < 20:
            count = 5 if weapon_type == "rocket" else 3
            self.game.particle_system.add_explosion(
                C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2, count=count
            )

            color = C.CYAN if weapon_type == "plasma" else C.ORANGE
            for _ in range(20):
                self.game.particle_system.add_particle(
                    x=C.SCREEN_WIDTH // 2,
                    y=C.SCREEN_HEIGHT // 2,
                    dx=random.uniform(-10, 10),
                    dy=random.uniform(-10, 10),
                    color=color,
                    timer=40,
                    size=random.randint(4, 8),
                )

        try:
            self.game.sound_manager.play_sound(
                "boom_real" if weapon_type == "rocket" else "shoot_plasma"
            )
        except Exception:
            pass

        for bot in self.game.bots:
            if not bot.alive:
                continue
            dx = bot.x - projectile.x
            dy = bot.y - projectile.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < radius:
                damage_factor = 1.0 - (dist / radius)
                damage = int(projectile.damage * damage_factor)

                if bot.take_damage(damage):
                    self._handle_kill(bot)

    def explode_plasma(self, projectile: Projectile) -> None:
        self._explode_generic(projectile, C.PLASMA_AOE_RADIUS, "plasma")

    def explode_rocket(self, projectile: Projectile) -> None:
        radius = float(C.WEAPONS["rocket"].get("aoe_radius", 6.0))
        self._explode_generic(projectile, radius, "rocket")
