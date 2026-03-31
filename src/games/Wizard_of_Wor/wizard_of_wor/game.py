"""
Main game file for Wizard of Wor remake.

The monolithic WizardOfWorGame class has been decomposed following SRP:
- Rendering is handled by :class:`~render_mixin.RenderMixin`.
- Audio wiring is handled by :class:`~audio_mixin.AudioMixin`.
- Collision detection is delegated to :class:`~collision_manager.CollisionManager`.
"""

# mypy: disable-error-code=unreachable

import random
import sys
from typing import NoReturn

import pygame
from audio_mixin import AudioMixin, SoundBoard
from bullet import Bullet
from collision_manager import CollisionManager
from constants import (
    CELL_SIZE,
    CYAN,
    ENEMIES_PER_LEVEL,
    FPS,
    GAME_AREA_HEIGHT,
    GAME_AREA_WIDTH,
    GAME_AREA_X,
    GAME_AREA_Y,
    GREEN,
    PLAYER_LIVES,
    PLAYER_SIZE,
    RESPAWN_SHIELD_FRAMES,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from dungeon import Dungeon
from effects import RadarPing, SparkleBurst, Vignette, VisualEffect
from enemy import Burwor, Enemy, Garwor, Thorwor, Wizard, Worluk
from player import Player
from radar import Radar
from render_mixin import RenderMixin

from games.shared.spatial_grid import SpatialGrid

from games.shared.spatial_grid import SpatialGrid


class WizardOfWorGame(RenderMixin, AudioMixin):
    """Main game class.

    Delegates rendering to :class:`~render_mixin.RenderMixin` and audio event
    wiring to :class:`~audio_mixin.AudioMixin`.  Collision detection is owned
    by :class:`~collision_manager.CollisionManager`.
    """

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
        self.bullets: list[Bullet] = []
        self.radar = Radar()
        # Spatial grid for O(1) average-case collision detection (fixes #681)
        self._enemy_grid: SpatialGrid = SpatialGrid(cell_size=float(CELL_SIZE))
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

        # Collision manager wired to game callbacks
        self._collision_manager = CollisionManager(
            enemy_grid=self._enemy_grid,
            on_enemy_hit=self._add_score,
            on_player_hit=self._handle_player_hit,
            on_audio_enemy_hit=self._audio_play_enemy_hit,
            on_audio_player_hit=self._audio_play_player_hit,
        )

        # Auto-start the first level
        self.start_level()

        # Play intro music
        self._audio_play_intro()

    # ------------------------------------------------------------------
    # Level management
    # ------------------------------------------------------------------

    def start_level(self) -> None:
        """Start a new level."""
        self.state = "playing"
        self.dungeon = Dungeon()
        self.bullets = []
        self.wizard_spawned = False
        self.effects = []

        self.respawn_player()

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
        self._audio_play_spawn()

    def spawn_wizard(self) -> None:
        """Spawn the Wizard of Wor."""
        if not self.wizard_spawned:
            pos = self.dungeon.get_random_spawn_position()
            self.enemies.append(Wizard(pos[0], pos[1]))
            self.wizard_spawned = True
            self._audio_play_wizard()

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

    def respawn_player(self) -> None:
        """Respawn the player at a valid spawn point."""
        pos = self.dungeon.get_random_spawn_position(prefer_player=True)
        self.player = Player(pos[0], pos[1])
        self.player.grant_shield(RESPAWN_SHIELD_FRAMES)
        self.effects.append(SparkleBurst(pos, GREEN, count=12))
        # Keep only player bullets when player dies
        self.bullets = [b for b in self.bullets if b.is_player_bullet]

    def set_player_position(self, x: float, y: float) -> None:
        """Move the player to (*x*, *y*) and keep the collision rect in sync.

        Prefer this over accessing ``player.rect`` directly from outside the
        game class (Law of Demeter).
        """
        if self.player is None:
            return
        self.player.x = x
        self.player.y = y
        self.player.rect.x = int(x) - PLAYER_SIZE // 2
        self.player.rect.y = int(y) - PLAYER_SIZE // 2

    # ------------------------------------------------------------------
    # Score / damage callbacks (used by CollisionManager)
    # ------------------------------------------------------------------

    def _add_score(self, points: int) -> None:
        """Add *points* to the player score.

        :param points: point value returned by ``enemy.take_damage()``.
        """
        self.score += points

    def _handle_player_hit(self) -> None:
        """React to the player taking damage (called by CollisionManager).

        Life-loss and respawn are deferred to update() so they happen once
        per frame regardless of how many collisions occurred.
        """

    # ------------------------------------------------------------------
    # Input / update / collision
    # ------------------------------------------------------------------

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
                                self._audio_play_shot()
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

        # Update bullets – use list-comprehension for O(n) deferred removal
        # instead of remove() inside the loop which is O(n^2).
        for bullet in self.bullets:
            bullet.update(self.dungeon)
        self.bullets = [b for b in self.bullets if b.active]

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
                self.respawn_player()
            else:
                self.state = "game_over"

        self._update_effects()

    def check_collisions(self) -> None:
        """Delegate collision detection to the CollisionManager.

        Keeps a thin adapter here so existing tests that call
        ``game.check_collisions()`` continue to work unchanged.

        Uses a spatial hash grid so each bullet only tests the handful of
        enemies that share its grid cell and its 8 neighbours, giving
        O(bullets * local_density) instead of O(bullets * total_enemies).
        """
        self.bullets = self._collision_manager.check(
            self.bullets,
            self.enemies,
            self.player,
            self.effects,
        )

    def _update_effects(self) -> None:
        """Advance and cull transient visual effects."""
        next_effects: list[VisualEffect] = []
        for effect in self.effects:
            if effect.update():
                next_effects.append(effect)
        self.effects = next_effects

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

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
