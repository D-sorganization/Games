from __future__ import annotations

import random
import pygame
from typing import TYPE_CHECKING
from .base import BaseBotStyleRenderer

if TYPE_CHECKING:
    from ..config import RaycasterConfig
    from ..interfaces import Bot


class CyberDemonStyleRenderer(BaseBotStyleRenderer):
    """Cyber Demon visual style renderer."""

    def render(
        self,
        screen: pygame.Surface,
        bot: Bot,
        cx: float,
        ry: float,
        rw: float,
        rh: float,
        color: tuple[int, int, int],
        config: RaycasterConfig,
    ) -> None:
        """Render the Cyber Demon visual style."""
        # Massive Mechanical Demon
        # Color is usually dark metallic (50, 50, 50)
        
        # 1. Legs (Hydraulics)
        leg_w = rw * 0.25
        leg_h = rh * 0.3
        leg_y = ry + rh * 0.7
        
        # Left Leg
        pygame.draw.rect(screen, (30, 30, 35), (int(cx - rw * 0.3), int(leg_y), int(leg_w), int(leg_h)))
        # Right Leg
        pygame.draw.rect(screen, (30, 30, 35), (int(cx + rw * 0.3 - leg_w), int(leg_y), int(leg_w), int(leg_h)))
        # Wires
        pygame.draw.line(screen, (200, 200, 0), (int(cx - rw * 0.2), int(leg_y)), (int(cx - rw * 0.2), int(leg_y + leg_h)), 2)
        pygame.draw.line(screen, (200, 200, 0), (int(cx + rw * 0.2), int(leg_y)), (int(cx + rw * 0.2), int(leg_y + leg_h)), 2)

        # 2. Torso (Armored Block)
        torso_w = rw * 0.8
        torso_h = rh * 0.5
        torso_y = ry + rh * 0.2
        torso_rect = pygame.Rect(int(cx - torso_w / 2), int(torso_y), int(torso_w), int(torso_h))
        pygame.draw.rect(screen, color, torso_rect)
        
        # Details (Rivets/Plates)
        pygame.draw.rect(screen, (70, 70, 70), torso_rect, 4)
        pygame.draw.line(screen, (30, 30, 30), (int(cx), int(torso_y)), (int(cx), int(torso_y + torso_h)), 3)

        # 3. Head (Horns + Visor)
        head_size = rw * 0.3
        head_y = ry
        head_rect = pygame.Rect(int(cx - head_size / 2), int(head_y), int(head_size), int(head_size))
        pygame.draw.rect(screen, (60, 60, 60), head_rect)
        
        # Horns (Technological)
        pygame.draw.line(screen, (150, 150, 150), (int(cx - head_size/2), int(head_y)), (int(cx - head_size), int(head_y - 20)), 5)
        pygame.draw.line(screen, (150, 150, 150), (int(cx + head_size/2), int(head_y)), (int(cx + head_size), int(head_y - 20)), 5)

        # Eyes/Visor (Glowing Red)
        pygame.draw.rect(screen, (255, 0, 0), (int(cx - head_size * 0.4), int(head_y + head_size * 0.4), int(head_size * 0.8), int(head_size * 0.2)))

        # 4. Weapon (Rocket Launcher Arm)
        # Left Arm (Humanoid)
        pygame.draw.rect(screen, color, (int(cx - rw/2 - 10), int(torso_y + 10), 20, int(rh * 0.4)))
        
        # Right Arm (Cannon)
        cannon_w = rw * 0.3
        cannon_h = rh * 0.4
        cannon_x = cx + rw/2 - 10
        cannon_y = torso_y + 10
        pygame.draw.rect(screen, (20, 20, 20), (int(cannon_x), int(cannon_y), int(cannon_w), int(cannon_h)))
        
        # Muzzle glow
        if getattr(bot, "shoot_animation", 0) > 0.5:
            pygame.draw.circle(screen, (255, 100, 0), (int(cannon_x + cannon_w/2), int(cannon_y + cannon_h)), 10)
