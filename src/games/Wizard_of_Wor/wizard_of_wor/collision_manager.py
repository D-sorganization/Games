"""Collision manager for Wizard of Wor.

Single-Responsibility: owns all collision-detection logic.  The manager
receives the mutable game collections it needs and produces side-effects
(damage, sound calls, score increments) through the callbacks injected at
construction time, keeping it decoupled from WizardOfWorGame.

Usage::

    manager = CollisionManager(
        enemy_grid=game._enemy_grid,
        on_enemy_hit=game._on_enemy_hit,
        on_player_hit=game._on_player_hit,
    )
    manager.check(game.bullets, game.enemies, game.player,
                  game.score_ref, game.effects)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from bullet import Bullet
from constants import RED
from effects import SparkleBurst

if TYPE_CHECKING:
    from enemy import Enemy
    from player import Player

    from games.shared.spatial_grid import SpatialGrid


class CollisionManager:
    """Performs all bullet/entity and player/enemy collision detection.

    Uses the caller-supplied :class:`~games.shared.spatial_grid.SpatialGrid`
    so each bullet only tests the handful of enemies that share its cell and
    its 8 neighbours: O(bullets * local_density) rather than O(bullets *
    total_enemies).

    :param enemy_grid: pre-built spatial grid; rebuilt each frame by
        :meth:`check`.
    :param on_enemy_hit: called with ``(points: int)`` when a player bullet
        kills an enemy; typically increments the score.
    :param on_player_hit: called with no arguments when the player takes
        damage; typically triggers a respawn or game-over transition.
    :param on_audio_enemy_hit: called to emit the enemy-hit sound.
    :param on_audio_player_hit: called to emit the player-hit sound.
    """

    def __init__(
        self,
        enemy_grid: SpatialGrid,
        on_enemy_hit: Callable[[int], None],
        on_player_hit: Callable[[], None],
        on_audio_enemy_hit: Callable[[], None],
        on_audio_player_hit: Callable[[], None],
    ) -> None:
        """Initialise the collision manager with the given grid and callbacks."""
        self._grid = enemy_grid
        self._on_enemy_hit = on_enemy_hit
        self._on_player_hit = on_player_hit
        self._on_audio_enemy_hit = on_audio_enemy_hit
        self._on_audio_player_hit = on_audio_player_hit

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(
        self,
        bullets: list[Bullet],
        enemies: list[Enemy],
        player: Player | None,
        effects: list,
    ) -> list[Bullet]:
        """Run all collision checks and return the surviving bullet list.

        :param bullets: current active bullet list; modified in place via
            deferred set-based removal.
        :param enemies: all enemies (alive or dead).
        :param player: the player entity, or ``None`` if not yet spawned.
        :param effects: effects list; ``SparkleBurst`` entries are appended.
        :returns: a new list containing only bullets that survived the frame.
        """
        alive_enemies = [e for e in enemies if e.alive]
        self._grid.update(alive_enemies)

        bullets_to_remove: set[Bullet] = set()

        self._check_player_bullets(bullets, bullets_to_remove, effects)
        self._check_enemy_bullets(bullets, player, bullets_to_remove, effects)
        self._check_player_enemy_contact(player, effects)

        if bullets_to_remove:
            return [b for b in bullets if b not in bullets_to_remove]
        return bullets

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_player_bullets(
        self,
        bullets: list[Bullet],
        bullets_to_remove: set[Bullet],
        effects: list,
    ) -> None:
        """Check player bullets against nearby enemies."""
        for bullet in bullets:
            if not bullet.is_player_bullet or not bullet.active:
                continue

            nearby = self._grid.get_nearby(bullet.x, bullet.y)
            for enemy in nearby:
                if enemy.alive and bullet.rect.colliderect(enemy.rect):
                    points = enemy.take_damage()
                    self._on_enemy_hit(points)
                    bullet.active = False
                    bullets_to_remove.add(bullet)
                    self._on_audio_enemy_hit()
                    effects.append(
                        SparkleBurst((enemy.x, enemy.y), enemy.color, count=10),
                    )
                    break

    def _check_enemy_bullets(
        self,
        bullets: list[Bullet],
        player: Player | None,
        bullets_to_remove: set[Bullet],
        effects: list,
    ) -> None:
        """Check enemy bullets against the player."""
        for bullet in bullets:
            if (
                bullet.is_player_bullet
                or not bullet.active
                or bullet in bullets_to_remove
            ):
                continue

            if (
                player is not None
                and player.alive
                and bullet.rect.colliderect(player.rect)
            ):
                took_damage = player.take_damage()
                bullet.active = False
                bullets_to_remove.add(bullet)
                if took_damage:
                    self._on_audio_player_hit()
                    effects.append(
                        SparkleBurst((player.x, player.y), RED, count=16),
                    )
                    self._on_player_hit()

    def _check_player_enemy_contact(
        self,
        player: Player | None,
        effects: list,
    ) -> None:
        """Check direct player-to-enemy body contact."""
        if player is None or not player.alive:
            return
        nearby = self._grid.get_nearby(player.x, player.y)
        for enemy in nearby:
            if enemy.alive and player.rect.colliderect(enemy.rect):
                took_damage = player.take_damage()
                if took_damage:
                    self._on_audio_player_hit()
                    effects.append(
                        SparkleBurst((player.x, player.y), RED, count=16),
                    )
                    self._on_player_hit()
                break
