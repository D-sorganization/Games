"""Tests for games.shared.input_manager_base module.

Tests key binding management and config persistence.
"""

from __future__ import annotations

import json
import os
from typing import ClassVar

from games.shared.input_manager_base import InputManagerBase

# ---------------------------------------------------------------------------
# Concrete subclass for testing
# ---------------------------------------------------------------------------


class MockInputManager(InputManagerBase):
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
        mgr = MockInputManager(config_file="__nonexistent__.json")
        assert mgr.bindings == MockInputManager.DEFAULT_BINDINGS
        # Verify it's a copy, not the same dict
        assert mgr.bindings is not MockInputManager.DEFAULT_BINDINGS

    def test_mouse_sensitivity_default(self) -> None:
        """Default mouse sensitivity should be 1.0."""
        mgr = MockInputManager(config_file="__nonexistent__.json")
        assert mgr.mouse_sensitivity == 1.0

    def test_invert_y_default_false(self) -> None:
        """Default invert Y should be False."""
        mgr = MockInputManager(config_file="__nonexistent__.json")
        assert mgr.invert_y is False


# ---------------------------------------------------------------------------
# Config file operations
# ---------------------------------------------------------------------------


class TestConfigPersistence:
    """Tests for save_config and load_config."""

    def test_save_and_load_roundtrip(self, tmp_path: object) -> None:
        """Saved config should be loadable and restore bindings."""
        config_file = os.path.join(str(tmp_path), "test_keys.json")
        mgr = MockInputManager(config_file=config_file)
        mgr.bindings["forward"] = 999
        mgr.save_config()

        # Create new manager that loads the saved config
        mgr2 = MockInputManager(config_file=config_file)
        assert mgr2.bindings["forward"] == 999

    def test_load_missing_file_uses_defaults(self) -> None:
        """Missing config file should leave defaults intact."""
        mgr = MockInputManager(config_file="__definitely_missing__.json")
        assert mgr.bindings == MockInputManager.DEFAULT_BINDINGS

    def test_load_invalid_json_uses_defaults(self, tmp_path: object) -> None:
        """Invalid JSON should fall back to defaults."""
        config_file = os.path.join(str(tmp_path), "bad.json")
        with open(config_file, "w") as f:
            f.write("not valid json {{{")
        mgr = MockInputManager(config_file=config_file)
        assert mgr.bindings == MockInputManager.DEFAULT_BINDINGS

    def test_load_partial_config_merges(self, tmp_path: object) -> None:
        """Config with only some keys should merge with defaults."""
        config_file = os.path.join(str(tmp_path), "partial.json")
        with open(config_file, "w") as f:
            json.dump({"bindings": {"forward": 42, "unsupported": 100}}, f)
        mgr = MockInputManager(config_file=config_file)
        assert mgr.bindings["forward"] == 42
        assert mgr.bindings["back"] == 115  # Default unchanged
        assert "unsupported" not in mgr.bindings

    def test_save_config_oserror(self, tmp_path: object) -> None:
        """Should catch OSError when saving fails."""
        config_file = os.path.join(str(tmp_path), "no_permission", "test.json")
        mgr = MockInputManager(config_file=config_file)
        mgr.save_config()  # Should trap the error and log, rather than crash


# ---------------------------------------------------------------------------
# Key binding
# ---------------------------------------------------------------------------


class TestBindKey:
    """Tests for bind_key."""

    def test_bind_existing_action(self) -> None:
        """Binding an existing action should update the key."""
        mgr = MockInputManager(config_file="__nonexistent__.json")
        mgr.bind_key("forward", 42)
        assert mgr.bindings["forward"] == 42

    def test_bind_nonexistent_action_is_noop(self) -> None:
        """Binding a nonexistent action should not add it."""
        mgr = MockInputManager(config_file="__nonexistent__.json")
        mgr.bind_key("fly", 999)
        assert "fly" not in mgr.bindings

    def test_is_action_pressed(self) -> None:
        from unittest.mock import patch
        mgr = MockInputManager(config_file="__nonexistent__.json")
        mgr.bindings["forward"] = 2

        # Test pressed
        with patch("games.shared.input_manager_base.pygame.key.get_pressed", return_value=[0, 0, 1, 0]):
            assert mgr.is_action_pressed("forward") is True
            assert mgr.is_action_pressed("back") is False

        # Test out of bounds / bad key
        with patch("games.shared.input_manager_base.pygame.key.get_pressed", return_value=[0, 0]):
            assert mgr.is_action_pressed("forward") is False
            assert mgr.is_action_pressed("unknown") is False

    def test_is_action_just_pressed(self) -> None:
        from unittest.mock import MagicMock
        mgr = MockInputManager(config_file="__nonexistent__.json")
        mgr.bindings["jump"] = 32

        # Make valid event
        import pygame
        ev = MagicMock()
        ev.type = pygame.KEYDOWN
        ev.key = 32
        assert mgr.is_action_just_pressed(ev, "jump") is True

        ev.key = 99
        assert mgr.is_action_just_pressed(ev, "jump") is False

        ev.type = pygame.KEYUP
        assert mgr.is_action_just_pressed(ev, "jump") is False

    def test_get_key_name(self) -> None:
        from unittest.mock import patch
        mgr = MockInputManager(config_file="__nonexistent__.json")
        mgr.bindings["action1"] = 99

        with patch("games.shared.input_manager_base.pygame.key.name", return_value="SPACE"):
            assert mgr.get_key_name("action1") == "SPACE"
            assert mgr.get_key_name("unknown") == "None"
