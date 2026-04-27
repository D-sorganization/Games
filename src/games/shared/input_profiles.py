"""Shared input binding profiles for FPS variants."""

from __future__ import annotations

import pygame

FPS_INPUT_PROFILES: dict[str, dict[str, int]] = {
    "duum": {
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
        "shoot_alt": pygame.K_0,
        "pause": pygame.K_ESCAPE,
        "interact": pygame.K_e,
        "weapon_1": pygame.K_1,
        "weapon_2": pygame.K_2,
        "weapon_3": pygame.K_3,
        "weapon_4": pygame.K_4,
        "weapon_5": pygame.K_5,
        "weapon_6": pygame.K_6,
    },
    "force_field": {
        "move_forward": pygame.K_w,
        "move_backward": pygame.K_s,
        "strafe_left": pygame.K_a,
        "strafe_right": pygame.K_d,
        "turn_left": pygame.K_LEFT,
        "turn_right": pygame.K_RIGHT,
        "look_up": pygame.K_UP,
        "look_down": pygame.K_DOWN,
        "shoot": pygame.K_LCTRL,  # Primary shoot (also Mouse 1)
        "reload": pygame.K_r,
        "zoom": pygame.K_z,
        "bomb": pygame.K_f,
        "shield": pygame.K_SPACE,  # Force Field Shield as documented
        "dash": pygame.K_LSHIFT,
        "sprint": pygame.K_TAB,
        "shoot_alt": pygame.K_0,
        "pause": pygame.K_ESCAPE,
        "interact": pygame.K_e,
        "weapon_1": pygame.K_1,
        "weapon_2": pygame.K_2,
        "weapon_3": pygame.K_3,
        "weapon_4": pygame.K_4,
        "weapon_5": pygame.K_5,
        "weapon_6": pygame.K_6,
        "weapon_minigun": pygame.K_7,  # Direct minigun access
    },
    "zombie_survival": {
        "move_forward": pygame.K_w,
        "move_backward": pygame.K_s,
        "strafe_left": pygame.K_a,
        "strafe_right": pygame.K_d,
        "turn_left": pygame.K_LEFT,
        "turn_right": pygame.K_RIGHT,
        "look_up": pygame.K_UP,
        "look_down": pygame.K_DOWN,
        "shoot": pygame.K_LCTRL,  # Primary shoot (also Mouse 1)
        "reload": pygame.K_r,
        "zoom": pygame.K_z,
        "bomb": pygame.K_f,
        "shield": pygame.K_SPACE,  # Force Field Shield as documented
        "sprint": pygame.K_LSHIFT,
        "shoot_alt": pygame.K_0,
        "pause": pygame.K_ESCAPE,
        "interact": pygame.K_e,
        "weapon_1": pygame.K_1,
        "weapon_2": pygame.K_2,
        "weapon_3": pygame.K_3,
        "weapon_4": pygame.K_4,
        "weapon_5": pygame.K_5,
        "weapon_6": pygame.K_6,
        "weapon_minigun": pygame.K_7,  # Direct minigun access
    },
}
