from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from . import constants as C  # noqa: N812
from .projectile import Projectile

if TYPE_CHECKING:
    from .game import Game

logger = logging.getLogger(__name__)


class GameInputHandler:
    """Handles all input events for the game."""

    def __init__(self, game: Game):
        self.game = game

    def handle_game_events(self) -> None:
        """Handle events during gameplay"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.running = False
            elif event.type == pygame.KEYDOWN:
                if self.game.cheat_mode_active:
                    self._handle_cheat_input(event)
                else:
                    self._handle_gameplay_input(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.game.paused:
                    self._handle_pause_menu_click(event)
                elif not self.game.cheat_mode_active:
                    # Gameplay Clicks (Shooting)
                    assert self.game.player is not None
                    if event.button == 1:
                        if self.game.player.shoot():
                            self.game.combat_system.fire_weapon()
                    elif event.button == 3:
                        if self.game.player.fire_secondary():
                            self.game.combat_system.fire_weapon(is_secondary=True)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.game.dragging_speed_slider = False

            elif event.type == pygame.MOUSEMOTION:
                if self.game.paused and self.game.dragging_speed_slider:
                    self._handle_speed_slider(event)
                elif not self.game.paused:
                    assert self.game.player is not None
                    self.game.player.rotate(
                        event.rel[0] * C.PLAYER_ROT_SPEED * C.SENSITIVITY_X
                    )
                    self.game.player.pitch_view(
                        -event.rel[1] * C.PLAYER_ROT_SPEED * 200
                    )

    def _handle_cheat_input(self, event: pygame.event.Event) -> None:
        """Handle input when cheat mode is active."""
        if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
            self.game.cheat_mode_active = False
            self.game.add_message("CHEAT INPUT CLOSED", C.GRAY)
        elif event.key == pygame.K_BACKSPACE:
            self.game.current_cheat_input = self.game.current_cheat_input[:-1]
        else:
            self.game.current_cheat_input += event.unicode
            code = self.game.current_cheat_input.upper()
            if code.endswith("IDFA"):
                self.game.unlocked_weapons = set(C.WEAPONS.keys())
                if self.game.player:
                    for w in self.game.player.ammo:
                        self.game.player.ammo[w] = 999
                self.game.add_message("ALL WEAPONS UNLOCKED", C.YELLOW)
                self.game.current_cheat_input = ""
                self.game.cheat_mode_active = False
            elif code.endswith("IDDQD"):
                self.game.god_mode = not self.game.god_mode
                msg = "GOD MODE ON" if self.game.god_mode else "GOD MODE OFF"
                self.game.add_message(msg, C.YELLOW)
                if self.game.player:
                    self.game.player.health = 100
                    self.game.player.god_mode = self.game.god_mode
                self.game.current_cheat_input = ""
                self.game.cheat_mode_active = False

    def _handle_gameplay_input(self, event: pygame.event.Event) -> None:
        """Handle standard gameplay keyboard events."""
        # Pause Toggle
        if self.game.input_manager.is_action_just_pressed(event, "pause"):
            self.game.paused = not self.game.paused
            if self.game.paused:
                self.game.sound_manager.pause_all()
                self.game.pause_start_time = pygame.time.get_ticks()
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)
            else:
                self.game.sound_manager.unpause_all()
                if self.game.pause_start_time > 0:
                    now = pygame.time.get_ticks()
                    pause_duration = now - self.game.pause_start_time
                    self.game.total_paused_time += pause_duration
                    self.game.pause_start_time = 0
                pygame.mouse.set_visible(False)
                pygame.event.set_grab(True)

        # Activate Cheat Mode
        elif event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
            self.game.cheat_mode_active = True
            self.game.current_cheat_input = ""
            self.game.add_message("CHEAT MODE: TYPE CODE", C.PURPLE)

        # Standard Gameplay Controls (only if not paused)
        elif not self.game.paused:
            if self.game.input_manager.is_action_just_pressed(event, "weapon_1"):
                self.game.switch_weapon_with_message("pistol")
            elif self.game.input_manager.is_action_just_pressed(event, "weapon_2"):
                self.game.switch_weapon_with_message("rifle")
            elif self.game.input_manager.is_action_just_pressed(event, "weapon_3"):
                self.game.switch_weapon_with_message("shotgun")
            elif self.game.input_manager.is_action_just_pressed(event, "weapon_4"):
                self.game.switch_weapon_with_message("laser")
            elif self.game.input_manager.is_action_just_pressed(event, "weapon_5"):
                self.game.switch_weapon_with_message("plasma")
            elif self.game.input_manager.is_action_just_pressed(event, "weapon_6"):
                self.game.switch_weapon_with_message("rocket")
            elif event.key == pygame.K_7:
                self.game.switch_weapon_with_message("minigun")
            elif event.key == pygame.K_9:
                self.game.switch_weapon_with_message("flamethrower")
            elif self.game.input_manager.is_action_just_pressed(event, "reload"):
                assert self.game.player is not None
                self.game.player.reload()
            elif self.game.input_manager.is_action_just_pressed(event, "zoom"):
                assert self.game.player is not None
                self.game.player.zoomed = not self.game.player.zoomed
            elif event.key == pygame.K_q:
                assert self.game.player is not None
                if self.game.player.melee_attack():
                    self.game.execute_melee_attack()
            elif self.game.input_manager.is_action_just_pressed(event, "bomb"):
                assert self.game.player is not None
                if self.game.player.activate_bomb():
                    bomb = Projectile(
                        self.game.player.x,
                        self.game.player.y,
                        self.game.player.angle,
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
                    self.game.entity_manager.add_projectile(bomb)
            elif self.game.input_manager.is_action_just_pressed(event, "shoot_alt"):
                assert self.game.player is not None
                if self.game.player.shoot():
                    self.game.combat_system.fire_weapon()
            elif event.key == pygame.K_m:
                self.game.show_minimap = not self.game.show_minimap
            elif event.key == pygame.K_F9:
                self.game.cycle_render_scale()
            elif self.game.input_manager.is_action_just_pressed(event, "dash"):
                assert self.game.player is not None
                self.game.player.dash()

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
        max_text_width = 0
        for item in menu_items:
            text_surf = self.game.ui_renderer.subtitle_font.render(item, True, C.WHITE)
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
                if i == 0:  # Resume
                    self.game.paused = False
                    self.game.sound_manager.unpause_all()
                    if self.game.pause_start_time > 0:
                        now = pygame.time.get_ticks()
                        pause_duration = now - self.game.pause_start_time
                        self.game.total_paused_time += pause_duration
                        self.game.pause_start_time = 0
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                elif i == 1:  # Save
                    self.game.save_game()
                    self.game.add_message("GAME SAVED", C.GREEN)
                elif i == 2:  # Enter Cheat
                    self.game.cheat_mode_active = True
                    self.game.current_cheat_input = ""
                elif i == 3:  # Controls
                    self.game.state = "key_config"
                    self.game.binding_action = None
                elif i == 4:  # Quit to Menu
                    self.game.state = "menu"
                    self.game.paused = False
                    self.game.sound_manager.start_music("music_loop")
                return

        # Check speed slider interaction
        slider_y = 350 + len(menu_items) * 60 + 30 + 30
        slider_width = 200
        slider_height = 10
        slider_x = C.SCREEN_WIDTH // 2 - slider_width // 2
        slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height + 10)

        if slider_rect.collidepoint(mx, my):
            relative_x = mx - slider_x
            speed_ratio = max(0.0, min(1.0, relative_x / slider_width))
            self.game.movement_speed_multiplier = 0.5 + speed_ratio * 1.5
            self.game.dragging_speed_slider = True

    def _handle_speed_slider(self, event: pygame.event.Event) -> None:
        """Handle dragging the speed slider."""
        mx, _ = event.pos
        slider_width = 200
        slider_x = C.SCREEN_WIDTH // 2 - slider_width // 2

        relative_x = mx - slider_x
        speed_ratio = max(0.0, min(1.0, relative_x / slider_width))
        self.game.movement_speed_multiplier = 0.5 + speed_ratio * 1.5
