"""Shared 2D/3D particle system for Pygame games.

Consolidates common particle logic from Force_Field, Duum, and
Zombie_Survival into one reusable module. Supports normal, laser,
and trace particle types, plus 3D world-space particles.

Usage:
    from games.shared.particle_system import ParticleSystem

    ps = ParticleSystem()
    ps.add_explosion(400, 300, count=20)
    ps.update()
    ps.render(screen)
"""

from __future__ import annotations

import math
import random


class Particle:
    """A single 2D screen-space particle."""

    __slots__ = (
        "x",
        "y",
        "dx",
        "dy",
        "color",
        "timer",
        "max_timer",
        "size",
        "initial_size",
        "ptype",
        "width",
        "start_pos",
        "end_pos",
        "gravity",
        "fade_color",
        "rotation",
        "rotation_speed",
    )

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
        gravity: float = 0.0,
        fade_color: tuple[int, int, int] | None = None,
        rotation: float = 0.0,
        rotation_speed: float = 0.0,
    ) -> None:
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.timer = timer
        self.max_timer = timer
        self.size = size
        self.initial_size = size
        self.ptype = ptype
        self.width = width
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.gravity = gravity
        self.fade_color = fade_color if fade_color is not None else color
        self.rotation = rotation
        self.rotation_speed = rotation_speed

    def update(self) -> bool:
        """Advance particle by one frame. Returns True if still alive."""
        self.timer -= 1
        if self.ptype == "normal":
            self.x += self.dx
            self.y += self.dy
            self.dy += self.gravity
            self.rotation += self.rotation_speed
            if self.max_timer > 0:
                life_ratio = max(0.0, self.timer / self.max_timer)
                self.size = self.initial_size * life_ratio
        return self.timer > 0

    def get_current_color(self) -> tuple[int, int, int, int]:
        """Get interpolated RGBA color based on remaining life."""
        life_ratio = (
            max(0.0, self.timer / self.max_timer) if self.max_timer > 0 else 0.0
        )
        alpha = int(255 * life_ratio)
        if self.fade_color != self.color:
            r = int(self.color[0] * life_ratio + self.fade_color[0] * (1 - life_ratio))
            g = int(self.color[1] * life_ratio + self.fade_color[1] * (1 - life_ratio))
            b = int(self.color[2] * life_ratio + self.fade_color[2] * (1 - life_ratio))
            return (r, g, b, alpha)
        return (*self.color, alpha)


class WorldParticle:
    """A 3D particle in world space (for raycaster games)."""

    __slots__ = (
        "x",
        "y",
        "z",
        "dx",
        "dy",
        "dz",
        "color",
        "timer",
        "size",
        "alive",
        "gravity",
    )

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
    ) -> None:
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
        """Advance particle. Returns True if still alive."""
        self.x += self.dx
        self.y += self.dy
        self.z += self.dz
        self.dz -= self.gravity
        if self.z < 0:
            self.z = 0
            self.dz = -self.dz * 0.5
            self.dx *= 0.8
            self.dy *= 0.8
        self.timer -= 1
        if self.timer <= 0:
            self.alive = False
        return self.alive


class ParticleSystem:
    """Manages 2D and 3D particles with convenience emitters."""

    def __init__(self, default_lifetime: int = 30) -> None:
        self.particles: list[Particle] = []
        self.world_particles: list[WorldParticle] = []
        self.default_lifetime = default_lifetime

    def add_particle(
        self,
        x: float,
        y: float,
        dx: float = 0.0,
        dy: float = 0.0,
        color: tuple[int, int, int] = (255, 255, 255),
        timer: int | None = None,
        size: float = 2.0,
        gravity: float = 0.0,
        fade_color: tuple[int, int, int] | None = None,
        rotation_speed: float = 0.0,
    ) -> None:
        """Add a single 2D particle."""
        self.particles.append(
            Particle(
                x,
                y,
                dx,
                dy,
                color,
                timer if timer is not None else self.default_lifetime,
                size,
                gravity=gravity,
                fade_color=fade_color,
                rotation_speed=rotation_speed,
            )
        )

    def add_explosion(
        self,
        x: float,
        y: float,
        count: int = 10,
        color: tuple[int, int, int] | None = None,
        speed: float = 5.0,
    ) -> None:
        """Spawn an outward burst of particles."""
        for _ in range(count):
            c = color or (
                random.randint(200, 255),
                random.randint(50, 200),
                random.randint(0, 50),
            )
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(1, speed)
            self.add_particle(
                x,
                y,
                dx=math.cos(angle) * spd,
                dy=math.sin(angle) * spd,
                color=c,
                size=random.uniform(2, 6),
            )

    def add_laser(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        color: tuple[int, int, int],
        timer: int = 5,
        width: int = 2,
    ) -> None:
        """Add a laser line particle."""
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
        """Add a bullet trace line particle."""
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
        """Add a single 3D world-space particle."""
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
        """Spawn a 3D outward burst of world particles."""
        for _ in range(count):
            c = color or (
                random.randint(200, 255),
                random.randint(50, 150),
                0,
            )
            v = random.uniform(0.05, speed)
            self.add_world_particle(
                x,
                y,
                z,
                v * random.uniform(-1, 1),
                v * random.uniform(-1, 1),
                v * random.uniform(-1, 1),
                c,
                timer=random.randint(30, 60),
                size=random.uniform(0.05, 0.15),
                gravity=0.005,
            )

    def update(self) -> None:
        """Advance all particles and remove dead ones."""
        self.particles = [p for p in self.particles if p.update()]
        self.world_particles = [p for p in self.world_particles if p.update()]

    def render(self, screen: object) -> None:
        """Render all 2D particles to a pygame surface."""
        import pygame

        for p in self.particles:
            if p.ptype == "laser" and p.start_pos and p.end_pos:
                pygame.draw.line(screen, p.color, p.start_pos, p.end_pos, p.width)
            elif p.ptype == "trace" and p.start_pos and p.end_pos:
                pygame.draw.line(screen, p.color, p.start_pos, p.end_pos, p.width)
            elif p.ptype == "normal" and p.size > 0:
                pygame.draw.rect(
                    screen, p.color, (int(p.x), int(p.y), int(p.size), int(p.size))
                )

    @property
    def particle_count(self) -> int:
        """Total number of active particles (2D + 3D)."""
        return len(self.particles) + len(self.world_particles)
