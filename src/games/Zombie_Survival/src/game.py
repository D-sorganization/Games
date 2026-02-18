from __future__ import annotations

import logging
import math
import random
import traceback
from contextlib import suppress
from typing import Any

import pygame

from games.shared.config import RaycasterConfig
from games.shared.constants import GameState
from games.shared.fps_game_base import FPSGameBase
from games.shared.interfaces import Portal
from games.shared.raycaster import Raycaster
from games.shared.sound_manager_base import SoundManagerBase

from . import constants as C  # noqa: N812
from .bot import Bot
from .entity_manager import EntityManager
from .input_manager import InputManager
from .map import Map
from .particle_system import ParticleSystem
from .player import Player
from .projectile import Projectile
from .renderer import GameRenderer
from .sound import SoundManager
from .ui_renderer import UIRenderer

logger = logging.getLogger(__name__)


class Game(FPSGameBase):
    """Main game class"""

    def __init__(
        self,
        sound_manager: SoundManagerBase | None = None,
    ) -> None:
        """Initialize game.

        Args:
            sound_manager: Optional sound manager instance.  If not
                provided, a default SoundManager is created.  Pass a
                NullSoundManager for testing or headless environments.
        """
        self.C = C
        flags = pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), flags)
        pygame.display.set_caption("Zombie Survival - Undead Nightmare")
        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize Renderer
        self.renderer = GameRenderer(self.screen)
        self.ui_renderer = UIRenderer(self.screen)

        # Game state
        self.state = GameState.INTRO
        self.intro_phase = 0
        self.intro_step = 0
        self.intro_timer = 0
        self.intro_start_time = 0
        self.last_death_pos: tuple[float, float] | None = None

        # Gameplay state
        self.level = 1
        self.kills = 0
        self.level_start_time = 0
        self.level_times: list[float] = []
        self.selected_map_size = C.DEFAULT_MAP_SIZE
        self.render_scale = C.DEFAULT_RENDER_SCALE
        self.paused = False
        self.pause_start_time = 0
        self.total_paused_time = 0
        self.show_damage = True
        self.selected_difficulty = C.DEFAULT_DIFFICULTY
        self.selected_lives = C.DEFAULT_LIVES
        self.selected_start_level = C.DEFAULT_START_LEVEL

        # Combo & Atmosphere
        self.kill_combo_count = 0
        self.kill_combo_timer = 0
        self.heartbeat_timer = 0
        self.breath_timer = 0
        self.groan_timer = 0
        self.beast_timer = 0

        # Visual effects (Game Logic owned)
        self.particle_system = ParticleSystem()
        self.damage_texts: list[dict[str, Any]] = []
        self.damage_flash_timer = 0

        # Game objects
        self.game_map: Map | None = None
        self.player: Player | None = None
        self.entity_manager = EntityManager()
        self.raycaster: Raycaster | None = None
        self.portal: Portal | None = None
        self.health = 100
        self.lives = C.DEFAULT_LIVES

        # Unlocked weapons tracking - start with basic weapons
        self.unlocked_weapons = {"pistol", "rifle"}
        self.cheat_mode_active = False
        self.current_cheat_input = ""
        self.god_mode = False

        self.game_over_timer = 0

        # Audio
        self.sound_manager = (
            sound_manager if sound_manager is not None else SoundManager()
        )
        self.sound_manager.start_music()

        # Input
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            try:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                logger.info("Controller detected: %s", self.joystick.get_name())
            except Exception:
                logger.exception("Controller init failed")

        # Fog of War
        self.visited_cells: set[tuple[int, int]] = set()
        self.show_minimap = True

        # Input Manager
        self.input_manager = InputManager()
        self.binding_action: str | None = None

    def start_game(self) -> None:
        """Start new game"""
        self.level = self.selected_start_level
        self.lives = self.selected_lives
        self.kills = 0
        self.level_times = []
        self.paused = False
        self.particle_system.particles = []
        self.damage_texts = []
        self.entity_manager.reset()

        # Reset Cheats/Progress
        self.unlocked_weapons = {"pistol", "rifle"}
        self.god_mode = False
        self.cheat_mode_active = False

        # Reset Combo & Atmosphere
        self.kill_combo_count = 0
        self.kill_combo_timer = 0
        self.heartbeat_timer = 0
        self.breath_timer = 0
        self.groan_timer = 0
        self.beast_timer = 0

        # Create map with selected size
        self.game_map = Map(self.selected_map_size)

        # Initialize Raycaster with Config
        ray_config = RaycasterConfig(
            SCREEN_WIDTH=C.SCREEN_WIDTH,
            SCREEN_HEIGHT=C.SCREEN_HEIGHT,
            FOV=C.FOV,
            HALF_FOV=C.HALF_FOV,
            ZOOM_FOV_MULT=C.ZOOM_FOV_MULT,
            DEFAULT_RENDER_SCALE=self.render_scale,
            MAX_DEPTH=C.MAX_DEPTH,
            FOG_START=C.FOG_START,
            FOG_COLOR=C.FOG_COLOR,
            LEVEL_THEMES=C.LEVEL_THEMES,
            ENEMY_TYPES=C.ENEMY_TYPES,
        )
        self.raycaster = Raycaster(self.game_map, ray_config)
        self.last_death_pos = None
        self.portal = None

        # Grab mouse
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        self.start_level()

    def start_level(self) -> None:
        """Start a new level"""
        assert self.game_map is not None
        self.level_start_time = pygame.time.get_ticks()
        self.total_paused_time = 0
        self.pause_start_time = 0
        self.particle_system.particles = []
        self.damage_texts = []
        self.damage_flash_timer = 0
        self.visited_cells = set()  # Reset fog of war
        self.portal = None

        # Grab mouse for FPS gameplay
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        # Player Spawn Logic
        player_pos = self._get_best_spawn_point()

        # Preserve ammo and weapon selection from previous level if player exists
        previous_ammo = None
        previous_weapon = "pistol"
        old_player = self.player
        if old_player:
            previous_ammo = old_player.ammo
            previous_weapon = old_player.current_weapon

        self.player = Player(player_pos[0], player_pos[1], player_pos[2])
        if previous_ammo:
            self.player.ammo = previous_ammo
            if previous_weapon in self.unlocked_weapons:
                self.player.current_weapon = previous_weapon
            else:
                self.player.current_weapon = "pistol"
        # Validate current weapon is unlocked
        # (e.g. Player init sets 'rifle' but it might be locked)
        if self.player.current_weapon not in self.unlocked_weapons:
            self.player.current_weapon = "pistol"

        # Propagate God Mode state
        self.player.god_mode = self.god_mode

        # Bots spawn in random locations, but respect safety radius
        self.entity_manager.reset()

        num_enemies = int(
            min(
                50,
                5
                + self.level
                * 2
                * C.DIFFICULTIES[self.selected_difficulty]["score_mult"],
            )
        )

        for _ in range(num_enemies):
            # Try to place bot with more attempts and flexible distance
            for attempt in range(50):  # Increased attempts
                bx = random.randint(2, self.game_map.size - 2)
                by = random.randint(2, self.game_map.size - 2)

                # More flexible distance check - but maintain safe minimum
                min_dist_sq = 225.0 if attempt < 40 else 144.0  # 15^2 / 12^2
                dist_sq = (bx - player_pos[0]) ** 2 + (by - player_pos[1]) ** 2
                if dist_sq < min_dist_sq:
                    continue

                if not self.game_map.is_wall(bx, by):
                    # Add bot - exclude items and special bosses from regular spawning
                    enemy_type = random.choice(list(C.ENEMY_TYPES.keys()))
                    while enemy_type in [
                        "boss",
                        "demon",
                        "ball",
                        "beast",
                        "pickup_rifle",
                        "pickup_shotgun",
                        "pickup_plasma",
                        "pickup_minigun",
                        "health_pack",
                        "ammo_box",
                        "bomb_item",
                        "pickup_rocket",
                    ]:
                        enemy_type = random.choice(list(C.ENEMY_TYPES.keys()))

                    self.entity_manager.add_bot(
                        Bot(
                            bx + 0.5,
                            by + 0.5,
                            self.level,
                            enemy_type,
                            difficulty=self.selected_difficulty,
                        )
                    )
                    break

        # Spawn Boss & Fast Enemy (Demon)
        boss_options = ["ball", "beast"]
        boss_type = random.choice(boss_options)

        upper_bound = max(2, self.game_map.size - 3)
        for attempt in range(100):  # More attempts for boss spawning
            cx = random.randint(2, upper_bound)
            cy = random.randint(2, upper_bound)

            # More flexible distance for boss spawning - but keep safe
            min_boss_dist_sq = 225.0 if attempt < 70 else 144.0  # 15^2 / 12^2
            if (
                not self.game_map.is_wall(cx, cy)
                and (cx - player_pos[0]) ** 2 + (cy - player_pos[1]) ** 2
                > min_boss_dist_sq
            ):
                self.entity_manager.add_bot(
                    Bot(
                        cx + 0.5,
                        cy + 0.5,
                        self.level,
                        enemy_type=boss_type,
                        difficulty=self.selected_difficulty,
                    )
                )
                break

        # Spawn Pickups
        possible_weapons = [
            "pickup_rifle",
            "pickup_shotgun",
            "pickup_plasma",
            "pickup_minigun",
        ]
        for w_pickup in possible_weapons:
            if random.random() < 0.4:  # 40% chance per level
                rx = random.randint(5, self.game_map.size - 5)
                ry = random.randint(5, self.game_map.size - 5)
                if not self.game_map.is_wall(rx, ry):
                    self.entity_manager.add_bot(
                        Bot(rx + 0.5, ry + 0.5, self.level, w_pickup)
                    )

        # Ammo / Bombs
        for _ in range(8):
            rx = random.randint(5, self.game_map.size - 5)
            ry = random.randint(5, self.game_map.size - 5)
            if not self.game_map.is_wall(rx, ry):
                choice = random.random()
                if choice < 0.2:
                    self.entity_manager.add_bot(
                        Bot(rx + 0.5, ry + 0.5, self.level, "bomb_item")
                    )
                elif choice < 0.7:
                    self.entity_manager.add_bot(
                        Bot(rx + 0.5, ry + 0.5, self.level, "ammo_box")
                    )
                else:
                    self.entity_manager.add_bot(
                        Bot(rx + 0.5, ry + 0.5, self.level, "health_pack")
                    )

        # Start Music
        music_tracks = [
            "music_loop",
            "music_drums",
            "music_wind",
            "music_horror",
            "music_piano",
            "music_action",
        ]
        if hasattr(self, "sound_manager"):
            self.sound_manager.start_music(random.choice(music_tracks))

    def handle_game_events(self) -> None:
        """Handle events during gameplay"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                # Cheat Input Handling
                if self.cheat_mode_active:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        self.cheat_mode_active = False
                        self.add_message("CHEAT INPUT CLOSED", C.GRAY)
                    elif event.key == pygame.K_BACKSPACE:
                        self.current_cheat_input = self.current_cheat_input[:-1]
                    else:
                        self.current_cheat_input += event.unicode
                        # Check cheats
                        code = self.current_cheat_input.upper()
                        if code.endswith("IDFA"):
                            # Unlock all weapons, full ammo
                            self.unlocked_weapons = set(C.WEAPONS.keys())
                            if self.player:
                                for w in self.player.ammo:
                                    self.player.ammo[w] = 999
                            self.add_message("ALL WEAPONS UNLOCKED", C.YELLOW)
                            self.current_cheat_input = ""
                            self.cheat_mode_active = False
                        elif code.endswith("IDDQD"):
                            # God Mode
                            self.god_mode = not self.god_mode
                            msg = "GOD MODE ON" if self.god_mode else "GOD MODE OFF"
                            self.add_message(msg, C.YELLOW)
                            if self.player:
                                self.player.health = 100
                                self.player.god_mode = self.god_mode
                            self.current_cheat_input = ""
                            self.cheat_mode_active = False
                    continue

                # Pause Toggle
                if self.input_manager.is_action_just_pressed(event, "pause"):
                    self.paused = not self.paused
                    if self.paused:
                        self.pause_start_time = pygame.time.get_ticks()
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                    else:
                        if self.pause_start_time > 0:
                            now = pygame.time.get_ticks()
                            pause_duration = now - self.pause_start_time
                            self.total_paused_time += pause_duration
                            self.pause_start_time = 0
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)

                # Activate Cheat Mode
                elif event.key == pygame.K_c and (
                    pygame.key.get_mods() & pygame.KMOD_CTRL
                ):
                    self.cheat_mode_active = True
                    self.current_cheat_input = ""
                    self.add_message("CHEAT MODE: TYPE CODE", C.PURPLE)
                    continue

                # Single press actions (switches, reload, etc)
                if not self.paused:
                    if self.input_manager.is_action_just_pressed(event, "weapon_1"):
                        self.switch_weapon_with_message("pistol")
                    elif self.input_manager.is_action_just_pressed(event, "weapon_2"):
                        self.switch_weapon_with_message("rifle")
                    elif self.input_manager.is_action_just_pressed(event, "weapon_3"):
                        self.switch_weapon_with_message("shotgun")
                    elif self.input_manager.is_action_just_pressed(event, "weapon_4"):
                        self.switch_weapon_with_message("laser")
                    elif self.input_manager.is_action_just_pressed(event, "weapon_5"):
                        self.switch_weapon_with_message("plasma")
                    elif self.input_manager.is_action_just_pressed(event, "weapon_6"):
                        self.switch_weapon_with_message("rocket")
                    elif event.key == pygame.K_7:
                        self.switch_weapon_with_message("minigun")
                    elif self.input_manager.is_action_just_pressed(event, "reload"):
                        assert self.player is not None
                        self.player.reload()
                    elif self.input_manager.is_action_just_pressed(event, "zoom"):
                        assert self.player is not None
                        self.player.zoomed = not self.player.zoomed
                    elif self.input_manager.is_action_just_pressed(event, "bomb"):
                        assert self.player is not None
                        if self.player.activate_bomb():
                            self.handle_bomb_explosion()
                    # Alt Shoot (e.g. Numpad 0)
                    elif self.input_manager.is_action_just_pressed(event, "shoot_alt"):
                        assert self.player is not None
                        if self.player.shoot():
                            self.fire_weapon()
                    elif event.key == pygame.K_m:
                        self.show_minimap = not self.show_minimap
                    elif event.key == pygame.K_F9:
                        self.cycle_render_scale()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.paused:
                    # Handle Pause Menu Clicks
                    mx, my = event.pos
                    if 500 <= mx <= 700:
                        if 350 <= my <= 400:  # Resume
                            self.paused = False
                            if self.pause_start_time > 0:
                                now = pygame.time.get_ticks()
                                pause_duration = now - self.pause_start_time
                                self.total_paused_time += pause_duration
                                self.pause_start_time = 0
                            pygame.mouse.set_visible(False)
                            pygame.event.set_grab(True)
                        elif 410 <= my <= 460:  # Save
                            self.save_game()
                            self.add_message("GAME SAVED", C.GREEN)
                        elif 470 <= my <= 520:  # Controls
                            self.state = GameState.KEY_CONFIG
                            self.binding_action = None  # Initialize binding state
                        elif 530 <= my <= 580:  # Quit to Menu
                            self.state = GameState.MENU
                            self.paused = False
                            self.sound_manager.start_music("music_loop")

                elif not self.cheat_mode_active:
                    assert self.player is not None
                    if event.button == 1:
                        if self.player.shoot():
                            self.fire_weapon()
                    elif event.button == 3:
                        if self.player.fire_secondary():
                            self.fire_weapon(is_secondary=True)

            elif event.type == pygame.MOUSEMOTION and not self.paused:
                assert self.player is not None
                self.player.rotate(event.rel[0] * C.PLAYER_ROT_SPEED * C.SENSITIVITY_X)
                self.player.pitch_view(-event.rel[1] * C.PLAYER_ROT_SPEED * 200)

    def save_game(self, filename: str = "savegame.txt") -> None:
        """Save game state to file.

        Args:
            filename (str): The file path to save the game state.
                Defaults to "savegame.txt".
        """
        # Simple save implementation
        try:
            with open(filename, "w") as f:
                f.write(f"{self.level}")
        except OSError:
            logger.exception("Save failed")

    def fire_weapon(self, is_secondary: bool = False) -> None:
        """Handle weapon firing (Hitscan or Projectile)"""
        assert self.player is not None
        weapon = self.player.current_weapon

        # Sound
        sound_name = f"shoot_{weapon}"
        self.sound_manager.play_sound(sound_name)

        # Visuals & Logic
        if weapon == "plasma" and not is_secondary:
            # Spawn Projectile
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
            self.entity_manager.add_projectile(p)
            return

        if weapon == "rocket" and not is_secondary:
            # Spawn Rocket
            p = Projectile(
                self.player.x,
                self.player.y,
                self.player.angle,
                speed=float(C.WEAPONS["rocket"].get("projectile_speed", 0.3)),
                damage=self.player.get_current_weapon_damage(),
                is_player=True,
                color=C.WEAPONS["rocket"].get("projectile_color", (255, 100, 0)),
                size=0.3,
                weapon_type="rocket",
            )
            self.entity_manager.add_projectile(p)
            return

        if weapon == "minigun" and not is_secondary:
            # Minigun rapid fire with multiple projectiles and visual effects
            damage = self.player.get_current_weapon_damage()
            num_bullets = 3  # Fire multiple bullets per shot for minigun effect
            for _ in range(num_bullets):
                angle_off = random.uniform(-0.15, 0.15)  # Increased spread for minigun
                final_angle = self.player.angle + angle_off

                # Create minigun projectile with tracer effect
                p = Projectile(
                    self.player.x,
                    self.player.y,
                    final_angle,
                    damage,
                    speed=2.0,  # Fast bullets
                    is_player=True,
                    color=(255, 255, 0),  # Yellow tracers for minigun
                    size=0.1,  # Smaller bullets
                    weapon_type="minigun",
                )
                self.entity_manager.add_projectile(p)

            # Add muzzle flash particles for minigun
            self.particle_system.add_explosion(
                C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2, count=8, color=(255, 255, 0)
            )
            return

        if weapon == "laser" and not is_secondary:
            # Hitscan with Beam Visual
            self.check_shot_hit(is_secondary=False, is_laser=True)
            return

        if weapon == "shotgun" and not is_secondary:
            # Spread Fire
            pellets = int(C.WEAPONS["shotgun"].get("pellets", 8))
            spread = float(C.WEAPONS["shotgun"].get("spread", 0.15))
            for _ in range(pellets):
                angle_off = random.uniform(-spread, spread)
                self.check_shot_hit(angle_offset=angle_off)
        else:
            # Single Hitscan
            self.check_shot_hit(is_secondary=is_secondary)

    def check_shot_hit(
        self,
        is_secondary: bool = False,
        angle_offset: float = 0.0,
        is_laser: bool = False,
    ) -> None:
        """Check if player's shot hit a bot"""
        assert self.player is not None
        assert self.raycaster is not None
        try:
            weapon_range = self.player.get_current_weapon_range()
            if is_secondary:
                weapon_range = 100

            weapon_damage = self.player.get_current_weapon_damage()

            # Aim Logic
            current_spread = C.SPREAD_ZOOM if self.player.zoomed else C.SPREAD_BASE
            if angle_offset == 0.0:
                spread_offset = random.uniform(-current_spread, current_spread)
                aim_angle = self.player.angle + spread_offset
            else:
                aim_angle = self.player.angle + angle_offset

            aim_angle %= 2 * math.pi

            # 1. Cast ray to find wall distance
            # Use Raycaster to avoid code duplication
            wall_dist, _, _, _, _ = self.raycaster.cast_ray(
                self.player.x, self.player.y, aim_angle
            )

            # Cap at weapon range
            if wall_dist > weapon_range:
                wall_dist = float(weapon_range)

            closest_bot = None
            closest_dist = float("inf")
            is_headshot = False

            # 2. Check bots
            # Optimization: Use squared distance check first
            wall_dist_sq = wall_dist * wall_dist

            for bot in self.bots:
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

                self.particle_system.add_laser(
                    start=(C.SCREEN_WIDTH - 200, C.SCREEN_HEIGHT - 180),
                    end=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2),
                    color=(0, 255, 255),
                    timer=C.LASER_DURATION,
                    width=C.LASER_WIDTH,
                )
                return

            if is_laser:
                self.particle_system.add_laser(
                    start=(C.SCREEN_WIDTH - 200, C.SCREEN_HEIGHT - 180),
                    end=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2),
                    color=(255, 0, 0),
                    timer=5,
                    width=3,
                )

            if closest_bot:
                range_factor = max(0.3, 1.0 - (closest_dist / weapon_range))

                dx = closest_bot.x - self.player.x
                dy = closest_bot.y - self.player.y
                bot_angle = math.atan2(dy, dx)
                angle = bot_angle if bot_angle >= 0 else bot_angle + 2 * math.pi
                bot_angle_norm = angle

                angle_diff = abs(bot_angle_norm - self.player.angle)
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff

                accuracy_factor = max(0.5, 1.0 - (angle_diff / 0.15))

                final_damage = int(weapon_damage * range_factor * accuracy_factor)

                closest_bot.take_damage(final_damage, is_headshot=is_headshot)

                damage_dealt = final_damage

                if self.show_damage:
                    self.damage_texts.append(
                        {
                            "x": C.SCREEN_WIDTH // 2 + random.randint(-20, 20),
                            "y": C.SCREEN_HEIGHT // 2 - 50,
                            "text": str(damage_dealt) + ("!" if is_headshot else ""),
                            "color": C.RED if is_headshot else C.DAMAGE_TEXT_COLOR,
                            "timer": 60,
                            "vy": -1.0,
                        }
                    )

                self.particle_system.add_explosion(
                    C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2, count=5
                )

                for _ in range(10):
                    self.particle_system.add_particle(
                        x=C.SCREEN_WIDTH // 2,
                        y=C.SCREEN_HEIGHT // 2,
                        dx=random.uniform(-5, 5),
                        dy=random.uniform(-5, 5),
                        color=C.BLUE_BLOOD,
                        timer=C.PARTICLE_LIFETIME,
                        size=random.randint(2, 5),
                    )

                if not closest_bot.alive:
                    self.kills += 1
                    self.kill_combo_count += 1
                    self.kill_combo_timer = 180
                    self.last_death_pos = (closest_bot.x, closest_bot.y)
                    self.sound_manager.play_sound("scream")

        except Exception:
            logger.exception("Error in check_shot_hit")

    def handle_bomb_explosion(self) -> None:
        """Handle bomb explosion logic"""
        assert self.player is not None
        self.particle_system.add_particle(
            x=C.SCREEN_WIDTH // 2,
            y=C.SCREEN_HEIGHT // 2,
            dx=0,
            dy=0,
            color=C.WHITE,
            timer=40,
            size=3000,
        )
        for _ in range(300):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5, 25)
            color = random.choice([C.ORANGE, C.RED, C.YELLOW, C.DARK_RED, (50, 50, 50)])
            self.particle_system.add_particle(
                x=C.SCREEN_WIDTH // 2,
                y=C.SCREEN_HEIGHT // 2,
                dx=math.cos(angle) * speed,
                dy=math.sin(angle) * speed,
                color=color,
                timer=random.randint(40, 100),
                size=random.randint(5, 25),
            )

        for bot in self.bots:
            if not bot.alive:
                continue
            dx = bot.x - self.player.x
            dy = bot.y - self.player.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < C.BOMB_RADIUS:
                if bot.take_damage(1000):
                    self.sound_manager.play_sound("scream")
                    self.kills += 1
                    self.kill_combo_count += 1
                    self.kill_combo_timer = 180
                    self.last_death_pos = (bot.x, bot.y)

                if dist < 5.0:
                    self.particle_system.add_explosion(
                        C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2, count=3
                    )

        try:
            self.sound_manager.play_sound("bomb")
        except BaseException:
            logger.exception("Bomb Audio Failed")

        self.damage_texts.append(
            {
                "x": C.SCREEN_WIDTH // 2,
                "y": C.SCREEN_HEIGHT // 2 - 100,
                "text": "BOMB DROPPED!",
                "color": C.ORANGE,
                "timer": 120,
                "vy": -0.5,
            }
        )

    def explode_laser(self, impact_x: float, impact_y: float) -> None:
        """Trigger Massive Laser Explosion at Impact Point"""
        try:
            self.sound_manager.play_sound("boom_real")
        except Exception:
            logger.exception("Boom sound failed")

        try:
            hits = 0
            for bot in self.bots:
                if not hasattr(bot, "alive"):
                    continue

                if bot.alive:
                    dist = math.sqrt((bot.x - impact_x) ** 2 + (bot.y - impact_y) ** 2)
                    if dist < C.LASER_AOE_RADIUS:
                        damage = 500
                        killed = bot.take_damage(damage)
                        hits += 1

                        if killed:
                            with suppress(Exception):
                                self.sound_manager.play_sound("scream")
                            self.kills += 1
                            self.kill_combo_count += 1
                            self.kill_combo_timer = 180
                            self.last_death_pos = (bot.x, bot.y)

                        for _ in range(10):
                            self.particle_system.add_particle(
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
                self.damage_texts.append(
                    {
                        "x": C.SCREEN_WIDTH // 2,
                        "y": C.SCREEN_HEIGHT // 2 - 80,
                        "text": "LASER ANNIHILATION!",
                        "color": (255, 0, 255),
                        "timer": 60,
                        "vy": -2,
                    }
                )
        except Exception:
            logger.exception("Critical Laser Error")

    def explode_plasma(self, projectile: Projectile) -> None:
        """Trigger plasma AOE explosion"""
        self._explode_generic(projectile, C.PLASMA_AOE_RADIUS, "plasma")

    def explode_rocket(self, projectile: Projectile) -> None:
        """Trigger rocket AOE explosion"""
        # Rocket has larger AOE
        radius = float(C.WEAPONS["rocket"].get("aoe_radius", 6.0))
        self._explode_generic(projectile, radius, "rocket")

    def _explode_generic(
        self, projectile: Projectile, radius: float, weapon_type: str
    ) -> None:
        """Generic explosion logic"""
        assert self.player is not None
        dist_to_player = math.sqrt(
            (projectile.x - self.player.x) ** 2 + (projectile.y - self.player.y) ** 2
        )
        if dist_to_player < 15:
            self.damage_flash_timer = 15

        # Visuals
        if dist_to_player < 20:
            count = 5 if weapon_type == "rocket" else 3
            self.particle_system.add_explosion(
                C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2, count=count
            )

            # Add some colored particles
            color = C.CYAN if weapon_type == "plasma" else C.ORANGE
            for _ in range(20):
                self.particle_system.add_particle(
                    x=C.SCREEN_WIDTH // 2,
                    y=C.SCREEN_HEIGHT // 2,
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

        for bot in self.bots:
            if not bot.alive:
                continue
            dx = bot.x - projectile.x
            dy = bot.y - projectile.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < radius:
                # Falloff damage
                damage_factor = 1.0 - (dist / radius)
                damage = int(projectile.damage * damage_factor)

                if bot.take_damage(damage):
                    self.sound_manager.play_sound("scream")
                    self.kills += 1
                    self.kill_combo_count += 1
                    self.kill_combo_timer = 180
                    self.last_death_pos = (bot.x, bot.y)

    def update_game(self) -> None:
        """Update game state"""
        if self.paused:
            return

        assert self.player is not None
        if not self.player.alive:
            if self.lives > 1:
                self.lives -= 1
                self.respawn_player()
                return
            level_time = (
                pygame.time.get_ticks() - self.level_start_time - self.total_paused_time
            ) / 1000.0
            self.level_times.append(level_time)
            self.lives = 0

            self.state = GameState.GAME_OVER
            self.game_over_timer = 0
            self.sound_manager.play_sound("game_over1")
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
            return

        enemies_alive = self.entity_manager.get_active_enemies()

        if not enemies_alive:
            if self.portal is None:
                self.spawn_portal()
                self.damage_texts.append(
                    {
                        "x": C.SCREEN_WIDTH // 2,
                        "y": C.SCREEN_HEIGHT // 2,
                        "text": "PORTAL OPENED!",
                        "color": C.CYAN,
                        "timer": 180,
                        "vy": 0,
                    }
                )

        if self.portal:
            dx = self.portal["x"] - self.player.x
            dy = self.portal["y"] - self.player.y
            dist_sq = dx * dx + dy * dy
            if dist_sq < 2.25:  # 1.5^2
                paused = self.total_paused_time
                now = pygame.time.get_ticks()
                level_time = (now - self.level_start_time - paused) / 1000.0
                self.level_times.append(level_time)
                self.state = GameState.LEVEL_COMPLETE
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)
                return

        assert self.player is not None
        assert self.game_map is not None
        keys = pygame.key.get_pressed()

        shield_active = self.input_manager.is_action_pressed("shield")

        if self.joystick and not self.paused and self.player and self.player.alive:
            axis_x = self.joystick.get_axis(0)
            axis_y = self.joystick.get_axis(1)

            if abs(axis_x) > C.JOYSTICK_DEADZONE:
                self.player.strafe(
                    self.game_map,
                    self.bots,
                    right=(axis_x > 0),
                    speed=abs(axis_x) * C.PLAYER_SPEED,
                )
                self.player.is_moving = True
            if abs(axis_y) > C.JOYSTICK_DEADZONE:
                self.player.move(
                    self.game_map,
                    self.bots,
                    forward=(axis_y < 0),
                    speed=abs(axis_y) * C.PLAYER_SPEED,
                )
                self.player.is_moving = True

            look_x = 0.0
            look_y = 0.0
            if self.joystick.get_numaxes() >= 4:
                look_x = self.joystick.get_axis(2)
                look_y = self.joystick.get_axis(3)

            if abs(look_x) > C.JOYSTICK_DEADZONE:
                self.player.rotate(look_x * C.PLAYER_ROT_SPEED * 15 * C.SENSITIVITY_X)
            if abs(look_y) > C.JOYSTICK_DEADZONE:
                self.player.pitch_view(-look_y * 10 * C.SENSITIVITY_Y)

            if self.joystick.get_numbuttons() > 0 and self.joystick.get_button(0):
                shield_active = True

            if self.joystick.get_numbuttons() > 2 and self.joystick.get_button(2):
                self.player.reload()

            if self.joystick.get_numbuttons() > 5 and self.joystick.get_button(5):
                if self.player.shoot():
                    self.fire_weapon()

            if self.joystick.get_numbuttons() > 4 and self.joystick.get_button(4):
                if self.player.fire_secondary():
                    self.fire_weapon(is_secondary=True)

            if self.joystick.get_numhats() > 0:
                hat = self.joystick.get_hat(0)
                if hat[0] == -1:
                    self.switch_weapon_with_message("pistol")
                if hat[0] == 1:
                    self.switch_weapon_with_message("rifle")
                if hat[1] == 1:
                    self.switch_weapon_with_message("shotgun")
                if hat[1] == -1:
                    self.switch_weapon_with_message("plasma")

        self.player.set_shield(shield_active)

        self.particle_system.update()

        for t in self.damage_texts:
            t["y"] += t["vy"]
            t["timer"] -= 1
        self.damage_texts = [t for t in self.damage_texts if t["timer"] > 0]

        sprint_key = keys[pygame.K_RSHIFT]
        is_sprinting = self.input_manager.is_action_pressed("sprint") or sprint_key
        if is_sprinting and self.player.stamina > 0:
            current_speed = C.PLAYER_SPRINT_SPEED
            self.player.stamina -= 1
            self.player.stamina_recharge_delay = 60
        else:
            current_speed = C.PLAYER_SPEED

        moving = False

        if self.input_manager.is_action_pressed("move_forward"):
            self.player.move(
                self.game_map, self.bots, forward=True, speed=current_speed
            )
            moving = True
        if self.input_manager.is_action_pressed("move_backward"):
            self.player.move(
                self.game_map, self.bots, forward=False, speed=current_speed
            )
            moving = True
        if self.input_manager.is_action_pressed("strafe_left"):
            self.player.strafe(
                self.game_map, self.bots, right=False, speed=current_speed
            )
            moving = True
        if self.input_manager.is_action_pressed("strafe_right"):
            self.player.strafe(
                self.game_map, self.bots, right=True, speed=current_speed
            )
            moving = True

        self.player.is_moving = moving

        if self.input_manager.is_action_pressed("turn_left"):
            self.player.rotate(-0.05)
        if self.input_manager.is_action_pressed("turn_right"):
            self.player.rotate(0.05)
        if self.input_manager.is_action_pressed("look_up"):
            self.player.pitch_view(5)
        if self.input_manager.is_action_pressed("look_down"):
            self.player.pitch_view(-5)

        self.player.update()

        self.entity_manager.update_bots(self.game_map, self.player, self)

        for bot in self.bots:
            is_item = bot.enemy_type.startswith(("health", "ammo", "bomb", "pickup"))
            if bot.alive and is_item:
                dx = bot.x - self.player.x
                dy = bot.y - self.player.y
                dist_sq = dx * dx + dy * dy
                if dist_sq < 0.64:  # 0.8^2
                    pickup_msg = ""
                    color = C.GREEN

                    if bot.enemy_type == "health_pack":
                        if self.player.health < 100:
                            self.player.health = min(100, self.player.health + 50)
                            pickup_msg = "HEALTH +50"
                    elif bot.enemy_type == "ammo_box":
                        for w in self.player.ammo:
                            self.player.ammo[w] += 20
                        pickup_msg = "AMMO FOUND"
                        color = C.YELLOW
                    elif bot.enemy_type == "bomb_item":
                        self.player.bombs += 1
                        pickup_msg = "BOMB +1"
                        color = C.ORANGE
                    elif bot.enemy_type.startswith("pickup_"):
                        w_name = bot.enemy_type.replace("pickup_", "")
                        if w_name not in self.unlocked_weapons:
                            self.unlocked_weapons.add(w_name)
                            self.player.switch_weapon(w_name)
                            pickup_msg = f"{w_name.upper()} ACQUIRED!"
                            color = C.CYAN
                        else:
                            if w_name in self.player.ammo:
                                clip_size = int(C.WEAPONS[w_name]["clip_size"])
                                self.player.ammo[w_name] += clip_size * 2
                                pickup_msg = f"{w_name.upper()} AMMO"
                                color = C.YELLOW

                    if pickup_msg:
                        bot.alive = False
                        bot.removed = True
                        self.damage_texts.append(
                            {
                                "x": C.SCREEN_WIDTH // 2,
                                "y": C.SCREEN_HEIGHT // 2 - 50,
                                "text": pickup_msg,
                                "color": color,
                                "timer": 60,
                                "vy": -1,
                            }
                        )

        self.entity_manager.update_projectiles(self.game_map, self.player, self)

        cx, cy = int(self.player.x), int(self.player.y)
        reveal_radius = 5
        for r_i in range(-reveal_radius, reveal_radius + 1):
            for r_j in range(-reveal_radius, reveal_radius + 1):
                if r_i * r_i + r_j * r_j <= reveal_radius * reveal_radius:
                    self.visited_cells.add((cx + r_j, cy + r_i))

        min_dist_sq = float("inf")
        for bot in self.bots:
            if bot.alive:
                dx = bot.x - self.player.x
                dy = bot.y - self.player.y
                d_sq = dx * dx + dy * dy
                if d_sq < min_dist_sq:
                    min_dist_sq = d_sq

        min_dist = (
            math.sqrt(min_dist_sq) if min_dist_sq != float("inf") else float("inf")
        )

        if min_dist < 15:
            self.beast_timer -= 1
            if self.beast_timer <= 0:
                self.sound_manager.play_sound("beast")
                self.beast_timer = random.randint(300, 900)

        if min_dist < 20:
            beat_delay = int(min(1.5, max(0.4, min_dist / 10.0)) * C.FPS)
            self.heartbeat_timer -= 1
            if self.heartbeat_timer <= 0:
                self.sound_manager.play_sound("heartbeat")
                self.sound_manager.play_sound("breath")
                self.heartbeat_timer = beat_delay

        if self.player.health < 50:
            self.groan_timer -= 1
            if self.groan_timer <= 0:
                self.sound_manager.play_sound("groan")
                self.groan_timer = 240

        if self.kill_combo_timer > 0:
            self.kill_combo_timer -= 1
            if self.kill_combo_timer <= 0:
                if self.kill_combo_count >= 3:
                    phrases = ["phrase_cool", "phrase_awesome", "phrase_brutal"]
                    phrase = random.choice(phrases)
                    self.sound_manager.play_sound(phrase)
                    self.damage_texts.append(
                        {
                            "x": C.SCREEN_WIDTH // 2,
                            "y": C.SCREEN_HEIGHT // 2 - 150,
                            "text": phrase.replace("phrase_", "").upper() + "!",
                            "color": C.YELLOW,
                            "timer": 120,
                            "vy": -0.2,
                        }
                    )
                self.kill_combo_count = 0

    def handle_intro_events(self) -> None:
        """Handle intro screen events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.ui_renderer.intro_video:
                    self.ui_renderer.intro_video.release()
                    self.ui_renderer.intro_video = None
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                    if self.ui_renderer.intro_video:
                        self.ui_renderer.intro_video.release()
                        self.ui_renderer.intro_video = None
                    self.state = GameState.MENU
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.ui_renderer.intro_video:
                    self.ui_renderer.intro_video.release()
                    self.ui_renderer.intro_video = None
                self.state = GameState.MENU

    def handle_menu_events(self) -> None:
        """Handle main menu events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.state = GameState.MAP_SELECT
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.state = GameState.MAP_SELECT

    def handle_map_select_events(self) -> None:
        """Handle map selection events"""
        self.ui_renderer.start_button.update(pygame.mouse.get_pos())
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU
                elif event.key == pygame.K_RETURN:
                    self.start_game()
                    self.state = GameState.PLAYING
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.ui_renderer.start_button.is_clicked(event.pos):
                    self.start_game()
                    self.state = GameState.PLAYING
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)

                my = event.pos[1]
                if 200 <= my < 200 + 4 * 80:
                    row = (my - 200) // 80
                    if row == 0:
                        sizes = C.MAP_SIZES
                        try:
                            idx = sizes.index(self.selected_map_size)
                            self.selected_map_size = sizes[(idx + 1) % len(sizes)]
                        except ValueError:
                            self.selected_map_size = 40
                    elif row == 1:
                        diffs = list(C.DIFFICULTIES.keys())
                        try:
                            idx = diffs.index(self.selected_difficulty)
                            self.selected_difficulty = diffs[(idx + 1) % len(diffs)]
                        except ValueError:
                            self.selected_difficulty = "NORMAL"
                    elif row == 2:
                        self.selected_start_level = (self.selected_start_level % 5) + 1
                    elif row == 3:
                        self.selected_lives = (self.selected_lives % 5) + 1

    def handle_level_complete_events(self) -> None:
        """Handle input events during the level complete screen."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.level += 1
                    self.start_level()
                    self.state = GameState.PLAYING
                elif event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU

    def handle_game_over_events(self) -> None:
        """Handle input events during the game over screen."""
        # Sequence Sound Logic
        self.game_over_timer += 1
        if self.game_over_timer == 120:
            self.sound_manager.play_sound("game_over2")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.start_game()
                    self.state = GameState.PLAYING
                elif event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU

    def handle_key_config_events(self) -> None:
        """Handle input events in Key Config menu."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if self.binding_action:
                    # Bind the key
                    if event.key != pygame.K_ESCAPE:
                        self.input_manager.bind_key(self.binding_action, event.key)
                    self.binding_action = None
                elif event.key == pygame.K_ESCAPE:
                    self.state = GameState.PLAYING if self.paused else GameState.MENU

            elif event.type == pygame.MOUSEBUTTONDOWN and not self.binding_action:
                mx, my = event.pos

                # Check clicks on bindings
                bindings = self.input_manager.bindings
                actions = sorted(bindings.keys())
                start_y = 120
                col_1_x = C.SCREEN_WIDTH // 4
                col_2_x = C.SCREEN_WIDTH * 3 // 4
                limit = 12

                for i, action in enumerate(actions):
                    col = 0 if i < limit else 1
                    idx = i if i < limit else i - limit
                    x = col_1_x if col == 0 else col_2_x
                    y = start_y + idx * 40

                    # Approximate hit box (Name + Key)
                    # Name ends at x-150, Key starts at x+20.
                    # Let's say click area is x-150 to x+150, height 30.
                    rect = pygame.Rect(x - 150, y, 300, 30)
                    if rect.collidepoint(mx, my):
                        self.binding_action = action
                        return

                # Back Button
                center_x = C.SCREEN_WIDTH // 2 - 50
                top_y = C.SCREEN_HEIGHT - 80
                back_rect = pygame.Rect(center_x, top_y, 100, 40)
                if back_rect.collidepoint(mx, my):
                    self.state = GameState.PLAYING if self.paused else GameState.MENU

    def _update_intro_logic(self, elapsed: int) -> None:
        """Update intro sequence logic and transitions.

        Args:
            elapsed: Elapsed time in milliseconds since intro started.
        """
        duration = 0
        if self.intro_phase == 0:
            duration = 3000
        elif self.intro_phase == 1:
            duration = 3000
        elif self.intro_phase == 2:
            slides_durations = [8000, 10000, 4000, 4000]
            if self.intro_step < len(slides_durations):
                duration = slides_durations[self.intro_step]

                if self.intro_step == 0 and elapsed < 50:
                    if not hasattr(self, "_laugh_played"):
                        self.sound_manager.play_sound("laugh")
                        self._laugh_played = True

                if elapsed > duration:
                    self.intro_step += 1
                    self.intro_start_time = 0
                    if hasattr(self, "_laugh_played"):
                        del self._laugh_played
            else:
                self.state = GameState.MENU
                return

        if self.intro_phase < 2:
            if self.intro_phase == 1 and elapsed < 50:
                if not hasattr(self, "_water_played"):
                    self.sound_manager.play_sound("water")
                    self._water_played = True

            if elapsed > duration:
                self.intro_phase += 1
                self.intro_start_time = 0
                # Only release video when transitioning from phase 1 to phase 2
                if self.intro_phase == 2 and self.ui_renderer.intro_video:
                    self.ui_renderer.intro_video.release()
                    self.ui_renderer.intro_video = None

    def run(self) -> None:
        """Main game loop"""
        try:
            while self.running:
                if self.state == GameState.INTRO:
                    self.handle_intro_events()
                    if self.intro_start_time == 0:
                        self.intro_start_time = pygame.time.get_ticks()
                    elapsed = pygame.time.get_ticks() - self.intro_start_time

                    self.ui_renderer.render_intro(
                        self.intro_phase, self.intro_step, elapsed
                    )
                    self._update_intro_logic(elapsed)

                elif self.state == GameState.MENU:
                    self.handle_menu_events()
                    self.ui_renderer.render_menu()

                elif self.state == GameState.KEY_CONFIG:
                    self.handle_key_config_events()
                    self.ui_renderer.render_key_config(self)

                elif self.state == GameState.MAP_SELECT:
                    self.handle_map_select_events()
                    self.ui_renderer.render_map_select(self)

                elif self.state == GameState.PLAYING:
                    self.handle_game_events()
                    if self.paused:
                        # Pause Menu Audio
                        # Heartbeat: 70 BPM -> ~0.85s delay -> ~51 frames (at 60FPS)
                        beat_delay = 51
                        self.heartbeat_timer -= 1
                        if self.heartbeat_timer <= 0:
                            self.sound_manager.play_sound("heartbeat")
                            self.sound_manager.play_sound("breath")
                            self.heartbeat_timer = beat_delay

                        if self.player and self.player.health < 50:
                            self.groan_timer -= 1
                            if self.groan_timer <= 0:
                                self.sound_manager.play_sound("groan")
                                self.groan_timer = 240
                    else:
                        self.update_game()
                    self.renderer.render_game(self)
                    # Decrement damage flash timer after rendering
                    # to maintain correct frame count
                    if not self.paused and self.damage_flash_timer > 0:
                        self.damage_flash_timer -= 1

                elif self.state == GameState.LEVEL_COMPLETE:
                    self.handle_level_complete_events()
                    self.ui_renderer.render_level_complete(self)

                elif self.state == GameState.GAME_OVER:
                    self.handle_game_over_events()
                    self.ui_renderer.render_game_over(self)

                self.clock.tick(C.FPS)
        except Exception as e:
            with open("crash_log.txt", "w") as f:
                f.write(traceback.format_exc())
            logger.critical("CRASH: %s", e)
            raise
