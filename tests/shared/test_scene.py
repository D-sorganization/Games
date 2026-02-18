"""Tests for SceneManager — scene registration, transitions, lifecycle."""

import pytest

from games.shared.contracts import ContractViolation
from games.shared.scene import SceneManager


class FakeScene:
    """Minimal Scene implementation for testing."""

    def __init__(self, name: str = "fake") -> None:
        self.name = name
        self.entered = False
        self.exited = False
        self.events_received: list = []
        self.updated = False
        self.rendered = False
        self.transition_on_events: str | None = None
        self.transition_on_update: str | None = None

    def on_enter(self) -> None:
        self.entered = True

    def on_exit(self) -> None:
        self.exited = True

    def handle_events(self, events: list) -> str | None:
        self.events_received = events
        return self.transition_on_events

    def update(self) -> str | None:
        self.updated = True
        return self.transition_on_update

    def render(self, screen: object) -> None:
        self.rendered = True


# --- Registration ---


class TestRegistration:
    def test_register_scene(self):
        mgr = SceneManager()
        mgr.register("menu", FakeScene("menu"))
        assert mgr.current_scene_name is None

    def test_register_none_name_raises(self):
        mgr = SceneManager()
        with pytest.raises(ContractViolation):
            mgr.register(None, FakeScene())

    def test_register_none_scene_raises(self):
        mgr = SceneManager()
        with pytest.raises(ContractViolation):
            mgr.register("x", None)


# --- Switching ---


class TestSwitching:
    def test_switch_to_calls_on_enter(self):
        mgr = SceneManager()
        scene = FakeScene()
        mgr.register("menu", scene)
        mgr.switch_to("menu")
        assert scene.entered
        assert mgr.current_scene_name == "menu"

    def test_switch_calls_on_exit_then_on_enter(self):
        mgr = SceneManager()
        scene_a = FakeScene("a")
        scene_b = FakeScene("b")
        mgr.register("a", scene_a)
        mgr.register("b", scene_b)
        mgr.switch_to("a")
        mgr.switch_to("b")
        assert scene_a.exited
        assert scene_b.entered

    def test_switch_tracks_previous(self):
        mgr = SceneManager()
        mgr.register("a", FakeScene())
        mgr.register("b", FakeScene())
        mgr.switch_to("a")
        mgr.switch_to("b")
        assert mgr.previous_scene_name == "a"
        assert mgr.current_scene_name == "b"

    def test_switch_to_unregistered_raises(self):
        mgr = SceneManager()
        with pytest.raises(KeyError):
            mgr.switch_to("nonexistent")

    def test_switch_to_none_raises(self):
        mgr = SceneManager()
        with pytest.raises(ContractViolation):
            mgr.switch_to(None)


# --- Tick ---


class TestTick:
    def test_tick_returns_false_when_no_scene(self):
        mgr = SceneManager()
        assert mgr.tick(None, []) is False

    def test_tick_renders(self):
        mgr = SceneManager()
        scene = FakeScene()
        mgr.register("play", scene)
        mgr.switch_to("play")
        result = mgr.tick("screen", [])
        assert result is True
        assert scene.rendered
        assert scene.updated

    def test_tick_passes_events(self):
        mgr = SceneManager()
        scene = FakeScene()
        mgr.register("play", scene)
        mgr.switch_to("play")
        events = ["event1", "event2"]
        mgr.tick("screen", events)
        assert scene.events_received == events

    def test_tick_handle_events_triggers_transition(self):
        mgr = SceneManager()
        scene_a = FakeScene()
        scene_a.transition_on_events = "b"
        scene_b = FakeScene()
        mgr.register("a", scene_a)
        mgr.register("b", scene_b)
        mgr.switch_to("a")
        mgr.tick("screen", [])
        assert mgr.current_scene_name == "b"
        assert scene_b.entered

    def test_tick_update_triggers_transition(self):
        mgr = SceneManager()
        scene_a = FakeScene()
        scene_a.transition_on_update = "b"
        scene_b = FakeScene()
        mgr.register("a", scene_a)
        mgr.register("b", scene_b)
        mgr.switch_to("a")
        mgr.tick("screen", [])
        assert mgr.current_scene_name == "b"

    def test_current_scene_property(self):
        mgr = SceneManager()
        scene = FakeScene()
        mgr.register("x", scene)
        mgr.switch_to("x")
        assert mgr.current_scene is scene
