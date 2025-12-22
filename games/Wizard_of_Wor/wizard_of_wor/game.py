"""
Main game file for Wizard of Wor remake.
"""

# mypy: disable-error-code=unreachable


import math
import random
import sys
from array import array
from typing import NoReturn

import pygame
from constants import (
    BLACK,
    CELL_SIZE,
    CYAN,
    DARK_GRAY,
    ENEMIES_PER_LEVEL,
    FPS,
    GAME_AREA_HEIGHT,
    GAME_AREA_WIDTH,
    GAME_AREA_X,
    GAME_AREA_Y,
    GREEN,
    ORANGE,
    PALE_YELLOW,
    PLAYER_LIVES,
    RADAR_SIZE,
    RADAR_X,
    RADAR_Y,
    RED,
    RESPAWN_SHIELD_FRAMES,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    YELLOW,
)
from dungeon import Dungeon
from effects import RadarPing, SparkleBurst, Vignette, VisualEffect
from enemy import Burwor, Enemy, Garwor, Thorwor, Wizard, Worluk
from player import Player
from radar import Radar


class SoundBoard:
    """Lightweight tone generator for classic arcade-style beeps."""

    def __init__(self) -> None:
        """Initialize the tone generator for arcade-style sound effects."""
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1)
            self.enabled = True
        except pygame.error:
            self.enabled = False

        self.sounds = {
            "shot": self._build_tone(920, 80),
            "enemy_hit": self._build_tone(480, 120),
            "player_hit": self._build_tone(220, 200),
            "spawn": self._build_tone(640, 150),
            "wizard": self._build_tone(300, 200),
        }

        # Create simple intro melody
        self.intro_melody = self._build_intro_melody()

    def _build_tone(self, frequency: int, duration_ms: int) -> pygame.mixer.Sound:
        """Build a tone sound effect with the given frequency and duration."""
        sample_rate = 22050
        sample_count = int(sample_rate * duration_ms / 1000)
        waveform = array("h")
        for i in range(sample_count):
            value = int(14000 * math.sin(2 * math.pi * frequency * (i / sample_rate)))
            waveform.append(value)
        return pygame.mixer.Sound(buffer=waveform.tobytes())

    def _build_intro_melody(self) -> pygame.mixer.Sound:
        """Build a retro-style intro melody reminiscent of classic arcade games."""
        sample_rate = 22050
        duration_ms = 3000  # 3 second intro
        sample_count = int(sample_rate * duration_ms / 1000)
        waveform = array("h")

        # Classic arcade-style melody notes (frequencies in Hz)
        melody = [
            (523, 300),  # C5
            (659, 300),  # E5
            (784, 300),  # G5
            (1047, 600), # C6
            (784, 300),  # G5
            (659, 300),  # E5
            (523, 600),  # C5
        ]

        current_sample = 0
        for freq, note_duration_ms in melody:
            note_samples = int(sample_rate * note_duration_ms / 1000)
            for i in range(note_samples):
                if current_sample >= sample_count:
                    break
                # Create a simple square wave with some envelope
                envelope = min(1.0, (note_samples - i) / (note_samples * 0.1))
                # Square wave generation
                square_wave = 1 if (i * freq // sample_rate) % 2 else -1
                value = int(8000 * envelope * square_wave)
                waveform.append(value)
                current_sample += 1

            # Small pause between notes
            pause_samples = int(sample_rate * 0.05)  # 50ms pause
            for _ in range(pause_samples):
                if current_sample >= sample_count:
                    break
                waveform.append(0)
                current_sample += 1

        # Fill remaining time with silence
        while current_sample < sample_count:
            waveform.append(0)
            current_sample += 1

        return pygame.mixer.Sound(buffer=waveform.tobytes())

    def play(self, name: str) -> None:
        """Play a sound effect by name."""
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def play_intro(self) -> None:
        """Play the intro melody."""
        if self.enabled and hasattr(self, 'intro_melody'):
            self.intro_melody.play()


class WizardOfWorGame:
    """Main game class."""

    def __init__(self) -> None:
        """Initialize the game."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Wizard of Wor Remake")
        self.clock = pygame.time.Clock()
        self.running = True

        # Game state - Start directly in playing mode for easier testing
        self.state = "playing"
        self.level = 1
        self.score = 0
        self.lives = PLAYER_LIVES

        # Game objects
        self.dungeon = Dungeon()
        self.player: Player | None = None
        self.enemies: list[Enemy] = []
        self.bullets: list["Bullet"] = []  # type: ignore[name-defined]  # noqa: F821, UP037
        self.radar = Radar()
        self.wizard_spawned = False
        self.soundboard = SoundBoard()
        self.effects: list[VisualEffect] = []
        self.vignette = Vignette(
            (GAME_AREA_WIDTH, GAME_AREA_HEIGHT),
            (GAME_AREA_X, GAME_AREA_Y),
        )

        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)

        # Auto-start the first level
        self.start_level()

        # Play intro music
        self.soundboard.play_intro()

    def start_level(self) -> None:
        """Start a new level."""
        self.state = "playing"
        self.dungeon = Dungeon()
        self.bullets = []
        self.wizard_spawned = False
        self.effects = []

        # Spawn player
        player_pos = self.dungeon.get_random_spawn_position(prefer_player=True)
        self.player = Player(player_pos[0], player_pos[1])
        self.player.grant_shield(RESPAWN_SHIELD_FRAMES)
        self.effects.append(SparkleBurst(player_pos, GREEN, count=14))

        # Spawn enemies based on level
        self.enemies = []
        level_config = ENEMIES_PER_LEVEL.get(min(self.level, 5), ENEMIES_PER_LEVEL[5])

        for _ in range(level_config["burwor"]):
            self._spawn_enemy(Burwor)

        for _ in range(level_config["garwor"]):
            self._spawn_enemy(Garwor)

        for _ in range(level_config["thorwor"]):
            self._spawn_enemy(Thorwor)

        # Occasionally spawn Worluk
        if self.level > 1 and len(self.enemies) > 0:
            self._spawn_enemy(Worluk)
        self.soundboard.play("spawn")

    def spawn_wizard(self) -> None:
        """Spawn the Wizard of Wor."""
        if not self.wizard_spawned:
            pos = self.dungeon.get_random_spawn_position()
            self.enemies.append(Wizard(pos[0], pos[1]))
            self.wizard_spawned = True
            self.soundboard.play("wizard")

    def _spawn_enemy(self, enemy_cls: type["Enemy"]) -> None:
        """Spawn a single enemy with spacing away from the player."""
        chosen_pos = None
        for _ in range(20):  # Increased attempts for better positioning
            pos = self.dungeon.get_random_spawn_position()
            if self.player is None:
                chosen_pos = pos
                break
            player_vector = pygame.math.Vector2(self.player.x, self.player.y)
            distance = player_vector.distance_to(pygame.math.Vector2(pos))
            # Require minimum distance of 4 cells from player
            if distance > CELL_SIZE * 4:
                chosen_pos = pos
                break

        # Fallback: if no good position found, use a corner spawn
        if chosen_pos is None:
            corner_positions = [
                (
                    GAME_AREA_X + CELL_SIZE * 2,
                    GAME_AREA_Y + CELL_SIZE * 2,
                ),
                (
                    GAME_AREA_X + GAME_AREA_WIDTH - CELL_SIZE * 2,
                    GAME_AREA_Y + CELL_SIZE * 2,
                ),
                (
                    GAME_AREA_X + CELL_SIZE * 2,
                    GAME_AREA_Y + GAME_AREA_HEIGHT - CELL_SIZE * 2,
                ),
                (
                    GAME_AREA_X + GAME_AREA_WIDTH - CELL_SIZE * 2,
                    GAME_AREA_Y + GAME_AREA_HEIGHT - CELL_SIZE * 2,
                ),
            ]
            chosen_pos = random.choice(corner_positions)

        self.enemies.append(enemy_cls(chosen_pos[0], chosen_pos[1]))
        self.effects.append(SparkleBurst(chosen_pos, CYAN, count=12))

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
                        if self.player is not None:
                            bullet, muzzle = self.player.shoot()
                            if bullet:
                                self.bullets.append(bullet)
                                if muzzle:
                                    self.effects.append(muzzle)
                                self.soundboard.play("shot")
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "paused"
                    elif event.key == pygame.K_p:
                        self.state = "paused"

                elif self.state == "paused":
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                        self.state = "playing"
                    elif event.key == pygame.K_q:
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
        if self.state not in ("playing", "paused"):
            return

        # Don't update game logic when paused
        if self.state == "paused":
            return

        previous_ping = self.radar.ping_timer
        self.radar.update()
        if self.radar.ping_timer > previous_ping:
            center = (
                self.radar.x + self.radar.size // 2,
                self.radar.y + self.radar.size // 2,
            )
            self.effects.append(RadarPing(center))

        # Get keys for continuous input
        keys = pygame.key.get_pressed()

        # Update player
        if self.player is not None:
            self.player.update(keys, self.dungeon, self.effects)

        # Update enemies
        if self.player is not None:
            player_pos = (self.player.x, self.player.y)
        else:
            player_pos = (0, 0)
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
        elif len(alive_enemies) <= 1 and not self.wizard_spawned:
            # Spawn wizard when only 1 enemy remains (more like original)
            self.spawn_wizard()

        # Check lose condition
        if self.player is not None and not self.player.alive:
            self.lives -= 1
            if self.lives > 0:
                # Respawn player
                pos = self.dungeon.get_random_spawn_position()
                self.player = Player(pos[0], pos[1])
                self.player.grant_shield(RESPAWN_SHIELD_FRAMES)

                self.effects.append(SparkleBurst(pos, GREEN, count=12))
                self.bullets = [b for b in self.bullets if b.is_player_bullet]
            else:
                self.state = "game_over"

        self._update_effects()

    def check_collisions(self) -> None:
        """Check for collisions between bullets and entities."""
        bullets_to_remove = []

        # Player bullets hitting enemies
        for bullet in self.bullets:
            if not bullet.is_player_bullet or not bullet.active:
                continue

            for enemy in self.enemies:
                if enemy.alive and bullet.rect.colliderect(enemy.rect):
                    points = enemy.take_damage()
                    self.score += points
                    bullet.active = False
                    bullets_to_remove.append(bullet)
                    self.soundboard.play("enemy_hit")
                    self.effects.append(
                        SparkleBurst((enemy.x, enemy.y), enemy.color, count=10),
                    )
                    break

        # Enemy bullets hitting player
        for bullet in self.bullets:
            if (
                bullet.is_player_bullet
                or not bullet.active
                or bullet in bullets_to_remove
            ):
                continue

            if (
                self.player is not None
                and self.player.alive
                and bullet.rect.colliderect(self.player.rect)
            ):
                took_damage = self.player.take_damage()
                bullet.active = False
                bullets_to_remove.append(bullet)
                if took_damage:
                    self.soundboard.play("player_hit")
                    self.effects.append(
                        SparkleBurst((self.player.x, self.player.y), RED, count=16),
                    )

        # Remove bullets that hit something
        for bullet in bullets_to_remove:
            if bullet in self.bullets:
                self.bullets.remove(bullet)

        # Player colliding with enemies
        if self.player is not None and self.player.alive:
            for enemy in self.enemies:
                if enemy.alive and self.player.rect.colliderect(enemy.rect):
                    took_damage = self.player.take_damage()
                    if took_damage:
                        self.soundboard.play("player_hit")
                        self.effects.append(
                            SparkleBurst((self.player.x, self.player.y), RED, count=16),
                        )
                    break

    def _update_effects(self) -> None:
        """Advance and cull transient visual effects."""
        next_effects: list[VisualEffect] = []
        for effect in self.effects:
            if effect.update():
                next_effects.append(effect)
        self.effects = next_effects

    def _draw_effects_by_layer(self, layer: str) -> None:
        """Draw all effects matching a specific layer."""
        for effect in self.effects:
            if getattr(effect, "layer", "") == layer:
                effect.draw(self.screen)

    def draw(self) -> None:
        """Draw everything."""
        self.screen.fill(BLACK)

        if self.state == "menu":
            self.draw_menu()
        elif self.state == "playing":
            self.draw_game()
        elif self.state == "paused":
            self.draw_paused()
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
            "P or ESC - Pause",
            "",
            "Press ENTER to Start",
            "Press ESC to Quit",
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

        # Effects under actors
        self._draw_effects_by_layer("floor")

        # Draw player
        if self.player is not None:
            self.player.draw(self.screen)

        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)

        self._draw_effects_by_layer("middle")

        # Draw bullets and top-layer effects
        for bullet in self.bullets:
            bullet.draw(self.screen)
        self._draw_effects_by_layer("top")

        # Vignette over playfield
        self.vignette.draw(self.screen)

        # Draw radar
        self.radar.draw(self.screen, self.enemies, self.player)
        self._draw_effects_by_layer("hud")

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

        # Shield indicator
        if self.player is not None:
            shield_ratio = 0.0
            if self.player.invulnerable_timer > 0:
                shield_ratio = min(
                    1.0,
                    self.player.invulnerable_timer / RESPAWN_SHIELD_FRAMES,
                )
            bar_width = 140
            bar_height = 10
            bar_x = GAME_AREA_X
            bar_y = GAME_AREA_Y + GAME_AREA_HEIGHT + 16
            pygame.draw.rect(
                self.screen,
                DARK_GRAY,
                (bar_x, bar_y, bar_width, bar_height),
            )
            if shield_ratio > 0:
                pygame.draw.rect(
                    self.screen,
                    PALE_YELLOW,
                    (bar_x, bar_y, int(bar_width * shield_ratio), bar_height),
                )
            shield_text = self.font_small.render("Shield", True, PALE_YELLOW)
            self.screen.blit(shield_text, (bar_x, bar_y - 18))

        # Wizard arrival meter
        total_enemies = sum(1 for e in self.enemies)
        if total_enemies > 0:
            progress = 1 - (alive_enemies / max(1, total_enemies))
            bar_width = 180
            bar_height = 8
            bar_x = GAME_AREA_X + 220
            bar_y = GAME_AREA_Y + GAME_AREA_HEIGHT + 16
            pygame.draw.rect(
                self.screen,
                DARK_GRAY,
                (bar_x, bar_y, bar_width, bar_height),
            )
            pygame.draw.rect(
                self.screen,
                ORANGE,
                (bar_x, bar_y, int(bar_width * progress), bar_height),
            )
            wizard_text = self.font_small.render("Wizard Warmup", True, ORANGE)
            self.screen.blit(wizard_text, (bar_x, bar_y - 18))

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
        continue_rect = continue_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50),
        )
        self.screen.blit(continue_text, continue_rect)

    def draw_game_over(self) -> None:
        """Draw game over screen."""
        title = self.font_large.render("GAME OVER", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.screen.blit(title, title_rect)

        score_text = self.font_medium.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(score_text, score_rect)

        level_text = self.font_medium.render(
            f"Reached Level: {self.level}",
            True,
            WHITE,
        )
        level_rect = level_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50),
        )
        self.screen.blit(level_text, level_rect)

        restart_text = self.font_small.render("Press ENTER to play again", True, WHITE)
        restart_rect = restart_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100),
        )
        self.screen.blit(restart_text, restart_rect)

        menu_text = self.font_small.render("Press ESC for menu", True, WHITE)
        menu_rect = menu_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 130),
        )
        self.screen.blit(menu_text, menu_rect)

    def draw_paused(self) -> None:
        """Draw pause screen."""
        self.draw_game()  # Draw game in background

        # Overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Text
        text = self.font_large.render("PAUSED", True, YELLOW)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(text, text_rect)

        instructions = [
            "P or ESC - Resume",
            "Q - Quit to Menu",
        ]

        y_offset = SCREEN_HEIGHT // 2
        for line in instructions:
            instruction_text = self.font_small.render(line, True, WHITE)
            instruction_rect = instruction_text.get_rect(
            center=(SCREEN_WIDTH // 2, y_offset)
        )
            self.screen.blit(instruction_text, instruction_rect)
            y_offset += 30

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
