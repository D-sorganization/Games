from __future__ import annotations

from typing import ClassVar

import pygame

from games.shared.input_manager_base import InputManagerBase


class InputManager(InputManagerBase):
    """Manages input bindings and state for Duum."""

    DEFAULT_BINDINGS: ClassVar[dict[str, int]] = {
        "move_forward": pygame.K_w,
        "move_backward": pygame.K_s,
        "strafe_left": pygame.K_a,
        "strafe_right": pygame.K_d,
        "turn_left": pygame.K_LEFT,
        "turn_right": pygame.K_RIGHT,
        "look_up": pygame.K_UP,
        "look_down": pygame.K_DOWN,
        "shoot": pygame.K_SPACE,  # Primary shoot (also Mouse 1)
        "reload": pygame.K_r,
        "zoom": pygame.K_z,
        "bomb": pygame.K_f,
        "shield": pygame.K_x,  # Changed from LSHIFT to avoid sprint conflict
        "sprint": pygame.K_LSHIFT,
        "shoot_alt": pygame.K_KP0,
        "pause": pygame.K_ESCAPE,
        "interact": pygame.K_e,
        "weapon_1": pygame.K_1,
        "weapon_2": pygame.K_2,
        "weapon_3": pygame.K_3,
        "weapon_4": pygame.K_4,
        "weapon_5": pygame.K_5,
        "weapon_6": pygame.K_6,
    }
