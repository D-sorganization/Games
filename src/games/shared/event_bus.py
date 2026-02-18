"""Lightweight synchronous event bus for decoupling game subsystems."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any


class EventBus:
    """Simple publish/subscribe event bus.

    Subsystems register callbacks for named events via ``subscribe()``.
    When ``emit()`` is called, every registered callback for that event
    is invoked synchronously with the provided keyword arguments.
    """

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[..., None]]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callable[..., None]) -> None:
        """Register *callback* to be called whenever *event* is emitted."""
        self._listeners[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable[..., None]) -> None:
        """Remove *callback* from *event*.  No-op if not found."""
        try:
            self._listeners[event].remove(callback)
        except ValueError:
            pass

    def emit(self, event: str, **kwargs: Any) -> None:
        """Emit *event*, calling all registered listeners with *kwargs*."""
        for callback in self._listeners[event]:
            callback(**kwargs)

    def clear(self) -> None:
        """Remove all listeners for all events."""
        self._listeners.clear()
