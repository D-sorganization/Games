from __future__ import annotations

import contextlib
import math
import os
import random
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple, cast

import pygame

from . import constants as C  # noqa: N812
from .bot import Bot
from .map import Map
from .player import Player
from .projectile import Projectile
from .raycaster import Raycaster
from .sound import SoundManager
from .ui import Button

try:
    import cv2

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class Game:
    """Main game class"""

    def __init__(self) -> None:
        """Initialize game"""
        # Allow resizing and maximizing (SCALED requires pygame 2.0+)
        flags = pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), flags)
        pygame.display.set_caption("Force Field - Arena Combat")
        self.clock = pygame.time.Clock()
        self.running = True

        # Game state
        self.state = "intro"
        self.intro_phase = 0
        self.intro_step = 0
        self.intro_timer = 0
        self.intro_alpha = 0
        self.intro_start_time = 0
        self.intro_images: Dict[str, pygame.Surface] = {}
        self.last_death_pos: Tuple[float, float] | None = None

        # Load Intro Images
        try:
            base_dir = Path(__file__).resolve().parent.parent
            self.assets_dir = str(base_dir / "assets")
            pics_dir = str(base_dir / "pics")

            # Willy Wonk
            willy_path = os.path.join(pics_dir, "WillyWonk.JPG")
            if os.path.exists(willy_path):
                img = pygame.image.load(willy_path)
                # Rotate clockwise 90 degrees
                img = pygame.transform.rotate(img, -90)
                scale = min(500 / img.get_height(), 800 / img.get_width())
                if scale < 1:
                    new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                    img = pygame.transform.scale(img, new_size)

                # Soften edges (Vignette/Alpha Mask)
                mask = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                mask.fill((0, 0, 0, 255))
                # Draw transparent circle in center to keep, fading out to edges?
                # Actually, standard way: draw white circle on black, sub from alpha.
                # Or just straightforward:
                # Create a new surface with SRCALPHA
                soft_img = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                soft_img.blit(img, (0, 0))

                # Simple loop for gradient (slow on init only)
                # Or just draw a big radial gradient?
                # Faster: Just rect border fade?
                # Pre-prepared vignette image is better but we construct one.
                # We will skip complex per-pixel and just rely on the black background.

                self.intro_images["willy"] = img

            # Setup Video for Upstream Drift
            self.intro_video = None
            video_path = os.path.join(pics_dir, "DeadFishSwimming.mp4")
            if HAS_CV2 and os.path.exists(video_path):
                self.intro_video = cv2.VideoCapture(video_path)

            # Keep GIF as fallback
            deadfish_path = os.path.join(pics_dir, "DeadFishSwimming_0.JPG")
            if os.path.exists(deadfish_path):
                img = pygame.image.load(deadfish_path)
                scale = min(500 / img.get_height(), 800 / img.get_width())
                if scale < 1:
                    new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                    img = pygame.transform.scale(img, new_size)
                self.intro_images["deadfish"] = img

        except Exception as e:  # noqa: BLE001
            print(f"Failed to load intro images: {e}")

        # Gameplay state
        self.level = 1
        self.kills = 0
        self.level_start_time = 0
        self.level_times: List[float] = []
        self.selected_map_size = C.DEFAULT_MAP_SIZE
        self.paused = False
        self.pause_start_time = 0
        self.total_paused_time = 0
        self.shooting = False
        self.shoot_timer = 0
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

        # Visual effects
        self.particles: List[Dict[str, Any]] = []
        self.damage_texts: List[Dict[str, Any]] = []

        # Game objects
        self.game_map: Map | None = None
        self.player: Player | None = None
        self.bots: List[Bot] = []
        self.projectiles: List[Projectile] = []
        self.raycaster: Raycaster | None = None
        self.portal: Dict[str, Any] | None = None
        self.health = 100
        self.max_health = 100
        # Unlocked weapons tracking
        self.unlocked_weapons = {"pistol"}
        self.cheat_mode_active = False
        self.current_cheat_input = ""
        self.god_mode = False

        self.is_moving = False  # Track movement state for bobbing
        if not hasattr(self, "intro_video"):
            self.intro_video = None

        self.game_over_timer = 0
        self.title_drips: List[Dict[str, Any]] = []

        # Fonts - Modern and Stylistic
        try:
            self.title_font = pygame.font.SysFont("impact", 100)  # Bold, impactful
            self.font = pygame.font.SysFont("franklingothicmedium", 40)  # Clean but heavy
            self.small_font = pygame.font.SysFont("franklingothicmedium", 28)
            self.tiny_font = pygame.font.SysFont("consolas", 20)
            self.subtitle_font = pygame.font.SysFont("georgia", 36)  # Noir style
        except Exception:  # noqa: BLE001
            # Fallback
            self.title_font = pygame.font.Font(None, 80)
            self.font = pygame.font.Font(None, 48)
            self.small_font = pygame.font.Font(None, 32)
            self.tiny_font = pygame.font.Font(None, 24)
            self.subtitle_font = pygame.font.Font(None, 40)

        # Cache static UI strings
        self.weapon_hints = " ".join(
            f"{weapon_data['key']}:{weapon_data['name']}" for weapon_data in C.WEAPONS.values()
        )

        # Menu buttons
        # Buttons will be created dynamically or just defined in render
        self.start_button = Button(
            C.SCREEN_WIDTH // 2 - 250,
            C.SCREEN_HEIGHT - 120,
            500,
            70,
            "ENTER THE NIGHTMARE",
            C.DARK_RED,
        )

        # Audio
        self.sound_manager = SoundManager()
        self.sound_manager.start_music()

        # Input
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            try:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                print(f"Controller detected: {self.joystick.get_name()}")
            except Exception as e:  # noqa: BLE001
                print(f"Controller init failed: {e}")

        # Fog of War
        self.visited_cells: set[tuple[int, int]] = set()

        # Optimization: Shared surface for alpha effects
        self.effects_surface = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)

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

    def get_corner_positions(self) -> List[Tuple[float, float, float]]:
        """Get spawn positions for four corners (x, y, angle)"""
        offset = 5
        map_size = self.game_map.size if self.game_map else self.selected_map_size

        # Try multiple positions near each corner to find one that's not in a building
        def find_safe_spawn(
            base_x: float,
            base_y: float,
            angle: float,
        ) -> Tuple[float, float, float]:
            """Find a safe spawn position near the base coordinates"""
            if not self.game_map:
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
                    if test_x < 2 or test_x >= map_size - 2 or test_y < 2 or test_y >= map_size - 2:
                        continue

                    # Check if not in building and not a wall
                    if not self.game_map.is_wall(
                        test_x,
                        test_y,
                    ) and not self.game_map.is_inside_building(test_x, test_y):
                        return (test_x, test_y, angle)

            # Fallback to base position if all attempts fail
            return (base_x, base_y, angle)

        # Building 4 occupies 0.75 * size to 0.95 * size,
        # so bottom-right spawn must be before 0.75 * size
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
            safe_corners.append(find_safe_spawn(x, y, angle))

        return safe_corners

    def respawn_player(self) -> None:
        """Respawn player after death if lives remain"""
        assert self.game_map is not None
        assert self.player is not None

        # Find safe spawn (similar to start_level)
        corners = self.get_corner_positions()
        random.shuffle(corners)
        player_pos = corners[0]

        # Check safety
        if self.game_map.is_wall(player_pos[0], player_pos[1]) or self.game_map.is_inside_building(
            player_pos[0], player_pos[1]
        ):
            # Find nearby
            for attempt in range(20):
                test_x = player_pos[0] + random.uniform(-3, 3)
                test_y = player_pos[1] + random.uniform(-3, 3)
                if not self.game_map.is_wall(
                    test_x, test_y
                ) and not self.game_map.is_inside_building(test_x, test_y):
                    player_pos = (test_x, test_y, player_pos[2])
                    break

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
        self.particles = []
        self.damage_texts = []

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
        self.particles = []
        self.damage_texts = []
        self.damage_flash_timer = 0
        self.visited_cells = set()  # Reset fog of war
        self.portal = None

        # Player Spawn Logic - Use corners
        corners = self.get_corner_positions()
        random.shuffle(corners)

        # Select best corner (safest)
        player_pos = corners[0]
        # Just in case, try to verify valid spot (though corners should be valid)
        if self.game_map.is_wall(int(player_pos[0]), int(player_pos[1])):
            # Fallback
            player_pos = (2.5, 2.5, 0.0)

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

        # Reset Fog/Mist surface on level load
        if hasattr(self, "mist_surface"):
            del self.mist_surface

        # Bots spawn in random locations, but respect safety radius
        self.bots = []
        self.projectiles = []

        num_enemies = int(
            min(50, 5 + self.level * 2 * C.DIFFICULTIES[self.selected_difficulty]["score_mult"])
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
                    ]:
                        enemy_type = random.choice(list(C.ENEMY_TYPES.keys()))

                    self.bots.append(
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
        for attempt in range(50):
            cx = random.randint(2, upper_bound)
            cy = random.randint(2, upper_bound)
            if (
                not self.game_map.is_wall(cx, cy)
                and not self.game_map.is_inside_building(cx, cy)
                and math.sqrt((cx - player_pos[0]) ** 2 + (cy - player_pos[1]) ** 2) > 15
            ):
                self.bots.append(
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
        possible_weapons = ["pickup_rifle", "pickup_shotgun", "pickup_plasma"]
        for w_pickup in possible_weapons:
            if random.random() < 0.4:  # 40% chance per level
                rx = random.randint(5, self.game_map.size - 5)
                ry = random.randint(5, self.game_map.size - 5)
                if not self.game_map.is_wall(rx, ry):
                    self.bots.append(Bot(rx + 0.5, ry + 0.5, self.level, w_pickup))

        # Ammo / Bombs
        for _ in range(8):
            rx = random.randint(5, self.game_map.size - 5)
            ry = random.randint(5, self.game_map.size - 5)
            if not self.game_map.is_wall(rx, ry):
                choice = random.random()
                if choice < 0.2:
                    self.bots.append(Bot(rx + 0.5, ry + 0.5, self.level, "bomb_item"))
                elif choice < 0.7:
                    self.bots.append(Bot(rx + 0.5, ry + 0.5, self.level, "ammo_box"))
                else:
                    self.bots.append(Bot(rx + 0.5, ry + 0.5, self.level, "health_pack"))

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

                # Normal Controls
                if event.key == pygame.K_ESCAPE:
                    self.paused = not self.paused
                    if self.paused:
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                    else:
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)

                # Activate Cheat Mode
                elif event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.cheat_mode_active = True
                    self.current_cheat_input = ""
                    self.add_message("CHEAT MODE: TYPE CODE", C.PURPLE)
                    continue

                if not self.paused:
                    if event.key == pygame.K_1:
                        self.switch_weapon_with_message("pistol")
                    elif event.key == pygame.K_2:
                        self.switch_weapon_with_message("rifle")
                    elif event.key == pygame.K_3:
                        self.switch_weapon_with_message("shotgun")
                    elif event.key == pygame.K_4:
                        self.switch_weapon_with_message("laser")
                    elif event.key == pygame.K_5:
                        self.switch_weapon_with_message("plasma")
                    elif event.key == pygame.K_r:
                        assert self.player is not None
                        self.player.reload()
                    elif event.key == pygame.K_z:
                        assert self.player is not None
                        self.player.zoomed = not self.player.zoomed
                    elif event.key == pygame.K_f:
                        # Bomb
                        assert self.player is not None
                        if self.player.activate_bomb():
                            self.handle_bomb_explosion()

            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and not self.paused
                and not self.cheat_mode_active
            ):
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
                speed=float(C.WEAPONS["plasma"].get("projectile_speed", 0.5)),  # type: ignore[arg-type]
                damage=self.player.get_current_weapon_damage(),
                is_player=True,
                color=tuple(C.WEAPONS["plasma"].get("projectile_color", (0, 255, 255))),  # type: ignore[arg-type]
                size=0.225,  # 3/4 of original 0.3
                weapon_type="plasma",
            )
            self.projectiles.append(p)
            return

        if weapon == "laser" and not is_secondary:
            # Hitscan with Beam Visual
            self.check_shot_hit(is_secondary=False, is_laser=True)
            return

        if weapon == "shotgun" and not is_secondary:
            # Spread Fire
            pellets = int(C.WEAPONS["shotgun"].get("pellets", 8))  # type: ignore[call-overload]
            spread = float(C.WEAPONS["shotgun"].get("spread", 0.15))  # type: ignore[arg-type]
            for _ in range(pellets):
                angle_off = random.uniform(-spread, spread)
                self.check_shot_hit(angle_offset=angle_off)
        else:
            # Single Hitscan
            self.check_shot_hit(is_secondary=is_secondary)

    def check_shot_hit(
        self, is_secondary: bool = False, angle_offset: float = 0.0, is_laser: bool = False
    ) -> None:
        """Check if player's shot hit a bot"""
        assert self.player is not None
        try:
            # Cast ray in player's view direction
            # Cast ray in player's view direction
            weapon_range = self.player.get_current_weapon_range()
            if is_secondary:
                weapon_range = 100  # Maximum range for laser beam

            weapon_damage = self.player.get_current_weapon_damage()

            closest_bot = None
            closest_dist = float("inf")
            is_headshot = False

            # Optimize: Find strict distance to wall in aiming direction first
            # Simple Raycast (DDA)
            ray_angle = self.player.angle + angle_offset
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)

            # Ray start
            rx, ry = self.player.x, self.player.y
            map_x, map_y = int(rx), int(ry)

            # Delta Dist
            delta_dist_x = abs(1 / cos_a) if cos_a != 0 else 1e30
            delta_dist_y = abs(1 / sin_a) if sin_a != 0 else 1e30

            # Step and side dist
            if cos_a < 0:
                step_x = -1
                side_dist_x = (rx - map_x) * delta_dist_x
            else:
                step_x = 1
                side_dist_x = (map_x + 1.0 - rx) * delta_dist_x

            if sin_a < 0:
                step_y = -1
                side_dist_y = (ry - map_y) * delta_dist_y
            else:
                step_y = 1
                side_dist_y = (map_y + 1.0 - ry) * delta_dist_y

            # DDA
            wall_dist: float = float(weapon_range)  # Max limit
            hit_wall = False
            steps = 0
            max_raycast_steps = C.MAX_RAYCAST_STEPS  # Maximum steps for raycasting

            while not hit_wall and steps < max_raycast_steps:
                steps += 1
                if side_dist_x < side_dist_y:
                    side_dist_x += delta_dist_x
                    map_x += step_x
                    dist = side_dist_x - delta_dist_x
                else:
                    side_dist_y += delta_dist_y
                    map_y += step_y
                    dist = side_dist_y - delta_dist_y

                if dist > weapon_range:
                    break

                # Bounds check to prevent infinite or OOB errors
                assert self.game_map is not None
                if (
                    map_x < 0
                    or map_x >= self.game_map.size
                    or map_y < 0
                    or map_y >= self.game_map.size
                ):
                    hit_wall = True
                    wall_dist = dist
                    break

                if self.game_map.is_wall(map_x, map_y):
                    wall_dist = dist
                    hit_wall = True

            for bot in self.bots:
                if not bot.alive:
                    continue

                # Calculate bot position relative to player
                assert self.player is not None
                dx = bot.x - self.player.x
                dy = bot.y - self.player.y
                distance = math.sqrt(dx**2 + dy**2)

                if distance > wall_dist:  # Blotched by wall
                    continue

                # Check if bot is in front of player
                bot_angle = math.atan2(dy, dx)
                bot_angle_norm = bot_angle if bot_angle >= 0 else bot_angle + 2 * math.pi

                # Add Aiming Randomness (Spread)
                # If we passed an angle_offset (shotgun), rely on that + base spread
                # Otherwise standard spread
                current_spread = C.SPREAD_ZOOM if self.player.zoomed else C.SPREAD_BASE

                # If angle_offset is provided, use it as the base aim direction
                # but still apply small spread?
                # Actually angle_offset IS the spread for shotgun.
                if angle_offset == 0.0:
                    spread_offset = random.uniform(-current_spread, current_spread)
                    aim_angle = self.player.angle + spread_offset
                else:
                    aim_angle = self.player.angle + angle_offset

                aim_angle %= 2 * math.pi

                angle_diff = abs(bot_angle_norm - aim_angle)
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff

                # Hit threshold (cone of fire)
                if angle_diff < 0.15:  # Small angle threshold
                    if distance < closest_dist:
                        closest_bot = bot
                        closest_dist = distance
                        # Headshot is tighter threshold
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
                except Exception as e:  # noqa: BLE001
                    print(f"Error in explode_laser: {e}")

                # Visual Beam
                # Visual Beam (handled by particles)

                # Add laser effect
                # For a raycaster, drawing 2D line from weapon to center is best approximation
                self.particles.append(
                    {
                        "type": "laser",
                        "start": (C.SCREEN_WIDTH - 200, C.SCREEN_HEIGHT - 180),  # Approx gun muzzle
                        "end": (C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2),  # Crosshair
                        "color": (0, 255, 255),
                        "timer": C.LASER_DURATION,
                        "width": C.LASER_WIDTH,
                    }
                )
                return

            if is_laser:
                # Laser Beam visual (Red, thinner)
                self.particles.append(
                    {
                        "type": "laser",
                        "start": (C.SCREEN_WIDTH - 200, C.SCREEN_HEIGHT - 180),
                        "end": (C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2),
                        "color": (255, 0, 0),
                        "timer": 5,
                        "width": 3,
                    }
                )
                # Fall through to damage logic

            if closest_bot:
                # Calculate hit position for blood

                # Display calculated damage (includes headshot multiplier)
                # Apply calculated factors
                # Recalculate range/accuracy factor for THE closest bot
                # (Ideally we stored this loop above, but re-calc is cheap)

                # ... Wait, I can't access locals from loop above easily unless I stored them.
                # Simplified approach: Use basic factors here since we have closest_bot
                # and closest_dist

                range_factor = max(
                    0.3, 1.0 - (closest_dist / weapon_range)
                )  # Damage drops with range

                # Centeredness
                dx = closest_bot.x - self.player.x
                dy = closest_bot.y - self.player.y
                bot_angle = math.atan2(dy, dx)
                bot_angle_norm = bot_angle if bot_angle >= 0 else bot_angle + 2 * math.pi
                # Use original player angle for center calculation (spread applied to hit check,
                # but damage based on true accuracy usually feels fair...
                # Actually user said "aiming randomness", so spread determines IF you hit.
                # "centeredness of contact" implies how close to center of crosshair.

                angle_diff = abs(bot_angle_norm - self.player.angle)
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff

                accuracy_factor = max(0.5, 1.0 - (angle_diff / 0.15))

                final_damage = int(weapon_damage * range_factor * accuracy_factor)

                if is_headshot:
                    pass  # Damage handled in take_damage

                closest_bot.take_damage(final_damage, is_headshot=is_headshot)
                # Scream handled in kill check below

                damage_dealt = final_damage  # Update for text

                # Spawn damage text
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

                # Random Blood Splatter (Screen)
                for _ in range(5):
                    self.particles.append(
                        {
                            "x": C.SCREEN_WIDTH // 2,
                            "y": C.SCREEN_HEIGHT // 2,
                            "dx": random.uniform(-5, 5),
                            "dy": random.uniform(-5, 5),
                            "color": (
                                random.randint(0, 255),
                                random.randint(0, 255),
                                random.randint(0, 255),
                            ),
                            "timer": 30,
                            "size": random.randint(2, 6),
                        }
                    )

                # Spawn Blue Blood
                for _ in range(10):
                    self.particles.append(
                        {
                            "x": C.SCREEN_WIDTH // 2,
                            "y": C.SCREEN_HEIGHT // 2,
                            "dx": random.uniform(-5, 5),
                            "dy": random.uniform(-5, 5),
                            "color": C.BLUE_BLOOD,
                            "timer": C.PARTICLE_LIFETIME,
                            "size": random.randint(2, 5),
                        }
                    )

                if not closest_bot.alive:
                    self.kills += 1
                    self.kill_combo_count += 1
                    self.kill_combo_timer = 180
                    self.last_death_pos = (closest_bot.x, closest_bot.y)
                    self.sound_manager.play_sound("scream")

        except Exception as e:  # noqa: BLE001
            # Prevent gameplay crash from targeting logic
            print(f"Error in check_shot_hit: {e}")

    def handle_bomb_explosion(self) -> None:
        """Handle bomb explosion logic"""
        assert self.player is not None
        # Visuals
        # 1. Big Flash
        self.particles.append(
            {
                "x": C.SCREEN_WIDTH // 2,
                "y": C.SCREEN_HEIGHT // 2,
                "dx": 0,
                "dy": 0,
                "color": C.WHITE,
                "timer": 40,  # longer flash
                "size": 3000,  # huge
            }
        )
        # 2. Fireball Particles (Michael Bay style - More, Faster, Chaos)
        for _ in range(300):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(5, 25)
            color = random.choice([C.ORANGE, C.RED, C.YELLOW, C.DARK_RED, (50, 50, 50)])
            self.particles.append(
                {
                    "x": C.SCREEN_WIDTH // 2,
                    "y": C.SCREEN_HEIGHT // 2,
                    "dx": math.cos(angle) * speed,
                    "dy": math.sin(angle) * speed,
                    "color": color,
                    "timer": random.randint(40, 100),
                    "size": random.randint(5, 25),
                }
            )

        # Damage enemies
        for bot in self.bots:
            if not bot.alive:
                continue
            dist = math.sqrt((bot.x - self.player.x) ** 2 + (bot.y - self.player.y) ** 2)
            if dist < C.BOMB_RADIUS:
                was_alive = bot.alive
                bot.take_damage(1000)  # massive damage
                if was_alive and not bot.alive:
                    self.sound_manager.play_sound("scream")  # type: ignore[unreachable]
                    self.kills += 1
                    self.kill_combo_count += 1
                    self.kill_combo_timer = 180
                    self.last_death_pos = (bot.x, bot.y)

                # Blood (if close)
                if dist < 5.0:
                    for _ in range(3):
                        self.particles.append(
                            {
                                "x": C.SCREEN_WIDTH // 2,
                                "y": C.SCREEN_HEIGHT // 2,
                                "dx": random.uniform(-4, 4),
                                "dy": random.uniform(-4, 4),
                                "color": (
                                    random.randint(0, 255),
                                    random.randint(0, 255),
                                    random.randint(0, 255),
                                ),
                                "timer": 20,
                                "size": 3,
                            }
                        )

        # Screen shake or feedback
        try:
            self.sound_manager.play_sound("bomb")
        except BaseException as e:  # noqa: BLE001
            print(f"Bomb Audio Failed: {e}")

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
        except Exception as e:  # noqa: BLE001
            print(f"Boom sound failed: {e}")

        try:
            # Huge AOE
            hits = 0
            for bot in self.bots:
                # Basic check
                if not hasattr(bot, "alive"):
                    continue

                if bot.alive:
                    dist = math.sqrt((bot.x - impact_x) ** 2 + (bot.y - impact_y) ** 2)
                    if dist < C.LASER_AOE_RADIUS:
                        damage = 500
                        was_alive = bot.alive
                        bot.take_damage(damage)
                        hits += 1

                        if was_alive and not bot.alive:
                            with contextlib.suppress(Exception):  # type: ignore[unreachable]
                                self.sound_manager.play_sound("scream")
                            self.kills += 1
                            self.kill_combo_count += 1
                            self.kill_combo_timer = 180
                            self.last_death_pos = (bot.x, bot.y)

                        # Massive Blood
                        for _ in range(10):
                            self.particles.append(
                                {
                                    "x": C.SCREEN_WIDTH // 2,
                                    "y": C.SCREEN_HEIGHT // 2,
                                    "dx": random.uniform(-10, 10),
                                    "dy": random.uniform(-10, 10),
                                    "color": (
                                        random.randint(200, 255),
                                        0,
                                        random.randint(200, 255),
                                    ),
                                    "timer": 40,
                                    "size": random.randint(4, 8),
                                }
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
        except Exception as e:  # noqa: BLE001
            print(f"Critical Laser Error: {e}")
            traceback.print_exc()

    def explode_plasma(self, projectile: Projectile) -> None:
        """Trigger plasma AOE explosion"""
        assert self.player is not None
        # Visuals - Shockwave / Expanding Circle
        # Visuals - Screen Flash
        dist_to_player = math.sqrt(
            (projectile.x - self.player.x) ** 2 + (projectile.y - self.player.y) ** 2
        )
        if dist_to_player < 15:
            self.damage_flash_timer = 15  # Re-use flash timer for feedback

        # Damage Logic - Flat Wave
        for bot in self.bots:
            if not bot.alive:
                continue
            dx = bot.x - projectile.x
            dy = bot.y - projectile.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < C.PLASMA_AOE_RADIUS:
                was_alive = bot.alive
                bot.take_damage(projectile.damage)
                if was_alive and not bot.alive:
                    self.sound_manager.play_sound("scream")  # type: ignore[unreachable]
                    self.kills += 1
                    self.kill_combo_count += 1
                    self.kill_combo_timer = 180
                    self.last_death_pos = (bot.x, bot.y)

                # Blood
                if dist < 5.0:
                    for _ in range(3):
                        self.particles.append(
                            {
                                "x": C.SCREEN_WIDTH // 2,
                                "y": C.SCREEN_HEIGHT // 2,
                                "dx": random.uniform(-4, 4),
                                "dy": random.uniform(-4, 4),
                                "color": (
                                    random.randint(0, 255),
                                    random.randint(0, 255),
                                    random.randint(0, 255),
                                ),
                                "timer": 20,
                                "size": 3,
                            }
                        )

    def update_game(self) -> None:
        """Update game state"""
        if self.paused:
            # Simple pause menu handling could go here
            return

        assert self.player is not None
        if not self.player.alive:
            # Check Lives
            if self.lives > 1:
                self.lives -= 1
                self.respawn_player()
                return
            # Capture final time for the failed level
            level_time = (
                pygame.time.get_ticks() - self.level_start_time - self.total_paused_time
            ) / 1000.0
            self.level_times.append(level_time)
            self.lives = 0  # Ensure 0

            self.state = "game_over"
            self.game_over_timer = 0
            self.sound_manager.play_sound("game_over1")
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
            return

        # Check for enemies remaining (exclude health packs)
        # Check for enemies remaining (exclude items)
        enemies_alive = [
            b for b in self.bots if b.alive and b.type_data.get("visual_style") != "item"
        ]

        if not enemies_alive:
            if self.portal is None:
                # Spawn Portal - Ensure it's reachable
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
            # Check collision
            dist = math.sqrt(
                (self.portal["x"] - self.player.x) ** 2 + (self.portal["y"] - self.player.y) ** 2
            )
            if dist < 1.5:
                # Level Complete
                level_time = (
                    pygame.time.get_ticks() - self.level_start_time - self.total_paused_time
                ) / 1000.0
                self.level_times.append(level_time)
                self.state = "level_complete"
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)
                return

        assert self.player is not None
        assert self.game_map is not None
        keys = pygame.key.get_pressed()

        # Shield Logic
        shield_active = keys[pygame.K_SPACE]

        # Controller Input (Continuous)
        if self.joystick and not self.paused and self.player and self.player.alive:
            # Left Stick (0, 1) - Move/Strafe
            axis_x = self.joystick.get_axis(0)
            axis_y = self.joystick.get_axis(1)

            if abs(axis_x) > C.JOYSTICK_DEADZONE:
                self.player.strafe(
                    self.game_map, self.bots, right=(axis_x > 0), speed=abs(axis_x) * C.PLAYER_SPEED
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

            # Right Stick
            look_x = 0.0
            look_y = 0.0
            if self.joystick.get_numaxes() >= 4:
                look_x = self.joystick.get_axis(2)
                look_y = self.joystick.get_axis(3)

            if abs(look_x) > C.JOYSTICK_DEADZONE:
                self.player.rotate(look_x * C.PLAYER_ROT_SPEED * 15 * C.SENSITIVITY_X)
            if abs(look_y) > C.JOYSTICK_DEADZONE:
                self.player.pitch_view(-look_y * 10 * C.SENSITIVITY_Y)

            # Buttons
            # 0: A (Shield)
            if self.joystick.get_numbuttons() > 0 and self.joystick.get_button(0):
                shield_active = True

            # 2: X (Reload)
            if self.joystick.get_numbuttons() > 2 and self.joystick.get_button(2):
                self.player.reload()

            # Triggers or Shoulders for Fire
            # 5: RB (Fire)
            if self.joystick.get_numbuttons() > 5 and self.joystick.get_button(5):
                if self.player.shoot():
                    self.fire_weapon()

            # Secondary Fire (LB)
            if self.joystick.get_numbuttons() > 4 and self.joystick.get_button(4):
                if self.player.fire_secondary():
                    self.fire_weapon(is_secondary=True)

            # Hat for Weapon Switch
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

        # Particles update
        for p in self.particles[:]:
            if "dx" in p and "dy" in p:
                p["x"] += p["dx"]
                p["y"] += p["dy"]
            p["timer"] -= 1
            if p["timer"] <= 0:
                self.particles.remove(p)

        # Damage text update
        for t in self.damage_texts[:]:
            t["y"] += t["vy"]
            t["timer"] -= 1
            if t["timer"] <= 0:
                self.damage_texts.remove(t)

        is_sprinting = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        current_speed = C.PLAYER_SPRINT_SPEED if is_sprinting else C.PLAYER_SPEED

        # Track movement for bobbing
        moving = False

        # Movement (move method checks for shield)
        if keys[pygame.K_w]:
            self.player.move(self.game_map, self.bots, forward=True, speed=current_speed)
            moving = True
        if keys[pygame.K_s]:
            self.player.move(self.game_map, self.bots, forward=False, speed=current_speed)
            moving = True
        if keys[pygame.K_a]:
            self.player.strafe(self.game_map, self.bots, right=False, speed=current_speed)
            moving = True
        if keys[pygame.K_d]:
            self.player.strafe(self.game_map, self.bots, right=True, speed=current_speed)

        self.player.is_moving = moving

        if keys[pygame.K_LEFT]:
            self.player.rotate(-0.05)
        if keys[pygame.K_RIGHT]:
            self.player.rotate(0.05)

        self.player.update()

        # Update Projectiles and Enemy Shooting (Merged from duplicate method)
        for bot in self.bots:
            projectile = bot.update(self.game_map, self.player, self.bots)
            if projectile:
                self.projectiles.append(projectile)
                self.sound_manager.play_sound("enemy_shoot")

            # Item Pickup Logic
            if bot.alive and bot.enemy_type.startswith(("health", "ammo", "bomb", "pickup")):
                dist = math.sqrt((bot.x - self.player.x) ** 2 + (bot.y - self.player.y) ** 2)
                if dist < 0.8:
                    pickup_msg = ""
                    color = C.GREEN

                    if bot.enemy_type == "health_pack":
                        if self.player.health < 100:
                            self.player.health = min(100, self.player.health + 50)
                            pickup_msg = "HEALTH +50"
                    elif bot.enemy_type == "ammo_box":
                        # Give ammo for current or all? Give all.
                        for w in self.player.ammo:
                            self.player.ammo[w] += 20  # Arbitrary amount
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
                            self.player.switch_weapon(w_name)  # Auto switch to new gun
                            pickup_msg = f"{w_name.upper()} ACQUIRED!"
                            color = C.CYAN
                        else:
                            # Just ammo
                            clip_size = int(cast(int, C.WEAPONS[w_name]["clip_size"]))
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

        assert self.game_map is not None
        assert self.player is not None
        for projectile in self.projectiles[:]:

            was_alive = projectile.alive
            projectile.update(self.game_map)

            # Check Wall Hit (projectile dies in update)
            if (
                was_alive
                and not projectile.alive
                and getattr(projectile, "weapon_type", "normal") == "plasma"
            ):
                self.explode_plasma(projectile)

            if projectile.alive:
                if not projectile.is_player:
                    dx = projectile.x - self.player.x
                    dy = projectile.y - self.player.y
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist < 0.5:
                        old_health = self.player.health
                        if not self.god_mode:
                            self.player.take_damage(projectile.damage)

                        if self.player.health < old_health:
                            # Hit flash
                            self.damage_flash_timer = 10
                            self.sound_manager.play_sound("oww")

                        projectile.alive = False
                else:
                    # Player Projectile hitting Bots
                    for bot in self.bots:
                        if not bot.alive:
                            continue
                        dx = projectile.x - bot.x
                        dy = projectile.y - bot.y
                        dist = math.sqrt(dx**2 + dy**2)
                        if dist < 0.8:  # Hit radius
                            was_alive = bot.alive
                            bot.take_damage(projectile.damage)
                            if was_alive and not bot.alive:
                                self.sound_manager.play_sound("scream")  # type: ignore[unreachable]
                                self.kills += 1
                                self.kill_combo_count += 1
                                self.kill_combo_timer = 180  # 3 seconds window
                                self.last_death_pos = (bot.x, bot.y)

                            # Blood
                            for _ in range(5):
                                self.particles.append(
                                    {
                                        "x": C.SCREEN_WIDTH // 2,
                                        "y": C.SCREEN_HEIGHT // 2,
                                        "dx": random.uniform(-5, 5),
                                        "dy": random.uniform(-5, 5),
                                        "color": (
                                            random.randint(0, 255),
                                            random.randint(0, 255),
                                            random.randint(0, 255),
                                        ),
                                        "timer": 25,
                                        "size": random.randint(2, 5),
                                    }
                                )

                            # Visual
                            projectile.alive = False

                            # Trigger AOE if Plasma
                            if getattr(projectile, "weapon_type", "normal") == "plasma":
                                self.explode_plasma(projectile)
                            break

        # Remove dead projectiles after processing all
        self.projectiles = [p for p in self.projectiles if p.alive]

        # Fog of War Update
        cx, cy = int(self.player.x), int(self.player.y)
        reveal_radius = 5
        for r_i in range(-reveal_radius, reveal_radius + 1):
            for r_j in range(-reveal_radius, reveal_radius + 1):
                if r_i * r_i + r_j * r_j <= reveal_radius * reveal_radius:
                    self.visited_cells.add((cx + r_j, cy + r_i))

        # Heartbeat Logic
        # Find nearest enemy
        min_dist = float("inf")
        for bot in self.bots:
            if bot.alive:  # Only alive bots trigger heartbeat
                dist = math.sqrt((bot.x - self.player.x) ** 2 + (bot.y - self.player.y) ** 2)
                min_dist = min(min_dist, dist)

        # Periodic Monster Roars
        if min_dist < 15:
            self.beast_timer -= 1
            if self.beast_timer <= 0:
                self.sound_manager.play_sound("beast")
                self.beast_timer = random.randint(300, 900)  # 5-15 seconds

        # Beat frequency based on distance
        # e.g. 5 tiles = fast (0.5s), 20 tiles = slow (1.5s)
        if min_dist < 20:
            beat_delay = int(min(1.5, max(0.4, min_dist / 10.0)) * C.FPS)
            self.heartbeat_timer -= 1
            if self.heartbeat_timer <= 0:
                self.sound_manager.play_sound("heartbeat")
                # Trigger breath slightly offset or same time?
                # User said "speed ... mirror heartrate".
                self.sound_manager.play_sound("breath")
                self.heartbeat_timer = beat_delay

        # Low Health Groans
        if self.player.health < 50:
            self.groan_timer -= 1
            if self.groan_timer <= 0:
                self.sound_manager.play_sound("groan")
                self.groan_timer = 240  # 4 seconds

        # Combo system / Catchphrases check
        if self.kill_combo_timer > 0:
            self.kill_combo_timer -= 1
            if self.kill_combo_timer <= 0:
                # Combo ended
                if self.kill_combo_count >= 3:
                    phrase = random.choice(["phrase_cool", "phrase_awesome", "phrase_brutal"])
                    self.sound_manager.play_sound(phrase)
                    # Text popup
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

    def update_blood_drips(self, rect: pygame.Rect) -> None:
        """Spawn and update blood drips interacting with text rect"""
        # Spawn
        if random.random() < 0.3:  # 30% chance per frame
            x = random.randint(rect.left, rect.right)
            # Bias slightly towards centers of letters? Random is fine for now.
            self.title_drips.append(
                {
                    "x": x,
                    "y": rect.top,  # Start at top
                    "start_y": rect.top,
                    "speed": random.uniform(0.5, 2.0),
                    "size": random.randint(2, 4),
                    "color": (random.randint(180, 255), 0, 0),
                }
            )

        # Update
        for drip in self.title_drips[:]:
            drip["y"] += drip["speed"]
            # Accelerate slightly
            drip["speed"] *= 1.02

            # Allow to go further down
            if drip["y"] > C.SCREEN_HEIGHT:
                self.title_drips.remove(drip)

    def draw_blood_drips(self) -> None:
        """Draw the blood drips"""
        for drip in self.title_drips:
            # Draw trail
            pygame.draw.line(
                self.screen,
                drip["color"],
                (drip["x"], drip["start_y"]),
                (drip["x"], drip["y"]),
                drip["size"],
            )
            # Draw droplet at bottom
            pygame.draw.circle(
                self.screen, drip["color"], (drip["x"], int(drip["y"])), drip["size"] + 1
            )

    def render_menu(self) -> None:
        """Render main menu (Title Screen)"""
        # (Video overlay logic handled elsewhere if needed)

        self.screen.fill(C.BLACK)

        # Menu Title
        # "Force Field The Arena Awaits"
        title = self.title_font.render("FORCE FIELD", True, C.RED)
        title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 100))

        sub = self.subtitle_font.render("THE ARENA AWAITS", True, C.WHITE)
        sub_rect = sub.get_rect(center=(C.SCREEN_WIDTH // 2, 160))

        self.screen.blit(title, title_rect)
        self.screen.blit(sub, sub_rect)

        # Blood Drips (Persistant)
        self.update_blood_drips(title_rect)
        self.draw_blood_drips()

        # "Press Start" style prompt
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            prompt = self.font.render("CLICK TO BEGIN", True, C.GRAY)
            prompt_rect = prompt.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 150))
            self.screen.blit(prompt, prompt_rect)

        credit = self.tiny_font.render("A Jasper Production", True, C.DARK_GRAY)
        credit_rect = credit.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 50))
        self.screen.blit(credit, credit_rect)
        pygame.display.flip()

    def render_map_select(self) -> None:
        """Render map select / mission setup screen"""
        self.screen.fill(C.BLACK)

        # Title - Stylized like "From the Demented Mind" (Georgia/Distorted vibe)
        # Using subtitle_font which is Georgia
        title = self.subtitle_font.render("MISSION SETUP", True, C.RED)

        # Add basic distortion/glow effect manual
        # Draw offsets
        for off in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            shadow = self.subtitle_font.render("MISSION SETUP", True, (50, 0, 0))
            s_rect = shadow.get_rect(center=(C.SCREEN_WIDTH // 2 + off[0], 100 + off[1]))
            self.screen.blit(shadow, s_rect)

        title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        mouse_pos = pygame.mouse.get_pos()
        start_y = 200
        line_height = 80  # Matches event handler spacing

        settings = [
            ("Map Size", str(self.selected_map_size)),
            ("Difficulty", self.selected_difficulty),
            ("Start Level", str(self.selected_start_level)),
            ("Lives", str(self.selected_lives)),
        ]

        # Draw Settings
        for i, (label, value) in enumerate(settings):
            y = start_y + i * line_height

            # Hover effect
            color = C.WHITE
            if abs(mouse_pos[1] - y) < 20:
                color = C.YELLOW

            # Use stylized font for items too? Or cleaner font for readability.
            # User said "Mission Setup screen... use same type of font".
            # I will use subtitle_font (Georgia) for labels too.
            label_surf = self.subtitle_font.render(f"{label}:", True, C.GRAY)
            label_rect = label_surf.get_rect(right=C.SCREEN_WIDTH // 2 - 20, centery=y)

            val_surf = self.subtitle_font.render(value, True, color)
            val_rect = val_surf.get_rect(left=C.SCREEN_WIDTH // 2 + 20, centery=y)

            self.screen.blit(label_surf, label_rect)
            self.screen.blit(val_surf, val_rect)

        # Draw Start Button
        # It's a standard button now (no blood)
        self.start_button.draw(self.screen, self.font)

        instructions = [
            "",
            "",
            "WASD: Move | Shift: Sprint | Mouse: Look | 1-4: Weapons",
            "Click: Shoot | Z: Zoom | F: Bomb | Space: Shield",
        ]

        y = C.SCREEN_HEIGHT - 260  # Moved up to avoid overlap with button
        for line in instructions:
            text = self.tiny_font.render(line, True, C.RED)
            text_rect = text.get_rect(center=(C.SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 30

        pygame.display.flip()

    def render_game(self) -> None:
        """Render gameplay"""
        assert self.raycaster is not None
        assert self.player is not None

        # Pass player object for angle and pitch
        self.raycaster.render_floor_ceiling(self.screen, self.player, self.level)
        self.raycaster.render_3d(self.screen, self.player, self.bots, self.level)

        # Render projectiles via raycaster
        self.raycaster.render_projectiles(self.screen, self.player, self.projectiles)

        # Mist removed based on feedback

        # Clear effects surface
        self.effects_surface.fill((0, 0, 0, 0))

        # Render Lasers (Secondary Fire)
        for p in self.particles:
            if p.get("type") == "laser":
                alpha = int(255 * (p["timer"] / C.LASER_DURATION))
                start = p["start"]
                end = p["end"]
                color = (*p["color"], alpha)
                # Draw on shared surface
                pygame.draw.line(self.effects_surface, color, start, end, p["width"])
                pygame.draw.line(self.effects_surface, color, start, end, p["width"])
                # Horizontal spread visualization removed

                # Draw main beam
                pygame.draw.line(self.effects_surface, color, start, end, p["width"])

                # Draw horizontal spread lines (Fanning out)
                for i in range(5):
                    offset = (i - 2) * 20  # Scatter horizontally at target
                    target_end = (end[0] + offset, end[1])
                    pygame.draw.line(
                        self.effects_surface,
                        (*p["color"], max(0, alpha - 50)),
                        start,
                        target_end,
                        max(1, p["width"] // 2),
                    )

                # Glow
                pygame.draw.line(
                    self.effects_surface, (*p["color"], alpha // 2), start, end, p["width"] * 3
                )

            elif "dx" in p:  # Normal particles
                # Draw directly to screen usually faster for small circles?
                # Or use effects surface for alpha
                ratio = p["timer"] / C.PARTICLE_LIFETIME
                alpha = int(255 * ratio)
                alpha = max(0, min(255, alpha))

                try:
                    color = p["color"]
                    rgba = (*color, alpha) if len(color) == 3 else (*color[:3], alpha)

                    pygame.draw.circle(
                        self.effects_surface,
                        rgba,
                        (int(p["x"]), int(p["y"])),
                        int(p["size"]),
                    )
                except (ValueError, TypeError):
                    continue  # Skip invalid particles

        # Damage Flash
        if self.damage_flash_timer > 0:
            alpha = int(100 * (self.damage_flash_timer / 10.0))
            self.effects_surface.fill((255, 0, 0, alpha), special_flags=pygame.BLEND_RGBA_ADD)
            self.damage_flash_timer -= 1

        # Shield effect (Draw onto effects surface)
        if self.player.shield_active:
            self.effects_surface.fill(
                (*C.SHIELD_COLOR, C.SHIELD_ALPHA), special_flags=pygame.BLEND_RGBA_ADD
            )  # Additive or just fill?
            # Simple fill with alpha works if surface is alpha.
            # Actually, filling whole surface checks previous pixels?
            # Just draw a rect.
            pygame.draw.rect(
                self.effects_surface,
                (*C.SHIELD_COLOR, C.SHIELD_ALPHA),
                (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT),
            )
            pygame.draw.rect(
                self.effects_surface, C.SHIELD_COLOR, (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT), 10
            )

            shield_text = self.title_font.render("SHIELD ACTIVE", True, C.SHIELD_COLOR)
            self.screen.blit(shield_text, (C.SCREEN_WIDTH // 2 - shield_text.get_width() // 2, 100))

            # Timer bar or text
            time_left = self.player.shield_timer / 60.0
            timer_text = self.small_font.render(f"{time_left:.1f}s", True, C.WHITE)
            self.screen.blit(timer_text, (C.SCREEN_WIDTH // 2 - timer_text.get_width() // 2, 160))

            # Flash if running out
            if self.player.shield_timer < 120 and (self.player.shield_timer // 10) % 2 == 0:
                pygame.draw.rect(
                    self.effects_surface, (255, 0, 0, 50), (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT)
                )

        # Show "Shield Ready" if full
        elif (
            self.player.shield_timer == C.SHIELD_MAX_DURATION
            and self.player.shield_recharge_delay <= 0
        ):
            ready_text = self.tiny_font.render("SHIELD READY", True, C.CYAN)
            self.screen.blit(ready_text, (20, C.SCREEN_HEIGHT - 120))

        # Blit all effects once
        self.screen.blit(self.effects_surface, (0, 0))

        self.render_crosshair()

        if self.player.shooting:
            self.render_muzzle_flash()

        # Secondary Charge UI
        charge_pct = 1.0 - (self.player.secondary_cooldown / C.SECONDARY_COOLDOWN)
        if charge_pct < 1.0:
            # Draw small reload bar near reticle
            bar_w = 40
            bar_h = 4
            cx, cy = C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 30
            pygame.draw.rect(self.screen, C.DARK_GRAY, (cx - bar_w // 2, cy, bar_w, bar_h))
            pygame.draw.rect(
                self.screen, C.CYAN, (cx - bar_w // 2, cy, int(bar_w * charge_pct), bar_h)
            )
        # Render Projectiles (Billboarding)
        # Actually standard Z-buffer is in raycaster,
        # but we don't have access to Z-buffer here easily.
        # We'll just draw them. If they are behind walls, we should check wall distance?
        # Raycaster.render doesn't expose Z-buffer.
        # Ideally projectiles are drawn INSIDE raycaster loop.
        # But retro style commonly draws sprites after walls (with Z-check if possible).
        # We'll just draw them and accept they might clip, or we check if visible before drawing.
        # Check simple line of sight?
        # Let's just draw them for now.
        assert self.player is not None
        for proj in self.projectiles:
            sx = proj.x - self.player.x
            sy = proj.y - self.player.y

            cs = math.cos(self.player.angle)
            sn = math.sin(self.player.angle)
            a = sy * cs - sx * sn
            b = sx * cs + sy * sn

            if b > 0.1:
                screen_x = int((0.5 * C.SCREEN_WIDTH) * (1 + a / b * 1.73))
                screen_y = C.SCREEN_HEIGHT // 2

                scale = C.SCREEN_HEIGHT / b
                size = int(scale * proj.size)

                if 0 < screen_x < C.SCREEN_WIDTH:
                    # Draw projectile
                    color = getattr(proj, "color", (255, 0, 0))  # default red
                    if proj.is_player:
                        pygame.draw.circle(self.screen, color, (screen_x, screen_y), max(2, size))
                        # Glow
                        s = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
                        pygame.draw.circle(s, (*color, 100), (size * 2, size * 2), size * 2)
                        self.screen.blit(s, (screen_x - size * 2, screen_y - size * 2))
                    else:
                        # Enemy projectile
                        pygame.draw.circle(self.screen, color, (screen_x, screen_y), max(2, size))

        # Render Portal (Projected)
        if self.portal:
            # Simple billboard projection for portal
            # Calculate sprite position relative to player
            sx = self.portal["x"] - self.player.x
            sy = self.portal["y"] - self.player.y

            # Rotate
            cs = math.cos(self.player.angle)
            sn = math.sin(self.player.angle)
            a = sy * cs - sx * sn
            b = sx * cs + sy * sn

            # Draw if in front
            if b > 0.1:
                # Projection
                screen_x = int((0.5 * C.SCREEN_WIDTH) * (1 + a / b * 2.0))  # projection
                screen_y = C.SCREEN_HEIGHT // 2

                size = int(800 / b)  # Scale size

                # Draw Portal Circle
                if -size < screen_x < C.SCREEN_WIDTH + size:
                    color = (0, 255, 255)
                    # Pulse alpha
                    alpha = 150 + int(50 * math.sin(pygame.time.get_ticks() * 0.01))

                    # Draw multiple rings
                    pygame.draw.circle(
                        self.screen, (*color, alpha), (screen_x, screen_y), size // 2
                    )
                    pygame.draw.circle(
                        self.screen, (255, 255, 255), (screen_x, screen_y), size // 4
                    )

        self.render_weapon()
        self.render_hud()

        if self.paused:
            overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))

            menu_items = ["RESUME", "SAVE GAME", "QUIT TO MENU"]
            mouse_pos = pygame.mouse.get_pos()

            for i, item in enumerate(menu_items):
                color = C.WHITE
                rect = pygame.Rect(
                    C.SCREEN_WIDTH // 2 - 100, C.SCREEN_HEIGHT // 2 - 50 + i * 60, 200, 50
                )

                if rect.collidepoint(mouse_pos):
                    color = C.YELLOW

                text = self.font.render(item, True, color)
                self.screen.blit(text, (C.SCREEN_WIDTH // 2 - text.get_width() // 2, rect.y + 10))

        pygame.display.flip()

    def render_weapon(self) -> None:
        """Render current weapon in FPS view (Centered) with high fidelity"""
        assert self.player is not None
        weapon = self.player.current_weapon
        cx = C.SCREEN_WIDTH // 2
        cy = C.SCREEN_HEIGHT

        # Bobbing effect
        bob_y = 0
        if self.player.is_moving:
            bob_y = int(math.sin(pygame.time.get_ticks() * 0.012) * 15)

        # Reload Animation (Dip)
        w_state = self.player.weapon_state[weapon]
        if w_state["reloading"]:
            w_data = C.WEAPONS.get(weapon, {})
            reload_max = w_data.get("reload_time", 60)
            if isinstance(reload_max, int) and reload_max > 0:
                pct = w_state["reload_timer"] / reload_max  # 1.0 to 0.0
                # Dip down and up. Peak at 0.5
                dip = math.sin(pct * math.pi) * 150
                cy += int(dip)

        cy += bob_y

        # Helper colors
        gun_metal = (40, 45, 50)
        gun_highlight = (70, 75, 80)
        gun_dark = (20, 25, 30)

        if weapon == "pistol":
            # High-Res Heavy Pistol (Deagle-ish)

            # 1. Grip (Darker)
            pygame.draw.polygon(
                self.screen,
                (30, 25, 20),
                [(cx - 30, cy), (cx + 30, cy), (cx + 35, cy - 100), (cx - 35, cy - 100)],
            )

            # 2. Main Body / Frame
            pygame.draw.rect(self.screen, gun_metal, (cx - 20, cy - 140, 40, 140))

            # 3. Slide (Lighter, detailed)
            slide_y = cy - 180
            # Recoil recoil (if shooting, slide moves back)
            if self.player.shooting:
                slide_y += 20

            pygame.draw.polygon(
                self.screen,
                gun_highlight,
                [
                    (cx - 25, slide_y),
                    (cx + 25, slide_y),
                    (cx + 25, slide_y + 120),
                    (cx - 25, slide_y + 120),
                ],
            )
            # Slide serrations
            for i in range(5):
                y_ser = slide_y + 80 + i * 8
                pygame.draw.line(self.screen, gun_dark, (cx - 20, y_ser), (cx + 20, y_ser), 2)

            # 4. Barrel Tip
            pygame.draw.rect(self.screen, (10, 10, 10), (cx - 8, slide_y - 5, 16, 10))

            # 5. Sights
            pygame.draw.rect(self.screen, (10, 10, 10), (cx - 20, slide_y - 12, 5, 12))  # Rear
            pygame.draw.rect(self.screen, (10, 10, 10), (cx + 15, slide_y - 12, 5, 12))  # Rear R
            pygame.draw.rect(self.screen, C.RED, (cx - 2, slide_y - 8, 4, 8))  # Front glowing dot

        elif weapon == "shotgun":
            # Double Barrel Sawed-off

            # Barrels (Side by Side)
            # Left Barrel
            pygame.draw.circle(self.screen, (20, 20, 20), (cx - 30, cy - 180), 22)
            pygame.draw.rect(self.screen, gun_metal, (cx - 52, cy - 180, 44, 200))
            pygame.draw.rect(self.screen, (10, 10, 10), (cx - 48, cy - 200, 36, 100))  # Hollow tone

            # Right Barrel
            pygame.draw.circle(self.screen, (20, 20, 20), (cx + 30, cy - 180), 22)
            pygame.draw.rect(self.screen, gun_metal, (cx + 8, cy - 180, 44, 200))
            pygame.draw.rect(self.screen, (10, 10, 10), (cx + 12, cy - 200, 36, 100))

            # Rib between barrels
            pygame.draw.rect(self.screen, gun_dark, (cx - 8, cy - 180, 16, 180))

            # Wooden Foregrip
            pygame.draw.polygon(
                self.screen,
                (100, 60, 20),
                [(cx - 60, cy - 50), (cx + 60, cy - 50), (cx + 50, cy), (cx - 50, cy)],
            )

            # Shell ejection feedback?

        elif weapon == "rifle":
            # Heavy Assault Rifle with Optic

            # Magazine
            pygame.draw.rect(self.screen, (20, 20, 20), (cx - 40, cy - 80, 30, 80))

            # Main Body
            pygame.draw.polygon(
                self.screen,
                gun_metal,
                [(cx - 30, cy - 150), (cx + 30, cy - 150), (cx + 40, cy), (cx - 40, cy)],
            )

            # Barrel Shroud
            pygame.draw.rect(self.screen, gun_highlight, (cx - 20, cy - 220, 40, 100))
            # Vents in shroud
            for i in range(6):
                y_vent = cy - 210 + i * 15
                pygame.draw.ellipse(self.screen, (10, 10, 10), (cx - 10, y_vent, 20, 8))

            # Barrel
            pygame.draw.rect(self.screen, (10, 10, 10), (cx - 5, cy - 240, 10, 40))

            # Optic
            pygame.draw.rect(self.screen, (10, 10, 10), (cx - 5, cy - 160, 10, 40))  # Mount
            pygame.draw.circle(self.screen, (30, 30, 30), (cx, cy - 170), 30)  # Scope body
            # Lens reflection
            pygame.draw.circle(self.screen, (0, 100, 0), (cx, cy - 170), 25)  # Dark green lens
            pygame.draw.circle(self.screen, (150, 255, 150), (cx - 10, cy - 180), 8)  # Glint
            # Crosshair inside scope (if zoomed)
            if self.player.zoomed:
                pygame.draw.line(self.screen, C.RED, (cx - 25, cy - 170), (cx + 25, cy - 170), 1)
                pygame.draw.line(self.screen, C.RED, (cx, cy - 195), (cx, cy - 145), 1)

        elif weapon == "plasma":
            # Sci-Fi BFG Style - High Tech

            # Rear Stock/Bulk
            pygame.draw.polygon(
                self.screen,
                (40, 40, 60),
                [(cx - 100, cy), (cx + 100, cy), (cx + 90, cy - 80), (cx - 90, cy - 80)],
            )

            # Main Barrel Housing
            pygame.draw.polygon(
                self.screen,
                (60, 60, 90),
                [(cx - 70, cy - 80), (cx + 70, cy - 80), (cx + 50, cy - 250), (cx - 50, cy - 250)],
            )

            # Side Vents (Glowing)
            pulse = int(25 * math.sin(pygame.time.get_ticks() * 0.01))
            vent_color = (
                (0, 150 + pulse, 200) if not w_state["overheated"] else (200 + pulse, 50, 0)
            )

            pygame.draw.rect(self.screen, vent_color, (cx - 90, cy - 150, 20, 100))
            pygame.draw.rect(self.screen, vent_color, (cx + 70, cy - 150, 20, 100))

            # Central Core (Exposed)
            core_width = 40 + pulse // 2
            pygame.draw.rect(
                self.screen,
                (20, 20, 30),
                (cx - 30, cy - 180, 60, 140),
            )  # Chamber background
            pygame.draw.rect(
                self.screen,
                vent_color,
                (cx - core_width // 2, cy - 190, core_width, 120),
                border_radius=10,
            )

            # Floating Rings / Coils
            for i in range(5):
                y_coil = cy - 230 + i * 35
                width_coil = 80 - i * 5
                pygame.draw.rect(
                    self.screen,
                    (30, 30, 40),
                    (cx - width_coil // 2, y_coil, width_coil, 15),
                    border_radius=4,
                )

            # Charging arcs (Lightning)
            if self.player.shooting:
                for _ in range(3):
                    lx1 = random.randint(cx - 40, cx + 40)
                    ly1 = random.randint(cy - 250, cy - 150)
                    lx2 = random.randint(cx - 40, cx + 40)
                    ly2 = random.randint(cy - 250, cy - 150)
                    pygame.draw.line(self.screen, C.WHITE, (lx1, ly1), (lx2, ly2), 2)

    def render_hud(self) -> None:
        """Render HUD in Doom-style"""
        hud_bottom = C.SCREEN_HEIGHT - 80
        health_width = 150
        health_height = 25
        health_x = 20
        health_y = hud_bottom

        pygame.draw.rect(
            self.screen, C.DARK_GRAY, (health_x, health_y, health_width, health_height)
        )
        assert self.player is not None
        health_percent = max(0, self.player.health / self.player.max_health)
        fill_width = int(health_width * health_percent)
        health_color = (
            C.GREEN if health_percent > 0.5 else (C.ORANGE if health_percent > 0.25 else C.RED)
        )

        pygame.draw.rect(self.screen, health_color, (health_x, health_y, fill_width, health_height))
        # Border
        pygame.draw.rect(self.screen, C.WHITE, (health_x, health_y, health_width, health_height), 2)

        # Ammo / State
        assert self.player is not None
        w_state = self.player.weapon_state[self.player.current_weapon]
        w_name = C.WEAPONS[self.player.current_weapon]["name"]

        # Reloading / Overheat Status
        status_text = ""
        status_color = C.WHITE

        if w_state["reloading"]:
            status_text = "RELOADING..."
            status_color = C.YELLOW
        elif w_state["overheated"]:
            status_text = "OVERHEATED!"
            status_color = C.RED

        if status_text:
            txt = self.small_font.render(status_text, True, status_color)
            tr = txt.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 60))
            self.screen.blit(txt, tr)

            # Heat bar drawing removed

        else:
            # Clip / Ammo + Bomb Count + Inventory
            assert self.player is not None
            ammo_val = self.player.ammo[self.player.current_weapon]
            ammo_text = f"{w_name}: {w_state['clip']} / {ammo_val}"

            # Show Bombs
            bomb_text = f"BOMBS: {self.player.bombs}"

            at = self.font.render(ammo_text, True, C.WHITE)
            bt = self.font.render(bomb_text, True, C.ORANGE)

            at_rect = at.get_rect(bottomright=(C.SCREEN_WIDTH - 20, hud_bottom + 25))
            bt_rect = bt.get_rect(bottomright=(C.SCREEN_WIDTH - 20, hud_bottom - 15))

            self.screen.blit(at, at_rect)
            self.screen.blit(bt, bt_rect)

            # Inventory List
            inv_y = hud_bottom - 80
            for w in ["pistol", "rifle", "shotgun", "laser", "plasma"]:
                color = C.GRAY
                if w in self.unlocked_weapons:
                    color = C.GREEN if w == self.player.current_weapon else C.WHITE

                inv_txt = self.tiny_font.render(
                    f"[{C.WEAPONS[w]['key']}] {C.WEAPONS[w]['name']}", True, color
                )
                inv_rect = inv_txt.get_rect(bottomright=(C.SCREEN_WIDTH - 20, inv_y))
                self.screen.blit(inv_txt, inv_rect)
                inv_y -= 25

        # Game Stats (Top Right)
        level_text = self.small_font.render(f"Level: {self.level}", True, C.YELLOW)
        level_rect = level_text.get_rect(topright=(C.SCREEN_WIDTH - 20, 20))
        self.screen.blit(level_text, level_rect)

        bots_alive = sum(1 for bot in self.bots if bot.alive and bot.enemy_type != "health_pack")
        kills_text = self.small_font.render(f"Enemies: {bots_alive}", True, C.RED)
        kills_rect = kills_text.get_rect(topright=(C.SCREEN_WIDTH - 20, 50))
        self.screen.blit(kills_text, kills_rect)

        # Radar
        radar_size = 120
        radar_x = C.SCREEN_WIDTH - radar_size - 20
        radar_y = 20
        assert self.game_map is not None
        scale = radar_size / self.game_map.size

        # Radar BG
        pygame.draw.rect(self.screen, (0, 50, 0), (radar_x, radar_y, radar_size, radar_size))
        pygame.draw.rect(self.screen, (0, 150, 0), (radar_x, radar_y, radar_size, radar_size), 2)

        # Draw Visited Walls
        for vx, vy in self.visited_cells:
            if 0 <= vx < self.game_map.size and 0 <= vy < self.game_map.size:
                wall_val = self.game_map.grid[vy][vx]
                if wall_val != 0:
                    wx = int(vx * scale)
                    wy = int(vy * scale)
                    # Draw wall block
                    color = C.WALL_COLORS.get(wall_val, C.GRAY)
                    pygame.draw.rect(
                        self.screen,
                        color,
                        (radar_x + wx, radar_y + wy, max(1, int(scale)), max(1, int(scale))),
                    )

        # Enemies
        for bot in self.bots:
            if bot.alive and bot.enemy_type != "health_pack":
                bx = int(bot.x * scale)
                by = int(bot.y * scale)
                pygame.draw.circle(self.screen, C.RED, (radar_x + bx, radar_y + by), 2)

        # Portal
        if self.portal:
            px = int(self.portal["x"] * scale)
            py = int(self.portal["y"] * scale)
            pygame.draw.circle(self.screen, C.CYAN, (radar_x + px, radar_y + py), 4)

        # Player (with direction)
        px = int(self.player.x * scale)
        py = int(self.player.y * scale)
        pygame.draw.circle(self.screen, C.WHITE, (radar_x + px, radar_y + py), 3)
        # Direction line
        dx = math.cos(self.player.angle) * 8
        dy = math.sin(self.player.angle) * 8
        pygame.draw.line(
            self.screen,
            C.WHITE,
            (radar_x + px, radar_y + py),
            (radar_x + px + dx, radar_y + py + dy),
        )

        # Shield Bar
        shield_width = 150
        shield_height = 10
        shield_x = health_x
        shield_y = health_y - 20

        shield_pct = self.player.shield_timer / C.SHIELD_MAX_DURATION
        pygame.draw.rect(
            self.screen, C.DARK_GRAY, (shield_x, shield_y, shield_width, shield_height)
        )
        pygame.draw.rect(
            self.screen, C.CYAN, (shield_x, shield_y, int(shield_width * shield_pct), shield_height)
        )
        pygame.draw.rect(self.screen, C.WHITE, (shield_x, shield_y, shield_width, shield_height), 1)

        # Check Recharge Delay
        if self.player.shield_recharge_delay > 0:
            status_text = "RECHARGING" if self.player.shield_active else "COOLDOWN"
            status_surf = self.tiny_font.render(status_text, True, C.WHITE)
            self.screen.blit(status_surf, (shield_x + shield_width + 5, shield_y - 2))

        # Laser Charge
        laser_y = shield_y - 15
        laser_pct = 1.0 - (self.player.secondary_cooldown / C.SECONDARY_COOLDOWN)
        laser_pct = max(laser_pct, 0)
        laser_pct = min(laser_pct, 1)

        pygame.draw.rect(self.screen, C.DARK_GRAY, (shield_x, laser_y, shield_width, shield_height))
        controls_hint_text = "WASD:Move | 1-5:Wpn | R:Reload | F:Bomb | SPACE:Shield | ESC:Menu"
        controls_hint = self.tiny_font.render(controls_hint_text, True, C.WHITE)
        controls_hint_rect = controls_hint.get_rect(topleft=(10, 10))
        bg_surface = pygame.Surface(
            (
                controls_hint_rect.width + C.HINT_BG_PADDING_H,
                controls_hint_rect.height + C.HINT_BG_PADDING_V,
            ),
            pygame.SRCALPHA,
        )
        bg_surface.fill(C.HINT_BG_COLOR)
        self.screen.blit(
            bg_surface,
            (
                controls_hint_rect.x - C.HINT_BG_PADDING_H // 2,
                controls_hint_rect.y - C.HINT_BG_PADDING_V // 2,
            ),
        )
        self.screen.blit(controls_hint, controls_hint_rect)

    def render_crosshair(self) -> None:
        """Render crosshair"""
        cx = C.SCREEN_WIDTH // 2
        cy = C.SCREEN_HEIGHT // 2
        size = 12

        pygame.draw.line(self.screen, C.RED, (cx - size, cy), (cx + size, cy), 2)
        pygame.draw.line(self.screen, C.RED, (cx, cy - size), (cx, cy + size), 2)
        pygame.draw.circle(self.screen, C.RED, (cx, cy), 2)

    def render_muzzle_flash(self) -> None:
        """Render muzzle flash"""
        # Center of screen horizontally, exactly at gun tip (approx -200 from bottom)
        flash_x = C.SCREEN_WIDTH // 2
        flash_y = C.SCREEN_HEIGHT - 210

        # Weapon specific flash
        assert self.player is not None
        if self.player.current_weapon == "plasma":
            # Blue
            pygame.draw.circle(self.screen, C.CYAN, (flash_x, flash_y), 30)
            pygame.draw.circle(self.screen, C.BLUE, (flash_x, flash_y), 20)
            pygame.draw.circle(self.screen, C.WHITE, (flash_x, flash_y), 10)
        elif self.player.current_weapon == "shotgun":
            # Huge Orange Flash

            # Random spikes?
            pygame.draw.circle(self.screen, (255, 100, 0), (flash_x, flash_y), 50)  # Dark Orange
            pygame.draw.circle(self.screen, C.ORANGE, (flash_x, flash_y), 35)
            pygame.draw.circle(self.screen, C.YELLOW, (flash_x, flash_y), 15)
        else:
            # Standard
            pygame.draw.circle(self.screen, C.YELLOW, (flash_x, flash_y), 25)
            pygame.draw.circle(self.screen, C.ORANGE, (flash_x, flash_y), 15)
            pygame.draw.circle(self.screen, C.WHITE, (flash_x, flash_y), 8)

    def render_stats_lines(
        self,
        stats: List[Tuple[str, Tuple[int, int, int]]],
        start_y: int,
    ) -> None:
        """Helper method to render stats lines with spacing"""
        y = start_y
        for line, color in stats:
            if line:
                text = self.small_font.render(line, True, color)
                text_rect = text.get_rect(center=(C.SCREEN_WIDTH // 2, y))
                self.screen.blit(text, text_rect)
            y += 40

    def render_level_complete(self) -> None:
        """Render level complete screen"""
        self.screen.fill(C.BLACK)
        title = self.title_font.render("SECTOR CLEARED", True, C.GREEN)
        title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        level_time = self.level_times[-1] if self.level_times else 0
        total_time = sum(self.level_times)
        stats = [
            (f"Level {self.level} cleared!", C.WHITE),
            (f"Time: {level_time:.1f}s", C.GREEN),
            (f"Total Time: {total_time:.1f}s", C.GREEN),
            (f"Total Kills: {self.kills}", C.WHITE),
            ("", C.WHITE),
            ("Next level: Enemies get stronger!", C.YELLOW),
            ("", C.WHITE),
            ("Press SPACE for next level", C.WHITE),
            ("Press ESC for menu", C.WHITE),
        ]

        self.render_stats_lines(stats, 250)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.level += 1
                    self.start_level()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"

    def render_game_over(self) -> None:
        """Render game over screen"""
        self.screen.fill(C.BLACK)
        title = self.title_font.render("SYSTEM FAILURE", True, C.RED)
        title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        # Sequence Sound Logic
        self.game_over_timer += 1
        if self.game_over_timer == 120:  # 2 seconds delay
            self.sound_manager.play_sound("game_over2")

        completed_levels = max(0, self.level - 1)
        total_time = sum(self.level_times)

        avg_time = total_time / len(self.level_times) if self.level_times else 0
        stats = [
            (
                f"You survived {completed_levels} level{'s' if completed_levels != 1 else ''}",
                C.WHITE,
            ),
            (f"Total Kills: {self.kills}", C.WHITE),
            (f"Total Time: {total_time:.1f}s", C.GREEN),
            (
                (f"Average Time/Level: {avg_time:.1f}s", C.GREEN)
                if self.level_times
                else ("", C.WHITE)
            ),
            ("", C.WHITE),
            ("Press SPACE to restart", C.WHITE),
            ("Press ESC for menu", C.WHITE),
        ]

        self.render_stats_lines(stats, 250)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.start_game()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"

    def run(self) -> None:
        """Main game loop"""
        try:
            while self.running:
                if self.state == "intro":
                    self.handle_intro_events()
                    self.render_intro()
                elif self.state == "menu":
                    self.handle_menu_events()
                    self.render_menu()
                elif self.state == "map_select":
                    self.handle_map_select_events()
                    self.render_map_select()
                elif self.state == "playing":
                    self.handle_game_events()
                    if self.paused:
                        # Pause Menu Audio
                        # Heartbeat: 70 BPM -> ~0.85s delay -> ~51 frames (at 60FPS)
                        # Actually 60 / 70 * 60 = 51.4
                        beat_delay = 51
                        self.heartbeat_timer -= 1
                        if self.heartbeat_timer <= 0:
                            self.sound_manager.play_sound("heartbeat")
                            self.sound_manager.play_sound("breath")  # Mirror heartbeat
                            self.heartbeat_timer = beat_delay

                        # Groan if health < 50
                        assert self.player is not None
                        if self.player.health < 50:
                            self.groan_timer -= 1
                            if self.groan_timer <= 0:
                                self.sound_manager.play_sound("groan")
                                self.groan_timer = 240
                    else:
                        self.update_game()
                    self.render_game()
                elif self.state == "level_complete":
                    self.render_level_complete()
                elif self.state == "game_over":
                    self.render_game_over()

                self.clock.tick(C.FPS)
        except Exception as e:
            with open("crash_log.txt", "w") as f:
                f.write(traceback.format_exc())
            print(f"CRASH: {e}")
            raise

    def handle_intro_events(self) -> None:
        """Handle intro screen events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.intro_video:
                    self.intro_video.release()
                    self.intro_video = None
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                    if self.intro_video:
                        self.intro_video.release()
                        self.intro_video = None
                    self.state = "menu"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.intro_video:
                    self.intro_video.release()
                    self.intro_video = None
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
                if self.start_button.is_clicked(event.pos):
                    self.start_game()
                    self.state = "playing"
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                    self.state = "playing"

                # Check for settings clicks (Simplified: Cycle on click anywhere in top area?)
                # For now just start button interaction is critical.

    def render_intro(self) -> None:
        """Render Max Payne style graphic novel intro"""
        self.screen.fill(C.BLACK)
        current_time = pygame.time.get_ticks()

        if self.intro_start_time == 0:
            self.intro_start_time = current_time

        elapsed = current_time - self.intro_start_time

        # Phase 0: Willy Wonk Production
        if self.intro_phase == 0:
            duration = 3000

            # Candy Aesthetics
            # Pastel Pink Title
            text = self.subtitle_font.render(
                "A Willy Wonk Production", True, (255, 182, 193)
            )  # Light Pink
            text_rect = text.get_rect(center=(C.SCREEN_WIDTH // 2, 100))
            self.screen.blit(text, text_rect)

            # Image
            if "willy" in self.intro_images:
                img = self.intro_images["willy"]
                img_rect = img.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 30))

                # Soft blend (simple alpha fade on edges is hard in realtime without prep)
                # We'll draw a "vignette" overlay using a texture if we had one.
                # Instead, let's draw a soft pink border around it.
                self.screen.blit(img, img_rect)
                pygame.draw.rect(
                    self.screen, (255, 192, 203), img_rect, 4, border_radius=10
                )  # Pink border

            if elapsed > duration:
                self.intro_phase = 1
                self.intro_start_time = 0

        # Phase 1: Upstream Drift Studios
        elif self.intro_phase == 1:
            duration = 3000  # User requested 2 seconds less (was 5000)

            # Play Water Sound once
            if elapsed < 50:  # Play at start
                if not hasattr(self, "_water_played"):
                    try:
                        self.sound_manager.play_sound("water")
                    except Exception as e:  # noqa: BLE001
                        print(f"Error playing water sound: {e}")
                    self._water_played = True

            # Text - Stylish Upstream Drift
            # Use Impact or bold font
            stylish_font = pygame.font.SysFont("impact", 70)

            # Dynamic Color (Pulsing Blue/Cyan)
            pulse = abs(math.sin(elapsed * 0.003))
            txt_color = (0, int(150 + 100 * pulse), int(200 + 55 * pulse))

            t2 = stylish_font.render("UPSTREAM DRIFT", True, txt_color)
            r2 = t2.get_rect(
                center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 - 180)
            )  # Closer to image

            # Shadow
            t2_shadow = stylish_font.render("UPSTREAM DRIFT", True, (0, 0, 0))
            r2_shadow = t2_shadow.get_rect(
                center=(C.SCREEN_WIDTH // 2 + 4, C.SCREEN_HEIGHT // 2 - 176)
            )
            self.screen.blit(t2_shadow, r2_shadow)
            self.screen.blit(t2, r2)

            t1 = self.tiny_font.render("in association with", True, C.CYAN)
            r1 = t1.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 - 230))
            self.screen.blit(t1, r1)

            # Video Playback
            try:
                if self.intro_video and self.intro_video.isOpened():
                    ret, frame = self.intro_video.read()
                    if ret:
                        # Convert CV2 frame (BGR) to Pygame (RGB)
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame = frame.swapaxes(0, 1)  # Transpose for pygame surface

                        surf = pygame.surfarray.make_surface(frame)

                        # Scale to fit
                        target_h = 400
                        scale = target_h / surf.get_height()
                        new_size = (int(surf.get_width() * scale), int(surf.get_height() * scale))
                        surf = pygame.transform.scale(surf, new_size)

                        r = surf.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 50))
                        self.screen.blit(surf, r)
                    else:
                        # Loop video?
                        self.intro_video.set(cv2.CAP_PROP_POS_FRAMES, 0)

                else:
                    # Debug info relative to user request
                    if not hasattr(self, "_video_debug_printed"):
                        vid_path = os.path.join(self.assets_dir, "video", "fish.mp4")
                        print(f"DEBUG: Video not opened or CV2 missing. Path: {vid_path}")
                        if os.path.exists(vid_path):
                            print("DEBUG: File exists on disk.")
                        else:
                            print("DEBUG: File DOES NOT exist on disk.")
                        self._video_debug_printed = True

                    # Fallback to Image
                    if "deadfish" in self.intro_images:
                        img = self.intro_images["deadfish"]
                        img_rect = img.get_rect(
                            center=(
                                C.SCREEN_WIDTH // 2,
                                C.SCREEN_HEIGHT // 2 + 50,
                            )
                        )
                        self.screen.blit(img, img_rect)
            except Exception as e:  # noqa: BLE001
                print(f"Video Playback Error: {e}")
                traceback.print_exc()
                # Fallback on error
                if "deadfish" in self.intro_images:
                    img = self.intro_images["deadfish"]
                    img_rect = img.get_rect(
                        center=(
                            C.SCREEN_WIDTH // 2,
                            C.SCREEN_HEIGHT // 2 + 50,
                        )
                    )
                    self.screen.blit(img, img_rect)

            if elapsed > duration:
                self.intro_phase = 2
                self.intro_start_time = 0
                if self.intro_video:
                    self.intro_video.release()
                    self.intro_video = None

        # Phase 2: Graphic Novel / Story
        elif self.intro_phase == 2:
            # Slides Config
            slides = [
                {
                    "type": "distortion",
                    "text": "FROM THE DEMENTED MIND",
                    "text2": "OF JASPER",
                    "duration": 8000,
                    "sound": "laugh",
                },
                {
                    "type": "story",
                    "lines": [
                        "They said the field would contain them.",
                        "They were wrong.",
                        "The specimens have breached the perimeter.",
                        "You are the last containment unit.",
                        "Objective: TERMINATE.",
                    ],
                    "duration": 10000,
                },
                {
                    "type": "static",
                    "text": "NO MERCY. NO ESCAPE.",
                    "duration": 4000,
                    "color": (200, 0, 0),
                },
                {
                    "type": "static",
                    "text": "FORCE FIELD",
                    "sub": "THE ARENA AWAITS",
                    "duration": 4000,
                    "color": C.WHITE,  # Will fade to RED
                },
            ]

            if self.intro_step < len(slides):
                slide = slides[self.intro_step]
                duration = cast("int", slide["duration"])

                # Sound Trigger
                if elapsed < 50 and "sound" in slide:
                    if slide["sound"] == "laugh" and not hasattr(self, "_laugh_played_2"):
                        self.sound_manager.play_sound("laugh")
                        self._laugh_played_2 = True

                # Distortion Effect
                if slide["type"] == "distortion":
                    # Try using a scary font (Chiller is good for Goosebumps vibes)
                    font = (
                        pygame.font.SysFont("chiller", 70)
                        if pygame.font.match_font("chiller")
                        else self.title_font
                    )

                    lines = [cast("str", slide["text"])]
                    if "text2" in slide:
                        lines.append(cast("str", slide["text2"]))

                    start_y = C.SCREEN_HEIGHT // 2 - (len(lines) * 80) // 2

                    for line_idx, text_str in enumerate(lines):
                        total_w = sum([font.size(char)[0] for char in text_str])
                        start_x = (C.SCREEN_WIDTH - total_w) // 2
                        y = start_y + line_idx * 100

                        x_off = 0
                        for index, char in enumerate(text_str):
                            # Slower Jitter
                            time_factor = pygame.time.get_ticks() * 0.003 + index * 0.2
                            jitter_x = math.sin(time_factor * 2.0) * 2
                            # More vertical dripping movement
                            jitter_y = math.cos(time_factor * 1.5) * 4

                            # Pulsing Blood Red
                            c_val = int(120 + 135 * abs(math.sin(time_factor * 0.8)))
                            color = (c_val, 0, 0)

                            char_surf = font.render(char, True, color)
                            # Blur/Glow effect (draw scaled up slightly behind?)
                            # Simple approach: Draw dark red shadow
                            shadow_surf = font.render(char, True, (50, 0, 0))
                            self.screen.blit(
                                shadow_surf, (start_x + x_off + jitter_x + 2, y + jitter_y + 2)
                            )

                            self.screen.blit(char_surf, (start_x + x_off + jitter_x, y + jitter_y))
                            x_off += font.size(char)[0]

                # Story Streaming
                elif slide["type"] == "story":
                    lines = cast("List[str]", slide["lines"])
                    # Calculate how many lines to show based on time
                    # Show one line every 1.5 seconds
                    lines_to_show = int((elapsed / duration) * (len(lines) + 1))
                    lines_to_show = min(lines_to_show, len(lines))

                    y = C.SCREEN_HEIGHT // 2 - (len(lines) * 50) // 2
                    for i in range(lines_to_show):
                        l_text = lines[i]
                        # User wants them to STAY red. No white changes.
                        # "In the intro, the letters in the lines change from red to white..."
                        color = C.RED

                        txt_surf = self.subtitle_font.render(l_text, True, color)
                        txt_rect = txt_surf.get_rect(center=(C.SCREEN_WIDTH // 2, y))
                        self.screen.blit(txt_surf, txt_rect)
                        y += 50

                # Static / Standard
                elif slide["type"] == "static":
                    color = cast("Tuple[int, int, int]", slide.get("color", C.WHITE))

                    if cast("str", slide.get("text")) == "FORCE FIELD":
                        # Fade White -> Red
                        fade_ratio = min(1.0, elapsed / duration)
                        # Linear interpolation White (255,255,255) -> Red (255,0,0)
                        start_c = (255, 255, 255)
                        end_c = (255, 0, 0)
                        cur_r = int(start_c[0] + (end_c[0] - start_c[0]) * fade_ratio)
                        cur_g = int(start_c[1] + (end_c[1] - start_c[1]) * fade_ratio)
                        cur_b = int(start_c[2] + (end_c[2] - start_c[2]) * fade_ratio)
                        color = (cur_r, cur_g, cur_b)

                    txt_surf = self.title_font.render(cast("str", slide["text"]), True, color)

                    # Position Check: If typical static, center. If Title, match Menu position.
                    scale_y = C.SCREEN_HEIGHT // 2
                    if cast("str", slide.get("text")) == "FORCE FIELD":
                        scale_y = C.SCREEN_HEIGHT // 2 - 100

                    txt_rect = txt_surf.get_rect(center=(C.SCREEN_WIDTH // 2, scale_y))
                    self.screen.blit(txt_surf, txt_rect)

                    # Blood Effect for Intro Title
                    if cast("str", slide.get("text")) == "FORCE FIELD":
                        # Check if color is close to red (fully faded)
                        if color[0] > 250 and color[1] < 10 and color[2] < 10:
                            self.update_blood_drips(txt_rect)
                            self.draw_blood_drips()

                    if "sub" in slide:
                        sub_text = cast("str", slide["sub"])
                        sub_surf = self.subtitle_font.render(sub_text, True, C.CYAN)
                        sub_rect = sub_surf.get_rect(
                            center=(
                                C.SCREEN_WIDTH // 2,
                                C.SCREEN_HEIGHT // 2 + 60,
                            )
                        )
                        self.screen.blit(sub_surf, sub_rect)

                if elapsed > duration:
                    self.intro_step += 1
                    self.intro_start_time = 0
            else:
                self.state = "menu"

        pygame.display.flip()
