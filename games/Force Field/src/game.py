from __future__ import annotations

import math
import random
import traceback
from contextlib import suppress
from typing import Any, Dict, List, Tuple, cast

import pygame

from . import constants as C  # noqa: N812
from .bot import Bot
from .map import Map
from .player import Player
from .projectile import Projectile
from .raycaster import Raycaster
from .renderer import GameRenderer
from .sound import SoundManager


class Game:
    """Main game class"""

    def __init__(self) -> None:
        """Initialize game"""
        flags = pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), flags)
        pygame.display.set_caption("Force Field - Arena Combat")
        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize Renderer
        self.renderer = GameRenderer(self.screen)

        # Game state
        self.state = "intro"
        self.intro_phase = 0
        self.intro_step = 0
        self.intro_timer = 0
        self.intro_start_time = 0
        self.last_death_pos: Tuple[float, float] | None = None

        # Gameplay state
        self.level = 1
        self.kills = 0
        self.level_start_time = 0
        self.level_times: List[float] = []
        self.selected_map_size = C.DEFAULT_MAP_SIZE
        self.paused = False
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
        self.particles: List[Dict[str, Any]] = []
        self.damage_texts: List[Dict[str, Any]] = []
        self.damage_flash_timer = 0

        # Game objects
        self.game_map: Map | None = None
        self.player: Player | None = None
        self.bots: List[Bot] = []
        self.projectiles: List[Projectile] = []
        self.raycaster: Raycaster | None = None
        self.portal: Dict[str, Any] | None = None
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
                print(f"Controller detected: {self.joystick.get_name()}")
            except Exception as e:  # noqa: BLE001
                print(f"Controller init failed: {e}")

        # Fog of War
        self.visited_cells: set[tuple[int, int]] = set()

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

        # Grab mouse for FPS gameplay
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        # Player Spawn Logic - Use corners
        corners = self.get_corner_positions()
        random.shuffle(corners)

        # Select best corner (safest)
        player_pos = corners[0]
        # Just in case, try to verify valid spot (though corners should be valid)
        if self.game_map.is_wall(int(player_pos[0]), int(player_pos[1])):
            # Fallback: Find first non-wall cell in the map
            found = False
            for y in range(self.game_map.height):
                for x in range(self.game_map.width):
                    if not self.game_map.is_wall(x, y):
                        player_pos = (x + 0.5, y + 0.5, 0.0)
                        found = True
                        break
                if found:
                    break
            else:
                # If no valid cell found, default to constant
                player_pos = C.DEFAULT_PLAYER_SPAWN

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
        # Validate current weapon is unlocked (e.g. Player init sets 'rifle' but it might be locked)
        if self.player.current_weapon not in self.unlocked_weapons:
            self.player.current_weapon = "pistol"

        # Propagate God Mode state
        self.player.god_mode = self.god_mode

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
                speed=float(C.WEAPONS["plasma"].get("projectile_speed", 0.5)),
                damage=self.player.get_current_weapon_damage(),
                is_player=True,
                color=tuple(C.WEAPONS["plasma"].get("projectile_color", (0, 255, 255))),
                size=0.225,
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
            pellets = int(C.WEAPONS["shotgun"].get("pellets", 8))
            spread = float(C.WEAPONS["shotgun"].get("spread", 0.15))
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
            weapon_range = self.player.get_current_weapon_range()
            if is_secondary:
                weapon_range = 100

            weapon_damage = self.player.get_current_weapon_damage()

            closest_bot = None
            closest_dist = float("inf")
            is_headshot = False

            ray_angle = self.player.angle + angle_offset
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)

            rx, ry = self.player.x, self.player.y
            map_x, map_y = int(rx), int(ry)

            delta_dist_x = abs(1 / cos_a) if cos_a != 0 else 1e30
            delta_dist_y = abs(1 / sin_a) if sin_a != 0 else 1e30

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

            wall_dist: float = float(weapon_range)
            hit_wall = False
            steps = 0
            max_raycast_steps = C.MAX_RAYCAST_STEPS

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

                assert self.player is not None
                dx = bot.x - self.player.x
                dy = bot.y - self.player.y
                distance = math.sqrt(dx**2 + dy**2)

                if distance > wall_dist:
                    continue

                bot_angle = math.atan2(dy, dx)
                bot_angle_norm = bot_angle if bot_angle >= 0 else bot_angle + 2 * math.pi

                current_spread = C.SPREAD_ZOOM if self.player.zoomed else C.SPREAD_BASE

                if angle_offset == 0.0:
                    spread_offset = random.uniform(-current_spread, current_spread)
                    aim_angle = self.player.angle + spread_offset
                else:
                    aim_angle = self.player.angle + angle_offset

                aim_angle %= 2 * math.pi

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
                except Exception as e:  # noqa: BLE001
                    print(f"Error in explode_laser: {e}")

                self.particles.append(
                    {
                        "type": "laser",
                        "start": (C.SCREEN_WIDTH - 200, C.SCREEN_HEIGHT - 180),
                        "end": (C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2),
                        "color": (0, 255, 255),
                        "timer": C.LASER_DURATION,
                        "width": C.LASER_WIDTH,
                    }
                )
                return

            if is_laser:
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

            if closest_bot:
                range_factor = max(0.3, 1.0 - (closest_dist / weapon_range))

                dx = closest_bot.x - self.player.x
                dy = closest_bot.y - self.player.y
                bot_angle = math.atan2(dy, dx)
                bot_angle_norm = bot_angle if bot_angle >= 0 else bot_angle + 2 * math.pi

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
            print(f"Error in check_shot_hit: {e}")

    def handle_bomb_explosion(self) -> None:
        """Handle bomb explosion logic"""
        assert self.player is not None
        self.particles.append(
            {
                "x": C.SCREEN_WIDTH // 2,
                "y": C.SCREEN_HEIGHT // 2,
                "dx": 0,
                "dy": 0,
                "color": C.WHITE,
                "timer": 40,
                "size": 3000,
            }
        )
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

        for bot in self.bots:
            if not bot.alive:
                continue
            dist = math.sqrt((bot.x - self.player.x) ** 2 + (bot.y - self.player.y) ** 2)
            if dist < C.BOMB_RADIUS:
                was_alive = bot.alive
                bot.take_damage(1000)
                if was_alive and not bot.alive:
                    self.sound_manager.play_sound("scream")
                    self.kills += 1
                    self.kill_combo_count += 1
                    self.kill_combo_timer = 180
                    self.last_death_pos = (bot.x, bot.y)

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
            hits = 0
            for bot in self.bots:
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
                            with suppress(Exception):
                                self.sound_manager.play_sound("scream")
                            self.kills += 1
                            self.kill_combo_count += 1
                            self.kill_combo_timer = 180
                            self.last_death_pos = (bot.x, bot.y)

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
        dist_to_player = math.sqrt(
            (projectile.x - self.player.x) ** 2 + (projectile.y - self.player.y) ** 2
        )
        if dist_to_player < 15:
            self.damage_flash_timer = 15

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
                    self.sound_manager.play_sound("scream")
                    self.kills += 1
                    self.kill_combo_count += 1
                    self.kill_combo_timer = 180
                    self.last_death_pos = (bot.x, bot.y)

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
            return

        # Decrement damage flash timer
        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= 1

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

        enemies_alive = [
            b for b in self.bots if b.alive and b.type_data.get("visual_style") != "item"
        ]

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
            dist = math.sqrt(
                (self.portal["x"] - self.player.x) ** 2 + (self.portal["y"] - self.player.y) ** 2
            )
            if dist < 1.5:
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

        shield_active = keys[pygame.K_SPACE]

        if self.joystick and not self.paused and self.player and self.player.alive:
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

        for p in self.particles[:]:
            if "dx" in p and "dy" in p:
                p["x"] += p["dx"]
                p["y"] += p["dy"]
            p["timer"] -= 1
            if p["timer"] <= 0:
                self.particles.remove(p)

        for t in self.damage_texts[:]:
            t["y"] += t["vy"]
            t["timer"] -= 1
            if t["timer"] <= 0:
                self.damage_texts.remove(t)

        is_sprinting = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        current_speed = C.PLAYER_SPRINT_SPEED if is_sprinting else C.PLAYER_SPEED

        moving = False

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

        for bot in self.bots:
            projectile = bot.update(self.game_map, self.player, self.bots)
            if projectile:
                self.projectiles.append(projectile)
                self.sound_manager.play_sound("enemy_shoot")

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

        assert self.game_map is not None
        assert self.player is not None
        for projectile in self.projectiles[:]:

            was_alive = projectile.alive
            projectile.update(self.game_map)

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
                        self.player.take_damage(projectile.damage)

                        if self.player.health < old_health:
                            self.damage_flash_timer = 10
                            self.sound_manager.play_sound("oww")

                        projectile.alive = False
                else:
                    for bot in self.bots:
                        if not bot.alive:
                            continue
                        dx = projectile.x - bot.x
                        dy = projectile.y - bot.y
                        dist = math.sqrt(dx**2 + dy**2)
                        if dist < 0.8:
                            was_alive = bot.alive
                            bot.take_damage(projectile.damage)
                            if was_alive and not bot.alive:
                                self.sound_manager.play_sound("scream")
                                self.kills += 1
                                self.kill_combo_count += 1
                                self.kill_combo_timer = 180
                                self.last_death_pos = (bot.x, bot.y)

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

                            projectile.alive = False

                            if getattr(projectile, "weapon_type", "normal") == "plasma":
                                self.explode_plasma(projectile)
                            break

        self.projectiles = [p for p in self.projectiles if p.alive]

        cx, cy = int(self.player.x), int(self.player.y)
        reveal_radius = 5
        for r_i in range(-reveal_radius, reveal_radius + 1):
            for r_j in range(-reveal_radius, reveal_radius + 1):
                if r_i * r_i + r_j * r_j <= reveal_radius * reveal_radius:
                    self.visited_cells.add((cx + r_j, cy + r_i))

        min_dist = float("inf")
        for bot in self.bots:
            if bot.alive:
                dist = math.sqrt((bot.x - self.player.x) ** 2 + (bot.y - self.player.y) ** 2)
                min_dist = min(min_dist, dist)

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
                    phrase = random.choice(["phrase_cool", "phrase_awesome", "phrase_brutal"])
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
                if self.renderer.intro_video:
                    self.renderer.intro_video.release()
                    self.renderer.intro_video = None
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                    if self.renderer.intro_video:
                        self.renderer.intro_video.release()
                        self.renderer.intro_video = None
                    self.state = "menu"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.renderer.intro_video:
                    self.renderer.intro_video.release()
                    self.renderer.intro_video = None
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
        self.renderer.start_button.update(pygame.mouse.get_pos())
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
                if self.renderer.start_button.is_clicked(event.pos):
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
                if self.renderer.intro_video:
                    self.renderer.intro_video.release()
                    self.renderer.intro_video = None

    def run(self) -> None:
        """Main game loop"""
        try:
            while self.running:
                if self.state == "intro":
                    self.handle_intro_events()
                    if self.intro_start_time == 0:
                        self.intro_start_time = pygame.time.get_ticks()
                    elapsed = pygame.time.get_ticks() - self.intro_start_time

                    self.renderer.render_intro(self.intro_phase, self.intro_step, elapsed)
                    self._update_intro_logic(elapsed)

                elif self.state == "menu":
                    self.handle_menu_events()
                    self.renderer.render_menu()

                elif self.state == "map_select":
                    self.handle_map_select_events()
                    self.renderer.render_map_select(self)

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

                elif self.state == "level_complete":
                    self.handle_level_complete_events()
                    self.renderer.render_level_complete(self)

                elif self.state == "game_over":
                    self.handle_game_over_events()
                    self.renderer.render_game_over(self)

                self.clock.tick(C.FPS)
        except Exception as e:
            with open("crash_log.txt", "w") as f:
                f.write(traceback.format_exc())
            print(f"CRASH: {e}")
            raise
