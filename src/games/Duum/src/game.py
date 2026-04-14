from __future__ import annotations

import logging
import random

import pygame

from games.shared.config import RaycasterConfig
from games.shared.constants import (
    PORTAL_RADIUS_SQ,
    GameState,
)
from games.shared.fps_game_base import FPSGameBase
from games.shared.raycaster import Raycaster
from games.shared.sound_manager_base import SoundManagerBase

from . import constants as C  # noqa: N812
from . import game_loop, gameplay_updater
from .atmosphere_manager import AtmosphereManager
from .combat_manager import DuumCombatManager
from .entity_manager import EntityManager
from .input_manager import InputManager
from .map import Map
from .particle_system import ParticleSystem
from .player import Player
from .projectile import Projectile
from .renderer import GameRenderer
from .screen_event_handler import ScreenEventHandler
from .sound import SoundManager
from .spawn_manager import DuumSpawnManager
from .ui_renderer import UIRenderer
from .weapon_system import WeaponSystem

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
        super().init_fps_game(
            C,
            caption="Duum - The Reimagining",
            sound_manager=sound_manager,
            sound_manager_factory=SoundManager,
            input_manager=InputManager(),
            entity_manager=EntityManager(),
            particle_system=ParticleSystem(),
            unlocked_weapons={"pistol"},
            render_cls=GameRenderer,
            ui_render_cls=UIRenderer,
        )
        self._init_audio_flags()
        self._init_game_managers()
        self._init_raycaster_config()

    def _init_audio_flags(self) -> None:
        """Set intro audio one-shot flags."""
        self.laugh_played = False
        self.water_played = False

    def _init_game_managers(self) -> None:
        """Construct and wire the game-specific subsystem managers."""
        self.spawn_manager = DuumSpawnManager(self.entity_manager)
        self.combat_manager = DuumCombatManager(
            self.entity_manager,
            self.particle_system,
            self.sound_manager,
            on_kill=lambda bot: self.event_bus.emit("bot_killed", x=bot.x, y=bot.y),
        )
        self.atmosphere_manager = AtmosphereManager(self)
        self.screen_event_handler = ScreenEventHandler(self)
        self.weapon_system = WeaponSystem(self)
        self.flash_intensity = 0.0

    def _init_raycaster_config(self) -> None:
        """Build the RaycasterConfig from game constants."""
        self.raycaster_config = RaycasterConfig(
            SCREEN_WIDTH=C.SCREEN_WIDTH,
            SCREEN_HEIGHT=C.SCREEN_HEIGHT,
            FOV=C.FOV,
            HALF_FOV=C.HALF_FOV,
            ZOOM_FOV_MULT=C.ZOOM_FOV_MULT,
            DEFAULT_RENDER_SCALE=C.DEFAULT_RENDER_SCALE,
            MAX_DEPTH=C.MAX_DEPTH,
            FOG_START=C.FOG_START,
            FOG_COLOR=C.FOG_COLOR,
            LEVEL_THEMES=C.LEVEL_THEMES,
            WALL_COLORS=C.WALL_COLORS,
            ENEMY_TYPES=C.ENEMY_TYPES,
            DARK_GRAY=C.DARK_GRAY,
            BLACK=C.BLACK,
            CYAN=C.CYAN,
            RED=C.RED,
            GREEN=C.GREEN,
            GRAY=C.GRAY,
            WHITE=C.WHITE,
            YELLOW=C.YELLOW,
        )

    def _wire_event_bus(self) -> None:
        """Subscribe subsystems to game events via the event bus."""
        self.event_bus.subscribe(
            "bot_killed",
            lambda **kw: self.sound_manager.play_sound("scream"),
        )

    def sync_combat_state(self) -> None:
        """Synchronize kill/combo state from the combat manager back to Game."""
        self.kills = self.combat_manager.kills
        self.kill_combo_count = self.combat_manager.kill_combo_count
        self.kill_combo_timer = self.combat_manager.kill_combo_timer
        self.last_death_pos = self.combat_manager.last_death_pos

    def _sync_combat_state(self) -> None:
        """Backward-compatible wrapper for older internal call sites."""
        self.sync_combat_state()

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

        # Reset combat manager state
        self.combat_manager.kills = 0
        self.combat_manager.kill_combo_count = 0
        self.combat_manager.kill_combo_timer = 0
        self.combat_manager.last_death_pos = None

        # Create map with selected size
        self.game_map = Map(self.selected_map_size)
        self.raycaster = Raycaster(self.game_map, self.raycaster_config)
        self.raycaster.set_render_scale(self.render_scale)
        self.last_death_pos = None

        # Grab mouse
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        self.start_level()

    def start_level(self) -> None:
        """Start a new level; orchestrates reset, spawn, and music."""
        if not (self.game_map is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        self._reset_level_state()
        player_pos = self._get_best_spawn_point()
        self._spawn_player(player_pos)
        self._spawn_entities(player_pos)
        self._start_level_music()

    def _reset_level_state(self) -> None:
        """Reset timers, particles, and fog for the new level."""
        self.level_start_time = pygame.time.get_ticks()
        self.total_paused_time = 0
        self.pause_start_time = 0
        self.particle_system.particles = []
        self.damage_texts = []
        self.damage_flash_timer = 0
        self.visited_cells = set()
        self.portal = None
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

    def _spawn_player(self, player_pos: tuple[float, float, float]) -> None:
        """Create player at spawn point, preserving ammo and weapon if available."""
        previous_ammo = None
        previous_weapon = "pistol"
        if self.player:
            previous_ammo = self.player.ammo
            previous_weapon = self.player.current_weapon
        self.player = Player(player_pos[0], player_pos[1], player_pos[2])
        if previous_ammo:
            self.player.ammo = previous_ammo
            unlocked = previous_weapon in self.unlocked_weapons
            self.player.current_weapon = previous_weapon if unlocked else "pistol"
        if self.player.current_weapon not in self.unlocked_weapons:
            self.player.current_weapon = "pistol"
        self.player.god_mode = self.god_mode

    def _spawn_entities(self, player_pos: tuple[float, float, float]) -> None:
        """Reset entity manager and spawn all level entities."""
        self.entity_manager.reset()
        self.spawn_manager.spawn_all(
            player_pos, self.game_map, self.level, self.selected_difficulty
        )

    def _start_level_music(self) -> None:
        """Pick and start a random music track for this level."""
        music_tracks = [
            "music_loop",
            "music_drums",
            "music_wind",
            "music_horror",
            "music_piano",
            "music_action",
        ]
        self.sound_manager.start_music(random.choice(music_tracks))

    def handle_intro_events(self) -> None:
        """Handle events during intro sequence"""
        self.screen_event_handler.handle_intro_events()

    def handle_menu_events(self) -> None:
        """Handle events in main menu"""
        self.screen_event_handler.handle_menu_events()

    def handle_key_config_events(self) -> None:
        """Handle events in key configuration screen"""
        self.screen_event_handler.handle_key_config_events()

    def handle_map_select_events(self) -> None:
        """Handle events in map selection screen"""
        self.screen_event_handler.handle_map_select_events()

    def handle_level_complete_events(self) -> None:
        """Handle events in level complete screen"""
        self.screen_event_handler.handle_level_complete_events()

    def handle_game_over_events(self) -> None:
        """Handle events in game over screen"""
        self.screen_event_handler.handle_game_over_events()

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

    def _check_game_over(self) -> bool:
        if not self.player.alive:
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
        """Process all joystick inputs; return updated shield_active flag."""
        self._joystick_move_axes()
        self._joystick_look_axes()
        shield_active = self._joystick_action_buttons(shield_active)
        self._joystick_hat_weapon_select()
        return shield_active

    def _joystick_move_axes(self) -> None:
        """Apply left-stick strafe/move axes to the player."""
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

    def _joystick_look_axes(self) -> None:
        """Apply right-stick look axes for rotation and pitch."""
        look_x = self.joystick.get_axis(2) if self.joystick.get_numaxes() >= 4 else 0.0
        look_y = self.joystick.get_axis(3) if self.joystick.get_numaxes() >= 4 else 0.0
        if abs(look_x) > C.JOYSTICK_DEADZONE:
            self.player.rotate(look_x * C.PLAYER_ROT_SPEED * 15 * C.SENSITIVITY_X)
        if abs(look_y) > C.JOYSTICK_DEADZONE:
            self.player.pitch_view(-look_y * 10 * C.SENSITIVITY_Y)

    def _joystick_action_buttons(self, shield_active: bool) -> bool:
        """Handle fire, reload, secondary-fire, and shield buttons."""
        n = self.joystick.get_numbuttons()
        if n > 0 and self.joystick.get_button(0):
            shield_active = True
        if n > 2 and self.joystick.get_button(2):
            self.player.reload()
        if n > 5 and self.joystick.get_button(5) and self.player.shoot():
            self.fire_weapon()
        if n > 4 and self.joystick.get_button(4) and self.player.fire_secondary():
            self.fire_weapon(is_secondary=True)
        return shield_active

    def _joystick_hat_weapon_select(self) -> None:
        """Use the D-pad hat to cycle weapons."""
        if self.joystick.get_numhats() < 1:
            return
        hat = self.joystick.get_hat(0)
        if hat[0] == -1:
            self.switch_weapon_with_message("pistol")
        if hat[0] == 1:
            self.switch_weapon_with_message("rifle")
        if hat[1] == 1:
            self.switch_weapon_with_message("shotgun")
        if hat[1] == -1:
            self.switch_weapon_with_message("plasma")

    def update_game(self) -> None:
        """Update game state through the extracted gameplay updater."""
        gameplay_updater.update_game(self)

    def _update_intro_logic(self, elapsed: int) -> None:
        """Update intro sequence logic and transitions.

        Args:
            elapsed: Elapsed time in milliseconds since intro started.
        """
        self.screen_event_handler.update_intro_logic(elapsed)

    def run(self) -> None:
        """Main game loop"""
        game_loop.run(self)
