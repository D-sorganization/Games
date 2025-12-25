import pygame
import random
import numpy as np
from typing import Dict

class TextureGenerator:
    """Generates procedural textures for the game."""

    @staticmethod
    def generate_noise(width: int, height: int, color_base: tuple[int, int, int], variation: int = 30) -> pygame.Surface:
        """Generates a simple noise texture."""
        arr = np.zeros((width, height, 3), dtype=np.uint8)

        # Base color
        r, g, b = color_base

        # Generate random noise
        noise = np.random.randint(-variation, variation, (width, height, 3))

        # Add base color
        arr[:, :, 0] = np.clip(r + noise[:, :, 0], 0, 255)
        arr[:, :, 1] = np.clip(g + noise[:, :, 1], 0, 255)
        arr[:, :, 2] = np.clip(b + noise[:, :, 2], 0, 255)

        surface = pygame.surfarray.make_surface(arr)
        return surface

    @staticmethod
    def generate_bricks(width: int, height: int, color_brick: tuple[int, int, int], color_mortar: tuple[int, int, int]) -> pygame.Surface:
        """Generates a brick pattern."""
        surface = TextureGenerator.generate_noise(width, height, color_brick, 20)
        arr = pygame.surfarray.pixels3d(surface)

        # Brick dimensions
        brick_w = width // 4
        brick_h = height // 4
        mortar_size = 2

        for y in range(0, height):
            row = y // brick_h
            offset = (brick_w // 2) if row % 2 == 1 else 0

            for x in range(0, width):
                # Mortar horizontal
                if y % brick_h < mortar_size:
                    arr[x, y] = color_mortar
                    continue

                # Mortar vertical
                if (x + offset) % brick_w < mortar_size:
                    arr[x, y] = color_mortar
                    continue

        del arr # Unlock surface
        return surface

    @staticmethod
    def generate_stone(width: int, height: int) -> pygame.Surface:
        """Generates a stone/cobble pattern."""
        return TextureGenerator.generate_noise(width, height, (100, 100, 100), 40)

    @staticmethod
    def generate_metal(width: int, height: int) -> pygame.Surface:
        """Generates a metal panel pattern."""
        surface = TextureGenerator.generate_noise(width, height, (150, 150, 160), 10)
        arr = pygame.surfarray.pixels3d(surface)

        # Draw some panel lines/rivets
        color_line = (100, 100, 110)

        # Border
        arr[0:2, :] = color_line
        arr[width-2:width, :] = color_line
        arr[:, 0:2] = color_line
        arr[:, height-2:height] = color_line

        # Cross
        arr[width//2-1:width//2+1, :] = color_line
        arr[:, height//2-1:height//2+1] = color_line

        del arr
        return surface

    @staticmethod
    def generate_tech(width: int, height: int) -> pygame.Surface:
        """Generates a sci-fi tech pattern."""
        surface = TextureGenerator.generate_noise(width, height, (20, 20, 40), 5)
        arr = pygame.surfarray.pixels3d(surface)

        color_glow = (0, 200, 255)
        color_dark = (10, 10, 20)

        # Grid
        step = 16
        for x in range(0, width, step):
            arr[x:x+1, :] = color_dark
        for y in range(0, height, step):
            arr[:, y:y+1] = color_dark

        # Random glowing bits
        for _ in range(5):
            rx = random.randint(0, (width//step)-1) * step
            ry = random.randint(0, (height//step)-1) * step
            arr[rx+2:rx+step-2, ry+2:ry+step-2] = color_glow

        del arr
        return surface

    @staticmethod
    def generate_textures() -> Dict[str, pygame.Surface]:
        """Generates all textures and returns them in a dictionary."""
        # Ensure pygame is initialized for surface creation (mostly for format)
        if not pygame.get_init():
            pygame.init()

        textures = {}
        size = 64

        textures["brick"] = TextureGenerator.generate_bricks(size, size, (160, 80, 60), (120, 120, 120))
        textures["stone"] = TextureGenerator.generate_stone(size, size)
        textures["metal"] = TextureGenerator.generate_metal(size, size)
        textures["tech"] = TextureGenerator.generate_tech(size, size)

        return textures
