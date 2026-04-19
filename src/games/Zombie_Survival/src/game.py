from __future__ import annotations

import logging

from games.shared.fps_game_base import FPSGameBase
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
        super().init_fps_game(
            C,
            caption="Zombie Survival - Undead Nightmare",
            sound_manager=sound_manager,
            sound_manager_factory=SoundManager,
            input_manager=InputManager(),
            entity_manager=EntityManager(),
            particle_system=ParticleSystem(),
            unlocked_weapons={"pistol", "rifle"},
            render_cls=GameRenderer,
            ui_render_cls=UIRenderer,
        )

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
        self.kills = self.kills  # type: ignore[has-type]
        self.kill_combo_count = self.kill_combo_count  # type: ignore[has-type]
        self.kill_combo_timer = self.kill_combo_timer  # type: ignore[has-type]
        self.last_death_pos = self.last_death_pos  # type: ignore[has-type]

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
        """Process all joystick inputs; return updated shield_active flag."""
        if not (self.player is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
        if not (self.game_map is not None):
            raise ValueError("DbC Blocked: Precondition failed.")
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
            self.player_is_moving = True
        if abs(axis_y) > C.JOYSTICK_DEADZONE:
            self.player.move(
                self.game_map,
                self.bots,
                forward=(axis_y < 0),
                speed=abs(axis_y) * C.PLAYER_SPEED,
            )
            self.player_is_moving = True

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
