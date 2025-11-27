"""
Main game file for Wizard of Wor remake.
"""
import sys
from typing import NoReturn

import pygame
from constants import *
from dungeon import Dungeon
from enemy import Burwor, Garwor, Thorwor, Wizard, Worluk
from player import Player
from radar import Radar


class WizardOfWorGame:
    """Main game class."""

    def __init__(self):
        """Initialize the game."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Wizard of Wor Remake")
        self.clock = pygame.time.Clock()
        self.running = True

        # Game state
        self.state = "menu"  # menu, playing, game_over, level_complete
        self.level = 1
        self.score = 0
        self.lives = PLAYER_LIVES

        # Game objects
        self.dungeon = Dungeon()
        self.player = None
        self.enemies = []
        self.bullets = []
        self.radar = Radar()
        self.wizard_spawned = False

        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)

    def start_level(self) -> None:
        """Start a new level."""
        self.state = "playing"
        self.dungeon = Dungeon()
        self.bullets = []
        self.wizard_spawned = False

        # Spawn player
        player_pos = self.dungeon.get_random_spawn_position()
        self.player = Player(player_pos[0], player_pos[1])

        # Spawn enemies based on level
        self.enemies = []
        level_config = ENEMIES_PER_LEVEL.get(min(self.level, 5), ENEMIES_PER_LEVEL[5])

        for _ in range(level_config["burwor"]):
            pos = self.dungeon.get_random_spawn_position()
            self.enemies.append(Burwor(pos[0], pos[1]))

        for _ in range(level_config["garwor"]):
            pos = self.dungeon.get_random_spawn_position()
            self.enemies.append(Garwor(pos[0], pos[1]))

        for _ in range(level_config["thorwor"]):
            pos = self.dungeon.get_random_spawn_position()
            self.enemies.append(Thorwor(pos[0], pos[1]))

        # Occasionally spawn Worluk
        if self.level > 1 and len(self.enemies) > 0:
            pos = self.dungeon.get_random_spawn_position()
            self.enemies.append(Worluk(pos[0], pos[1]))

    def spawn_wizard(self) -> None:
        """Spawn the Wizard of Wor."""
        if not self.wizard_spawned:
            pos = self.dungeon.get_random_spawn_position()
            self.enemies.append(Wizard(pos[0], pos[1]))
            self.wizard_spawned = True

    def handle_events(self) -> None:
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if self.state == "menu":
                    if event.key == pygame.K_RETURN:
                        self.start_level()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

                elif self.state == "playing":
                    if event.key == pygame.K_SPACE:
                        bullet = self.player.shoot()
                        if bullet:
                            self.bullets.append(bullet)
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "menu"

                elif self.state == "game_over":
                    if event.key == pygame.K_RETURN:
                        self.level = 1
                        self.score = 0
                        self.lives = PLAYER_LIVES
                        self.start_level()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "menu"

                elif self.state == "level_complete":
                    if event.key == pygame.K_RETURN:
                        self.level += 1
                        self.start_level()

    def update(self) -> None:
        """Update game state."""
        if self.state != "playing":
            return

        # Get keys for continuous input
        keys = pygame.key.get_pressed()

        # Update player
        self.player.update(keys, self.dungeon)

        # Update enemies
        player_pos = (self.player.x, self.player.y)
        for enemy in self.enemies:
            enemy.update(self.dungeon, player_pos)

            # Enemy shooting
            bullet = enemy.try_shoot()
            if bullet:
                self.bullets.append(bullet)

        # Update bullets
        for bullet in self.bullets[:]:
            bullet.update(self.dungeon)
            if not bullet.active:
                self.bullets.remove(bullet)

        # Check collisions
        self.check_collisions()

        # Check win condition
        alive_enemies = [e for e in self.enemies if e.alive]
        if len(alive_enemies) == 0:
            self.state = "level_complete"
        elif len(alive_enemies) <= 2 and not self.wizard_spawned:
            # Spawn wizard when few enemies remain
            self.spawn_wizard()

        # Check lose condition
        if not self.player.alive:
            self.lives -= 1
            if self.lives > 0:
                # Respawn player
                pos = self.dungeon.get_random_spawn_position()
                self.player = Player(pos[0], pos[1])
                self.bullets = [b for b in self.bullets if b.is_player_bullet]
            else:
                self.state = "game_over"

    def check_collisions(self) -> None:
        """Check for collisions between bullets and entities."""
        # Player bullets hitting enemies
        for bullet in self.bullets[:]:
            if not bullet.is_player_bullet or not bullet.active:
                continue

            for enemy in self.enemies:
                if enemy.alive and bullet.rect.colliderect(enemy.rect):
                    points = enemy.take_damage()
                    self.score += points
                    bullet.active = False
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break

        # Enemy bullets hitting player
        for bullet in self.bullets[:]:
            if bullet.is_player_bullet or not bullet.active:
                continue

            if self.player.alive and bullet.rect.colliderect(self.player.rect):
                self.player.take_damage()
                bullet.active = False
                if bullet in self.bullets:
                    self.bullets.remove(bullet)

        # Player colliding with enemies
        if self.player.alive:
            for enemy in self.enemies:
                if enemy.alive and self.player.rect.colliderect(enemy.rect):
                    self.player.take_damage()
                    break

    def draw(self) -> None:
        """Draw everything."""
        self.screen.fill(BLACK)

        if self.state == "menu":
            self.draw_menu()
        elif self.state == "playing":
            self.draw_game()
        elif self.state == "level_complete":
            self.draw_level_complete()
        elif self.state == "game_over":
            self.draw_game_over()

        pygame.display.flip()

    def draw_menu(self) -> None:
        """Draw main menu."""
        title = self.font_large.render("WIZARD OF WOR", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(title, title_rect)

        instructions = [
            "WASD or Arrow Keys - Move",
            "SPACE - Shoot",
            "ESC - Pause/Menu",
            "",
            "Press ENTER to Start",
            "Press ESC to Quit"
        ]

        y_offset = SCREEN_HEIGHT // 2
        for line in instructions:
            text = self.font_small.render(line, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 30

    def draw_game(self) -> None:
        """Draw game screen."""
        # Draw dungeon
        self.dungeon.draw(self.screen)

        # Draw player
        self.player.draw(self.screen)

        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(self.screen)

        # Draw radar
        self.radar.draw(self.screen, self.enemies, self.player)

        # Draw UI
        self.draw_ui()

    def draw_ui(self) -> None:
        """Draw user interface (score, lives, level)."""
        # Score
        score_text = self.font_medium.render(f"SCORE: {self.score}", True, WHITE)
        self.screen.blit(score_text, (GAME_AREA_X, 10))

        # Lives
        lives_text = self.font_medium.render(f"LIVES: {self.lives}", True, WHITE)
        self.screen.blit(lives_text, (GAME_AREA_X + 250, 10))

        # Level
        level_text = self.font_medium.render(f"LEVEL: {self.level}", True, WHITE)
        self.screen.blit(level_text, (GAME_AREA_X + 450, 10))

        # Enemies remaining
        alive_enemies = sum(1 for e in self.enemies if e.alive)
        enemies_text = self.font_small.render(f"Enemies: {alive_enemies}", True, CYAN)
        self.screen.blit(enemies_text, (RADAR_X, RADAR_Y + RADAR_SIZE + 10))

    def draw_level_complete(self) -> None:
        """Draw level complete screen."""
        self.draw_game()  # Draw game in background

        # Overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Text
        text = self.font_large.render("LEVEL COMPLETE!", True, GREEN)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(text, text_rect)

        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(score_text, score_rect)

        continue_text = self.font_small.render("Press ENTER to continue", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(continue_text, continue_rect)

    def draw_game_over(self) -> None:
        """Draw game over screen."""
        title = self.font_large.render("GAME OVER", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(title, title_rect)

        score_text = self.font_medium.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(score_text, score_rect)

        level_text = self.font_medium.render(f"Reached Level: {self.level}", True, WHITE)
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(level_text, level_rect)

        restart_text = self.font_small.render("Press ENTER to play again", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        self.screen.blit(restart_text, restart_rect)

        menu_text = self.font_small.render("Press ESC for menu", True, WHITE)
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 130))
        self.screen.blit(menu_text, menu_rect)

    def run(self) -> NoReturn:
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def main() -> NoReturn:
    """Entry point."""
    game = WizardOfWorGame()
    game.run()


if __name__ == "__main__":
    main()
