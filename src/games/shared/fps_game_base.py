"""Base class for FPS raycaster games (Duum, Force_Field, Zombie_Survival).

Consolidates identical methods shared across FPS games to eliminate
code duplication. Each game subclass passes its own constants module
via __init__ and overrides game-specific behavior.

Usage:
    from games.shared.fps_game_base import FPSGameBase
    from . import constants as C

    class Game(FPSGameBase):
        def __init__(self):
            super().__init__(C)
            # game-specific init...
"""

from __future__ import annotations

import logging
import math
import random
from collections.abc import Callable
from typing import Any

import pygame

from games.shared.constants import GameState
from games.shared.event_bus import EventBus
from games.shared.sound_manager_base import SoundManagerBase

logger = logging.getLogger(__name__)


class FPSGameBase:
    """Base class for FPS raycaster games.

    Subclasses must set up the following attributes before calling
    any base methods:
        - self.C: constants module
        - self.render_scale: int
        - self.raycaster: Raycaster | None
        - self.damage_texts: list[dict]
        - self.unlocked_weapons: set[str]
        - self.player: Player | None
        - self.game_map: Map | None
        - self.selected_map_size: int
        - self.portal: dict | None
        - self.last_death_pos: tuple | None
        - self.entity_manager: EntityManager
        - self.running: bool
        - self.state: GameState
        - self.paused: bool
        - self.pause_start_time: int
        - self.total_paused_time: int
        - self.cheat_mode_active: bool
        - self.current_cheat_input: str
        - self.god_mode: bool
        - self.input_manager: InputManager
        - self.binding_action: str | None
        - self.sound_manager: SoundManager
        - self.show_minimap: bool
        - self.show_damage: bool
    """

    C: Any
    render_scale: int
    raycaster: Any
    damage_texts: list[dict[str, Any]]
    unlocked_weapons: set[str]
    player: Any
    game_map: Any
    selected_map_size: int
    portal: dict[str, Any] | None
    last_death_pos: tuple[float, float] | None
    entity_manager: Any
    running: bool
    state: Any  # GameState
    paused: bool
    pause_start_time: int
    total_paused_time: int
    cheat_mode_active: bool
    current_cheat_input: str
    god_mode: bool
    input_manager: Any
    binding_action: str | None
    sound_manager: Any
    show_minimap: bool
    show_damage: bool

    # --- Properties ---

    @property
    def bots(self) -> list[Any]:
        """Get list of active bots."""
        return self.entity_manager.bots

    @property
    def projectiles(self) -> list[Any]:
        """Get list of active projectiles."""
        return self.entity_manager.projectiles

    def init_fps_game(
        self,
        C: Any,
        *,
        caption: str,
        sound_manager: SoundManagerBase | None,
        input_manager: Any,
        entity_manager: Any,
        particle_system: Any,
        unlocked_weapons: set[str],
        render_cls: Any,
        ui_render_cls: Any,
        sound_manager_factory: Callable[[], SoundManagerBase],
    ) -> None:
        """Initialize common FPS game state shared across all FPS variants."""
        self.C = C
        self._init_display(C, caption, render_cls, ui_render_cls)
        self._init_game_state(C)
        self._init_gameplay_state(C)
        self._init_atmosphere_state()
        self._init_visual_effects(particle_system)
        self._init_game_objects(C, entity_manager)
        self._init_player_options(C, unlocked_weapons)
        self._init_sound(sound_manager, sound_manager_factory)
        self._init_input_and_fog(input_manager)

    def _init_display(
        self, C: Any, caption: str, render_cls: Any, ui_render_cls: Any
    ) -> None:
        """Set up the pygame window, clock, and renderer objects."""
        flags = pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), flags)
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()
        self.running = True
        self.renderer = render_cls(self.screen)
        self.ui_renderer = ui_render_cls(self.screen)

    def _init_game_state(self, C: Any) -> None:
        """Initialize intro / game-flow state variables."""
        self.state = GameState.INTRO
        self.intro_phase = 0
        self.intro_step = 0
        self.intro_timer = 0
        self.intro_start_time = 0
        self.last_death_pos = None

    def _init_gameplay_state(self, C: Any) -> None:
        """Initialize level, score, and difficulty settings."""
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

    def _init_atmosphere_state(self) -> None:
        """Initialize combo-tracking and ambient audio timers."""
        self.kill_combo_count = 0
        self.kill_combo_timer = 0
        self.heartbeat_timer = 0
        self.breath_timer = 0
        self.groan_timer = 0
        self.beast_timer = 0

    def _init_visual_effects(self, particle_system: Any) -> None:
        """Initialize particle system and damage-text/flash state."""
        self.particle_system = particle_system
        self.damage_texts: list[dict[str, Any]] = []
        self.damage_flash_timer = 0

    def _init_game_objects(self, C: Any, entity_manager: Any) -> None:
        """Initialize map, player, raycaster and entity-manager references."""
        self.game_map = None
        self.player = None
        self.entity_manager = entity_manager
        self.raycaster = None
        self.portal = None
        self.health = C.PLAYER_HEALTH
        self.lives = C.DEFAULT_LIVES

    def _init_player_options(self, C: Any, unlocked_weapons: set[str]) -> None:
        """Initialize cheat/god-mode flags and unlocked weapon set."""
        self.unlocked_weapons = unlocked_weapons
        self.cheat_mode_active = False
        self.current_cheat_input = ""
        self.god_mode = False
        self.game_over_timer = 0

    def _init_sound(
        self,
        sound_manager: SoundManagerBase | None,
        sound_manager_factory: Callable[[], SoundManagerBase],
    ) -> None:
        """Initialize sound manager and event bus."""
        self.sound_manager = (
            sound_manager if sound_manager is not None else sound_manager_factory()
        )
        self.sound_manager.start_music()
        self.event_bus = EventBus()
        self._wire_event_bus()

    def _init_input_and_fog(self, input_manager: Any) -> None:
        """Initialize joystick, fog-of-war state, and input manager."""
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            try:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                logger.info("Controller detected: %s", self.joystick.get_name())
            except (pygame.error, OSError):
                logger.exception("Controller init failed")
        self.visited_cells: set[tuple[int, int]] = set()
        self.show_minimap = True
        self.input_manager = input_manager
        self.binding_action = None

    # --- Identical methods extracted from all 3 FPS games ---

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
        self.add_message(msg, self.C.WHITE)

    def add_message(self, text: str, color: tuple[int, int, int]) -> None:
        """Add a temporary message to the center of the screen."""
        self.damage_texts.append(
            {
                "x": self.C.SCREEN_WIDTH // 2,
                "y": self.C.SCREEN_HEIGHT // 2 - 50,
                "text": text,
                "color": color,
                "timer": 60,
                "vy": -0.5,
            }
        )

    def switch_weapon_with_message(self, weapon_name: str) -> None:
        """Switch weapon and show a message if successful."""
        if weapon_name not in self.unlocked_weapons:
            self.add_message("WEAPON LOCKED", self.C.RED)
            return

        if not (self.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        if self.player.current_weapon != weapon_name:
            self.player.switch_weapon(weapon_name)
            self.add_message(f"SWITCHED TO {weapon_name.upper()}", self.C.YELLOW)

    def spawn_portal(self) -> None:
        """Spawn exit portal at last death position or near player."""
        if self.last_death_pos:
            self.portal = {
                "x": self.last_death_pos[0],
                "y": self.last_death_pos[1],
            }
            return

        if not (self.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
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
        """Find a safe spawn position near the base coordinates."""
        game_map = self.game_map
        map_size = game_map.size if game_map else self.selected_map_size
        if not game_map:
            return (base_x, base_y, angle)

        for attempt in range(10):
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

                in_x = test_x >= 2 and test_x < map_size - 2
                in_y = test_y >= 2 and test_y < map_size - 2
                if not (in_x and in_y):
                    continue

                if not game_map.is_wall(test_x, test_y):
                    return (test_x, test_y, angle)

        return (base_x, base_y, angle)

    def get_corner_positions(self) -> list[tuple[float, float, float]]:
        """Get spawn positions for four corners (x, y, angle)."""
        offset = 5
        map_size = self.game_map.size if self.game_map else self.selected_map_size

        building4_start = int(map_size * 0.75)
        bottom_right_offset = map_size - building4_start + self.C.SPAWN_SAFETY_MARGIN

        corners = [
            (offset, offset, math.pi / 4),
            (offset, map_size - offset, 7 * math.pi / 4),
            (map_size - offset, offset, 3 * math.pi / 4),
            (
                map_size - bottom_right_offset,
                map_size - bottom_right_offset,
                5 * math.pi / 4,
            ),
        ]

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
            return self.C.DEFAULT_PLAYER_SPAWN

        for pos in corners:
            if not game_map.is_wall(pos[0], pos[1]):
                return pos

        for y in range(game_map.height):
            for x in range(game_map.width):
                if not game_map.is_wall(x, y):
                    return (x + 0.5, y + 0.5, 0.0)

        return self.C.DEFAULT_PLAYER_SPAWN

    def respawn_player(self) -> None:
        """Respawn player after death if lives remain."""
        if not (self.game_map is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        if not (self.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")

        player_pos = self._get_best_spawn_point()

        self.player.x = player_pos[0]
        self.player.y = player_pos[1]
        self.player.angle = player_pos[2]
        self.player.health = 100
        self.player.alive = True
        self.player.shield_active = False

        self.damage_texts.append(
            {
                "x": self.C.SCREEN_WIDTH // 2,
                "y": self.C.SCREEN_HEIGHT // 2,
                "text": "RESPAWNED",
                "color": self.C.GREEN,
                "timer": 120,
                "vy": -0.5,
            }
        )

    # --- Shared event-handling methods (identical across all 3 FPS games) ---

    def _handle_cheat_input(self, event: pygame.event.Event) -> bool:
        """Handle keyboard input while cheat mode is active.

        Returns True to signal the caller should ``continue`` to the next event.
        """
        if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.cheat_mode_active = False
            self.add_message("CHEAT INPUT CLOSED", self.C.GRAY)
        elif event.key == pygame.K_BACKSPACE:
            self.current_cheat_input = self.current_cheat_input[:-1]
        else:
            self.current_cheat_input += event.unicode
            code = self.current_cheat_input.upper()
            if code.endswith("IDFA"):
                self.unlocked_weapons = set(self.C.WEAPONS.keys())
                if self.player:
                    for w in self.player.ammo:
                        self.player.ammo[w] = self.C.CHEAT_AMMO_AMOUNT
                self.add_message("ALL WEAPONS UNLOCKED", self.C.YELLOW)
                self.current_cheat_input = ""
                self.cheat_mode_active = False
            elif code.endswith("IDDQD"):
                self.god_mode = not self.god_mode
                msg = "GOD MODE ON" if self.god_mode else "GOD MODE OFF"
                self.add_message(msg, self.C.YELLOW)
                if self.player:
                    self.player.health = self.C.PLAYER_HEALTH
                    self.player.god_mode = self.god_mode
                self.current_cheat_input = ""
                self.cheat_mode_active = False
        return True  # caller should continue

    def _handle_pause_toggle(self, event: pygame.event.Event) -> None:
        """Toggle pause state and update timers/mouse grab accordingly."""
        self.paused = not self.paused
        if self.paused:
            self.pause_start_time = pygame.time.get_ticks()
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
        else:
            if self.pause_start_time > 0:
                now = pygame.time.get_ticks()
                self.total_paused_time += now - self.pause_start_time
                self.pause_start_time = 0
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)

    def _handle_weapon_keys(self, event: pygame.event.Event) -> None:
        """Handle weapon-switch, reload, zoom, bomb and shoot key presses."""
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
            if not (self.player is not None):
                raise ValueError("DbC Blocked: Precondition failed.")
            self.player.reload()
        elif self.input_manager.is_action_just_pressed(event, "zoom"):
            if not (self.player is not None):
                raise ValueError("DbC Blocked: Precondition failed.")
            self.player.zoomed = not self.player.zoomed
        elif self.input_manager.is_action_just_pressed(event, "bomb"):
            if not (self.player is not None):
                raise ValueError("DbC Blocked: Precondition failed.")
            if self.player.activate_bomb():
                self.handle_bomb_explosion()
        elif self.input_manager.is_action_just_pressed(event, "shoot_alt"):
            if not (self.player is not None):
                raise ValueError("DbC Blocked: Precondition failed.")
            if self.player.shoot():
                self.fire_weapon()
        elif event.key == pygame.K_m:
            self.show_minimap = not self.show_minimap
        elif event.key == pygame.K_F9:
            self.cycle_render_scale()

    def _handle_pause_menu_click(self, mx: int, my: int) -> None:
        """Process a mouse click inside the pause menu."""
        if 500 <= mx <= 700:
            if 350 <= my <= 400:  # Resume
                self.paused = False
                if self.pause_start_time > 0:
                    now = pygame.time.get_ticks()
                    self.total_paused_time += now - self.pause_start_time
                    self.pause_start_time = 0
                pygame.mouse.set_visible(False)
                pygame.event.set_grab(True)
            elif 410 <= my <= 460:  # Save
                self.save_game()
                self.add_message("GAME SAVED", self.C.GREEN)
            elif 470 <= my <= 520:  # Controls
                self.state = GameState.KEY_CONFIG
                self.binding_action = None
            elif 530 <= my <= 580:  # Quit to Menu
                self.state = GameState.MENU
                self.paused = False
                self.sound_manager.start_music("music_loop")

    def _handle_gameplay_mouse_click(self, event: pygame.event.Event) -> None:
        """Process a mouse button click during active gameplay (not paused)."""
        if not (self.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        if event.button == 1:
            if self.player.shoot():
                self.fire_weapon()
        elif event.button == 3:
            if self.player.fire_secondary():
                self.fire_weapon(is_secondary=True)

    def handle_game_events(self) -> None:
        """Handle events during gameplay."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if self.cheat_mode_active:
                    self._handle_cheat_input(event)
                    continue

                if self.input_manager.is_action_just_pressed(event, "pause"):
                    self._handle_pause_toggle(event)
                elif event.key == pygame.K_c and (
                    pygame.key.get_mods() & pygame.KMOD_CTRL
                ):
                    self.cheat_mode_active = True
                    self.current_cheat_input = ""
                    self.add_message("CHEAT MODE: TYPE CODE", self.C.PURPLE)
                    continue

                if not self.paused:
                    self._handle_weapon_keys(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.paused:
                    mx, my = event.pos
                    self._handle_pause_menu_click(mx, my)
                elif not self.cheat_mode_active:
                    self._handle_gameplay_mouse_click(event)

            elif event.type == pygame.MOUSEMOTION and not self.paused:
                if not (self.player is not None):
                    raise ValueError("DbC Blocked: Precondition failed.")
                self.player.rotate(
                    event.rel[0] * self.C.PLAYER_ROT_SPEED * self.C.SENSITIVITY_X
                )
                self.player.pitch_view(-event.rel[1] * self.C.PLAYER_ROT_SPEED * 200)

    def save_game(self, filename: str = "savegame.txt") -> None:
        """Save game state to file.

        Args:
            filename (str): The file path to save the game state.
                Defaults to "savegame.txt".
        """
        try:
            with open(filename, "w") as f:
                f.write(f"{self.level}")
        except OSError:
            logger.exception("Save failed")
