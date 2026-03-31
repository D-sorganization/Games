"""Rendering mixin for Wizard of Wor – separates all draw logic from game state.

Single-Responsibility: this module owns every pixel that appears on screen.
It reads game state but never mutates it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from constants import (
    BLACK,
    CYAN,
    DARK_GRAY,
    GAME_AREA_HEIGHT,
    GAME_AREA_X,
    GAME_AREA_Y,
    GREEN,
    ORANGE,
    PALE_YELLOW,
    RADAR_SIZE,
    RADAR_X,
    RADAR_Y,
    RED,
    RESPAWN_SHIELD_FRAMES,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIELD_BAR_WIDTH,
    WHITE,
    WIZARD_ARRIVAL_BAR_WIDTH,
    YELLOW,
)

if TYPE_CHECKING:
    pass


class RenderMixin:
    """Mixin that provides all rendering methods for WizardOfWorGame.

    Pre-condition: ``self.screen``, ``self.state``, ``self.font_large``,
    ``self.font_medium``, ``self.font_small``, ``self.dungeon``,
    ``self.player``, ``self.enemies``, ``self.bullets``, ``self.effects``,
    ``self.vignette``, ``self.radar``, ``self.score``, ``self.lives``,
    ``self.level`` are all initialised by WizardOfWorGame.__init__ before
    any draw method is called.
    """

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def draw(self) -> None:
        """Draw everything to screen and flip the display."""
        self.screen.fill(BLACK)  # type: ignore[attr-defined]

        state = self.state  # type: ignore[attr-defined]
        if state == "menu":
            self.draw_menu()
        elif state == "playing":
            self.draw_game()
        elif state == "paused":
            self.draw_paused()
        elif state == "level_complete":
            self.draw_level_complete()
        elif state == "game_over":
            self.draw_game_over()

        pygame.display.flip()

    # ------------------------------------------------------------------
    # Screen-state drawers
    # ------------------------------------------------------------------

    def draw_menu(self) -> None:
        """Draw the main menu screen."""
        title = self.font_large.render("WIZARD OF WOR", True, YELLOW)  # type: ignore[attr-defined]
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(title, title_rect)  # type: ignore[attr-defined]

        instructions = [
            "WASD or Arrow Keys - Move",
            "SPACE - Shoot",
            "P or ESC - Pause",
            "",
            "Press ENTER to Start",
            "Press ESC to Quit",
        ]

        y_offset = SCREEN_HEIGHT // 2
        for line in instructions:
            text = self.font_medium.render(line, True, WHITE)  # type: ignore[attr-defined]
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(text, text_rect)  # type: ignore[attr-defined]
            y_offset += 30

    def draw_game(self) -> None:
        """Draw the main gameplay screen."""
        self.dungeon.draw(self.screen)  # type: ignore[attr-defined]

        self._draw_effects_by_layer("floor")

        if self.player is not None:  # type: ignore[attr-defined]
            self.player.draw(self.screen)  # type: ignore[attr-defined]

        for enemy in self.enemies:  # type: ignore[attr-defined]
            enemy.draw(self.screen)

        self._draw_effects_by_layer("middle")

        for bullet in self.bullets:  # type: ignore[attr-defined]
            bullet.draw(self.screen)
        self._draw_effects_by_layer("top")

        self.vignette.draw(self.screen)  # type: ignore[attr-defined]

        self.radar.draw(self.screen, self.enemies, self.player)  # type: ignore[attr-defined]
        self._draw_effects_by_layer("hud")

        self.draw_ui()

    def draw_ui(self) -> None:
        """Draw the HUD: score, lives, level, shield bar, wizard meter."""
        score_text = self.font_medium.render(f"SCORE: {self.score}", True, WHITE)  # type: ignore[attr-defined]
        self.screen.blit(score_text, (GAME_AREA_X, 10))  # type: ignore[attr-defined]

        lives_text = self.font_medium.render(f"LIVES: {self.lives}", True, WHITE)  # type: ignore[attr-defined]
        self.screen.blit(lives_text, (GAME_AREA_X + 250, 10))  # type: ignore[attr-defined]

        level_text = self.font_medium.render(f"LEVEL: {self.level}", True, WHITE)  # type: ignore[attr-defined]
        self.screen.blit(level_text, (GAME_AREA_X + 450, 10))  # type: ignore[attr-defined]

        alive_enemies = sum(1 for e in self.enemies if e.alive)  # type: ignore[attr-defined]
        enemies_text = self.font_small.render(f"Enemies: {alive_enemies}", True, CYAN)  # type: ignore[attr-defined]
        self.screen.blit(enemies_text, (RADAR_X, RADAR_Y + RADAR_SIZE + 10))  # type: ignore[attr-defined]

        self._draw_shield_bar()
        self._draw_wizard_meter(alive_enemies)

    def draw_level_complete(self) -> None:
        """Draw the level-complete overlay."""
        self.draw_game()

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))  # type: ignore[attr-defined]

        text = self.font_large.render("LEVEL COMPLETE!", True, GREEN)  # type: ignore[attr-defined]
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(text, text_rect)  # type: ignore[attr-defined]

        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)  # type: ignore[attr-defined]
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(score_text, score_rect)  # type: ignore[attr-defined]

        continue_text = self.font_small.render("Press ENTER to continue", True, WHITE)  # type: ignore[attr-defined]
        continue_rect = continue_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50),
        )
        self.screen.blit(continue_text, continue_rect)  # type: ignore[attr-defined]

    def draw_game_over(self) -> None:
        """Draw the game-over screen."""
        title = self.font_large.render("GAME OVER", True, RED)  # type: ignore[attr-defined]
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(title, title_rect)  # type: ignore[attr-defined]

        score_text = self.font_medium.render(f"Final Score: {self.score}", True, WHITE)  # type: ignore[attr-defined]
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(score_text, score_rect)  # type: ignore[attr-defined]

        level_text = self.font_medium.render(
            f"Reached Level: {self.level}",
            True,
            WHITE,
        )  # type: ignore[attr-defined]
        level_rect = level_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50),
        )
        self.screen.blit(level_text, level_rect)  # type: ignore[attr-defined]

        restart_text = self.font_small.render(  # type: ignore[attr-defined]
            "Press ENTER to play again", True, WHITE
        )
        restart_rect = restart_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100),
        )
        self.screen.blit(restart_text, restart_rect)  # type: ignore[attr-defined]

        menu_text = self.font_small.render("Press ESC for menu", True, WHITE)  # type: ignore[attr-defined]
        menu_rect = menu_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 130),
        )
        self.screen.blit(menu_text, menu_rect)  # type: ignore[attr-defined]

    def draw_paused(self) -> None:
        """Draw the pause overlay."""
        self.draw_game()

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))  # type: ignore[attr-defined]

        text = self.font_large.render("PAUSED", True, YELLOW)  # type: ignore[attr-defined]
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(text, text_rect)  # type: ignore[attr-defined]

        instructions = [
            "P or ESC - Resume",
            "Q - Quit to Menu",
        ]

        y_offset = SCREEN_HEIGHT // 2
        for line in instructions:
            instruction_text = self.font_small.render(line, True, WHITE)  # type: ignore[attr-defined]
            instruction_rect = instruction_text.get_rect(
                center=(SCREEN_WIDTH // 2, y_offset)
            )
            self.screen.blit(instruction_text, instruction_rect)  # type: ignore[attr-defined]
            y_offset += 30

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _draw_effects_by_layer(self, layer: str) -> None:
        """Draw all visual effects on the given rendering layer."""
        for effect in self.effects:  # type: ignore[attr-defined]
            if getattr(effect, "layer", "") == layer:
                effect.draw(self.screen)  # type: ignore[attr-defined]

    def _draw_shield_bar(self) -> None:
        """Render the respawn-shield progress bar."""
        if self.player is None:  # type: ignore[attr-defined]
            return
        shield_ratio = 0.0
        if self.player.invulnerable_timer > 0:  # type: ignore[attr-defined]
            shield_ratio = min(
                1.0,
                self.player.invulnerable_timer / RESPAWN_SHIELD_FRAMES,  # type: ignore[attr-defined]
            )
        bar_width = SHIELD_BAR_WIDTH
        bar_height = 10
        bar_x = GAME_AREA_X
        bar_y = GAME_AREA_Y + GAME_AREA_HEIGHT + 16
        pygame.draw.rect(
            self.screen,  # type: ignore[attr-defined]
            DARK_GRAY,
            (bar_x, bar_y, bar_width, bar_height),
        )
        if shield_ratio > 0:
            pygame.draw.rect(
                self.screen,  # type: ignore[attr-defined]
                PALE_YELLOW,
                (bar_x, bar_y, int(bar_width * shield_ratio), bar_height),
            )
        shield_text = self.font_small.render("Shield", True, PALE_YELLOW)  # type: ignore[attr-defined]
        self.screen.blit(shield_text, (bar_x, bar_y - 18))  # type: ignore[attr-defined]

    def _draw_wizard_meter(self, alive_enemies: int) -> None:
        """Render the wizard-arrival progress bar.

        :param alive_enemies: number of enemies currently alive.
        """
        total_enemies = sum(1 for _ in self.enemies)  # type: ignore[attr-defined]
        if total_enemies <= 0:
            return
        progress = 1 - (alive_enemies / max(1, total_enemies))
        bar_width = WIZARD_ARRIVAL_BAR_WIDTH
        bar_height = 8
        bar_x = GAME_AREA_X + 220
        bar_y = GAME_AREA_Y + GAME_AREA_HEIGHT + 16
        pygame.draw.rect(
            self.screen,  # type: ignore[attr-defined]
            DARK_GRAY,
            (bar_x, bar_y, bar_width, bar_height),
        )
        pygame.draw.rect(
            self.screen,  # type: ignore[attr-defined]
            ORANGE,
            (bar_x, bar_y, int(bar_width * progress), bar_height),
        )
        wizard_text = self.font_small.render("Wizard Warmup", True, ORANGE)  # type: ignore[attr-defined]
        self.screen.blit(wizard_text, (bar_x, bar_y - 18))  # type: ignore[attr-defined]
