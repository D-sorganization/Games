from __future__ import annotations

import logging

from games.shared.config import RaycasterConfig
from games.shared.fps_game_base import FPSGameBase

# Shared components
from games.shared.sound_manager_base import SoundManagerBase

from . import combat_actions, game_loop, game_session, gameplay_runtime, screen_flow
from . import constants as C  # noqa: N812
from .combat_system import CombatSystem
from .entity_manager import EntityManager
from .game_input import GameInputHandler
from .input_manager import InputManager
from .particle_system import ParticleSystem
from .projectile import Projectile
from .renderer import GameRenderer
from .sound import SoundManager
from .spawn_manager import FFSpawnManager
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
        super().init_fps_game(
            C,
            caption="Force Field - Arena Combat",
            sound_manager=sound_manager,
            sound_manager_factory=SoundManager,
            input_manager=InputManager(),
            entity_manager=EntityManager(),
            particle_system=ParticleSystem(),
            unlocked_weapons={"pistol", "rifle"},
            render_cls=GameRenderer,
            ui_render_cls=UIRenderer,
        )

        # Movement speed multiplier (1.0 = default, 0.5 = half, 2.0 = double speed)
        self.movement_speed_multiplier = 1.0

        # Slider interaction state
        self.dragging_speed_slider = False

        self.screen_shake = 0.0
        self.spawn_manager = FFSpawnManager(self.entity_manager)
        self.combat_system = CombatSystem(self)

        # Game Input Handler
        self.game_input_handler = GameInputHandler(self)

        # Raycaster Config
        self.raycaster_config = self._make_raycaster_config()

    def _make_raycaster_config(self) -> RaycasterConfig:
        """Build and return the RaycasterConfig from game constants."""
        return RaycasterConfig(
            SCREEN_WIDTH=C.SCREEN_WIDTH,
            SCREEN_HEIGHT=C.SCREEN_HEIGHT,
            FOV=C.FOV,  # type: ignore
            HALF_FOV=C.HALF_FOV,  # type: ignore
            ZOOM_FOV_MULT=C.ZOOM_FOV_MULT,
            DEFAULT_RENDER_SCALE=C.DEFAULT_RENDER_SCALE,  # type: ignore
            MAX_DEPTH=C.MAX_DEPTH,  # type: ignore
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

    def start_game(self) -> None:
        """Start a new run using the configured campaign options."""
        game_session.start_game(self)

    def start_level(self) -> None:
        """Start the current level with a fresh spawn and preserved loadout."""
        game_session.start_level(self)

    # save_game is inherited from FPSGameBase.

    def explode_bomb(self, projectile: Projectile) -> None:
        """Handle bomb explosion logic"""
        self.combat_system.explode_bomb(projectile)

    def explode_laser(self, impact_x: float, impact_y: float) -> None:
        """Trigger Massive Laser Explosion at Impact Point"""
        self.combat_system.explode_laser(impact_x, impact_y)

    def explode_plasma(self, projectile: Projectile) -> None:
        """Trigger plasma AOE explosion"""
        self.combat_system.explode_plasma(projectile)

    def explode_pulse(self, projectile: Projectile) -> None:
        """Trigger pulse AOE explosion (smaller than plasma)"""
        self.combat_system.explode_pulse(projectile)

    def explode_rocket(self, projectile: Projectile) -> None:
        """Trigger rocket AOE explosion"""
        self.combat_system.explode_rocket(projectile)

    def explode_freezer(self, projectile: Projectile) -> None:
        """Trigger freezer AOE explosion"""
        self.combat_system.explode_freezer(projectile)

    def execute_melee_attack(self) -> None:
        """Execute the melee attack owned by the combat-actions subsystem."""
        combat_actions.execute_melee_attack(self)

    def create_melee_sweep_effect(self) -> None:
        """Create the melee slash particles via the combat-actions module."""
        combat_actions.create_melee_sweep_effect(self)

    def _check_game_over(self) -> bool:
        """Delegate death handling to the gameplay runtime subsystem."""
        return gameplay_runtime.check_game_over(self)

    def _update_screen_shake(self) -> None:
        """Delegate screen-shake decay to the gameplay runtime subsystem."""
        gameplay_runtime.update_screen_shake(self)

    def _check_portal_completion(self) -> bool:
        """Delegate portal logic to the gameplay runtime subsystem."""
        return gameplay_runtime.check_portal_completion(self)

    def _handle_combat_input(self) -> None:
        """Delegate held-fire handling to the gameplay runtime subsystem."""
        gameplay_runtime.handle_combat_input(self)

    def _handle_joystick_input(self, shield_active: bool) -> bool:
        """Delegate controller input handling to the gameplay runtime."""
        return gameplay_runtime.handle_joystick_input(self, shield_active)

    def _update_damage_texts(self) -> None:
        """Delegate damage-text animation to the gameplay runtime."""
        gameplay_runtime.update_damage_texts(self)

    def _handle_keyboard_movement(self, keys) -> None:
        """Delegate keyboard movement to the gameplay runtime subsystem."""
        gameplay_runtime.handle_keyboard_movement(self, keys)

    def _update_fog_of_war(self) -> None:
        """Delegate near-field fog reveal to the gameplay runtime."""
        gameplay_runtime.update_fog_of_war(self)

    def _check_item_pickups(self) -> None:
        """Delegate pickup handling to the gameplay runtime subsystem."""
        gameplay_runtime.check_item_pickups(self)

    def _update_large_fog_reveal(self) -> None:
        """Delegate wide minimap reveal to the gameplay runtime."""
        gameplay_runtime.update_large_fog_reveal(self)

    def _update_atmosphere(self) -> None:
        """Delegate ambient audio updates to the gameplay runtime."""
        gameplay_runtime.update_atmosphere(self)

    def _check_kill_combo(self) -> None:
        """Delegate combo expiry logic to the gameplay runtime."""
        gameplay_runtime.check_kill_combo(self)

    def update_game(self) -> None:
        """Update one active gameplay frame through the runtime subsystem."""
        gameplay_runtime.update_game(self)

    def handle_intro_events(self) -> None:
        """Delegate intro events to the screen-flow subsystem."""
        screen_flow.handle_intro_events(self)

    def handle_menu_events(self) -> None:
        """Delegate main-menu events to the screen-flow subsystem."""
        screen_flow.handle_menu_events(self)

    def handle_map_select_events(self) -> None:
        """Delegate setup-screen events to the screen-flow subsystem."""
        screen_flow.handle_map_select_events(self)

    def handle_level_complete_events(self) -> None:
        """Delegate level-complete events to the screen-flow subsystem."""
        screen_flow.handle_level_complete_events(self)

    def handle_game_over_events(self) -> None:
        """Delegate game-over events to the screen-flow subsystem."""
        screen_flow.handle_game_over_events(self)

    def handle_key_config_events(self) -> None:
        """Delegate key-config events to the screen-flow subsystem."""
        screen_flow.handle_key_config_events(self)

    def _update_intro_logic(self, elapsed: int) -> None:
        """Delegate intro timing to the screen-flow subsystem."""
        screen_flow.update_intro_logic(self, elapsed)

    def run(self) -> None:
        """Delegate top-level frame dispatch to the loop subsystem."""
        game_loop.run(self)
