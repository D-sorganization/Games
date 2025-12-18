from __future__ import annotations

import random

import pygame

from . import constants as C  # noqa: N812


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
        if self.ptype == "normal":
            # These are usually 2D UI particles or overlay particles?
            # Wait, the game code draws particles in render_game?
            # Let's check where they are drawn.
            pass
        elif self.ptype == "laser" and self.start_pos and self.end_pos:
            pygame.draw.line(screen, self.color, self.start_pos, self.end_pos, self.width)


class ParticleSystem:
    def __init__(self):
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
    ) -> None:
        self.particles.append(Particle(x, y, dx, dy, color, timer, size))

    def add_laser(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        color: tuple[int, int, int],
        timer: int,
        width: int,
    ) -> None:
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
        self, x: float, y: float, count: int = 10, color: tuple[int, int, int] | None = None
    ) -> None:
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
        self.particles = [p for p in self.particles if p.update()]

    def render(self, screen: pygame.Surface) -> None:
        # Note: Some particles are 3D world particles, some are UI?
        # In Game.render_game, particles were likely drawn on top.
        # Let's verify where they are used.
        for p in self.particles:
            if p.ptype == "laser":
                p.render(screen)
            else:
                # UI Overlay particles (blood, hit effects)
                pygame.draw.rect(screen, p.color, (p.x, p.y, p.size, p.size))
