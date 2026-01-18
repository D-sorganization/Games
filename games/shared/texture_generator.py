import random

import numpy as np
import pygame


class TextureGenerator:
    """Generates procedural textures for the game."""

    @staticmethod
    def generate_noise(
        width: int, height: int, color_base: tuple[int, int, int], variation: int = 30
    ) -> pygame.Surface:
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
    def generate_bricks(
        width: int,
        height: int,
        color_brick: tuple[int, int, int],
        color_mortar: tuple[int, int, int],
    ) -> pygame.Surface:
        """Generates a brick pattern."""
        surface = pygame.Surface((width, height))
        surface.fill(color_brick)
        arr = pygame.surfarray.pixels3d(surface)

        # Subtle noise for texture (reduced variation)
        noise = np.random.randint(-15, 15, (width, height, 3))
        # Ensure we don't overflow uint8 wrapping
        base_arr = np.array(arr, dtype=np.int16)
        base_arr += noise
        np.clip(base_arr, 0, 255, out=base_arr)
        arr[:] = base_arr.astype(np.uint8)

        # Brick dimensions
        brick_w = width // 2
        brick_h = height // 4
        mortar_size = 2

        for y in range(height):
            row = y // brick_h
            offset = (brick_w // 2) if row % 2 == 1 else 0

            # Mortar horizontal
            if y % brick_h < mortar_size:
                arr[:, y] = color_mortar
                continue

            # Mortar vertical
            for x in range(width):
                if (x + offset) % brick_w < mortar_size:
                    arr[x, y] = color_mortar

        del arr  # Unlock surface
        return surface

    @staticmethod
    def generate_stone(width: int, height: int) -> pygame.Surface:
        """Generates a large slate blocks pattern."""
        surface = pygame.Surface((width, height))
        base_shade = 80
        surface.fill((base_shade, base_shade, base_shade))
        arr = pygame.surfarray.pixels3d(surface)

        # Large blocky noise
        block_size = 16
        for bx in range(0, width, block_size):
            for by in range(0, height, block_size):
                shade = random.randint(-20, 20)
                val = max(0, base_shade + shade)
                color = (val, val, val)

                # Safe slice assignment
                x_end = min(width, bx + block_size)
                y_end = min(height, by + block_size)
                arr[bx:x_end, by:y_end] = color

        # Add some cracks/variation
        for _ in range(10):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            # Safe slice for cracks
            x_end = min(width, x + 2)
            y_end = min(height, y + 6)
            arr[x:x_end, y:y_end] = (40, 40, 40)

        del arr
        return surface

    @staticmethod
    def generate_metal(width: int, height: int) -> pygame.Surface:
        """Generates a metal panel pattern with rivets."""
        surface = pygame.Surface((width, height))
        surface.fill((140, 140, 150))
        arr = pygame.surfarray.pixels3d(surface)

        # Work with int16 to handle negative shading safely
        base_arr = np.array(arr, dtype=np.int16)

        # Horizontal streaks (brushed)
        for y in range(height):
            shade = random.randint(-10, 10)
            base_arr[:, y] += shade

        np.clip(base_arr, 0, 255, out=base_arr)
        arr[:] = base_arr.astype(np.uint8)

        # Border/Panel lines
        color_line = (80, 80, 90)
        arr[0:2, :] = color_line
        arr[width - 2 : width, :] = color_line
        arr[:, 0:2] = color_line
        arr[:, height - 2 : height] = color_line

        # Rivets
        rivet_color = (180, 180, 190)
        rivet_shadow = (50, 50, 60)
        rivets = [(4, 4), (width - 6, 4), (4, height - 6), (width - 6, height - 6)]
        for rx, ry in rivets:
            # Safe slice
            rx_end = min(width, rx + 2)
            ry_end = min(height, ry + 2)
            arr[rx:rx_end, ry:ry_end] = rivet_color
            if rx + 2 < width and ry + 2 < height:
                arr[rx + 2, ry + 2] = rivet_shadow

        del arr
        return surface

    @staticmethod
    def generate_tech(width: int, height: int) -> pygame.Surface:
        """Generates a sci-fi tech pattern with clean grid and glow."""
        surface = pygame.Surface((width, height))
        surface.fill((20, 20, 30))
        arr = pygame.surfarray.pixels3d(surface)

        color_glow = (0, 255, 255)
        color_grid = (40, 40, 60)

        # Grid lines
        step = 16
        arr[::step, :] = color_grid
        arr[:, ::step] = color_grid

        # Random glowing rectangular panels
        for _ in range(2):
            w_rect = random.randint(4, 12)
            h_rect = random.randint(4, 20)
            x = random.randint(2, width - w_rect - 2)
            y = random.randint(2, height - h_rect - 2)

            # Safe bounds
            x_end = min(width, x + w_rect)
            y_end = min(height, y + h_rect)

            # Fill rect
            arr[x:x_end, y:y_end] = (30, 30, 50)

            # Border glow (with safe clipping)
            arr[x:x_end, y] = color_glow  # Top
            arr[x:x_end, min(height - 1, y_end - 1)] = color_glow  # Bottom
            arr[x, y:y_end] = color_glow  # Left
            arr[min(width - 1, x_end - 1), y:y_end] = color_glow  # Right

        del arr
        return surface

    @staticmethod
    def generate_secret(width: int, height: int) -> pygame.Surface:
        """Generates a secret wall (cracked)."""
        # Start with standard bricks but darker/different tint
        surface = TextureGenerator.generate_bricks(
            width, height, (130, 60, 50), (100, 100, 100)
        )
        arr = pygame.surfarray.pixels3d(surface)

        # Add visual hint (Dark Cracks)
        # Use simple random walk for a crack
        center_x = width // 2
        color_crack = (20, 20, 20)

        # Draw a jagged crack
        curr_x = center_x
        for y in range(10, height - 10):
            if 0 <= curr_x < width:
                # Draw thick line
                for dx in range(-1, 2):
                    nx = curr_x + dx
                    if 0 <= nx < width:
                        arr[nx, y] = color_crack

            curr_x += random.randint(-1, 1)

        del arr
        return surface

    @staticmethod
    def generate_textures() -> dict[str, pygame.Surface]:
        """Generates all textures and returns them in a dictionary."""
        # Ensure pygame is initialized for surface creation (mostly for format)
        if not pygame.get_init():
            pygame.init()

        textures = {}
        size = 128

        textures["brick"] = TextureGenerator.generate_bricks(
            size, size, (160, 80, 60), (120, 120, 120)
        )
        textures["stone"] = TextureGenerator.generate_stone(size, size)
        textures["metal"] = TextureGenerator.generate_metal(size, size)
        textures["tech"] = TextureGenerator.generate_tech(size, size)
        textures["secret"] = TextureGenerator.generate_secret(size, size)

        return textures
