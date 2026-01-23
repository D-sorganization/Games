from __future__ import annotations

import random

import pygame

from . import constants as C  # noqa: N812


class WorldParticle:
    """3D Particle in the world space."""

    def __init__(
        self,
        x: float,
        y: float,
        z: float,
        dx: float,
        dy: float,
        dz: float,
        color: tuple[int, int, int],
        timer: int,
        size: float,
        gravity: float = 0.0,
    ):
        self.x = x
        self.y = y
        self.z = z
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.color = color
        self.timer = timer
        self.size = size
        self.alive = True
        self.gravity = gravity

    def update(self) -> bool:
        """Update particle physics."""
        self.x += self.dx
        self.y += self.dy
        self.z += self.dz
        self.dz -= self.gravity

        # Ground collision
        if self.z < 0:
            self.z = 0
            self.dz = -self.dz * 0.5
            self.dx *= 0.8
            self.dy *= 0.8

        self.timer -= 1
        if self.timer <= 0:
            self.alive = False
        return self.alive


class Particle:
    def __init__(
        self,
        x: float,
        y: float,
        dx: float = 0.0,
        dy: float = 0.0,
        color: tuple[int, int, int] = (255, 255, 255),
        timer: int = 30,
        size: float = 2.0,
        ptype: str = "normal",
        width: int = 1,
        start_pos: tuple[float, float] | None = None,
        end_pos: tuple[float, float] | None = None,
    ):
        """Initialize a particle."""
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.timer = timer
        self.size = size
        self.ptype = ptype
        self.width = width
        self.start_pos = start_pos
        self.end_pos = end_pos

    def update(self) -> bool:
        """Update particle state. Returns False if particle should be removed."""
        if self.ptype == "normal":
            self.x += self.dx
            self.y += self.dy

        self.timer -= 1
        return self.timer > 0

    def render(self, screen: pygame.Surface) -> None:
        """Render the particle."""
        if self.ptype == "normal":
            # These are usually 2D UI particles or overlay particles?
            # Wait, the game code draws particles in render_game?
            # Let's check where they are drawn.
            # Render logic for normal particles is handled in ParticleSystem.render
            return
        elif self.ptype == "laser" and self.start_pos and self.end_pos:
            pygame.draw.line(
                screen, self.color, self.start_pos, self.end_pos, self.width
            )


class ParticleSystem:
    def __init__(self) -> None:
        """Initialize the particle system."""
        self.particles: list[Particle] = []
        self.world_particles: list[WorldParticle] = []

    def add_world_particle(
        self,
        x: float,
        y: float,
        z: float,
        dx: float,
        dy: float,
        dz: float,
        color: tuple[int, int, int],
        timer: int = 60,
        size: float = 0.1,
        gravity: float = 0.01,
    ) -> None:
        """Add a 3D world particle."""
        self.world_particles.append(
            WorldParticle(x, y, z, dx, dy, dz, color, timer, size, gravity)
        )

    def add_world_explosion(
        self,
        x: float,
        y: float,
        z: float,
        count: int = 20,
        color: tuple[int, int, int] | None = None,
        speed: float = 0.2,
    ) -> None:
        """Create a 3D explosion in the world."""
        for _ in range(count):
            c = (
                color
                if color
                else (
                    random.randint(200, 255),
                    random.randint(50, 150),
                    0,
                )
            )

            v = random.uniform(0.05, speed)
            dx = v * random.uniform(-1, 1)
            dy = v * random.uniform(-1, 1)
            dz = v * random.uniform(-1, 1)

            self.add_world_particle(
                x,
                y,
                z,
                dx,
                dy,
                dz,
                c,
                timer=random.randint(30, 60),
                size=random.uniform(0.05, 0.15),
                gravity=0.005,
            )

    def add_particle(
        self,
        x: float,
        y: float,
        dx: float,
        dy: float,
        color: tuple[int, int, int],
        timer: int = 30,
        size: float = 2.0,
    ) -> None:
        """Add a standard particle."""
        self.particles.append(Particle(x, y, dx, dy, color, timer, size))

    def add_laser(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        color: tuple[int, int, int],
        timer: int,
        width: int,
    ) -> None:
        """Add a laser particle."""
        self.particles.append(
            Particle(
                0,
                0,
                color=color,
                timer=timer,
                ptype="laser",
                width=width,
                start_pos=start,
                end_pos=end,
            )
        )

    def add_trace(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        color: tuple[int, int, int],
        timer: int = 5,
        width: int = 1,
    ) -> None:
        """Add a bullet trace particle."""
        self.particles.append(
            Particle(
                0,
                0,
                color=color,
                timer=timer,
                ptype="trace",
                width=width,
                start_pos=start,
                end_pos=end,
            )
        )

    def add_explosion(
        self,
        x: float,
        y: float,
        count: int = 10,
        color: tuple[int, int, int] | None = None,
    ) -> None:
        """Create an explosion effect."""
        for _ in range(count):
            c = (
                color
                if color
                else (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                )
            )
            self.add_particle(
                x,
                y,
                dx=random.uniform(-5, 5),
                dy=random.uniform(-5, 5),
                color=c,
                timer=C.PARTICLE_LIFETIME,
                size=random.randint(2, 6),
            )

    def update(self) -> None:
        """Update all particles."""
        self.particles = [p for p in self.particles if p.update()]
        self.world_particles = [p for p in self.world_particles if p.update()]

    def render(self, screen: pygame.Surface) -> None:
        """Render all particles."""
        # Note: Some particles are 3D world particles, some are UI?
        # In Game.render_game, particles were likely drawn on top.
        # Let's verify where they are used.
        for p in self.particles:
            if p.ptype == "laser":
                p.render(screen)
            else:
                # UI Overlay particles (blood, hit effects)
                pygame.draw.rect(screen, p.color, (p.x, p.y, p.size, p.size))
