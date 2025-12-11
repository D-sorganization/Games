import pygame
import json
import os
from typing import Dict, Any

class InputManager:
    """Manages input bindings and state."""
    
    DEFAULT_BINDINGS = {
        "move_forward": pygame.K_w,
        "move_backward": pygame.K_s,
        "strafe_left": pygame.K_a,
        "strafe_right": pygame.K_d,
        "turn_left": pygame.K_LEFT,
        "turn_right": pygame.K_RIGHT,
        "look_up": pygame.K_UP,
        "look_down": pygame.K_DOWN,
        "shoot": pygame.K_SPACE, # Primary shoot (also Mouse 1)
        "reload": pygame.K_r,
        "zoom": pygame.K_z,
        "bomb": pygame.K_f,
        "shield": pygame.K_LSHIFT, # Shield is bound to Left Shift; shoot is bound to Space and Numpad 0.
        "shoot_alt": pygame.K_KP0,
        "pause": pygame.K_ESCAPE,
        "interact": pygame.K_e,
        "weapon_1": pygame.K_1,
        "weapon_2": pygame.K_2,
        "weapon_3": pygame.K_3,
        "weapon_4": pygame.K_4,
        "weapon_5": pygame.K_5,
    }

    def __init__(self, config_file: str = "keybindings.json"):
        self.config_file = config_file
        self.bindings: Dict[str, int] = self.DEFAULT_BINDINGS.copy()
        self.load_config()
        
        # Mouse settings
        self.mouse_sensitivity = 1.0
        self.invert_y = False

    def load_config(self) -> None:
        """Load bindings from disk."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for action, key in data.get("bindings", {}).items():
                        if action in self.bindings:
                            self.bindings[action] = key
            except Exception as e:
                print(f"Failed to load keybindings: {e}")

    def save_config(self) -> None:
        """Save bindings to disk."""
        try:
            with open(self.config_file, "w") as f:
                json.dump({"bindings": self.bindings}, f, indent=4)
        except Exception as e:
            print(f"Failed to save keybindings: {e}")

    def is_action_pressed(self, action: str) -> bool:
        """Check if the key for an action is currently held down."""
        keys = pygame.key.get_pressed()
        key_code = self.bindings.get(action)
        if key_code is not None and 0 <= key_code < len(keys):
            return keys[key_code]
        return False

    def is_action_just_pressed(self, event: pygame.event.Event, action: str) -> bool:
        """Check if an action was just pressed in an event loop."""
        if event.type == pygame.KEYDOWN:
            if event.key == self.bindings.get(action):
                return True
        return False
    
    def get_key_name(self, action: str) -> str:
        """Get human-readable name of the key bound to an action."""
        key_code = self.bindings.get(action)
        if key_code is None:
            return "None"
        return pygame.key.name(key_code).upper()

    def bind_key(self, action: str, key_code: int) -> None:
        """Rebind an action to a new key."""
        if action in self.bindings:
            self.bindings[action] = key_code
            self.save_config()
