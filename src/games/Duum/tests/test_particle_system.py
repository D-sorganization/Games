from unittest.mock import MagicMock, patch

from src.particle_system import Particle, ParticleSystem, WorldParticle


def test_world_particle_update():
    wp = WorldParticle(0, 0, 10, 1, 1, 0, (255, 0, 0), 2, 0.1, gravity=2.0)
    assert wp.update() is True  # timer drops to 1
    assert wp.x == 1
    assert wp.y == 1
    assert wp.z == 10
    assert wp.dz == -2.0

    # Force ground collision on next frame
    wp.z = 1
    wp.dz = -5.0
    wp.update()  # timer 0 -> False
    assert wp.z == 0
    assert wp.dz == 3.5  # -(-5.0 - 2.0) * 0.5
    assert not wp.alive


def test_particle_update():
    p = Particle(0, 0, 1, 1, timer=2)
    assert p.update() is True
    assert p.x == 1
    assert p.y == 1

    assert p.update() is False

    p2 = Particle(0, 0, 1, 1, timer=2, ptype="laser")
    assert p2.update() is True
    assert p2.x == 0  # Does not move


def test_particle_render():
    p = Particle(0, 0, ptype="normal")
    screen = MagicMock()
    p.render(screen)
    # normal particle does nothing specific in its own render

    p2 = Particle(
        0,
        0,
        color=(255, 0, 0),
        ptype="laser",
        width=2,
        start_pos=(0, 0),
        end_pos=(10, 10),
    )
    with patch("pygame.draw.line", create=True) as mock_line:
        p2.render(screen)
        mock_line.assert_called_with(screen, (255, 0, 0), (0, 0), (10, 10), 2)


def test_particle_system_adds():
    sys = ParticleSystem()
    sys.add_world_particle(0, 0, 0, 1, 1, 1, (255, 255, 255))
    assert len(sys.world_particles) == 1

    with (
        patch("random.uniform", return_value=0.1),
        patch("random.randint", return_value=100),
    ):
        sys.add_world_explosion(0, 0, 0, count=5)
        assert len(sys.world_particles) == 6

        sys.add_world_explosion(0, 0, 0, count=5, color=(255, 0, 0))
        assert len(sys.world_particles) == 11

    sys.add_particle(0, 0, 1, 1, (255, 255, 255))
    assert len(sys.particles) == 1

    sys.add_laser((0, 0), (10, 10), (255, 0, 0), 10, 2)
    assert len(sys.particles) == 2
    assert sys.particles[-1].ptype == "laser"

    sys.add_trace((0, 0), (10, 10), (255, 0, 0))
    assert len(sys.particles) == 3
    assert sys.particles[-1].ptype == "trace"

    with (
        patch("random.uniform", return_value=1.0),
        patch("random.randint", return_value=100),
    ):
        sys.add_explosion(0, 0, count=2)
        assert len(sys.particles) == 5

        sys.add_explosion(0, 0, count=2, color=(255, 0, 0))
        assert len(sys.particles) == 7


def test_particle_system_update_render():
    sys = ParticleSystem()

    sys.world_particles.append(WorldParticle(0, 0, 0, 0, 0, 0, (255, 0, 0), 1, 0.1))
    sys.world_particles.append(WorldParticle(0, 0, 0, 0, 0, 0, (255, 0, 0), 2, 0.1))

    sys.particles.append(Particle(0, 0, 0, 0, timer=1))
    sys.particles.append(Particle(0, 0, 0, 0, timer=2))
    sys.particles.append(Particle(0, 0, timer=2, ptype="laser", start_pos=(0, 0), end_pos=(1, 1)))

    sys.update()
    assert len(sys.world_particles) == 1
    assert len(sys.particles) == 2

    screen = MagicMock()
    with (
        patch("pygame.draw.rect", create=True) as mock_rect,
        patch("src.particle_system.Particle.render") as mock_render,
    ):
        sys.render(screen)
        mock_render.assert_called_once_with(screen)
        mock_rect.assert_called_once()
