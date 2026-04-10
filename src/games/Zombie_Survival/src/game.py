from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import pygame

from games.shared.constants import GameState
from games.shared.event_bus import EventBus
from games.shared.fps_game_base import FPSGameBase
from games.shared.interfaces import Portal
from games.shared.raycaster import Raycaster
from games.shared.sound_manager_base import SoundManagerBase

from . import constants as C  # noqa: N812
from . import game_loop, gameplay_updater, progression_flow
from .atmosphere_manager import AtmosphereManager
from .combat_manager import ZSCombatManager
from .entity_manager import EntityManager
from .input_manager import InputManager
from .particle_system import ParticleSystem
from .projectile import Projectile
from .renderer import GameRenderer
from .screen_event_handler import ScreenEventHandler
from .sound import SoundManager
from .spawn_manager import ZSSpawnManager
from .ui_renderer import UIRenderer
from .weapon_system import WeaponSystem

if TYPE_CHECKING:
    from .map import Map
    from .player import Player

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
            except (pygame.error, OSError):
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
        """Player world X position, or 0.0 if no player exists."""
        return self.player.x if self.player else 0.0

    @property
    def player_y(self) -> float:
        """Player world Y position, or 0.0 if no player exists."""
        return self.player.y if self.player else 0.0

    @property
    def player_angle(self) -> float:
        """Player facing angle in radians, or 0.0 if no player exists."""
        return self.player.angle if self.player else 0.0

    @property
    def player_health(self) -> int:
        """Current player health points, or 0 if no player exists."""
        return self.player.health if self.player else 0

    @player_health.setter
    def player_health(self, value: int) -> None:
        """Set player health, no-op if no player exists."""
        if self.player:
            self.player.health = value

    @property
    def player_alive(self) -> bool:
        """True if the player is alive, False if dead or absent."""
        return self.player.alive if self.player else False

    @property
    def player_is_moving(self) -> bool:
        """True if the player is currently in motion."""
        return self.player.is_moving if self.player else False

    @player_is_moving.setter
    def player_is_moving(self, value: bool) -> None:
        """Set the player movement flag, no-op if no player exists."""
        if self.player:
            self.player.is_moving = value

    @property
    def player_current_weapon(self) -> str:
        """Name of the player's currently equipped weapon."""
        return self.player.current_weapon if self.player else "pistol"

    @player_current_weapon.setter
    def player_current_weapon(self, value: str) -> None:
        """Switch the player's active weapon, no-op if no player exists."""
        if self.player:
            self.player.current_weapon = value

    @property
    def player_stamina(self) -> float:
        """Player stamina level (0.0–1.0), or 0.0 if no player exists."""
        return self.player.stamina if self.player else 0.0

    @player_stamina.setter
    def player_stamina(self, value: float) -> None:
        """Set player stamina, no-op if no player exists."""
        if self.player:
            self.player.stamina = value

    @property
    def player_bombs(self) -> int:
        """Number of bombs the player is carrying, or 0 if no player exists."""
        return self.player.bombs if self.player else 0

    @player_bombs.setter
    def player_bombs(self, value: int) -> None:
        """Set player bomb count, no-op if no player exists."""
        if self.player:
            self.player.bombs = value

    # ------------------------------------------------

    def _wire_event_bus(self) -> None:
        """Subscribe subsystems to game events via the event bus."""
        self.event_bus.subscribe(
            "bot_killed",
            lambda **kw: self.sound_manager.play_sound("scream"),
        )

    def sync_combat_state(self) -> None:
        """Synchronize kill/combo state from the combat manager back to Game."""
        self.kills = self.kills
        self.kill_combo_count = self.kill_combo_count
        self.kill_combo_timer = self.kill_combo_timer
        self.last_death_pos = self.last_death_pos

    def start_game(self) -> None:
        """Start new game"""
        progression_flow.start_game(self)

    def start_level(self) -> None:
        """Start a new level"""
        progression_flow.start_level(self)

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
        return progression_flow.check_game_over(self)

    def _check_portal_completion(self) -> bool:
        """Spawn portal when all enemies are dead; transition on portal entry.

        Returns True when the caller should stop further update processing.
        """
        return progression_flow.check_portal_completion(self)

    def _handle_joystick_input(self, shield_active: bool) -> bool:
        """Process joystick axes and buttons; returns updated shield_active."""
        if not (self.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        if not (self.game_map is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
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

    def update_game(self) -> None:
        """Update game state through the extracted gameplay updater."""
        gameplay_updater.update_game(self)

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
        """Main game loop."""
        game_loop.run(self)
