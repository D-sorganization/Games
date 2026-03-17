"""Tests for games.Zombie_Survival.src.particle_system."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from games.Zombie_Survival.src.particle_system import Particle, ParticleSystem


class TestZSParticle:
    def test_init_attributes(self) -> None:
        p = Particle(10.0, 20.0, dx=1.0, dy=-1.0, color=(255, 0, 0), timer=30)
        assert p.x == 10.0
        assert p.y == 20.0
        assert p.dx == 1.0
        assert p.dy == -1.0
        assert p.color == (255, 0, 0)
        assert p.timer == 30

    def test_update_normal_moves(self) -> None:
        p = Particle(0.0, 0.0, dx=2.0, dy=3.0, timer=5)
        p.update()
        assert p.x == 2.0
        assert p.y == 3.0

    def test_update_timer_decrements(self) -> None:
        p = Particle(0.0, 0.0, timer=5)
        p.update()
        assert p.timer == 4

    def test_update_returns_true_while_alive(self) -> None:
        p = Particle(0.0, 0.0, timer=3)
        assert p.update() is True

    def test_update_returns_false_when_expired(self) -> None:
        p = Particle(0.0, 0.0, timer=1)
        assert p.update() is False

    def test_update_laser_type_no_movement(self) -> None:
        p = Particle(5.0, 5.0, dx=10.0, dy=10.0, timer=3, ptype="laser")
        p.update()
        assert p.x == 5.0
        assert p.y == 5.0

    def test_render_normal_returns_none(self) -> None:
        p = Particle(0.0, 0.0)
        screen = MagicMock()
        result = p.render(screen)
        assert result is None

    def test_render_laser_draws_line(self) -> None:
        p = Particle(
            0.0,
            0.0,
            color=(255, 0, 0),
            timer=5,
            ptype="laser",
            start_pos=(0.0, 0.0),
            end_pos=(100.0, 100.0),
        )
        screen = MagicMock()
        with patch("games.Zombie_Survival.src.particle_system.pygame") as mock_pygame:
            p.render(screen)
            mock_pygame.draw.line.assert_called_once()

    def test_render_laser_no_positions_skips(self) -> None:
        """Laser particle without start/end positions should not call draw.line."""
        p = Particle(0.0, 0.0, color=(255, 0, 0), timer=5, ptype="laser")
        screen = MagicMock()
        with patch("games.Zombie_Survival.src.particle_system.pygame") as mock_pygame:
            p.render(screen)
            mock_pygame.draw.line.assert_not_called()


class TestZSParticleSystem:
    def test_init_empty(self) -> None:
        ps = ParticleSystem()
        assert ps.particles == []

    def test_add_particle(self) -> None:
        ps = ParticleSystem()
        ps.add_particle(10.0, 20.0, 1.0, 0.0, (255, 0, 0))
        assert len(ps.particles) == 1

    def test_add_laser(self) -> None:
        ps = ParticleSystem()
        ps.add_laser((0.0, 0.0), (100.0, 100.0), (0, 255, 255), timer=5, width=2)
        assert len(ps.particles) == 1
        assert ps.particles[0].ptype == "laser"

    def test_add_explosion_default_color(self) -> None:
        ps = ParticleSystem()
        ps.add_explosion(50.0, 50.0, count=8)
        assert len(ps.particles) == 8

    def test_add_explosion_with_color(self) -> None:
        ps = ParticleSystem()
        ps.add_explosion(50.0, 50.0, count=4, color=(255, 100, 0))
        assert len(ps.particles) == 4
        for p in ps.particles:
            assert p.color == (255, 100, 0)

    def test_update_removes_dead_particles(self) -> None:
        ps = ParticleSystem()
        ps.add_particle(0.0, 0.0, 0.0, 0.0, (255, 0, 0), timer=1)
        ps.add_particle(0.0, 0.0, 0.0, 0.0, (0, 255, 0), timer=10)
        ps.update()
        assert len(ps.particles) == 1
        assert ps.particles[0].color == (0, 255, 0)

    def test_render_draws_normal_particles(self) -> None:
        ps = ParticleSystem()
        ps.add_particle(10.0, 20.0, 0.0, 0.0, (255, 0, 0), size=5.0)
        screen = MagicMock()
        with patch("games.Zombie_Survival.src.particle_system.pygame") as mock_pygame:
            ps.render(screen)
            mock_pygame.draw.rect.assert_called_once()

    def test_render_draws_laser_particles(self) -> None:
        ps = ParticleSystem()
        ps.add_laser((0.0, 0.0), (50.0, 50.0), (255, 0, 0), timer=5, width=1)
        screen = MagicMock()
        with patch("games.Zombie_Survival.src.particle_system.pygame") as mock_pygame:
            ps.render(screen)
            mock_pygame.draw.line.assert_called_once()
