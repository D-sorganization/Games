from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

import pygame

from . import constants as C  # noqa: N812
from .bot import Bot
from .map import Map
from .player import Player
from .raycaster import Raycaster
from .ui import Button

if TYPE_CHECKING:
    from .projectile import Projectile


class Game:
    """Main game class"""

    def __init__(self) -> None:
        """Initialize game"""
        self.screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT))
        pygame.display.set_caption("Force Field - Arena Combat")
        self.clock = pygame.time.Clock()
        self.running = True

        # Game state
        # Game state
        self.state = "intro"
        self.intro_step = 0
        self.intro_timer = 0
        self.intro_alpha = 0
        self.intro_start_time = 0

        # Gameplay state
        self.level = 1
        self.kills = 0
        self.level_start_time = 0
        self.level_times: List[float] = []
        self.selected_map_size = C.DEFAULT_MAP_SIZE
        self.paused = False
        self.pause_start_time = 0
        self.total_paused_time = 0
        self.show_damage = True

        # Visual effects
        self.particles: List[Dict[str, Any]] = []
        self.damage_texts: List[Dict[str, Any]] = []

        # Game objects
        self.game_map: Map | None = None
        self.player: Player | None = None
        self.bots: List[Bot] = []
        self.projectiles: List[Projectile] = []
        self.raycaster: Raycaster | None = None

        # Fonts - Modern and Stylistic
        try:
            self.title_font = pygame.font.SysFont("impact", 80)
            self.font = pygame.font.SysFont("arial", 48)
            self.small_font = pygame.font.SysFont("arial", 32)
            self.tiny_font = pygame.font.SysFont("arial", 24)
            self.subtitle_font = pygame.font.SysFont("comicsansms", 40)  # For narrative text
        except:
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
        self.start_button = Button(
            C.SCREEN_WIDTH // 2 - 150,
            C.SCREEN_HEIGHT // 2 + 50,
            300,
            60,
            "ENTER BATTLE",
            C.BLUE_BLOOD,
        )
        self.map_size_buttons = []
        map_sizes = [30, 40, 50, 60, 70]
        button_width = 80
        button_spacing = 10
        total_width = len(map_sizes) * (button_width + button_spacing) - button_spacing
        start_x = C.SCREEN_WIDTH // 2 - total_width // 2
        for i, size in enumerate(map_sizes):
            x = start_x + i * (button_width + button_spacing)
            y = C.SCREEN_HEIGHT // 2 - 20
            color = C.GREEN if size == self.selected_map_size else C.DARK_GRAY
            btn = Button(x, y, button_width, 40, str(size), color)
            self.map_size_buttons.append((btn, size))

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

    def start_game(self) -> None:
        """Start new game"""
        self.level = 1
        self.kills = 0
        self.level_times = []
        self.paused = False
        self.particles = []
        self.damage_texts = []
        # Create map with selected size
        self.game_map = Map(self.selected_map_size)
        self.raycaster = Raycaster(self.game_map)
        self.start_level()

    def start_level(self) -> None:
        """Start a new level"""
        assert self.game_map is not None
        self.level_start_time = pygame.time.get_ticks()
        self.total_paused_time = 0
        self.particles = []
        self.damage_texts = []
        corners = self.get_corner_positions()
        random.shuffle(corners)

        # Player spawns in first corner - ensure it's safe
        player_pos = corners[0]
        # Double-check player spawn is safe
        if self.game_map.is_wall(
            player_pos[0],
            player_pos[1],
        ) or self.game_map.is_inside_building(player_pos[0], player_pos[1]):
            # Find a nearby safe position
            for attempt in range(20):
                test_x = player_pos[0] + random.uniform(-3, 3)
                test_y = player_pos[1] + random.uniform(-3, 3)
                if (
                    not self.game_map.is_wall(test_x, test_y)
                    and not self.game_map.is_inside_building(test_x, test_y)
                    and 2 <= test_x < self.game_map.size - 2
                    and 2 <= test_y < self.game_map.size - 2
                ):
                    player_pos = (test_x, test_y, player_pos[2])
                    break
        self.player = Player(player_pos[0], player_pos[1], player_pos[2])

        # Bots spawn in other three corners with varied types
        self.bots = []
        self.projectiles = []
        enemies_per_corner = 4 + (self.level - 1)

        available_types = list(C.ENEMY_TYPES.keys())
        random.shuffle(available_types)

        for i in range(1, 4):
            bot_pos = corners[i]
            # Use a different enemy type for each corner (cycling if we run out)
            enemy_type = available_types[(i - 1) % len(available_types)]

            # Spawn enemies around corner
            for j in range(enemies_per_corner):
                angle_offset = j * 2 * math.pi / enemies_per_corner
                radius = 1.5 + (j % 2) * 0.5
                spawn_x = bot_pos[0] + math.cos(angle_offset) * radius
                spawn_y = bot_pos[1] + math.sin(angle_offset) * radius

                if (
                    not self.game_map.is_wall(spawn_x, spawn_y)
                    and not self.game_map.is_inside_building(spawn_x, spawn_y)
                    and 2 <= spawn_x < self.game_map.size - 2
                    and 2 <= spawn_y < self.game_map.size - 2
                ):
                    self.bots.append(Bot(spawn_x, spawn_y, self.level, enemy_type))
                else:
                    # Retry nearby
                    found_pos = False
                    for attempt in range(15):
                        test_x = bot_pos[0] + random.uniform(
                            -C.SPAWN_RETRY_RADIUS, C.SPAWN_RETRY_RADIUS
                        )
                        test_y = bot_pos[1] + random.uniform(
                            -C.SPAWN_RETRY_RADIUS, C.SPAWN_RETRY_RADIUS
                        )
                        if (
                            not self.game_map.is_wall(test_x, test_y)
                            and not self.game_map.is_inside_building(test_x, test_y)
                            and 2 <= test_x < self.game_map.size - 2
                            and 2 <= test_y < self.game_map.size - 2
                        ):
                            self.bots.append(Bot(test_x, test_y, self.level, enemy_type))
                            found_pos = True
                            break

                    if not found_pos:
                        # Last resort: spawn at corner if safe, otherwise skip ONE bot (safety)
                        if not self.game_map.is_wall(
                            bot_pos[0], bot_pos[1]
                        ) and not self.game_map.is_inside_building(bot_pos[0], bot_pos[1]):
                            self.bots.append(Bot(bot_pos[0], bot_pos[1], self.level, enemy_type))

        self.state = "playing"

        # Enable mouse capture
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

    def handle_menu_events(self) -> None:
        """Handle menu events"""
        mouse_pos = pygame.mouse.get_pos()
        self.start_button.update(mouse_pos)
        for btn, _ in self.map_size_buttons:
            btn.update(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.start_button.is_clicked(mouse_pos):
                        self.start_game()
                    else:
                        # Check map size buttons
                        for btn, size in self.map_size_buttons:
                            if btn.is_clicked(mouse_pos):
                                self.selected_map_size = size
                                # Update button colors
                                for b, s in self.map_size_buttons:
                                    b.color = C.GREEN if s == size else C.DARK_GRAY
                                break

    def handle_game_events(self) -> None:
        """Handle gameplay events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and self.paused:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    menu_items = ["RESUME", "SAVE GAME", "QUIT TO MENU"]
                    for i, item in enumerate(menu_items):
                        rect = pygame.Rect(
                            C.SCREEN_WIDTH // 2 - 100, C.SCREEN_HEIGHT // 2 - 50 + i * 60, 200, 50
                        )
                        if rect.collidepoint(mouse_pos):
                            if item == "RESUME":
                                self.paused = False
                                self.total_paused_time += (
                                    pygame.time.get_ticks() - self.pause_start_time
                                )
                                pygame.mouse.set_visible(False)
                                pygame.event.set_grab(True)
                            elif item == "SAVE GAME":
                                try:
                                    with open(C.SAVE_FILE_PATH, "w") as f:
                                        f.write(f"{self.level}")
                                except OSError as e:
                                    print(f"Save failed: {e}")
                                    self.damage_texts.append(
                                        {
                                            "x": C.SCREEN_WIDTH // 2,
                                            "y": C.SCREEN_HEIGHT // 2,
                                            "text": "SAVE FAILED!",
                                            "color": C.RED,
                                            "timer": 60,
                                            "vy": -0.5,
                                        }
                                    )
                                self.paused = False
                                self.total_paused_time += (
                                    pygame.time.get_ticks() - self.pause_start_time
                                )
                                pygame.mouse.set_visible(False)
                                pygame.event.set_grab(True)
                            elif item == "QUIT TO MENU":
                                self.state = "menu"
                                self.paused = False
                                pygame.mouse.set_visible(True)
                                pygame.event.set_grab(False)
                            break  # Handle one click

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                    if self.paused:
                        self.pause_start_time = pygame.time.get_ticks()
                    else:
                        self.total_paused_time += pygame.time.get_ticks() - self.pause_start_time
                    pygame.mouse.set_visible(self.paused)
                    pygame.event.set_grab(not self.paused)
                # Weapon switching
                elif not self.paused:
                    if event.key == pygame.K_1:
                        assert self.player is not None
                        self.player.switch_weapon("pistol")
                    elif event.key == pygame.K_2:
                        assert self.player is not None
                        self.player.switch_weapon("rifle")
                    elif event.key == pygame.K_3:
                        assert self.player is not None
                        self.player.switch_weapon("shotgun")
                    elif event.key == pygame.K_4:
                        assert self.player is not None
                        self.player.switch_weapon("plasma")
            elif event.type == pygame.MOUSEBUTTONDOWN and not self.paused:
                assert self.player is not None
                if event.button == 3:  # Right-click to fire
                    if self.player.shoot():
                        self.check_shot_hit()
            elif event.type == pygame.MOUSEMOTION and not self.paused:
                assert self.player is not None
                self.player.rotate(event.rel[0] * C.PLAYER_ROT_SPEED)

    def check_shot_hit(self) -> None:
        """Check if player's shot hit a bot"""
        assert self.player is not None
        # Cast ray in player's view direction
        weapon_range = self.player.get_current_weapon_range()
        weapon_damage = self.player.get_current_weapon_damage()

        closest_bot = None
        closest_dist = float("inf")
        is_headshot = False

        for bot in self.bots:
            if not bot.alive:
                continue

            # Calculate bot position relative to player
            assert self.player is not None
            dx = bot.x - self.player.x
            dy = bot.y - self.player.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > weapon_range:
                continue

            # Check if bot is in front of player
            bot_angle = math.atan2(dy, dx)
            bot_angle_norm = bot_angle if bot_angle >= 0 else bot_angle + 2 * math.pi
            angle_diff = abs(bot_angle_norm - self.player.angle)
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff

            if angle_diff < 0.15:
                hit = True
                steps = int(distance * 10)
                for i in range(1, steps):
                    t = i / steps
                    check_x = self.player.x + dx * t
                    check_y = self.player.y + dy * t
                    if self.game_map.is_wall(check_x, check_y):
                        hit = False
                        break

                if hit and distance < closest_dist:
                    closest_bot = bot
                    closest_dist = distance
                    is_headshot = angle_diff < C.HEADSHOT_THRESHOLD

        if closest_bot:
            # Calculate hit position for blood

            # Display calculated damage (includes headshot multiplier)
            # Note: Bot.take_damage() handles the actual health reduction logic internally,
            # using the base weapon_damage and is_headshot flag.
            # We calculate damage_dealt here purely for the visual text.
            damage_dealt = weapon_damage * 3 if is_headshot else weapon_damage
            closest_bot.take_damage(weapon_damage, is_headshot=is_headshot)

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

    def update_game(self) -> None:
        """Update game state"""
        if self.paused:
            pygame.mouse.get_pos()
            # Simple pause menu handling could go here
            return

        assert self.player is not None
        if not self.player.alive:
            # Capture final time for the failed level
            level_time = (
                pygame.time.get_ticks() - self.level_start_time - self.total_paused_time
            ) / 1000.0
            self.level_times.append(level_time)

            self.state = "game_over"
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
            return

        all_dead = all(not bot.alive for bot in self.bots)
        if all_dead:
            # Only add time if we haven't already for this level
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
        self.player.shield_active = keys[pygame.K_SPACE]

        # Particles update
        for p in self.particles[:]:
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

        # Movement (move method checks for shield)
        if keys[pygame.K_w]:
            self.player.move(self.game_map, self.bots, forward=True, speed=current_speed)
        if keys[pygame.K_s]:
            self.player.move(self.game_map, self.bots, forward=False, speed=current_speed)
        if keys[pygame.K_a]:
            self.player.strafe(self.game_map, self.bots, right=False, speed=current_speed)
        if keys[pygame.K_d]:
            self.player.strafe(self.game_map, self.bots, right=True, speed=current_speed)

        if keys[pygame.K_LEFT]:
            self.player.rotate(-0.05)
        if keys[pygame.K_RIGHT]:
            self.player.rotate(0.05)

        self.player.update()

        for bot in self.bots:
            projectile = bot.update(self.game_map, self.player, self.bots)
            if projectile:
                self.projectiles.append(projectile)

        assert self.game_map is not None
        assert self.player is not None
        for projectile in self.projectiles[:]:
            if projectile is None:
                continue
            projectile.update(self.game_map)

            if not projectile.is_player:
                dx = projectile.x - self.player.x
                dy = projectile.y - self.player.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist < 0.5:
                    self.player.take_damage(projectile.damage)
                    projectile.alive = False

            if not projectile.alive:
                self.projectiles.remove(projectile)

    def render_menu(self) -> None:
        """Render main menu"""
        self.screen.fill(C.BLACK)

        title_y = 120
        title_text = "FORCE FIELD"
        for offset_x, offset_y in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            title_outline = self.title_font.render(title_text, True, C.BLUE)
            title_rect_outline = title_outline.get_rect(
                center=(C.SCREEN_WIDTH // 2 + offset_x, title_y + offset_y),
            )
            self.screen.blit(title_outline, title_rect_outline)
        title = self.title_font.render(title_text, True, C.CYAN)
        title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, title_y))
        self.screen.blit(title, title_rect)

        subtitle = self.small_font.render("Arena Combat", True, C.WHITE)
        subtitle_rect = subtitle.get_rect(center=(C.SCREEN_WIDTH // 2, title_y + 80))
        self.screen.blit(subtitle, subtitle_rect)

        map_label = self.small_font.render("Map Size:", True, C.CYAN)
        map_label_rect = map_label.get_rect(
            center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 - 50),
        )
        self.screen.blit(map_label, map_label_rect)

        for btn, _ in self.map_size_buttons:
            btn.draw(self.screen, self.tiny_font)

        instructions = [
            "Fight waves of enemy monsters!",
            "Each level, enemies get stronger",
            "",
            "WASD: Move | Shift: Sprint | Mouse: Look | 1-4: Weapons | Right: Shoot",
        ]

        y = C.SCREEN_HEIGHT // 2 + 130
        for line in instructions:
            text = self.tiny_font.render(line, True, C.CYAN)
            text_rect = text.get_rect(center=(C.SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 30

        self.start_button.draw(self.screen, self.font)

        pygame.display.flip()

    def render_game(self) -> None:
        """Render gameplay"""
        assert self.raycaster is not None
        assert self.player is not None

        # Pass player angle for parallax stars
        self.raycaster.render_floor_ceiling(self.screen, self.player.angle)
        self.raycaster.render_3d(self.screen, self.player, self.bots)

        # Render projectiles via raycaster
        self.raycaster.render_projectiles(self.screen, self.player, self.projectiles)

        # Render particles
        for p in self.particles:
            alpha = int(255 * (p["timer"] / C.PARTICLE_LIFETIME))
            surf = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p["color"], alpha), (p["size"], p["size"]), p["size"])
            self.screen.blit(surf, (p["x"] - p["size"], p["y"] - p["size"]))

        # Render damage texts
        for t in self.damage_texts:
            surf = self.title_font.render(t["text"], True, t["color"])  # Use larger font for impact
            # Scale down slightly based on distance look
            scale = 0.5
            w = int(surf.get_width() * scale)
            h = int(surf.get_height() * scale)
            scaled_surf = pygame.transform.scale(surf, (w, h))
            self.screen.blit(scaled_surf, (t["x"] - w // 2, t["y"] - h // 2))

        self.render_rifle()
        self.raycaster.render_minimap(self.screen, self.player, self.bots)
        self.render_hud()

        # Shield effect
        if self.player.shield_active:
            overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((*C.SHIELD_COLOR, C.SHIELD_ALPHA))  # Semi-transparent cyan overlay
            # Add hexagon pattern or grid? Simple border for now
            pygame.draw.rect(overlay, C.SHIELD_COLOR, (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT), 10)
            self.screen.blit(overlay, (0, 0))

            shield_text = self.title_font.render("SHIELD ACTIVE", True, C.SHIELD_COLOR)
            self.screen.blit(shield_text, (C.SCREEN_WIDTH // 2 - shield_text.get_width() // 2, 100))

        self.render_crosshair()

        if self.player.shooting:
            self.render_muzzle_flash()

        # Pause Menu
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

    def render_rifle(self) -> None:
        """Render rifle weapon in first-person view"""
        rifle_color = C.DARK_BROWN
        barrel_color = (30, 30, 30)
        rifle_x = C.SCREEN_WIDTH - 250
        rifle_y = C.SCREEN_HEIGHT - 200

        pygame.draw.rect(self.screen, rifle_color, (rifle_x + 150, rifle_y + 120, 80, 40))
        pygame.draw.rect(self.screen, rifle_color, (rifle_x + 80, rifle_y + 100, 120, 30))
        pygame.draw.rect(self.screen, barrel_color, (rifle_x, rifle_y + 105, 120, 20))
        pygame.draw.rect(self.screen, C.BLACK, (rifle_x + 10, rifle_y + 95, 5, 15))
        pygame.draw.rect(self.screen, C.BLACK, (rifle_x + 110, rifle_y + 125, 30, 50))
        pygame.draw.rect(self.screen, barrel_color, (rifle_x + 140, rifle_y + 125, 15, 25))

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
        pygame.draw.rect(self.screen, C.WHITE, (health_x, health_y, health_width, health_height), 2)
        health_text = self.tiny_font.render(f"HP: {self.player.health}", True, C.WHITE)
        self.screen.blit(health_text, (health_x + 5, health_y + 3))

        weapon_x = C.SCREEN_WIDTH // 2 - 100
        weapon_y = hud_bottom
        weapon_width = 200
        weapon_height = 70

        pygame.draw.rect(
            self.screen, C.DARK_GRAY, (weapon_x, weapon_y, weapon_width, weapon_height)
        )
        pygame.draw.rect(self.screen, C.WHITE, (weapon_x, weapon_y, weapon_width, weapon_height), 2)

        current_weapon_data: Dict[str, Any] = C.WEAPONS[self.player.current_weapon]
        weapon_name = self.small_font.render(str(current_weapon_data["name"]), True, C.YELLOW)
        weapon_name_rect = weapon_name.get_rect(
            center=(weapon_x + weapon_width // 2, weapon_y + 15),
        )
        self.screen.blit(weapon_name, weapon_name_rect)

        ammo_text = self.tiny_font.render(
            f"Ammo: {self.player.ammo[self.player.current_weapon]}",
            True,
            C.CYAN,
        )
        ammo_rect = ammo_text.get_rect(
            center=(weapon_x + weapon_width // 2, weapon_y + 40),
        )
        self.screen.blit(ammo_text, ammo_rect)

        hints_text = self.tiny_font.render(self.weapon_hints, True, C.GRAY)
        hints_rect = hints_text.get_rect(
            center=(weapon_x + weapon_width // 2, weapon_y + 58),
        )
        self.screen.blit(hints_text, hints_rect)

        level_text = self.small_font.render(f"Level: {self.level}", True, C.YELLOW)
        self.screen.blit(level_text, (C.SCREEN_WIDTH - 200, hud_bottom))

        bots_alive = sum(1 for bot in self.bots if bot.alive)
        total_enemies = (4 + (self.level - 1)) * 3
        kills_text = self.small_font.render(f"Enemies: {bots_alive}/{total_enemies}", True, C.RED)
        self.screen.blit(kills_text, (C.SCREEN_WIDTH - 200, hud_bottom + 30))

        controls_hint_text = "WASD:Move | Shift:Sprint | ESC:Menu"
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
        flash_x = C.SCREEN_WIDTH - 350
        flash_y = C.SCREEN_HEIGHT - 85

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
        while self.running:
            if self.state == "intro":
                self.handle_intro_events()
                self.render_intro()
            elif self.state == "menu":
                self.handle_menu_events()
                self.render_menu()
            elif self.state == "playing":
                self.handle_game_events()
                self.update_game()
                self.render_game()
            elif self.state == "level_complete":
                self.render_level_complete()
            elif self.state == "game_over":
                self.render_game_over()

            self.clock.tick(C.FPS)

    def handle_intro_events(self) -> None:
        """Handle intro screen events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                    self.state = "menu"

    def render_intro(self) -> None:
        """Render Max Payne style graphic novel intro"""
        self.screen.fill(C.BLACK)
        current_time = pygame.time.get_ticks()

        if self.intro_start_time == 0:
            self.intro_start_time = current_time

        elapsed = current_time - self.intro_start_time

        # Intro slides
        slides = [
            ("FROM THE DEMENTED MIND", "OF JASPER", 3000),
            ("THEY TOOK MY TOYS", "NOW I TAKE THEIR LIVES", 4000),
            ("FORCE FIELD", "THE ARENA AWAITS", 4000),
        ]

        if self.intro_step < len(slides):
            line1, line2, duration = slides[self.intro_step]

            # Fade in/out logic
            alpha = min(
                C.INTRO_FADE_MAX,
                max(
                    0,
                    C.INTRO_FADE_MAX
                    - abs(elapsed - duration / 2) * (C.INTRO_FADE_SCALE / duration),
                ),
            )

            line1_surf = self.title_font.render(line1, True, (255, 255, 255))
            line2_surf = self.subtitle_font.render(line2, True, (255, 0, 0))  # Subtitle line in red

            # Apply alpha approx (by set_alpha on blit or color) - simplistic here:
            line1_surf.set_alpha(int(alpha))
            line2_surf.set_alpha(int(alpha))

            rect1 = line1_surf.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 - 40))
            rect2 = line2_surf.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 40))

            self.screen.blit(line1_surf, rect1)
            self.screen.blit(line2_surf, rect2)

            if elapsed > duration:
                self.intro_step += 1
                self.intro_start_time = 0  # Reset for next slide
        else:
            self.state = "menu"

        pygame.display.flip()
