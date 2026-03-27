"""Tests for the lightweight EventBus."""

from __future__ import annotations

import pytest

from games.shared.event_bus import EventBus


@pytest.fixture()
def bus() -> EventBus:
    return EventBus()


# ---------------------------------------------------------------------------
# Subscribe / Emit
# ---------------------------------------------------------------------------
class TestSubscribeEmit:
    def test_single_listener_receives_kwargs(self, bus: EventBus) -> None:
        captured: list[dict] = []
        bus.subscribe("hit", lambda **kw: captured.append(kw))
        bus.emit("hit", x=1.5, y=2.5, damage=42)
        assert captured == [{"x": 1.5, "y": 2.5, "damage": 42}]

    def test_multiple_listeners_all_called(self, bus: EventBus) -> None:
        calls: list[str] = []
        bus.subscribe("boom", lambda **kw: calls.append("a"))
        bus.subscribe("boom", lambda **kw: calls.append("b"))
        bus.subscribe("boom", lambda **kw: calls.append("c"))
        bus.emit("boom")
        assert calls == ["a", "b", "c"]

    def test_listeners_called_in_registration_order(self, bus: EventBus) -> None:
        order: list[int] = []

        def _make_cb(idx: int):  # noqa: ANN202
            return lambda **kw: order.append(idx)

        for i in range(5):
            bus.subscribe("seq", _make_cb(i))
        bus.emit("seq")
        assert order == [0, 1, 2, 3, 4]

    def test_different_events_are_independent(self, bus: EventBus) -> None:
        a_calls: list[str] = []
        b_calls: list[str] = []
        bus.subscribe("event_a", lambda **kw: a_calls.append("a"))
        bus.subscribe("event_b", lambda **kw: b_calls.append("b"))
        bus.emit("event_a")
        assert a_calls == ["a"]
        assert b_calls == []

    def test_emit_with_no_kwargs(self, bus: EventBus) -> None:
        captured: list[dict] = []
        bus.subscribe("simple", lambda **kw: captured.append(kw))
        bus.emit("simple")
        assert captured == [{}]


# ---------------------------------------------------------------------------
# Emit with no listeners
# ---------------------------------------------------------------------------
class TestEmitNoListeners:
    def test_emit_unknown_event_does_not_raise(self, bus: EventBus) -> None:
        bus.emit("nonexistent", foo="bar")

    def test_emit_returns_none(self, bus: EventBus) -> None:
        result = bus.emit("nothing")
        assert result is None


# ---------------------------------------------------------------------------
# Unsubscribe
# ---------------------------------------------------------------------------
class TestUnsubscribe:
    def test_unsubscribed_callback_not_called(self, bus: EventBus) -> None:
        calls: list[str] = []

        def callback(**kw: object) -> None:
            calls.append("hit")

        bus.subscribe("test", callback)
        bus.unsubscribe("test", callback)
        bus.emit("test")
        assert calls == []

    def test_unsubscribe_nonexistent_callback_does_not_raise(
        self, bus: EventBus
    ) -> None:
        bus.unsubscribe("test", lambda **kw: None)

    def test_unsubscribe_from_nonexistent_event_does_not_raise(
        self, bus: EventBus
    ) -> None:
        bus.unsubscribe("never_registered", lambda **kw: None)

    def test_unsubscribe_only_removes_target(self, bus: EventBus) -> None:
        calls_a: list[str] = []
        calls_b: list[str] = []

        def cb_a(**kw: object) -> None:
            calls_a.append("a")

        def cb_b(**kw: object) -> None:
            calls_b.append("b")

        bus.subscribe("ev", cb_a)
        bus.subscribe("ev", cb_b)
        bus.unsubscribe("ev", cb_a)
        bus.emit("ev")
        assert calls_a == []
        assert calls_b == ["b"]

    def test_unsubscribe_duplicate_removes_first_occurrence(
        self, bus: EventBus
    ) -> None:
        calls: list[str] = []

        def cb(**kw: object) -> None:
            calls.append("x")

        bus.subscribe("dup", cb)
        bus.subscribe("dup", cb)
        bus.unsubscribe("dup", cb)
        bus.emit("dup")
        assert calls == ["x"]


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------
class TestClear:
    def test_clear_removes_all_listeners(self, bus: EventBus) -> None:
        calls: list[str] = []
        bus.subscribe("a", lambda **kw: calls.append("a"))
        bus.subscribe("b", lambda **kw: calls.append("b"))
        bus.clear()
        bus.emit("a")
        bus.emit("b")
        assert calls == []

    def test_clear_allows_resubscription(self, bus: EventBus) -> None:
        calls: list[str] = []
        bus.subscribe("ev", lambda **kw: calls.append("old"))
        bus.clear()
        bus.subscribe("ev", lambda **kw: calls.append("new"))
        bus.emit("ev")
        assert calls == ["new"]

    def test_clear_on_empty_bus_does_not_raise(self, bus: EventBus) -> None:
        bus.clear()


# ---------------------------------------------------------------------------
# Kwargs passing
# ---------------------------------------------------------------------------
class TestKwargsPassing:
    def test_string_kwargs(self, bus: EventBus) -> None:
        captured: list[dict] = []
        bus.subscribe("msg", lambda **kw: captured.append(kw))
        bus.emit("msg", text="hello", color="red")
        assert captured == [{"text": "hello", "color": "red"}]

    def test_numeric_kwargs(self, bus: EventBus) -> None:
        captured: list[dict] = []
        bus.subscribe("pos", lambda **kw: captured.append(kw))
        bus.emit("pos", x=3.14, y=-2.71, z=0)
        assert captured == [{"x": 3.14, "y": -2.71, "z": 0}]

    def test_mixed_type_kwargs(self, bus: EventBus) -> None:
        captured: list[dict] = []
        bus.subscribe("complex", lambda **kw: captured.append(kw))
        bus.emit("complex", name="bot", hp=100, pos=(1.0, 2.0), alive=True)
        assert captured[0]["name"] == "bot"
        assert captured[0]["hp"] == 100
        assert captured[0]["pos"] == (1.0, 2.0)
        assert captured[0]["alive"] is True

    def test_each_listener_gets_same_kwargs(self, bus: EventBus) -> None:
        results: list[dict] = []
        bus.subscribe("shared", lambda **kw: results.append(kw))
        bus.subscribe("shared", lambda **kw: results.append(kw))
        bus.emit("shared", val=42)
        assert results == [{"val": 42}, {"val": 42}]


# ---------------------------------------------------------------------------
# Multiple emits
# ---------------------------------------------------------------------------
class TestMultipleEmits:
    def test_listener_called_on_every_emit(self, bus: EventBus) -> None:
        count: list[int] = []
        bus.subscribe("tick", lambda **kw: count.append(1))
        for _ in range(5):
            bus.emit("tick")
        assert len(count) == 5

    def test_different_kwargs_per_emit(self, bus: EventBus) -> None:
        received: list[int] = []
        bus.subscribe("num", lambda **kw: received.append(kw["n"]))
        for i in range(3):
            bus.emit("num", n=i)
        assert received == [0, 1, 2]
