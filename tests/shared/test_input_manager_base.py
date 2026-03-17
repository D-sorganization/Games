"""Tests for games.shared.input_manager_base module.

Tests key binding management and config persistence.
"""

from __future__ import annotations

import json
import os
from typing import ClassVar
from unittest.mock import MagicMock, patch

import pygame

from games.shared.input_manager_base import InputManagerBase

# ---------------------------------------------------------------------------
# Concrete subclass for testing
# ---------------------------------------------------------------------------


class ConcreteInputManager(InputManagerBase):
    """Concrete InputManager with test bindings."""

    DEFAULT_BINDINGS: ClassVar[dict[str, int]] = {
        "forward": 119,  # w
        "back": 115,  # s
        "left": 97,  # a
        "right": 100,  # d
        "shoot": 32,  # space
    }


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestInit:
    """Tests for InputManagerBase initialization."""

    def test_default_bindings_copied(self) -> None:
        """Bindings should be a copy of DEFAULT_BINDINGS."""
        mgr = ConcreteInputManager(config_file="__nonexistent__.json")
        assert mgr.bindings == ConcreteInputManager.DEFAULT_BINDINGS
        # Verify it's a copy, not the same dict
        assert mgr.bindings is not ConcreteInputManager.DEFAULT_BINDINGS

    def test_mouse_sensitivity_default(self) -> None:
        """Default mouse sensitivity should be 1.0."""
        mgr = ConcreteInputManager(config_file="__nonexistent__.json")
        assert mgr.mouse_sensitivity == 1.0

    def test_invert_y_default_false(self) -> None:
        """Default invert Y should be False."""
        mgr = ConcreteInputManager(config_file="__nonexistent__.json")
        assert mgr.invert_y is False


# ---------------------------------------------------------------------------
# Config file operations
# ---------------------------------------------------------------------------


class TestConfigPersistence:
    """Tests for save_config and load_config."""

    def test_save_and_load_roundtrip(self, tmp_path: object) -> None:
        """Saved config should be loadable and restore bindings."""
        config_file = os.path.join(str(tmp_path), "test_keys.json")
        mgr = ConcreteInputManager(config_file=config_file)
        mgr.bindings["forward"] = 999
        mgr.save_config()

        # Create new manager that loads the saved config
        mgr2 = ConcreteInputManager(config_file=config_file)
        assert mgr2.bindings["forward"] == 999

    def test_load_missing_file_uses_defaults(self) -> None:
        """Missing config file should leave defaults intact."""
        mgr = ConcreteInputManager(config_file="__definitely_missing__.json")
        assert mgr.bindings == ConcreteInputManager.DEFAULT_BINDINGS

    def test_load_invalid_json_uses_defaults(self, tmp_path: object) -> None:
        """Invalid JSON should fall back to defaults."""
        config_file = os.path.join(str(tmp_path), "bad.json")
        with open(config_file, "w") as f:
            f.write("not valid json {{{")
        mgr = ConcreteInputManager(config_file=config_file)
        assert mgr.bindings == ConcreteInputManager.DEFAULT_BINDINGS

    def test_load_partial_config_merges(self, tmp_path: object) -> None:
        """Config with only some keys should merge with defaults."""
        config_file = os.path.join(str(tmp_path), "partial.json")
        with open(config_file, "w") as f:
            json.dump({"bindings": {"forward": 42}}, f)
        mgr = ConcreteInputManager(config_file=config_file)
        assert mgr.bindings["forward"] == 42
        assert mgr.bindings["back"] == 115  # Default unchanged

    def test_load_ignores_unknown_actions(self, tmp_path: object) -> None:
        config_file = os.path.join(str(tmp_path), "unknown.json")
        with open(config_file, "w") as f:
            json.dump({"bindings": {"forward": 42, "unknown_bob": 99}}, f)
        mgr = ConcreteInputManager(config_file=config_file)
        assert "unknown_bob" not in mgr.bindings

    def test_save_config_oserror(self, tmp_path: object) -> None:
        # Use a directory path to trigger OSError on write
        mgr = ConcreteInputManager(config_file=str(tmp_path))
        # Should not raise exception
        mgr.save_config()


# ---------------------------------------------------------------------------
# Key binding
# ---------------------------------------------------------------------------


class TestBindKey:
    """Tests for bind_key."""

    def test_bind_existing_action(self) -> None:
        """Binding an existing action should update the key."""
        mgr = ConcreteInputManager(config_file="__nonexistent__.json")
        mgr.bind_key("forward", 42)
        assert mgr.bindings["forward"] == 42

    def test_bind_nonexistent_action_is_noop(self) -> None:
        """Binding a nonexistent action should not add it."""
        mgr = ConcreteInputManager(config_file="__nonexistent__.json")
        mgr.bind_key("fly", 999)
        assert "fly" not in mgr.bindings


class TestActionChecks:
    @patch("pygame.key.get_pressed")
    def test_is_action_pressed(self, mock_get_pressed) -> None:
        mgr = ConcreteInputManager(config_file="__nonexistent__.json")
        mgr.bind_key("forward", 10)

        mock_keys = [False] * 20
        mock_keys[10] = True
        mock_get_pressed.return_value = mock_keys

        assert mgr.is_action_pressed("forward") is True
        assert mgr.is_action_pressed("back") is False
        assert mgr.is_action_pressed("nonexistent") is False

    def test_is_action_just_pressed(self) -> None:
        mgr = ConcreteInputManager(config_file="__nonexistent__.json")
        mgr.bind_key("forward", 10)

        event = MagicMock()
        event.type = pygame.KEYDOWN
        event.key = 10
        assert mgr.is_action_just_pressed(event, "forward") is True
        assert mgr.is_action_just_pressed(event, "back") is False

        event.type = pygame.KEYUP
        assert mgr.is_action_just_pressed(event, "forward") is False

    @patch("pygame.key.name")
    def test_get_key_name(self, mock_name) -> None:
        mock_name.return_value = "w"
        mgr = ConcreteInputManager(config_file="__nonexistent__.json")
        mgr.bind_key("forward", 10)

        assert mgr.get_key_name("forward") == "W"
        mock_name.assert_called_with(10)
        assert mgr.get_key_name("nonexistent") == "None"
