from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from . import constants as C  # noqa: N812
from .projectile import Projectile

if TYPE_CHECKING:
    from .game import Game
    from .player import Player

logger = logging.getLogger(__name__)


class GameInputHandler:
    """Handles all input events for the game."""

    def __init__(self, game: Game):
        self._game = game

    @property
    def game(self) -> Game:
        """Return the owned game object."""
        return self._game

    @property
    def player(self) -> Player:
        """Return the active player, raising when the game is not ready."""
        if self._game.player is None:
            raise ValueError("DbC Blocked: Precondition failed.")
        return self._game.player

    @property
    def input_manager(self):
        return self._game.input_manager

    @property
    def combat_system(self):
        return self._game.combat_system

    @property
    def entity_manager(self):
        return self._game.entity_manager

    @property
    def sound_manager(self):
        return self._game.sound_manager

    @property
    def ui_renderer(self):
        return self._game.ui_renderer

    def _set_mouse_grab(self, grabbed: bool) -> None:
        pygame.mouse.set_visible(not grabbed)
        pygame.event.set_grab(grabbed)

    def _pause_game(self) -> None:
        game = self._game
        game.paused = True
        self.sound_manager.pause_all()
        game.pause_start_time = pygame.time.get_ticks()
        self._set_mouse_grab(False)

    def _resume_game(self) -> None:
        game = self._game
        game.paused = False
        self.sound_manager.unpause_all()
        if game.pause_start_time > 0:
            now = pygame.time.get_ticks()
            pause_duration = now - game.pause_start_time
            game.total_paused_time += pause_duration
            game.pause_start_time = 0
        self._set_mouse_grab(True)

    def _open_cheat_input(self) -> None:
        game = self._game
        game.cheat_mode_active = True
        game.current_cheat_input = ""

    def _close_cheat_input(self, message: str | None = None) -> None:
        game = self._game
        game.cheat_mode_active = False
        if message is not None:
            game.add_message(message, C.GRAY)

    def _trigger_all_weapons_cheat(self) -> None:
        game = self._game
        game.unlocked_weapons = set(C.WEAPONS.keys())
        if game.player:
            for weapon_name in game.player.ammo:
                game.player.ammo[weapon_name] = 999
        game.add_message("ALL WEAPONS UNLOCKED", C.YELLOW)
        game.current_cheat_input = ""
        game.cheat_mode_active = False

    def _trigger_god_mode_cheat(self) -> None:
        game = self._game
        game.god_mode = not game.god_mode
        game.add_message(
            "GOD MODE ON" if game.god_mode else "GOD MODE OFF",
            C.YELLOW,
        )
        if game.player:
            game.player.health = 100
            game.player.god_mode = game.god_mode
        game.current_cheat_input = ""
        game.cheat_mode_active = False

    def _shoot_primary(self) -> None:
        if self.player.shoot():
            self.combat_system.fire_weapon()

    def _shoot_secondary(self) -> None:
        if self.player.fire_secondary():
            self.combat_system.fire_weapon(is_secondary=True)

    def _spawn_bomb(self) -> None:
        player = self.player
        if player.activate_bomb():
            bomb = Projectile(
                player.x,
                player.y,
                player.angle,
                damage=1000,
                speed=0.4,
                is_player=True,
                color=(50, 50, 50),
                size=0.4,
                weapon_type="bomb",
                z=0.5,
                vz=0.15,
                gravity=0.015,
            )
            self.entity_manager.add_projectile(bomb)

    def _toggle_pause(self) -> None:
        if self._game.paused:
            self._resume_game()
        else:
            self._pause_game()

    def handle_game_events(self) -> None:
        """Handle events during gameplay."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._game.running = False
            elif event.type == pygame.KEYDOWN:
                if self._game.cheat_mode_active:
                    self._handle_cheat_input(event)
                else:
                    self._handle_gameplay_input(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self._game.paused:
                    self._handle_pause_menu_click(event)
                elif not self._game.cheat_mode_active:
                    if event.button == 1:
                        self._shoot_primary()
                    elif event.button == 3:
                        self._shoot_secondary()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self._game.dragging_speed_slider = False
            elif event.type == pygame.MOUSEMOTION:
                if self._game.paused and self._game.dragging_speed_slider:
                    self._handle_speed_slider(event)
                elif not self._game.paused:
                    self.player.rotate(
                        event.rel[0] * C.PLAYER_ROT_SPEED * C.SENSITIVITY_X
                    )
                    self.player.pitch_view(-event.rel[1] * C.PLAYER_ROT_SPEED * 200)

    def _handle_cheat_input(self, event: pygame.event.Event) -> None:
        """Handle input when cheat mode is active."""
        if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
            self._close_cheat_input("CHEAT INPUT CLOSED")
        elif event.key == pygame.K_BACKSPACE:
            self._game.current_cheat_input = self._game.current_cheat_input[:-1]
        else:
            self._game.current_cheat_input += event.unicode
            code = self._game.current_cheat_input.upper()
            if code.endswith("IDFA"):
                self._trigger_all_weapons_cheat()
            elif code.endswith("IDDQD"):
                self._trigger_god_mode_cheat()

    def _handle_gameplay_input(self, event: pygame.event.Event) -> None:
        """Handle standard gameplay keyboard events."""
        if self.input_manager.is_action_just_pressed(event, "pause"):
            self._toggle_pause()
        elif event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
            self._open_cheat_input()
            self._game.add_message("CHEAT MODE: TYPE CODE", C.PURPLE)
        elif not self._game.paused:
            self._handle_weapon_switch_keys(event)

    def _handle_weapon_switch_keys(self, event: pygame.event.Event) -> None:
        """Dispatch weapon-select, action, and utility key events during gameplay."""
        if self.input_manager.is_action_just_pressed(event, "weapon_1"):
            self._game.switch_weapon_with_message("pistol")
        elif self.input_manager.is_action_just_pressed(event, "weapon_2"):
            self._game.switch_weapon_with_message("rifle")
        elif self.input_manager.is_action_just_pressed(event, "weapon_3"):
            self._game.switch_weapon_with_message("shotgun")
        elif self.input_manager.is_action_just_pressed(event, "weapon_4"):
            self._game.switch_weapon_with_message("laser")
        elif self.input_manager.is_action_just_pressed(event, "weapon_5"):
            self._game.switch_weapon_with_message("plasma")
        elif self.input_manager.is_action_just_pressed(event, "weapon_6"):
            self._game.switch_weapon_with_message("rocket")
        elif event.key == pygame.K_7:
            self._game.switch_weapon_with_message("minigun")
        elif event.key == pygame.K_9:
            self._game.switch_weapon_with_message("flamethrower")
        elif self.input_manager.is_action_just_pressed(event, "reload"):
            self.player.reload()
        elif self.input_manager.is_action_just_pressed(event, "zoom"):
            self.player.zoomed = not self.player.zoomed
        elif event.key == pygame.K_q:
            if self.player.melee_attack():
                self._game.execute_melee_attack()
        elif self.input_manager.is_action_just_pressed(event, "bomb"):
            self._spawn_bomb()
        elif self.input_manager.is_action_just_pressed(event, "shoot_alt"):
            self._shoot_primary()
        elif event.key == pygame.K_m:
            self._game.show_minimap = not self._game.show_minimap
        elif event.key == pygame.K_F9:
            self._game.cycle_render_scale()
        elif self.input_manager.is_action_just_pressed(event, "dash"):
            self.player.dash()

    def _handle_pause_menu_click(self, event: pygame.event.Event) -> None:
        """Handle clicks in pause menu."""
        mx, my = event.pos
        menu_items = [
            "RESUME",
            "SAVE GAME",
            "ENTER CHEAT",
            "CONTROLS",
            "QUIT TO MENU",
        ]
        if self._handle_pause_menu_item_click(mx, my, menu_items):
            return
        self._handle_speed_slider_click(mx, my, menu_items)

    def _handle_pause_menu_item_click(
        self, mx: int, my: int, menu_items: list[str]
    ) -> bool:
        """Test if (mx, my) hits a menu button and execute its action.

        Returns True if a button was clicked (caller should return early).
        """
        max_text_width = 0
        for item in menu_items:
            text_surf = self.ui_renderer.render_subtitle_text(item, True, C.WHITE)
            max_text_width = max(max_text_width, text_surf.get_width())

        box_width = max_text_width + 60
        box_height = 50

        for i, _ in enumerate(menu_items):
            rect = pygame.Rect(
                C.SCREEN_WIDTH // 2 - box_width // 2,
                350 + i * 60,
                box_width,
                box_height,
            )
            if rect.collidepoint(mx, my):
                if i == 0:
                    self._resume_game()
                elif i == 1:
                    self._game.save_game()
                    self._game.add_message("GAME SAVED", C.GREEN)
                elif i == 2:
                    self._open_cheat_input()
                elif i == 3:
                    self._game.state = "key_config"
                    self._game.binding_action = None
                elif i == 4:
                    self._game.state = "menu"
                    self._game.paused = False
                    self.sound_manager.start_music("music_loop")
                return True
        return False

    def _handle_speed_slider_click(
        self, mx: int, my: int, menu_items: list[str]
    ) -> None:
        """Handle a click on the speed slider below the pause menu."""
        slider_y = 350 + len(menu_items) * 60 + 30 + 30
        slider_width = 200
        slider_height = 10
        slider_x = C.SCREEN_WIDTH // 2 - slider_width // 2
        slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height + 10)

        if slider_rect.collidepoint(mx, my):
            relative_x = mx - slider_x
            speed_ratio = max(0.0, min(1.0, relative_x / slider_width))
            self._game.movement_speed_multiplier = 0.5 + speed_ratio * 1.5
            self._game.dragging_speed_slider = True

    def _handle_speed_slider(self, event: pygame.event.Event) -> None:
        """Handle dragging the speed slider."""
        mx, _ = event.pos
        slider_width = 200
        slider_x = C.SCREEN_WIDTH // 2 - slider_width // 2

        relative_x = mx - slider_x
        speed_ratio = max(0.0, min(1.0, relative_x / slider_width))
        self._game.movement_speed_multiplier = 0.5 + speed_ratio * 1.5
