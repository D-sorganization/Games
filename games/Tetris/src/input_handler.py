from typing import Any, cast

import pygame

from .constants import GameState
from .game_logic import TetrisLogic


class InputHandler:
    """Handles keyboard and controller input"""

    def __init__(self) -> None:
        """Initialize input handler"""
        self.controller_enabled = True
        self.awaiting_controller_action: str | None = None
        self.controller_mapping = {
            "move_left": {"type": "hat", "index": 0, "value": (-1, 0)},
            "move_right": {"type": "hat", "index": 0, "value": (1, 0)},
            "soft_drop": {"type": "hat", "index": 0, "value": (0, -1)},
            "rotate": {"type": "button", "index": 0},
            "hard_drop": {"type": "button", "index": 1},
            "hold": {"type": "button", "index": 2},
            "pause": {"type": "button", "index": 7},
            "restart": {"type": "button", "index": 6},
            "rewind": {"type": "button", "index": 3},
        }
        self.controller_action_labels = {
            "move_left": "Move Left",
            "move_right": "Move Right",
            "soft_drop": "Soft Drop",
            "rotate": "Rotate",
            "hard_drop": "Hard Drop",
            "hold": "Hold",
            "pause": "Pause / Resume",
            "restart": "Restart",
            "rewind": "Rewind",
        }
        pygame.joystick.init()
        self.joystick: Any = None
        self.init_controller()

    def init_controller(self) -> None:
        """Initialize the first available controller"""
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
        else:
            self.joystick = None

    def handle_controller_state(self, logic: TetrisLogic) -> None:
        """Handle held controller inputs for continuous movement"""
        if not self.controller_enabled or self.joystick is None:
            return

        move_left = self.controller_mapping.get("move_left")
        move_right = self.controller_mapping.get("move_right")
        soft_drop = self.controller_mapping.get("soft_drop")

        if move_left and move_left.get("type") == "hat":
            if (
                self.joystick.get_hat(int(cast(int, move_left["index"])))
                == move_left.get("value")
            ):
                if logic.valid_move(logic.current_piece, x_offset=-1):
                    logic.current_piece.x -= 1
                    pygame.time.wait(100)

        if move_right and move_right.get("type") == "hat":
            if (
                self.joystick.get_hat(int(cast(int, move_right["index"])))
                == move_right.get("value")
            ):
                if logic.valid_move(logic.current_piece, x_offset=1):
                    logic.current_piece.x += 1
                    pygame.time.wait(100)

        if soft_drop and soft_drop.get("type") == "hat":
            if (
                self.joystick.get_hat(int(cast(int, soft_drop["index"])))
                == soft_drop.get("value")
            ):
                if logic.valid_move(logic.current_piece, y_offset=1):
                    logic.current_piece.y += 1
                    logic.score += 1
                pygame.time.wait(50)

    def trigger_action(
        self, action: str, logic: TetrisLogic, game_state_manager: Any
    ) -> None:
        """Execute an action from controller or keyboard"""
        if action == "pause":
            game_state_manager.toggle_pause()
            return

        if action == "restart":
            game_state_manager.restart_game()
            return

        if action == "rewind":
            if game_state_manager.state == GameState.PLAYING:
                logic.rewind()
            return

        if game_state_manager.state != GameState.PLAYING:
            return

        if action == "move_left" and logic.valid_move(
            logic.current_piece, x_offset=-1
        ):
            logic.current_piece.x -= 1
        elif action == "move_right" and logic.valid_move(
            logic.current_piece, x_offset=1
        ):
            logic.current_piece.x += 1
        elif action == "soft_drop":
            if logic.valid_move(logic.current_piece, y_offset=1):
                logic.current_piece.y += 1
                logic.score += 1
        elif action == "rotate" and logic.valid_move(
            logic.current_piece, rotation_offset=1
        ):
            logic.current_piece.rotate()
        elif action == "hard_drop":
            logic.hard_drop()
        elif action == "hold":
            logic.hold_piece()

    def process_events(
        self,
        events: list[pygame.event.Event],
        logic: TetrisLogic,
        game_state_manager: Any,
    ) -> None:
        """Process all input events"""
        for event in events:
            if event.type in {pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED}:
                self.init_controller()

            if event.type in [pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION]:
                self.handle_controller_event(event, logic, game_state_manager)

            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event, logic, game_state_manager)

    def handle_keydown(
        self, event: pygame.event.Event, logic: TetrisLogic, game_state_manager: Any
    ) -> None:
        """Handle key press events"""
        if event.key == pygame.K_r:
            game_state_manager.restart_game()
            return

        if event.key == pygame.K_p:
            game_state_manager.toggle_pause()
            return

        if game_state_manager.state == GameState.GAME_OVER:
            if event.key == pygame.K_RETURN:
                game_state_manager.state = GameState.MENU
            return

        if game_state_manager.state != GameState.PLAYING:
            return

        if event.key == pygame.K_UP:
            if logic.valid_move(logic.current_piece, rotation_offset=1):
                logic.current_piece.rotate()
        elif event.key == pygame.K_SPACE:
            logic.hard_drop()
        elif event.key == pygame.K_c:
            logic.hold_piece()
        elif event.key == pygame.K_b:
            logic.rewind()

    def handle_controller_event(
        self, event: pygame.event.Event, logic: TetrisLogic, game_state_manager: Any
    ) -> None:
        """Handle controller input events"""
        if self.joystick is None:
            return

        if not self.controller_enabled:
            return

        if event.type == pygame.JOYBUTTONDOWN:
            for action, binding in self.controller_mapping.items():
                if (
                    binding.get("type") == "button"
                    and binding.get("index") == event.button
                ):
                    self.trigger_action(action, logic, game_state_manager)
        elif event.type == pygame.JOYHATMOTION:
            for action, binding in self.controller_mapping.items():
                if binding.get("type") == "hat" and binding.get("index") == event.hat:
                    if binding.get("value") == event.value:
                        self.trigger_action(action, logic, game_state_manager)

    def apply_controller_binding(self, event: pygame.event.Event) -> bool:
        """Bind the awaiting action to the next controller input"""
        if not self.awaiting_controller_action:
            return False

        action = self.awaiting_controller_action

        if event.type == pygame.JOYBUTTONDOWN:
            self.controller_mapping[action] = {"type": "button", "index": event.button}
            self.awaiting_controller_action = None
            return True

        if event.type == pygame.JOYHATMOTION:
            if event.value == (0, 0):
                return False
            self.controller_mapping[action] = {
                "type": "hat",
                "index": event.hat,
                "value": event.value,
            }
            self.awaiting_controller_action = None
            return True

        return False

    def get_binding_label(self, action: str) -> str:
        """Readable label for a controller binding"""
        binding = self.controller_mapping.get(action)
        if not binding:
            return "Unbound"
        if binding.get("type") == "button":
            return f"Button {binding.get('index')}"
        if binding.get("type") == "hat":
            value = binding.get("value")
            return f"D-pad {binding.get('index')} {value}"
        return "Unbound"
