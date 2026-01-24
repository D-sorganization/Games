"""Base input manager with common functionality for all games."""

from __future__ import annotations

import json
import logging
import os
from typing import ClassVar

import pygame

logger = logging.getLogger(__name__)


class InputManagerBase:
    """Base class for managing input bindings and state."""

    # Subclasses should override this
    DEFAULT_BINDINGS: ClassVar[dict[str, int]] = {}

    def __init__(self, config_file: str = "keybindings.json"):
        """Initialize the input manager.

        Args:
            config_file: Path to the keybindings JSON file.
        """
        self.config_file = config_file
        self.bindings: dict[str, int] = self.DEFAULT_BINDINGS.copy()
        self.load_config()

        # Mouse settings
        self.mouse_sensitivity = 1.0
        self.invert_y = False

    def load_config(self) -> None:
        """Load bindings from disk."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file) as f:
                    data = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for action, key in data.get("bindings", {}).items():
                        if action in self.bindings:
                            self.bindings[action] = key
            except (OSError, json.JSONDecodeError):
                logger.exception("Failed to load keybindings")

    def save_config(self) -> None:
        """Save bindings to disk."""
        try:
            with open(self.config_file, "w") as f:
                json.dump({"bindings": self.bindings}, f, indent=4)
        except OSError:
            logger.exception("Failed to save keybindings")

    def is_action_pressed(self, action: str) -> bool:
        """Check if the key for an action is currently held down."""
        keys = pygame.key.get_pressed()
        key_code = self.bindings.get(action)
        if key_code is not None and 0 <= key_code < len(keys):
            return bool(keys[key_code])
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
        return str(pygame.key.name(key_code).upper())

    def bind_key(self, action: str, key_code: int) -> None:
        """Rebind an action to a new key."""
        if action in self.bindings:
            self.bindings[action] = key_code
