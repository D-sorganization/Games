from __future__ import annotations

import logging
import math
import random
import traceback
from contextlib import suppress
from typing import Any, cast

import pygame

from . import constants as C  # noqa: N812
from .bot import Bot
from .entity_manager import EntityManager
from .input_manager import InputManager
from .map import Map
from .particle_system import ParticleSystem
from .player import Player
from .projectile import Projectile
from .raycaster import Raycaster
from .renderer import GameRenderer
from .sound import SoundManager
from .ui_renderer import UIRenderer

logger = logging.getLogger(__name__)


class Game:
    """Main game class"""

    def __init__(self) -> None:
        """Initialize game"""
        flags = pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), flags)
        pygame.display.set_caption("Duum - The Reimagining")
        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize Renderer
        self.renderer = GameRenderer(self.screen)
        self.ui_renderer = UIRenderer(self.screen)

        # Game state
        self.state = "intro"
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
        self.portal: dict[str, Any] | None = None
        self.health = 100
        self.lives = C.DEFAULT_LIVES

        # Unlocked weapons tracking
        self.unlocked_weapons = {"pistol"}
        self.cheat_mode_active = False
        self.current_cheat_input = ""
        self.god_mode = False

        self.game_over_timer = 0

        # Audio
        self.sound_manager = SoundManager()
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

    @property
    def bots(self) -> list[Bot]:
        """Get list of active bots."""
        return self.entity_manager.bots

    @property
    def projectiles(self) -> list[Projectile]:
        """Get list of active projectiles."""
        return self.entity_manager.projectiles

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
        self.add_message(msg, C.WHITE)

    def add_message(self, text: str, color: tuple[int, int, int]) -> None:
        """Add a temporary message to the center of the screen"""
        self.damage_texts.append(
            {
                "x": C.SCREEN_WIDTH // 2,
                "y": C.SCREEN_HEIGHT // 2 - 50,
                "text": text,
                "color": color,
                "timer": 60,
                "vy": -0.5,
            }
        )

    def switch_weapon_with_message(self, weapon_name: str) -> None:
        """Switch weapon and show a message if successful"""
        if weapon_name not in self.unlocked_weapons:
            self.add_message("WEAPON LOCKED", C.RED)
            return

        assert self.player is not None
        if self.player.current_weapon != weapon_name:
            self.player.switch_weapon(weapon_name)
            self.add_message(f"SWITCHED TO {weapon_name.upper()}", C.YELLOW)

    def spawn_portal(self) -> None:
        """Spawn exit portal"""
        # Spawn at last enemy death position if possible (guaranteed accessible usually)
        if self.last_death_pos:
            self.portal = {"x": self.last_death_pos[0], "y": self.last_death_pos[1]}
            return

        # Fallback: Find a spot near player
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
        """Find a safe spawn position near the base coordinates"""
        game_map = self.game_map
        map_size = game_map.size if game_map else self.selected_map_size
        if not game_map:
            return (base_x, base_y, angle)

        for attempt in range(10):
            # Try positions in a small radius around the corner
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

                # Ensure within bounds
                in_x = test_x >= 2 and test_x < map_size - 2
                in_y = test_y >= 2 and test_y < map_size - 2
                if not (in_x and in_y):
                    continue

                # Check if not a wall
                if not game_map.is_wall(test_x, test_y):
                    return (test_x, test_y, angle)

        # Fallback to base position if all attempts fail
        return (base_x, base_y, angle)

    def get_corner_positions(self) -> list[tuple[float, float, float]]:
        """Get spawn positions for four corners (x, y, angle)"""
        offset = 5
        map_size = self.game_map.size if self.game_map else self.selected_map_size

        # Reserve space near the bottom-right corner so the spawn point
        # stays well inside the map and away from large structures/boundaries.
        # The 0.75 factor is a historical heuristic kept for compatibility.
        building4_start = int(map_size * 0.75)
        bottom_right_offset = map_size - building4_start + C.SPAWN_SAFETY_MARGIN

        corners = [
            (offset, offset, math.pi / 4),  # Top-left
            (offset, map_size - offset, 7 * math.pi / 4),  # Bottom-left
            (map_size - offset, offset, 3 * math.pi / 4),  # Top-right
            (
                map_size - bottom_right_offset,
                map_size - bottom_right_offset,
                5 * math.pi / 4,
            ),  # Bottom-right
        ]

        # Find safe spawns for each corner
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
            return C.DEFAULT_PLAYER_SPAWN

        for pos in corners:
            if not game_map.is_wall(pos[0], pos[1]):
                return pos

        # Fallback linear search
        for y in range(game_map.height):
            for x in range(game_map.width):
                if not game_map.is_wall(x, y):
                    return (x + 0.5, y + 0.5, 0.0)

        return C.DEFAULT_PLAYER_SPAWN

    def respawn_player(self) -> None:
        """Respawn player after death if lives remain"""
        assert self.game_map is not None
        assert self.player is not None

        player_pos = self._get_best_spawn_point()

        # Reset Player
        self.player.x = player_pos[0]
        self.player.y = player_pos[1]
        self.player.angle = player_pos[2]
        self.player.health = 100
        self.player.alive = True
        self.player.shield_active = False  # Reset shield

        # Show message
        self.damage_texts.append(
            {
                "x": C.SCREEN_WIDTH // 2,
                "y": C.SCREEN_HEIGHT // 2,
                "text": "RESPAWNED",
                "color": C.GREEN,
                "timer": 120,
                "vy": -0.5,
            }
        )

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
        self.unlocked_weapons = {"pistol"}
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
        self.raycaster = Raycaster(self.game_map)
        self.raycaster.set_render_scale(self.render_scale)
        self.last_death_pos = None

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
            # Try to place bot
            for _ in range(20):
                bx = random.randint(2, self.game_map.size - 2)
                by = random.randint(2, self.game_map.size - 2)

                # Distance check (Increased safety but ensuring spawns)
                dist = math.sqrt((bx - player_pos[0]) ** 2 + (by - player_pos[1]) ** 2)
                if dist < 15.0:  # Safe zone radius (was 20.0, blocked too much)
                    continue

                if not self.game_map.is_wall(bx, by):
                    # Add bot
                    enemy_type = random.choice(list(C.ENEMY_TYPES.keys()))
                    while enemy_type in [
                        "boss",
                        "demon",
                        "ball",
                        "beast",
                        "pickup_rifle",
                        "pickup_shotgun",
                        "pickup_plasma",
                        "health_pack",
                        "ammo_box",
                        "bomb_item",
                        "pickup_rocket",
                        "pickup_minigun",
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
        for _ in range(50):
            cx = random.randint(2, upper_bound)
            cy = random.randint(2, upper_bound)
            if (
                not self.game_map.is_wall(cx, cy)
                and math.sqrt((cx - player_pos[0]) ** 2 + (cy - player_pos[1]) ** 2)
                > 15
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
            "pickup_plasma",
            "pickup_minigun",
            "pickup_rocket",
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
                            self.state = "key_config"
                            self.binding_action = None  # Initialize binding state
                        elif 530 <= my <= 580:  # Quit to Menu
                            self.state = "menu"
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
                speed=float(
                    cast("float", C.WEAPONS["plasma"].get("projectile_speed", 0.5))
                ),
                damage=self.player.get_current_weapon_damage(),
                is_player=True,
                color=cast(
                    "tuple[int, int, int]",
                    C.WEAPONS["plasma"].get("projectile_color", (0, 255, 255)),
                ),
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
                speed=float(
                    cast("float", C.WEAPONS["rocket"].get("projectile_speed", 0.3))
                ),
                damage=self.player.get_current_weapon_damage(),
                is_player=True,
                color=cast(
                    "tuple[int, int, int]",
                    C.WEAPONS["rocket"].get("projectile_color", (255, 100, 0)),
                ),
                size=0.3,
                weapon_type="rocket",
            )
            self.entity_manager.add_projectile(p)
            return

        if weapon == "minigun" and not is_secondary:
            # Minigun spread
            angle_off = random.uniform(-0.1, 0.1)
            self.check_shot_hit(angle_offset=angle_off)
            return

        if weapon == "laser" and not is_secondary:
            # Hitscan with Beam Visual
            self.check_shot_hit(is_secondary=False, is_laser=True)
            return

        if weapon == "shotgun" and not is_secondary:
            # Spread Fire
            pellets = int(cast("int", C.WEAPONS["shotgun"].get("pellets", 8)))
            spread = float(cast("float", C.WEAPONS["shotgun"].get("spread", 0.15)))
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
            wall_dist, _ = self.raycaster.cast_ray(
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

            # Visual Traces
            # Calculate Screen Hit Point
            # We know the object hit is at distance closest_dist (bot) or wall_dist
            # (wall)

            # Simple screen projection for trace endpoint
            # In a raycaster, x is derived from angle difference
            angle_diff = aim_angle - self.player.angle
            # Normalize to -PI to PI
            angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

            # Project to screen X
            # Screen width corresponds to FOV.
            # x = (0.5 - angle_diff / FOV) * SCREEN_WIDTH
            # But wait, angle increases counter-clockwise?
            # Usually raycaster:
            # screen_x 0 -> angle + FOV/2, screen_x Width -> angle - FOV/2
            # Let's approximate:
            screen_hit_x = (0.5 - angle_diff / C.FOV) * C.SCREEN_WIDTH

            # Project to screen Y
            # y = H/2 + (player_z - hit_z) / dist * height_scale + pitch_offset
            # Assuming hit is at same height roughly (center of screen vertically if 0)
            # But we have pitch.
            # pitch_view adds offset in pixels.
            # Wall height on screen is proportional to 1/dist.
            # Let's aim for the "center" of the hit view.
            screen_hit_y = C.SCREEN_HEIGHT // 2 + self.player.pitch

            # Weapon Start Position (Bottom Center-ish)
            weapon_start_x = C.SCREEN_WIDTH * 0.6  # Slightly right
            weapon_start_y = C.SCREEN_HEIGHT

            # Adjust start for "hand" position
            self.particle_system.add_trace(
                start=(weapon_start_x, weapon_start_y),
                end=(screen_hit_x, screen_hit_y),
                color=(255, 255, 100), # Pale yellow trace
                timer=5,
                width=1
            )

            if not closest_bot:
                # Wall Hit Effect at screen_hit_x, screen_hit_y
                # Add sparks
                for _ in range(5):
                    self.particle_system.add_particle(
                        x=screen_hit_x,
                        y=screen_hit_y,
                        dx=random.uniform(-3, 3),
                        dy=random.uniform(-3, 3),
                        color=(255, 200, 100), # Spark color
                        timer=20,
                        size=random.randint(1, 3)
                    )

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
        radius = float(cast("float", C.WEAPONS["rocket"].get("aoe_radius", 6.0)))
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

            self.state = "game_over"
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
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 1.5:
                paused = self.total_paused_time
                now = pygame.time.get_ticks()
                level_time = (now - self.level_start_time - paused) / 1000.0
                self.level_times.append(level_time)
                self.state = "level_complete"
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

        for t in self.damage_texts[:]:
            t["y"] += t["vy"]
            t["timer"] -= 1
            if t["timer"] <= 0:
                self.damage_texts.remove(t)

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
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 0.8:
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
                            clip_size = int(cast("int", C.WEAPONS[w_name]["clip_size"]))
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
                    self.state = "menu"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.ui_renderer.intro_video:
                    self.ui_renderer.intro_video.release()
                    self.ui_renderer.intro_video = None
                self.state = "menu"

    def handle_menu_events(self) -> None:
        """Handle main menu events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.state = "map_select"
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.state = "map_select"

    def handle_map_select_events(self) -> None:
        """Handle map selection events"""
        self.ui_renderer.start_button.update(pygame.mouse.get_pos())
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                elif event.key == pygame.K_RETURN:
                    self.start_game()
                    self.state = "playing"
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.ui_renderer.start_button.is_clicked(event.pos):
                    self.start_game()
                    self.state = "playing"
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
                    self.state = "playing"
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"

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
                    self.state = "playing"
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"

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
                    self.state = "playing" if self.paused else "menu"

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
                    self.state = "playing" if self.paused else "menu"

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
                self.state = "menu"
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
                if self.state == "intro":
                    self.handle_intro_events()
                    if self.intro_start_time == 0:
                        self.intro_start_time = pygame.time.get_ticks()
                    elapsed = pygame.time.get_ticks() - self.intro_start_time

                    self.ui_renderer.render_intro(
                        self.intro_phase, self.intro_step, elapsed
                    )
                    self._update_intro_logic(elapsed)

                elif self.state == "menu":
                    self.handle_menu_events()
                    self.ui_renderer.render_menu()

                elif self.state == "key_config":
                    self.handle_key_config_events()
                    self.ui_renderer.render_key_config(self)

                elif self.state == "map_select":
                    self.handle_map_select_events()
                    self.ui_renderer.render_map_select(self)

                elif self.state == "playing":
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

                elif self.state == "level_complete":
                    self.handle_level_complete_events()
                    self.ui_renderer.render_level_complete(self)

                elif self.state == "game_over":
                    self.handle_game_over_events()
                    self.ui_renderer.render_game_over(self)

                self.clock.tick(C.FPS)
        except Exception as e:
            with open("crash_log.txt", "w") as f:
                f.write(traceback.format_exc())
            logger.critical("CRASH: %s", e)
            raise
