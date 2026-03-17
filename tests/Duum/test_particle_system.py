"""Tests for games.Duum.src.particle_system."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from games.Duum.src.particle_system import Particle, ParticleSystem, WorldParticle


class TestWorldParticle:
    def test_init_attributes(self) -> None:
        wp = WorldParticle(1.0, 2.0, 3.0, 0.1, 0.2, 0.3, (255, 0, 0), 30, 0.1)
        assert wp.x == 1.0
        assert wp.y == 2.0
        assert wp.z == 3.0
        assert wp.alive is True

    def test_update_moves_particle(self) -> None:
        wp = WorldParticle(
            0.0, 0.0, 5.0, 0.1, 0.2, -0.1, (255, 0, 0), 10, 0.1, gravity=0.0
        )
        wp.update()
        assert wp.x == pytest.approx(0.1)
        assert wp.y == pytest.approx(0.2)
        assert wp.z == pytest.approx(4.9)

    def test_update_applies_gravity(self) -> None:
        wp = WorldParticle(
            0.0, 0.0, 5.0, 0.0, 0.0, 0.0, (255, 0, 0), 10, 0.1, gravity=0.5
        )
        wp.update()
        # dz starts at 0.0, then z += dz (0.0) → z = 5.0, then dz -= gravity (0.5) → dz = -0.5
        assert wp.dz == pytest.approx(-0.5)
        assert wp.z == pytest.approx(5.0)

    def test_update_ground_collision_bounce(self) -> None:
        # Particle moving downward through floor
        wp = WorldParticle(0.0, 0.0, 0.1, 0.5, 0.5, -0.2, (255, 0, 0), 10, 0.1)
        wp.update()
        if wp.z < 0:
            # ground collision should bounce
            assert wp.z >= 0
        # dx and dy slow down on ground
        assert wp.dx < 0.5 or wp.z > 0  # Either bounced or didn't hit ground

    def test_update_returns_false_when_expired(self) -> None:
        wp = WorldParticle(0.0, 0.0, 5.0, 0.0, 0.0, 0.0, (255, 0, 0), 1, 0.1)
        result = wp.update()
        assert result is False
        assert wp.alive is False

    def test_update_returns_true_while_alive(self) -> None:
        wp = WorldParticle(0.0, 0.0, 5.0, 0.0, 0.0, 0.0, (255, 0, 0), 10, 0.1)
        result = wp.update()
        assert result is True
        assert wp.alive is True


class TestDuumParticle:
    def test_init_attributes(self) -> None:
        p = Particle(10.0, 20.0, dx=1.0, dy=-1.0, color=(0, 255, 0), timer=5)
        assert p.x == 10.0
        assert p.y == 20.0
        assert p.color == (0, 255, 0)

    def test_update_normal_moves(self) -> None:
        p = Particle(0.0, 0.0, dx=2.0, dy=3.0, timer=5)
        p.update()
        assert p.x == 2.0
        assert p.y == 3.0

    def test_update_timer_decrements(self) -> None:
        p = Particle(0.0, 0.0, timer=5)
        p.update()
        assert p.timer == 4

    def test_update_returns_false_when_expired(self) -> None:
        p = Particle(0.0, 0.0, timer=1)
        assert p.update() is False

    def test_update_laser_no_movement(self) -> None:
        p = Particle(5.0, 5.0, dx=10.0, dy=10.0, timer=5, ptype="laser")
        p.update()
        assert p.x == 5.0
        assert p.y == 5.0

    def test_render_normal_no_draw(self) -> None:
        p = Particle(0.0, 0.0)
        screen = MagicMock()
        result = p.render(screen)
        assert result is None

    def test_render_laser_draws_line(self) -> None:
        p = Particle(
            0.0,
            0.0,
            timer=5,
            ptype="laser",
            color=(255, 0, 0),
            start_pos=(0.0, 0.0),
            end_pos=(100.0, 100.0),
        )
        screen = MagicMock()
        with patch("games.Duum.src.particle_system.pygame") as mock_pygame:
            p.render(screen)
            mock_pygame.draw.line.assert_called_once()

    def test_render_laser_no_positions_skips(self) -> None:
        p = Particle(0.0, 0.0, timer=5, ptype="laser")
        screen = MagicMock()
        with patch("games.Duum.src.particle_system.pygame") as mock_pygame:
            p.render(screen)
            mock_pygame.draw.line.assert_not_called()


class TestDuumParticleSystem:
    def test_init_empty(self) -> None:
        ps = ParticleSystem()
        assert ps.particles == []
        assert ps.world_particles == []

    def test_add_particle(self) -> None:
        ps = ParticleSystem()
        ps.add_particle(0.0, 0.0, 1.0, 0.0, (255, 0, 0))
        assert len(ps.particles) == 1

    def test_add_world_particle(self) -> None:
        ps = ParticleSystem()
        ps.add_world_particle(1.0, 2.0, 3.0, 0.1, 0.0, 0.0, (255, 0, 0))
        assert len(ps.world_particles) == 1

    def test_add_world_explosion_creates_multiple(self) -> None:
        ps = ParticleSystem()
        ps.add_world_explosion(5.0, 5.0, 1.0, count=15)
        assert len(ps.world_particles) == 15

    def test_add_world_explosion_with_color(self) -> None:
        ps = ParticleSystem()
        ps.add_world_explosion(5.0, 5.0, 1.0, count=5, color=(255, 0, 0))
        for wp in ps.world_particles:
            assert wp.color == (255, 0, 0)

    def test_add_laser(self) -> None:
        ps = ParticleSystem()
        ps.add_laser((0.0, 0.0), (100.0, 100.0), (255, 0, 0), timer=5, width=2)
        assert len(ps.particles) == 1
        assert ps.particles[0].ptype == "laser"

    def test_add_trace(self) -> None:
        ps = ParticleSystem()
        ps.add_trace((0.0, 0.0), (50.0, 50.0), (200, 200, 200))
        assert len(ps.particles) == 1
        assert ps.particles[0].ptype == "trace"

    def test_add_explosion_default_color(self) -> None:
        ps = ParticleSystem()
        ps.add_explosion(50.0, 50.0, count=8)
        assert len(ps.particles) == 8

    def test_add_explosion_with_color(self) -> None:
        ps = ParticleSystem()
        ps.add_explosion(50.0, 50.0, count=5, color=(0, 255, 0))
        assert len(ps.particles) == 5
        for p in ps.particles:
            assert p.color == (0, 255, 0)

    def test_update_removes_dead_particles(self) -> None:
        ps = ParticleSystem()
        ps.add_particle(0.0, 0.0, 0.0, 0.0, (255, 0, 0), timer=1)
        ps.add_particle(0.0, 0.0, 0.0, 0.0, (0, 255, 0), timer=50)
        ps.update()
        assert len(ps.particles) == 1

    def test_update_removes_dead_world_particles(self) -> None:
        ps = ParticleSystem()
        ps.add_world_particle(0.0, 0.0, 5.0, 0.0, 0.0, 0.0, (255, 0, 0), timer=1)
        ps.add_world_particle(0.0, 0.0, 5.0, 0.0, 0.0, 0.0, (0, 255, 0), timer=50)
        ps.update()
        assert len(ps.world_particles) == 1

    def test_render_normal_particle(self) -> None:
        ps = ParticleSystem()
        ps.add_particle(10.0, 20.0, 0.0, 0.0, (255, 0, 0), size=5.0)
        screen = MagicMock()
        with patch("games.Duum.src.particle_system.pygame") as mock_pygame:
            ps.render(screen)
            mock_pygame.draw.rect.assert_called_once()

    def test_render_laser_particle(self) -> None:
        ps = ParticleSystem()
        ps.add_laser((0.0, 0.0), (50.0, 50.0), (255, 0, 0), timer=5, width=1)
        screen = MagicMock()
        with patch("games.Duum.src.particle_system.pygame") as mock_pygame:
            ps.render(screen)
            mock_pygame.draw.line.assert_called_once()
