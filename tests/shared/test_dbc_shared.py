"""Tests for Design by Contract validation in shared modules."""

import pytest

from games.shared.components import Animated, HasVelocity, Positioned
from games.shared.contracts import ContractViolation
from games.shared.particle_system import ParticleSystem

# --- Components DbC ---


class TestAnimatedDbC:
    def test_advance_animation_negative_dt_raises(self):
        a = Animated()
        with pytest.raises(ContractViolation):
            a.advance_animation(-1.0)

    def test_advance_animation_zero_dt_ok(self):
        a = Animated()
        a.advance_animation(0.0)
        assert a.animation_timer == 0.0


class TestHasVelocityDbC:
    def test_apply_friction_above_one_raises(self):
        class Entity(Positioned, HasVelocity):
            pass

        e = Entity()
        with pytest.raises(ContractViolation):
            e.apply_friction(1.5)

    def test_apply_friction_negative_raises(self):
        class Entity(Positioned, HasVelocity):
            pass

        e = Entity()
        with pytest.raises(ContractViolation):
            e.apply_friction(-0.1)

    def test_apply_friction_zero_ok(self):
        class Entity(Positioned, HasVelocity):
            pass

        e = Entity()
        e.vx = 10.0
        e.apply_friction(0.0)
        assert e.vx == 0.0

    def test_apply_friction_one_ok(self):
        class Entity(Positioned, HasVelocity):
            pass

        e = Entity()
        e.vx = 10.0
        e.apply_friction(1.0)
        assert e.vx == 10.0


# --- ParticleSystem DbC ---


class TestParticleSystemDbC:
    def test_add_explosion_zero_count_raises(self):
        ps = ParticleSystem()
        with pytest.raises(ContractViolation):
            ps.add_explosion(0, 0, count=0)

    def test_add_explosion_negative_speed_raises(self):
        ps = ParticleSystem()
        with pytest.raises(ContractViolation):
            ps.add_explosion(0, 0, speed=-1.0)

    def test_add_laser_zero_timer_raises(self):
        ps = ParticleSystem()
        with pytest.raises(ContractViolation):
            ps.add_laser((0, 0), (1, 1), (255, 0, 0), timer=0)

    def test_add_laser_zero_width_raises(self):
        ps = ParticleSystem()
        with pytest.raises(ContractViolation):
            ps.add_laser((0, 0), (1, 1), (255, 0, 0), width=0)

    def test_add_trace_zero_timer_raises(self):
        ps = ParticleSystem()
        with pytest.raises(ContractViolation):
            ps.add_trace((0, 0), (1, 1), (255, 0, 0), timer=0)

    def test_add_world_explosion_zero_count_raises(self):
        ps = ParticleSystem()
        with pytest.raises(ContractViolation):
            ps.add_world_explosion(0, 0, 0, count=0)

    def test_add_world_explosion_negative_speed_raises(self):
        ps = ParticleSystem()
        with pytest.raises(ContractViolation):
            ps.add_world_explosion(0, 0, 0, speed=-1.0)
