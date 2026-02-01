from __future__ import annotations

import math
from typing import TYPE_CHECKING

from games.shared.player_base import PlayerBase

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .bot import Bot
    from .map import Map


class Player(PlayerBase):
    """Player with position, rotation, and shooting capabilities"""

    # Explicitly re-annotate inherited attributes for mypy
    health: int
    alive: bool
    pitch: float

    def __init__(self, x: float, y: float, angle: float):
        """Initialize player"""
        super().__init__(x, y, angle, C.WEAPONS, C)

        self.bob_phase = 0.0

        # Dash Constants
        self.DASH_SPEED_MULT = 2.5
        self.DASH_STAMINA_COST = 20
        self.DASH_DURATION = 10
        self.DASH_COOLDOWN = 60

        # Melee attack system
        self.melee_cooldown = 0
        self.melee_active = False
        self.melee_timer = 0

        # Invincibility system
        self.invincible = True
        self.invincibility_timer = 300
        self.respawn_delay = 0
        self.respawning = False

        # Weapon Sway / Turn tracking
        self.sway_timer = 0

        # Dash mechanics
        self.dash_cooldown = 0
        self.dash_active = False
        self.dash_timer = 0

        # Visual Effects
        self.damage_flash_timer = 0

    def move(
        self,
        game_map: Map,
        bots: list[Bot],
        forward: bool = True,
        speed: float = C.PLAYER_SPEED,
    ) -> None:
        """Move player forward or backward"""
        if self.zoomed:
            return
        if self.shield_active:
            return

        current_speed = speed
        if self.dash_active:
            current_speed *= C.DASH_SPEED_MULT

        dx = math.cos(self.angle) * current_speed * (1 if forward else -1)
        dy = math.sin(self.angle) * current_speed * (1 if forward else -1)

        from games.shared.utils import try_move_entity

        try_move_entity(self, dx, dy, game_map, bots, radius=0.5)

    def strafe(
        self,
        game_map: Map,
        bots: list[Bot],
        right: bool = True,
        speed: float = C.PLAYER_SPEED,
    ) -> None:
        """Strafe left or right"""
        if self.zoomed:
            return
        if self.shield_active:
            return

        current_speed = speed
        if self.dash_active:
            current_speed *= C.DASH_SPEED_MULT

        angle = self.angle + math.pi / 2 * (1 if right else -1)
        dx = math.cos(angle) * current_speed
        dy = math.sin(angle) * current_speed

        from games.shared.utils import try_move_entity

        try_move_entity(self, dx, dy, game_map, bots, radius=0.5)

    def dash(self) -> None:
        """Attempt to perform a dash."""
        if self.dash_cooldown <= 0 and self.stamina >= C.DASH_STAMINA_COST:
            self.stamina -= C.DASH_STAMINA_COST
            self.dash_active = True
            self.dash_timer = C.DASH_DURATION
            self.dash_cooldown = C.DASH_COOLDOWN
            self.stamina_recharge_delay = C.DASH_COOLDOWN

    def melee_attack(self) -> bool:
        """Execute melee attack"""
        if self.melee_cooldown <= 0:
            self.melee_cooldown = 30
            self.melee_active = True
            self.melee_timer = 15
            return True
        return False

    def take_damage(self, damage: int) -> bool:
        """Take damage and return True if player died"""
        if self.invincible or not self.alive or self.god_mode or self.shield_active:
            return False

        self.health -= damage
        self.damage_flash_timer = 15

        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.respawning = True
            self.respawn_delay = 180
            return True
        return False

    def update(self) -> None:
        """Update player state (timers, etc)"""
        self.update_timers()

        # Head Bob & Sway
        if self.is_moving:
            bob_speed = 0.15 if self.dash_active else 0.1
            self.bob_phase += bob_speed
        else:
            # Idle Sway (Breathing)
            self.sway_timer += 1
            sway_pitch = math.sin(self.sway_timer * 0.03) * 2.0
            sway_angle = math.cos(self.sway_timer * 0.015) * 0.001

            self.pitch += sway_pitch * 0.05
            self.angle += sway_angle

            target_phase = round(self.bob_phase / math.pi) * math.pi
            self.bob_phase = self.bob_phase * 0.9 + target_phase * 0.1

        # Constrain pitch
        self.pitch = max(-C.PITCH_LIMIT, min(C.PITCH_LIMIT, self.pitch))

        # Dash logic
        if self.dash_active:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.dash_active = False

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # Melee attack timers
        if self.melee_cooldown > 0:
            self.melee_cooldown -= 1

        if self.melee_timer > 0:
            self.melee_timer -= 1
            if self.melee_timer <= 0:
                self.melee_active = False

        # Invincibility timer
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1
            if self.invincibility_timer <= 0:
                self.invincible = False

        # Respawn delay
        if self.respawn_delay > 0:
            self.respawn_delay -= 1
            if self.respawn_delay <= 0:
                self.respawning = False
                self.alive = True
                self.health = self.max_health
                self.invincible = True
                self.invincibility_timer = 300

        # Visual Effects
        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= 1

        self.update_weapon_state()
