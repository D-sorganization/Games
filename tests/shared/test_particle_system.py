"""Tests for shared ParticleSystem — 2D particles, world particles, emitters."""

from games.shared.particle_system import Particle, ParticleSystem, WorldParticle

# --- Particle ---


class TestParticle:
    def test_timer_decrements(self):
        p = Particle(0, 0, timer=10)
        p.update()
        assert p.timer == 9

    def test_dies_at_zero_timer(self):
        p = Particle(0, 0, timer=1)
        alive = p.update()
        assert not alive

    def test_position_updates(self):
        p = Particle(0, 0, dx=5.0, dy=-3.0, timer=10)
        p.update()
        assert abs(p.x - 5.0) < 1e-6
        assert abs(p.y - (-3.0)) < 1e-6

    def test_gravity_affects_dy(self):
        p = Particle(0, 0, dy=0.0, gravity=0.5, timer=10)
        p.update()
        assert abs(p.dy - 0.5) < 1e-6

    def test_size_shrinks(self):
        p = Particle(0, 0, timer=10, size=10.0)
        initial = p.size
        p.update()
        assert p.size < initial

    def test_size_at_half_life(self):
        p = Particle(0, 0, timer=10, size=10.0)
        for _ in range(5):
            p.update()
        assert abs(p.size - 5.0) < 1e-6

    def test_color_fade(self):
        p = Particle(
            0,
            0,
            color=(255, 0, 0),
            fade_color=(0, 0, 255),
            timer=10,
        )
        rgba = p.get_current_color()
        assert rgba[0] == 255  # Full red at start
        assert rgba[2] == 0

        for _ in range(5):
            p.update()
        rgba_mid = p.get_current_color()
        assert rgba_mid[0] < 255  # Fading
        assert rgba_mid[2] > 0  # Blue increasing

    def test_laser_type_no_movement(self):
        p = Particle(
            5,
            5,
            dx=10,
            dy=10,
            timer=5,
            ptype="laser",
            start_pos=(0, 0),
            end_pos=(100, 100),
        )
        p.update()
        assert p.x == 5  # Laser doesn't move
        assert p.y == 5


# --- WorldParticle ---


class TestWorldParticle:
    def test_position_updates(self):
        wp = WorldParticle(
            0, 0, 1, dx=1, dy=0, dz=0, color=(255, 0, 0), timer=10, size=0.1
        )
        wp.update()
        assert abs(wp.x - 1.0) < 1e-6

    def test_gravity_affects_dz(self):
        wp = WorldParticle(
            0,
            0,
            1,
            dx=0,
            dy=0,
            dz=0,
            color=(255, 0, 0),
            timer=10,
            size=0.1,
            gravity=0.1,
        )
        wp.update()
        assert wp.dz < 0  # Gravity pulls down

    def test_ground_bounce(self):
        wp = WorldParticle(
            0,
            0,
            0.05,
            dx=1,
            dy=0,
            dz=-0.1,
            color=(255, 0, 0),
            timer=10,
            size=0.1,
            gravity=0.0,
        )
        wp.update()
        # z went below 0, should bounce
        assert wp.z == 0
        assert wp.dz > 0  # Reversed

    def test_dies_at_zero_timer(self):
        wp = WorldParticle(
            0, 0, 0, dx=0, dy=0, dz=0, color=(255, 0, 0), timer=1, size=0.1
        )
        alive = wp.update()
        assert not alive
        assert not wp.alive


# --- ParticleSystem ---


class TestParticleSystem:
    def test_add_and_count(self):
        ps = ParticleSystem()
        ps.add_particle(0, 0, color=(255, 0, 0))
        assert ps.particle_count == 1

    def test_update_removes_dead(self):
        ps = ParticleSystem(default_lifetime=2)
        ps.add_particle(0, 0)
        ps.update()  # timer: 2 -> 1
        assert ps.particle_count == 1
        ps.update()  # timer: 1 -> 0, dies
        assert ps.particle_count == 0

    def test_explosion_creates_particles(self):
        ps = ParticleSystem()
        ps.add_explosion(100, 200, count=15)
        assert ps.particle_count == 15

    def test_explosion_particles_move(self):
        ps = ParticleSystem()
        ps.add_explosion(100, 200, count=5)
        positions_before = [(p.x, p.y) for p in ps.particles]
        ps.update()
        moved = any(
            abs(p.x - bx) > 0.01 or abs(p.y - by) > 0.01
            for p, (bx, by) in zip(ps.particles, positions_before, strict=True)
        )
        assert moved

    def test_add_laser(self):
        ps = ParticleSystem()
        ps.add_laser((0, 0), (100, 100), (255, 0, 0), timer=5, width=2)
        assert ps.particle_count == 1
        assert ps.particles[0].ptype == "laser"

    def test_add_trace(self):
        ps = ParticleSystem()
        ps.add_trace((0, 0), (50, 50), (0, 255, 0))
        assert ps.particle_count == 1
        assert ps.particles[0].ptype == "trace"

    def test_world_particle(self):
        ps = ParticleSystem()
        ps.add_world_particle(1, 2, 3, dx=0.1, dy=0, dz=0, color=(255, 255, 255))
        assert ps.particle_count == 1
        ps.update()
        assert ps.world_particles[0].x > 1.0

    def test_world_explosion(self):
        ps = ParticleSystem()
        ps.add_world_explosion(0, 0, 1, count=10)
        assert ps.particle_count == 10

    def test_mixed_count(self):
        ps = ParticleSystem()
        ps.add_particle(0, 0)
        ps.add_world_particle(0, 0, 0, 0, 0, 0, (0, 0, 0))
        assert ps.particle_count == 2
