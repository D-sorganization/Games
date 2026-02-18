"""Tests for component mixins.

Covers Positioned, HasHealth, Collidable, Animated, HasVelocity.
"""

import pytest

from games.shared.components import (
    Animated,
    Collidable,
    HasHealth,
    HasVelocity,
    Positioned,
)
from games.shared.contracts import ContractViolation

# --- Positioned ---


class TestPositioned:
    def test_default_position(self):
        p = Positioned()
        assert p.x == 0.0
        assert p.y == 0.0

    def test_custom_position(self):
        p = Positioned(x=3.0, y=4.0)
        assert p.x == 3.0
        assert p.y == 4.0

    def test_distance_to(self):
        a = Positioned(x=0, y=0)
        b = Positioned(x=3, y=4)
        assert abs(a.distance_to(b) - 5.0) < 1e-6

    def test_distance_to_self(self):
        p = Positioned(x=5, y=5)
        assert p.distance_to(p) == 0.0

    def test_move_toward(self):
        p = Positioned(x=0, y=0)
        p.move_toward(10.0, 0.0, 3.0)
        assert abs(p.x - 3.0) < 1e-6
        assert abs(p.y) < 1e-6

    def test_move_toward_caps_at_target(self):
        p = Positioned(x=0, y=0)
        p.move_toward(1.0, 0.0, 100.0)
        assert abs(p.x - 1.0) < 1e-6

    def test_move_toward_negative_speed_raises(self):
        p = Positioned()
        with pytest.raises(ContractViolation):
            p.move_toward(1.0, 1.0, -1.0)


# --- HasHealth ---


class TestHasHealth:
    def test_initial_health(self):
        h = HasHealth(max_health=50.0)
        assert h.health == 50.0
        assert h.alive

    def test_take_damage(self):
        h = HasHealth()
        killed = h.take_damage(30.0)
        assert not killed
        assert abs(h.health - 70.0) < 1e-6

    def test_take_damage_kills(self):
        h = HasHealth(max_health=50.0)
        killed = h.take_damage(50.0)
        assert killed
        assert not h.alive
        assert h.health == 0

    def test_overkill_clamps_at_zero(self):
        h = HasHealth()
        h.take_damage(999.0)
        assert h.health == 0

    def test_dead_entity_ignores_damage(self):
        h = HasHealth()
        h.take_damage(100.0)
        result = h.take_damage(50.0)
        assert not result

    def test_heal(self):
        h = HasHealth()
        h.take_damage(40.0)
        h.heal(20.0)
        assert abs(h.health - 80.0) < 1e-6

    def test_heal_caps_at_max(self):
        h = HasHealth(max_health=100.0)
        h.take_damage(10.0)
        h.heal(50.0)
        assert h.health == 100.0

    def test_heal_dead_does_nothing(self):
        h = HasHealth()
        h.take_damage(100.0)
        h.heal(50.0)
        assert h.health == 0

    def test_health_fraction(self):
        h = HasHealth(max_health=200.0)
        h.take_damage(50.0)
        assert abs(h.health_fraction - 0.75) < 1e-6

    def test_negative_damage_raises(self):
        h = HasHealth()
        with pytest.raises(ContractViolation):
            h.take_damage(-10.0)

    def test_zero_max_health_raises(self):
        with pytest.raises(ContractViolation):
            HasHealth(max_health=0)


# --- Collidable ---


class TestCollidable:
    def test_overlaps(self):
        class Entity(Positioned, Collidable):
            pass

        a = Entity(x=0, y=0, radius=1.0)
        b = Entity(x=1.0, y=0, radius=1.0)
        assert a.overlaps(b)

    def test_no_overlap(self):
        class Entity(Positioned, Collidable):
            pass

        a = Entity(x=0, y=0, radius=0.5)
        b = Entity(x=10, y=0, radius=0.5)
        assert not a.overlaps(b)

    def test_zero_radius_raises(self):
        with pytest.raises(ContractViolation):
            Collidable(radius=0)


# --- Animated ---


class TestAnimated:
    def test_default_animation(self):
        a = Animated()
        assert a.current_animation == "idle"
        assert a.animation_timer == 0.0

    def test_advance_animation(self):
        a = Animated()
        a.advance_animation(0.5)
        assert abs(a.animation_timer - 0.5) < 1e-6

    def test_advance_with_speed(self):
        a = Animated()
        a.animation_speed = 2.0
        a.advance_animation(1.0)
        assert abs(a.animation_timer - 2.0) < 1e-6

    def test_set_animation_resets_timer(self):
        a = Animated()
        a.advance_animation(5.0)
        a.set_animation("walk")
        assert a.current_animation == "walk"
        assert a.animation_timer == 0.0

    def test_set_same_animation_keeps_timer(self):
        a = Animated()
        a.advance_animation(5.0)
        a.set_animation("idle")
        assert a.animation_timer == 5.0


# --- HasVelocity ---


class TestHasVelocity:
    def test_apply_velocity(self):
        class Entity(Positioned, HasVelocity):
            pass

        e = Entity(x=0, y=0)
        e.vx = 3.0
        e.vy = 4.0
        e.apply_velocity()
        assert abs(e.x - 3.0) < 1e-6
        assert abs(e.y - 4.0) < 1e-6

    def test_apply_friction(self):
        class Entity(Positioned, HasVelocity):
            pass

        e = Entity(x=0, y=0)
        e.vx = 10.0
        e.vy = 10.0
        e.apply_friction(0.5)
        assert abs(e.vx - 5.0) < 1e-6
        assert abs(e.vy - 5.0) < 1e-6


# --- Composition ---


class TestComposition:
    def test_full_entity(self):
        class Enemy(Positioned, HasHealth, Collidable, Animated, HasVelocity):
            pass

        e = Enemy(x=5, y=10, max_health=200, radius=0.8)
        assert e.x == 5
        assert e.health == 200
        assert abs(e.collision_radius - 0.8) < 1e-6
        assert e.current_animation == "idle"
        assert e.vx == 0.0

    def test_partial_composition(self):
        class Pickup(Positioned, Collidable):
            pass

        p = Pickup(x=1, y=2, radius=0.3)
        assert p.x == 1
        assert abs(p.collision_radius - 0.3) < 1e-6
