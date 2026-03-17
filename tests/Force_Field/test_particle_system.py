"""Tests for games.Force_Field.src.particle_system (Particle and ParticleSystem)."""

from __future__ import annotations

from games.Force_Field.src.particle_system import Particle, ParticleSystem


class TestParticle:
    def test_init_defaults(self) -> None:
        p = Particle(10.0, 20.0)
        assert p.x == 10.0
        assert p.y == 20.0
        assert p.dx == 0.0
        assert p.dy == 0.0
        assert p.timer == 30
        assert p.ptype == "normal"

    def test_init_with_fade_color(self) -> None:
        p = Particle(0.0, 0.0, fade_color=(100, 100, 100))
        assert p.fade_color == (100, 100, 100)

    def test_init_fade_color_defaults_to_color(self) -> None:
        p = Particle(0.0, 0.0, color=(200, 100, 50))
        assert p.fade_color == (200, 100, 50)

    def test_update_normal_returns_true_while_alive(self) -> None:
        p = Particle(0.0, 0.0, dx=1.0, dy=0.0, timer=5)
        result = p.update()
        assert result is True
        assert p.timer == 4
        assert p.x == 1.0

    def test_update_normal_applies_gravity(self) -> None:
        p = Particle(0.0, 0.0, dy=0.0, gravity=1.0, timer=5)
        p.update()
        assert p.dy == 1.0  # Gravity applied

    def test_update_returns_false_when_timer_reaches_zero(self) -> None:
        p = Particle(0.0, 0.0, timer=1)
        result = p.update()
        assert result is False
        assert p.timer == 0

    def test_update_non_normal_ptype_skips_position(self) -> None:
        p = Particle(5.0, 5.0, dx=10.0, dy=10.0, timer=3, ptype="laser")
        initial_x = p.x
        p.update()
        assert p.x == initial_x  # laser type doesn't move

    def test_update_rotation(self) -> None:
        p = Particle(0.0, 0.0, rotation=0.0, rotation_speed=0.5, timer=5)
        p.update()
        assert p.rotation == 0.5

    def test_update_size_shrinks(self) -> None:
        # life_ratio is computed then timer decrements, so size at tick N
        # corresponds to timer(N-1)/max_timer. We need 2 ticks to see shrink.
        p = Particle(0.0, 0.0, size=10.0, timer=10)
        p.update()  # size = 10 * (10/10) = 10 (same), timer -> 9
        size_after_first = p.size
        p.update()  # size = 10 * (9/10) = 9, timer -> 8
        assert p.size < size_after_first

    def test_get_current_color_with_same_fade_color(self) -> None:
        p = Particle(0.0, 0.0, color=(255, 100, 0), timer=10)
        color = p.get_current_color()
        assert len(color) == 4
        assert color[3] == 255  # Full alpha at start

    def test_get_current_color_with_fade(self) -> None:
        p = Particle(0.0, 0.0, color=(255, 0, 0), timer=10, fade_color=(0, 0, 255))
        color = p.get_current_color()
        assert len(color) == 4

    def test_get_current_color_at_zero_timer(self) -> None:
        p = Particle(0.0, 0.0, color=(255, 100, 0), timer=1)
        p.update()  # timer now 0
        color = p.get_current_color()
        assert color[3] == 0  # Alpha = 0 at end of life


class TestParticleSystem:
    def test_init_empty(self) -> None:
        ps = ParticleSystem()
        assert ps.particles == []

    def test_add_particle(self) -> None:
        ps = ParticleSystem()
        ps.add_particle(10.0, 20.0, 1.0, 0.0, (255, 0, 0))
        assert len(ps.particles) == 1

    def test_add_particle_with_options(self) -> None:
        ps = ParticleSystem()
        ps.add_particle(
            10.0,
            20.0,
            1.0,
            0.0,
            (255, 0, 0),
            timer=60,
            size=5.0,
            gravity=0.1,
            fade_color=(100, 0, 0),
            rotation_speed=0.2,
        )
        p = ps.particles[0]
        assert p.timer == 60
        assert p.gravity == 0.1

    def test_add_plasma_particle(self) -> None:
        ps = ParticleSystem()
        ps.add_plasma_particle(5.0, 5.0, 1.0, 0.0)
        # Should add 3 particles total (1 main + 2 sparks)
        assert len(ps.particles) == 3

    def test_add_spark_burst(self) -> None:
        ps = ParticleSystem()
        ps.add_spark_burst(10.0, 10.0, count=5)
        assert len(ps.particles) == 5

    def test_add_laser(self) -> None:
        ps = ParticleSystem()
        ps.add_laser((0.0, 0.0), (100.0, 100.0), (255, 0, 0), timer=10, width=2)
        assert len(ps.particles) == 1
        p = ps.particles[0]
        assert p.ptype == "laser"
        assert p.start_pos == (0.0, 0.0)
        assert p.end_pos == (100.0, 100.0)

    def test_add_explosion_default_color(self) -> None:
        ps = ParticleSystem()
        ps.add_explosion(50.0, 50.0, count=10)
        assert len(ps.particles) == 10

    def test_add_explosion_with_color(self) -> None:
        ps = ParticleSystem()
        ps.add_explosion(50.0, 50.0, count=5, color=(255, 0, 0))
        assert len(ps.particles) == 5
        for p in ps.particles:
            assert p.color == (255, 0, 0)

    def test_add_victory_fireworks(self) -> None:
        ps = ParticleSystem()
        ps.add_victory_fireworks()
        assert len(ps.particles) == 50

    def test_update_removes_expired_particles(self) -> None:
        ps = ParticleSystem()
        # Add one particle that will die after 1 tick
        ps.add_particle(0.0, 0.0, 0.0, 0.0, (255, 0, 0), timer=1)
        # Add one that survives longer
        ps.add_particle(0.0, 0.0, 0.0, 0.0, (0, 255, 0), timer=50)
        ps.update()
        assert len(ps.particles) == 1
        assert ps.particles[0].color == (0, 255, 0)

    def test_update_all_dead(self) -> None:
        ps = ParticleSystem()
        ps.add_particle(0.0, 0.0, 0.0, 0.0, (255, 0, 0), timer=1)
        ps.update()
        assert ps.particles == []
