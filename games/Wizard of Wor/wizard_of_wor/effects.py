"""Visual effects helpers for the Wizard of Wor remake."""

from __future__ import annotations

import math
import random
from typing import ClassVar, Protocol

import pygame
from constants import (
    BLACK,
    CYAN,
    FOOTSTEP_INTERVAL,
    MUZZLE_FLASH_TIME,
    RADAR_PING_INTERVAL,
    SPARKLE_LIFETIME,
    VIGNETTE_ALPHA,
)


class VisualEffect(Protocol):
    """Protocol for transient visual effects."""

    layer: str

    def update(self) -> bool:
        """Return True while the effect should stay alive."""

    def draw(self, screen: pygame.Surface) -> None:
        """Render the effect on screen."""


class Footstep:
    """Dusty footstep decal when characters move."""

    layer = "floor"

    def __init__(
        self, position: tuple[float, float], color: tuple[int, int, int]
    ) -> None:
        """Initialize a footstep effect at the given position with the given color."""
        self.position = pygame.math.Vector2(position)
        self.life = FOOTSTEP_INTERVAL
        self.color = color

    def update(self) -> bool:
        """Update the footstep effect and return whether it's still alive."""
        self.life -= 1
        return self.life > 0

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the footstep effect on the screen."""
        alpha = max(40, int(180 * (self.life / FOOTSTEP_INTERVAL)))
        radius = 6
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        faded_color = (*self.color, alpha)
        pygame.draw.circle(surface, faded_color, (radius, radius), radius)
        screen.blit(
            surface,
            (self.position.x - radius, self.position.y - radius),
        )


class SparkleBurst:
    """Particle burst used for spawns, hits, and radar pings."""

    layer = "top"

    def __init__(
        self,
        position: tuple[float, float],
        color: tuple[int, int, int],
        count: int = 10,
    ) -> None:
        """Initialize a sparkle burst effect at the given position."""
        self.color = color
        self.life = SPARKLE_LIFETIME
        self.particles: list[tuple[pygame.math.Vector2, pygame.math.Vector2]] = []
        center = pygame.math.Vector2(position)

        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(1.2, 2.8)
            velocity = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * speed
            self.particles.append((center.copy(), velocity))

    def update(self) -> bool:
        """Update the sparkle burst and return whether it's still alive."""
        self.life -= 1
        decay = 0.9
        for idx, particle in enumerate(self.particles):
            position, velocity = particle
            position += velocity
            velocity *= decay
            self.particles[idx] = (position, velocity)
        return self.life > 0

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the sparkle burst particles on the screen."""
        alpha = max(60, int(255 * (self.life / SPARKLE_LIFETIME)))
        radius = 2
        dot = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(dot, (*self.color, alpha), (radius, radius), radius)
        for pos, _ in self.particles:
            screen.blit(dot, (pos.x - radius, pos.y - radius))


class MuzzleFlash:
    """Short-lived bolt flash at gun barrels."""

    layer = "middle"

    def __init__(self, position: tuple[float, float]) -> None:
        """Initialize a muzzle flash effect at the given position."""
        self.position = pygame.math.Vector2(position)
        self.life = MUZZLE_FLASH_TIME

    def update(self) -> bool:
        """Update the muzzle flash and return whether it's still alive."""
        self.life -= 1
        return self.life > 0

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the muzzle flash on the screen."""
        alpha = max(100, int(255 * (self.life / MUZZLE_FLASH_TIME)))
        radius = 8
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surface, (255, 255, 170, alpha), (radius, radius), radius)
        pygame.draw.circle(
            surface, (255, 255, 255, alpha), (radius, radius), radius // 2
        )
        screen.blit(surface, (self.position.x - radius, self.position.y - radius))


class RadarPing:
    """Expanding ring on the radar for nearby activity."""

    layer = "hud"

    def __init__(self, center: tuple[int, int]) -> None:
        """Initialize a radar ping at the given center position."""
        self.center = center
        self.life = RADAR_PING_INTERVAL

    def update(self) -> bool:
        """Update the radar ping and return whether it's still alive."""
        self.life -= 1
        return self.life > 0

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the radar ping on the screen."""
        progress = 1 - (self.life / RADAR_PING_INTERVAL)
        radius = int(progress * 40)
        alpha = max(40, 160 - int(progress * 160))
        if radius <= 0:
            return

        surface = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        center = (surface.get_width() // 2, surface.get_height() // 2)
        pygame.draw.circle(surface, (*CYAN, alpha), center, radius, width=2)
        screen.blit(surface, (self.center[0] - center[0], self.center[1] - center[1]))


class Vignette:
    """A subtle darkening around the playfield to focus action."""

    layer = "overlay"

    _surface_cache: ClassVar[dict[tuple[int, int], pygame.Surface]] = {}

    def __init__(
        self, size: tuple[int, int], top_left: tuple[int, int] = (0, 0)
    ) -> None:
        """Initialize a vignette effect with the given size and position."""
        self.top_left = top_left
        width, height = size
        cached = self._surface_cache.get(size)
        if cached is not None:
            self.surface = cached
            return

        self.surface = pygame.Surface(size, pygame.SRCALPHA)
        max_distance = math.hypot(width / 2, height / 2)
        for y in range(height):
            for x in range(width):
                distance = pygame.math.Vector2(x - width / 2, y - height / 2).length()
                intensity = min(1.0, distance / max_distance)
                alpha = int(intensity * VIGNETTE_ALPHA)
                self.surface.set_at((x, y), (*BLACK, alpha))

        self._surface_cache[size] = self.surface

    def update(self) -> bool:
        """Update the vignette effect (always returns True as it's persistent)."""
        return True

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the vignette effect on the screen."""
        screen.blit(self.surface, self.top_left, special_flags=pygame.BLEND_RGBA_MULT)
