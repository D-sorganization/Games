#!/usr/bin/env python3
"""
Enhanced Tetris Game Clone
A fully featured Tetris implementation with levels, scoring, and modern features
Refactored into modules.
"""

import sys
import pygame
import src.constants as C
from src.game_logic import TetrisLogic
from src.renderer import TetrisRenderer
from src.input_handler import InputHandler

# Initialize Pygame
pygame.init()

class TetrisGame:
    """Main Tetris game class"""

    def __init__(self) -> None:
        """Initialize the Tetris game with display and initial state"""
        self.screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT))
        pygame.display.set_caption("Enhanced Tetris")
        self.clock = pygame.time.Clock()

        self.logic = TetrisLogic()
        self.renderer = TetrisRenderer(self.screen)
        self.input_handler = InputHandler()

        self.state = C.GameState.MENU

        # UI State
        self.show_next_piece = True
        self.show_hold_piece = True
        self.show_ghost_piece = True
        self.show_controls_panel = True
        self.settings_selection = 0

        self.restart_button = pygame.Rect(
            C.SCREEN_WIDTH - C.BUTTON_WIDTH - 20,
            C.SCREEN_HEIGHT - C.BUTTON_HEIGHT - 10,
            C.BUTTON_WIDTH,
            C.BUTTON_HEIGHT,
        )
        self.controls_toggle_rect = pygame.Rect(
            C.SCREEN_WIDTH - C.BUTTON_WIDTH - 20,
            C.TOP_LEFT_Y - 40,
            C.BUTTON_WIDTH,
            C.BUTTON_HEIGHT,
        )

    def toggle_pause(self) -> None:
        """Toggle game pause state"""
        if self.state in [C.GameState.PLAYING, C.GameState.PAUSED]:
            self.state = C.GameState.PAUSED if self.state == C.GameState.PLAYING else C.GameState.PLAYING

    def restart_game(self) -> None:
        """Restart the current game"""
        if self.state in [C.GameState.PLAYING, C.GameState.PAUSED, C.GameState.GAME_OVER]:
            self.logic.reset_game()
            self.state = C.GameState.PLAYING

    def handle_menu_input(self, event: pygame.event.Event) -> None:
        """Handle input events in the main menu"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                levels = [1, 5, 10, 15, 20]
                current_idx = levels.index(self.logic.starting_level)
                self.logic.starting_level = levels[max(0, current_idx - 1)]
            elif event.key == pygame.K_DOWN:
                levels = [1, 5, 10, 15, 20]
                current_idx = levels.index(self.logic.starting_level)
                self.logic.starting_level = levels[min(len(levels) - 1, current_idx + 1)]
            elif event.key == pygame.K_RETURN:
                self.logic.reset_game()
                self.state = C.GameState.PLAYING
            elif event.key == pygame.K_s:
                self.state = C.GameState.SETTINGS

    def get_settings_entries(self) -> list[dict]:
        """Return the settings configuration items"""
        entries = [
            {"label": "Show Next Piece", "key": "show_next_piece", "type": "bool"},
            {"label": "Show Held Piece", "key": "show_hold_piece", "type": "bool"},
            {"label": "Show Ghost Piece", "key": "show_ghost_piece", "type": "bool"},
            {
                "label": "Show Controls Panel",
                "key": "show_controls_panel",
                "type": "bool",
            },
            {"label": "Enable Controller", "key": "controller_enabled", "type": "bool"},
            {"label": "Allow Rewind", "key": "allow_rewind", "type": "bool"},
            {"label": "Controller Mappings", "type": "header", "key": ""},
        ]

        for action_key, description in self.input_handler.controller_action_labels.items():
            entries.append(
                {
                    "label": description,
                    "key": action_key,
                    "type": "mapping",
                },
            )

        return entries

    def handle_settings_input(self, event: pygame.event.Event) -> None:
        """Handle input events in the settings menu"""
        if event.type != pygame.KEYDOWN:
            return

        entries = self.get_settings_entries()

        if event.key == pygame.K_ESCAPE:
            self.input_handler.awaiting_controller_action = None
            self.state = C.GameState.MENU
        elif event.key == pygame.K_UP:
            self.settings_selection = max(0, self.settings_selection - 1)
        elif event.key == pygame.K_DOWN:
            self.settings_selection = min(len(entries) - 1, self.settings_selection + 1)
        elif event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN]:
            entry = entries[self.settings_selection]
            if entry["type"] == "bool":
                key = entry["key"]
                # key might be on self or input_handler or logic
                if hasattr(self, key):
                    current = getattr(self, key)
                    setattr(self, key, not current)
                elif hasattr(self.input_handler, key):
                    current = getattr(self.input_handler, key)
                    setattr(self.input_handler, key, not current)
                elif hasattr(self.logic, key):
                    current = getattr(self.logic, key)
                    setattr(self.logic, key, not current)
                    if key == "allow_rewind":
                        self.logic.rewind_history.clear()

            elif entry["type"] == "mapping" and self.input_handler.controller_enabled and self.input_handler.joystick:
                self.input_handler.awaiting_controller_action = entry["key"]

    def draw_settings(self) -> None:
        """Render the settings menu"""
        # Implementing draw_settings here as it was missing from renderer and needs state access
        self.screen.fill(C.BLACK)
        title = self.renderer.font_large.render("Settings", True, C.CYAN)
        title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)

        entries = self.get_settings_entries()
        y_offset = 160

        for idx, entry in enumerate(entries):
            color = C.GOLD if idx == self.settings_selection else C.WHITE
            label = entry["label"]
            value_text = ""

            if entry["type"] == "bool":
                key = entry["key"]
                value = False
                if hasattr(self, key):
                    value = getattr(self, key)
                elif hasattr(self.input_handler, key):
                    value = getattr(self.input_handler, key)
                elif hasattr(self.logic, key):
                    value = getattr(self.logic, key)
                value_text = "On" if value else "Off"
            elif entry["type"] == "mapping":
                value_text = self.input_handler.get_binding_label(entry["key"])

            label_text = self.renderer.font.render(label, True, color)
            value_render = self.renderer.small_font.render(value_text, True, C.LIGHT_GRAY)

            self.screen.blit(label_text, (140, y_offset))
            if value_text:
                self.screen.blit(value_render, (520, y_offset + 6))
            y_offset += 40

        hint = self.renderer.tiny_font.render(
            "Arrow keys to navigate, ENTER to toggle or remap, ESC to return",
            True,
            C.GRAY,
        )
        hint_rect = hint.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 60))
        self.screen.blit(hint, hint_rect)

        if self.input_handler.awaiting_controller_action:
            action_label = self.input_handler.controller_action_labels[self.input_handler.awaiting_controller_action]
            waiting = self.renderer.small_font.render(
                f"Waiting for input to bind {action_label}",
                True,
                C.YELLOW,
            )
            waiting_rect = waiting.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 100))
            self.screen.blit(waiting, waiting_rect)

    def handle_mouse_input(self, pos: tuple[int, int]) -> None:
        """Handle mouse clicks on UI buttons"""
        if self.controls_toggle_rect.collidepoint(pos):
            if self.state in [C.GameState.PLAYING, C.GameState.PAUSED]:
                self.show_controls_panel = not self.show_controls_panel
        if self.restart_button.collidepoint(pos):
            if self.state in [C.GameState.PLAYING, C.GameState.PAUSED, C.GameState.GAME_OVER]:
                self.restart_game()

    def run(self) -> None:
        """Main game loop"""
        while True:
            dt = self.clock.get_time()
            self.clock.tick(60)

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_input(event.pos)

                if self.state == C.GameState.MENU:
                    self.handle_menu_input(event)
                elif self.state == C.GameState.SETTINGS:
                    self.handle_settings_input(event)
                    # Input handler binding logic
                    if self.input_handler.awaiting_controller_action:
                        if event.type in [pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION]:
                             if self.input_handler.apply_controller_binding(event):
                                 # Binding applied, no specific action needed
                                 pass

            # Process events for input handler
            self.input_handler.process_events(events, self.logic, self)

            # Polling for continuous movement
            keys = pygame.key.get_pressed()
            if self.state == C.GameState.PLAYING:
                 if keys[pygame.K_LEFT] and self.logic.valid_move(self.logic.current_piece, x_offset=-1):
                    self.logic.current_piece.x -= 1
                    pygame.time.wait(100)
                 if keys[pygame.K_RIGHT] and self.logic.valid_move(self.logic.current_piece, x_offset=1):
                    self.logic.current_piece.x += 1
                    pygame.time.wait(100)
                 if keys[pygame.K_DOWN]:
                    if self.logic.valid_move(self.logic.current_piece, y_offset=1):
                        self.logic.current_piece.y += 1
                        self.logic.score += 1
                    pygame.time.wait(50)

                 self.input_handler.handle_controller_state(self.logic)
                 self.logic.update(dt)

            # Drawing
            if self.state == C.GameState.MENU:
                self.renderer.draw_menu(self.logic.starting_level)
            elif self.state == C.GameState.SETTINGS:
                self.draw_settings()
            elif self.state in [C.GameState.PLAYING, C.GameState.PAUSED]:
                self.screen.fill(C.BLACK)
                self.renderer.draw_grid(self.logic)
                if self.show_ghost_piece:
                    self.renderer.draw_ghost_piece(self.logic)
                self.renderer.draw_piece(self.logic.current_piece)
                if self.show_next_piece:
                    self.renderer.draw_next_piece(self.logic)
                if self.show_hold_piece:
                    self.renderer.draw_held_piece(self.logic)
                self.renderer.draw_stats(self.logic)
                self.renderer.draw_controls(self.show_controls_panel)
                self.renderer.draw_button(
                    self.controls_toggle_rect,
                    "Hide Controls" if self.show_controls_panel else "Show Controls",
                )
                self.renderer.draw_button(self.restart_button, "Restart Run")

                if self.state == C.GameState.PLAYING:
                    self.renderer.draw_particles(self.logic)
                    self.renderer.draw_score_popups(self.logic)
                else:
                    # Draw static particles when paused
                    pass

                if self.state == C.GameState.PAUSED:
                    overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT))
                    overlay.fill(C.BLACK)
                    overlay.set_alpha(128)
                    self.screen.blit(overlay, (0, 0))
                    pause_text = self.renderer.font_large.render("PAUSED", True, C.YELLOW)
                    pause_rect = pause_text.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2))
                    self.screen.blit(pause_text, pause_rect)

            elif self.state == C.GameState.GAME_OVER:
                self.renderer.draw_game_over(self.logic)

            pygame.display.flip()

if __name__ == "__main__":
    game = TetrisGame()
    game.run()
