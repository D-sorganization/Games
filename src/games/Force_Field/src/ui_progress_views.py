from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .game import Game
    from .ui_renderer import UIRenderer


def render_level_complete(renderer: UIRenderer, game: Game) -> None:
    """Render the level-complete screen."""
    renderer.screen.fill(C.BLACK)

    _render_victory_fireworks(renderer, game)

    title = renderer.title_font.render("SECTOR CLEARED", True, C.GREEN)
    renderer.screen.blit(title, title.get_rect(center=(C.SCREEN_WIDTH // 2, 150)))

    level_time = game.level_times[-1] if game.level_times else 0
    total_time = sum(game.level_times)
    stats = [
        (f"Level {game.level} cleared!", C.WHITE),
        (f"Time: {level_time:.1f}s", C.GREEN),
        (f"Total Time: {total_time:.1f}s", C.GREEN),
        (f"Total Kills: {game.kills}", C.WHITE),
        ("", C.WHITE),
        ("Next level: Enemies get stronger!", C.YELLOW),
        ("", C.WHITE),
        ("Press SPACE for next level", C.WHITE),
        ("Press ESC for menu", C.WHITE),
    ]
    render_stats_lines(renderer, stats, 250)
    pygame.display.flip()


def _render_victory_fireworks(renderer: UIRenderer, game: Game) -> None:
    """Spawn and draw particle fireworks on the level-complete screen."""
    if not game.particle_system:
        return

    if random.random() < 0.1:
        game.particle_system.add_victory_fireworks()

    renderer.particle_surface.fill((0, 0, 0, 0))

    for particle in game.particle_system.particles:
        life_ratio = particle.timer / particle.max_timer
        alpha = int(255 * life_ratio)
        color = (
            (*particle.color, alpha) if len(particle.color) == 3 else particle.color
        )
        pygame.draw.circle(
            renderer.particle_surface,
            color,
            (int(particle.x), int(particle.y)),
            int(particle.size),
        )

    renderer.screen.blit(renderer.particle_surface, (0, 0))
    game.particle_system.update()


def render_game_over(renderer: UIRenderer, game: Game) -> None:
    """Render the game-over screen."""
    renderer.screen.fill(C.BLACK)
    title = renderer.title_font.render("SYSTEM FAILURE", True, C.RED)
    title_rect = title.get_rect(center=(C.SCREEN_WIDTH // 2, 200))
    renderer.screen.blit(title, title_rect)

    completed_levels = max(0, game.level - 1)
    total_time = sum(game.level_times)
    avg_time = total_time / len(game.level_times) if game.level_times else 0

    stats = [
        (
            f"You survived {completed_levels} "
            f"level{'s' if completed_levels != 1 else ''}",
            C.WHITE,
        ),
        (f"Total Kills: {game.kills}", C.WHITE),
        (f"Total Time: {total_time:.1f}s", C.GREEN),
        (
            (
                f"Average Time/Level: {avg_time:.1f}s",
                C.GREEN,
            )
            if game.level_times
            else ("", C.WHITE)
        ),
        ("", C.WHITE),
        ("Press SPACE to restart", C.WHITE),
        ("Press ESC for menu", C.WHITE),
    ]
    render_stats_lines(renderer, stats, 250)
    pygame.display.flip()


def render_stats_lines(
    renderer: UIRenderer,
    stats: list[tuple[str, tuple[int, int, int]]],
    start_y: int,
) -> None:
    """Render a centered stack of stat lines."""
    y_pos = start_y
    for line, color in stats:
        if line:
            text = renderer.small_font.render(line, True, color)
            text_rect = text.get_rect(center=(C.SCREEN_WIDTH // 2, y_pos))
            renderer.screen.blit(text, text_rect)
        y_pos += 40
