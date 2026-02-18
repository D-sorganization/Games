"""Scene management system for game state transitions.

Provides a SceneManager that handles menu->playing->paused->gameover
transitions. Games register Scene instances and the manager handles
enter/exit lifecycle, event routing, and rendering dispatch.

Usage:
    from games.shared.scene import SceneManager, Scene

    class MenuScene:
        def on_enter(self): ...
        def on_exit(self): ...
        def handle_events(self, events): return None
        def update(self): return None
        def render(self, screen): ...

    manager = SceneManager()
    manager.register("menu", MenuScene())
    manager.switch_to("menu")
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from games.shared.contracts import validate_not_none


@runtime_checkable
class Scene(Protocol):
    """Protocol for a game scene (state)."""

    def on_enter(self) -> None:
        """Called when this scene becomes active."""
        ...

    def on_exit(self) -> None:
        """Called when this scene is deactivated."""
        ...

    def handle_events(self, events: list[Any]) -> str | None:
        """Process input events. Return scene name to transition, or None."""
        ...

    def update(self) -> str | None:
        """Update scene logic. Return scene name to transition, or None."""
        ...

    def render(self, screen: Any) -> None:
        """Render the scene to the given surface."""
        ...


class SceneManager:
    """Manages scene registration, transitions, and lifecycle.

    Scenes are registered by name and activated via switch_to().
    The tick() method runs one frame: handle_events -> update -> render.
    """

    def __init__(self) -> None:
        self._scenes: dict[str, Scene] = {}
        self._current: str | None = None
        self._previous: str | None = None

    @property
    def current_scene_name(self) -> str | None:
        """Name of the currently active scene."""
        return self._current

    @property
    def previous_scene_name(self) -> str | None:
        """Name of the previously active scene."""
        return self._previous

    @property
    def current_scene(self) -> Scene | None:
        """The currently active Scene instance, or None."""
        if self._current is None:
            return None
        return self._scenes.get(self._current)

    def register(self, name: str, scene: Scene) -> None:
        """Register a scene by name."""
        validate_not_none(name, "scene_name")
        validate_not_none(scene, "scene")
        self._scenes[name] = scene

    def switch_to(self, name: str) -> None:
        """Switch to a registered scene, calling on_exit/on_enter."""
        validate_not_none(name, "scene_name")
        if name not in self._scenes:
            raise KeyError(f"Scene '{name}' not registered")
        if self._current and self._current in self._scenes:
            self._scenes[self._current].on_exit()
        self._previous = self._current
        self._current = name
        self._scenes[name].on_enter()

    def tick(self, screen: Any, events: list[Any]) -> bool:
        """Run one frame: handle_events -> update -> render.

        Args:
            screen: The rendering surface to pass to render().
            events: Pre-collected input events for this frame.

        Returns:
            True to continue, False if no scene is active.
        """
        scene = self.current_scene
        if scene is None:
            return False

        next_state = scene.handle_events(events)
        if next_state is not None:
            self.switch_to(next_state)
            return True

        next_state = scene.update()
        if next_state is not None:
            self.switch_to(next_state)
            return True

        scene.render(screen)
        return True
