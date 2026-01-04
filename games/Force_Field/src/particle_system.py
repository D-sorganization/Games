from __future__ import annotations

import math
import random

from . import constants as C  # noqa: N812


class Particle:
    """Represents a single particle in the system."""

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
    ):
        """Initialize a particle."""
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
        self.fade_color = fade_color or color
        self.rotation = rotation
        self.rotation_speed = rotation_speed

    def update(self) -> bool:
        """Update particle state. Returns False if particle should be removed."""
        if self.ptype == "normal":
            self.x += self.dx
            self.y += self.dy
            self.dy += self.gravity  # Apply gravity

            # Update rotation
            self.rotation += self.rotation_speed

            # Size animation (shrink over time)
            life_ratio = self.timer / self.max_timer
            self.size = self.initial_size * life_ratio

        self.timer -= 1
        return self.timer > 0

    def get_current_color(self) -> tuple[int, int, int, int]:
        """Get current color with alpha based on lifetime."""
        life_ratio = max(0.0, self.timer / self.max_timer)
        alpha = int(255 * life_ratio)

        # Interpolate between initial color and fade color
        if self.fade_color != self.color:
            r = int(self.color[0] * life_ratio + self.fade_color[0] * (1 - life_ratio))
            g = int(self.color[1] * life_ratio + self.fade_color[1] * (1 - life_ratio))
            b = int(self.color[2] * life_ratio + self.fade_color[2] * (1 - life_ratio))
            return (r, g, b, alpha)

        return (*self.color, alpha)


class ParticleSystem:
    """Manages all active particles."""

    def __init__(self) -> None:
        """Initialize the particle system."""
        self.particles: list[Particle] = []

    def add_particle(
        self,
        x: float,
        y: float,
        dx: float,
        dy: float,
        color: tuple[int, int, int],
        timer: int = 30,
        size: float = 2.0,
        gravity: float = 0.0,
        fade_color: tuple[int, int, int] | None = None,
        rotation_speed: float = 0.0,
    ) -> None:
        """Add a standard particle."""
        self.particles.append(
            Particle(
                x,
                y,
                dx,
                dy,
                color,
                timer,
                size,
                gravity=gravity,
                fade_color=fade_color,
                rotation_speed=rotation_speed,
            )
        )

    def add_plasma_particle(
        self,
        x: float,
        y: float,
        dx: float,
        dy: float,
        timer: int = 60,
    ) -> None:
        """Add a plasma particle with special effects."""
        # Main plasma particle
        self.add_particle(
            x,
            y,
            dx,
            dy,
            color=(0, 255, 255),
            timer=timer,
            size=random.uniform(3, 6),
            gravity=0.02,
            fade_color=(0, 100, 255),
            rotation_speed=random.uniform(-0.1, 0.1),
        )

        # Add trailing sparks
        for _ in range(2):
            self.add_particle(
                x + random.uniform(-2, 2),
                dx * 0.5 + random.uniform(-1, 1),
                dy * 0.5 + random.uniform(-1, 1),
                color=(100, 255, 255),
                timer=timer // 2,
                size=random.uniform(1, 3),
                gravity=0.01,
                fade_color=(0, 50, 100),
            )

    def add_spark_burst(
        self,
        x: float,
        y: float,
        count: int = 8,
        color: tuple[int, int, int] = (255, 255, 0),
    ) -> None:
        """Create a burst of sparks."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed

            self.add_particle(
                x,
                y,
                dx,
                dy,
                color=color,
                timer=random.randint(20, 40),
                size=random.uniform(1, 3),
                gravity=0.1,
                fade_color=(100, 50, 0),
                rotation_speed=random.uniform(-0.2, 0.2),
            )

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

    def add_victory_fireworks(self) -> None:
        """Create a large firework explosion for victory."""
        cx = C.SCREEN_WIDTH // 2
        cy = C.SCREEN_HEIGHT // 2
        for _ in range(50):
            color = (
                random.randint(100, 255),
                random.randint(100, 255),
                random.randint(100, 255),
            )
            self.add_particle(
                x=cx + random.randint(-200, 200),
                y=cy + random.randint(-100, 100),
                dx=random.uniform(-5, 5),
                dy=random.uniform(-5, 5),
                color=color,
                timer=60,
                size=random.randint(4, 10),
                gravity=0.05,
            )

    def update(self) -> None:
        """Update all particles."""
        self.particles = [p for p in self.particles if p.update()]
