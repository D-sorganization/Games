from __future__ import annotations

import logging
import random
from typing import Any

import pygame

from games.shared.config import RaycasterConfig
from games.shared.constants import (
    PICKUP_RADIUS_SQ,
    PORTAL_RADIUS_SQ,
    GameState,
)
from games.shared.event_bus import EventBus
from games.shared.fps_game_base import FPSGameBase
from games.shared.interfaces import Portal
from games.shared.raycaster import Raycaster
from games.shared.sound_manager_base import SoundManagerBase

from . import constants as C  # noqa: N812
from .atmosphere_manager import AtmosphereManager
from .combat_manager import ZSCombatManager
from .entity_manager import EntityManager
from .input_manager import InputManager
from .map import Map
from .particle_system import ParticleSystem
from .player import Player
from .projectile import Projectile
from .renderer import GameRenderer
from .screen_event_handler import ScreenEventHandler
from .sound import SoundManager
from .spawn_manager import ZSSpawnManager
from .ui_renderer import UIRenderer
from .weapon_system import WeaponSystem

logger = logging.getLogger(__name__)


class Game(FPSGameBase):
    """Main game class — orchestrates subsystems for Zombie Survival."""

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
        self.health = C.PLAYER_HEALTH
        self.lives = C.DEFAULT_LIVES

        # Unlocked weapons tracking - start with basic weapons
        self.unlocked_weapons = {"pistol", "rifle"}
        self.cheat_mode_active = False
        self.current_cheat_input = ""
        self.god_mode = False

        self.game_over_timer = 0

        # Audio (must be initialized before managers that depend on it)
        self.sound_manager = (
            sound_manager if sound_manager is not None else SoundManager()
        )
        self.sound_manager.start_music()

        # Event Bus -- lightweight pub/sub for decoupling subsystems
        self.event_bus = EventBus()
        self._wire_event_bus()

        # Managers (decomposed from Game god object -- constructor injection)
        self.spawn_manager = ZSSpawnManager(self.entity_manager)
        self.combat_manager = ZSCombatManager(
            self.entity_manager,
            self.particle_system,
            self.sound_manager,
            on_kill=lambda bot: self.event_bus.emit("bot_killed", x=bot.x, y=bot.y),
        )

        # Subsystem helpers (extracted to keep Game within size budget)
        self.weapon_system = WeaponSystem(self)
        self.atmosphere_manager = AtmosphereManager(self)
        self.screen_event_handler = ScreenEventHandler(self)

        # Input
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            try:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                logger.info("Controller detected: %s", self.joystick.get_name())
            except Exception:  # noqa: BLE001
                logger.exception("Controller init failed")

        # Fog of War
        self.visited_cells: set[tuple[int, int]] = set()
        self.show_minimap = True

        # Input Manager
        self.input_manager = InputManager()
        self.binding_action: str | None = None

    # --- Law of Demeter (LOD) Flattened Properties ---
    @property
    def player_x(self) -> float:
        return self.player.x if self.player else 0.0

    @property
    def player_y(self) -> float:
        return self.player.y if self.player else 0.0

    @property
    def player_angle(self) -> float:
        return self.player.angle if self.player else 0.0

    @property
    def player_health(self) -> int:
        return self.player.health if self.player else 0

    @player_health.setter
    def player_health(self, value: int) -> None:
        if self.player:
            self.player.health = value

    @property
    def player_alive(self) -> bool:
        return self.player.alive if self.player else False

    @property
    def player_is_moving(self) -> bool:
        return self.player.is_moving if self.player else False

    @player_is_moving.setter
    def player_is_moving(self, value: bool) -> None:
        if self.player:
            self.player.is_moving = value

    @property
    def player_current_weapon(self) -> str:
        return self.player.current_weapon if self.player else "pistol"

    @player_current_weapon.setter
    def player_current_weapon(self, value: str) -> None:
        if self.player:
            self.player.current_weapon = value

    @property
    def player_stamina(self) -> float:
        return self.player.stamina if self.player else 0.0

    @player_stamina.setter
    def player_stamina(self, value: float) -> None:
        if self.player:
            self.player.stamina = value

    @property
    def player_bombs(self) -> int:
        return self.player.bombs if self.player else 0

    @player_bombs.setter
    def player_bombs(self, value: int) -> None:
        if self.player:
            self.player.bombs = value

    # ------------------------------------------------

    def _wire_event_bus(self) -> None:
        """Subscribe subsystems to game events via the event bus."""
        self.event_bus.subscribe(
            "bot_killed",
            lambda **kw: self.sound_manager.play_sound("scream"),
        )

    def _sync_combat_state(self) -> None:
        """Synchronize kill/combo state from the combat manager back to Game."""
        self.kills = self.kills
        self.kill_combo_count = self.kill_combo_count
        self.kill_combo_timer = self.kill_combo_timer
        self.last_death_pos = self.last_death_pos

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

        # Reset combat manager state
        self.kills = 0
        self.kill_combo_count = 0
        self.kill_combo_timer = 0
        self.last_death_pos = None

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
                self.player_current_weapon = previous_weapon
            else:
                self.player_current_weapon = "pistol"
        # Validate current weapon is unlocked
        # (e.g. Player init sets 'rifle' but it might be locked)
        if self.player_current_weapon not in self.unlocked_weapons:
            self.player_current_weapon = "pistol"

        # Propagate God Mode state
        self.player.god_mode = self.god_mode

        # Delegate spawning to SpawnManager
        self.entity_manager.reset()
        self.spawn_manager.spawn_all(
            player_pos, self.game_map, self.level, self.selected_difficulty
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

    # _handle_cheat_input, _handle_pause_toggle, _handle_weapon_keys,
    # _handle_pause_menu_click, _handle_gameplay_mouse_click,
    # handle_game_events, and save_game are inherited from FPSGameBase.

    # ------------------------------------------------------------------
    # Weapon firing — delegated to WeaponSystem
    # ------------------------------------------------------------------

    def fire_weapon(self, is_secondary: bool = False) -> None:
        """Handle weapon firing via data-driven dispatch."""
        self.weapon_system.fire_weapon(is_secondary=is_secondary)

    def check_shot_hit(
        self,
        is_secondary: bool = False,
        angle_offset: float = 0.0,
        is_laser: bool = False,
    ) -> None:
        """Delegate hitscan hit detection to the combat manager."""
        self.weapon_system.check_shot_hit(
            is_secondary=is_secondary,
            angle_offset=angle_offset,
            is_laser=is_laser,
        )

    def handle_bomb_explosion(self) -> None:
        """Delegate bomb explosion to the combat manager."""
        self.weapon_system.handle_bomb_explosion()

    def explode_laser(self, impact_x: float, impact_y: float) -> None:
        """Delegate laser explosion to the combat manager."""
        self.weapon_system.explode_laser(impact_x, impact_y)

    def explode_plasma(self, projectile: Projectile) -> None:
        """Delegate plasma explosion to the combat manager."""
        self.weapon_system.explode_plasma(projectile)

    def explode_rocket(self, projectile: Projectile) -> None:
        """Delegate rocket explosion to the combat manager."""
        self.weapon_system.explode_rocket(projectile)

    # ------------------------------------------------------------------
    # Game update helpers
    # ------------------------------------------------------------------

    def _check_game_over(self) -> bool:
        """Check if the player is dead and handle lives/game-over transitions.

        Returns True when the caller should stop further update processing.
        """
        if not self.player_alive:
            if self.lives > 1:
                self.lives -= 1
                self.respawn_player()
                return True
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
            return True
        return False

    def _check_portal_completion(self) -> bool:
        """Spawn portal when all enemies are dead; transition on portal entry.

        Returns True when the caller should stop further update processing.
        """
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
            dx = self.portal["x"] - self.player_x
            dy = self.portal["y"] - self.player_y
            dist_sq = dx * dx + dy * dy
            if dist_sq < PORTAL_RADIUS_SQ:
                paused = self.total_paused_time
                now = pygame.time.get_ticks()
                level_time = (now - self.level_start_time - paused) / 1000.0
                self.level_times.append(level_time)
                self.state = GameState.LEVEL_COMPLETE
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)
                return True
        return False

    def _handle_joystick_input(self, shield_active: bool) -> bool:
        """Process joystick axes and buttons; returns updated shield_active."""
        assert self.player is not None
        assert self.game_map is not None
        axis_x = self.joystick.get_axis(0)
        axis_y = self.joystick.get_axis(1)

        if abs(axis_x) > C.JOYSTICK_DEADZONE:
            self.player.strafe(
                self.game_map,
                self.bots,
                right=(axis_x > 0),
                speed=abs(axis_x) * C.PLAYER_SPEED,
            )
            self.player_is_moving = True
        if abs(axis_y) > C.JOYSTICK_DEADZONE:
            self.player.move(
                self.game_map,
                self.bots,
                forward=(axis_y < 0),
                speed=abs(axis_y) * C.PLAYER_SPEED,
            )
            self.player_is_moving = True

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

        return shield_active

    def _update_damage_texts(self) -> None:
        """Tick floating damage text positions and remove expired entries."""
        for t in self.damage_texts:
            t["y"] += t["vy"]
            t["timer"] -= 1
        self.damage_texts = [t for t in self.damage_texts if t["timer"] > 0]

    def _handle_keyboard_movement(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Apply keyboard-driven player movement and camera rotation."""
        assert self.player is not None
        assert self.game_map is not None
        sprint_key = keys[pygame.K_RSHIFT]
        is_sprinting = self.input_manager.is_action_pressed("sprint") or sprint_key
        if is_sprinting and self.player_stamina > 0:
            current_speed = C.PLAYER_SPRINT_SPEED
            self.player_stamina -= 1
            self.player_stamina_recharge_delay = 60
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

        self.player_is_moving = moving

        if self.input_manager.is_action_pressed("turn_left"):
            self.player.rotate(-0.05)
        if self.input_manager.is_action_pressed("turn_right"):
            self.player.rotate(0.05)
        if self.input_manager.is_action_pressed("look_up"):
            self.player.pitch_view(5)
        if self.input_manager.is_action_pressed("look_down"):
            self.player.pitch_view(-5)

    def _check_item_pickups(self) -> None:
        """Detect player proximity to pickup items and apply their effects."""
        assert self.player is not None
        for bot in self.bots:
            is_item = bot.enemy_type.startswith(("health", "ammo", "bomb", "pickup"))
            if not (bot.alive and is_item):
                continue
            dx = bot.x - self.player_x
            dy = bot.y - self.player_y
            if dx * dx + dy * dy >= PICKUP_RADIUS_SQ:
                continue

            pickup_msg = ""
            color = C.GREEN
            if bot.enemy_type == "health_pack":
                if self.player_health < 100:
                    self.player_health = min(100, self.player_health + 50)
                    pickup_msg = "HEALTH +50"
            elif bot.enemy_type == "ammo_box":
                for w in self.player.ammo:
                    self.player.ammo[w] += 20
                pickup_msg = "AMMO FOUND"
                color = C.YELLOW
            elif bot.enemy_type == "bomb_item":
                self.player_bombs += 1
                pickup_msg = "BOMB +1"
                color = C.ORANGE
            elif bot.enemy_type.startswith("pickup_"):
                w_name = bot.enemy_type.replace("pickup_", "")
                if w_name not in self.unlocked_weapons:
                    self.unlocked_weapons.add(w_name)
                    self.player.switch_weapon(w_name)
                    pickup_msg = f"{w_name.upper()} ACQUIRED!"
                    color = C.CYAN
                elif w_name in self.player.ammo:
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

    def update_game(self) -> None:
        """Update game state"""
        if self.paused:
            return

        assert self.player is not None
        assert self.game_map is not None
        if self._check_game_over():
            return
        if self._check_portal_completion():
            return

        keys = pygame.key.get_pressed()
        shield_active = self.input_manager.is_action_pressed("shield")

        if self.joystick and self.player_alive:
            shield_active = self._handle_joystick_input(shield_active)

        self.player.set_shield(shield_active)
        self.particle_system.update()
        self._update_damage_texts()
        self._handle_keyboard_movement(keys)
        self.player.update()

        self.entity_manager.update_bots(self.game_map, self.player, self)
        self._check_item_pickups()
        self.entity_manager.update_projectiles(self.game_map, self.player, self)

        self.atmosphere_manager.update_fog_reveal()
        self.atmosphere_manager.update_atmosphere()
        self.atmosphere_manager.check_kill_combo()

    # ------------------------------------------------------------------
    # Screen event handlers — delegated to ScreenEventHandler
    # ------------------------------------------------------------------

    def handle_intro_events(self) -> None:
        """Handle intro screen events"""
        self.screen_event_handler.handle_intro_events()

    def handle_menu_events(self) -> None:
        """Handle main menu events"""
        self.screen_event_handler.handle_menu_events()

    def handle_map_select_events(self) -> None:
        """Handle map selection events"""
        self.screen_event_handler.handle_map_select_events()

    def handle_level_complete_events(self) -> None:
        """Handle input events during the level complete screen."""
        self.screen_event_handler.handle_level_complete_events()

    def handle_game_over_events(self) -> None:
        """Handle input events during the game over screen."""
        self.screen_event_handler.handle_game_over_events()

    def handle_key_config_events(self) -> None:
        """Handle input events in Key Config menu."""
        self.screen_event_handler.handle_key_config_events()

    def _update_intro_logic(self, elapsed: int) -> None:
        """Update intro sequence logic and transitions."""
        self.screen_event_handler.update_intro_logic(elapsed)

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
                    self.screen_event_handler.handle_playing_state()

                elif self.state == GameState.LEVEL_COMPLETE:
                    self.handle_level_complete_events()
                    self.ui_renderer.render_level_complete(self)

                elif self.state == GameState.GAME_OVER:
                    self.handle_game_over_events()
                    self.ui_renderer.render_game_over(self)

                self.clock.tick(C.FPS)
        except Exception as e:  # noqa: BLE001
            logger.critical("CRASH: %s", e, exc_info=True)
            raise
