"""Gameplay-frame update helpers for Duum."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from games.shared.constants import PICKUP_RADIUS_SQ

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .game import Game


def update_damage_texts(game: Game) -> None:
    """Tick floating damage text positions and prune expired messages."""
    for text in game.damage_texts:
        text["y"] += text["vy"]
        text["timer"] -= 1
    game.damage_texts = [text for text in game.damage_texts if text["timer"] > 0]


def handle_keyboard_movement(game: Game, keys) -> None:
    """Apply keyboard-driven movement and view updates."""
    if not (game.player is not None):
        raise ValueError("DbC Blocked: Precondition failed.")
    if not (game.game_map is not None):
        raise ValueError("DbC Blocked: Precondition failed.")

    sprint_key = keys[pygame.K_RSHIFT]
    is_sprinting = game.input_manager.is_action_pressed("sprint") or sprint_key
    if is_sprinting and game.player.stamina > 0:
        current_speed = C.PLAYER_SPRINT_SPEED
        game.player.stamina -= 1
        game.player.stamina_recharge_delay = 60
    else:
        current_speed = C.PLAYER_SPEED

    moving = False
    if game.input_manager.is_action_pressed("move_forward"):
        game.player.move(game.game_map, game.bots, forward=True, speed=current_speed)
        moving = True
    if game.input_manager.is_action_pressed("move_backward"):
        game.player.move(game.game_map, game.bots, forward=False, speed=current_speed)
        moving = True
    if game.input_manager.is_action_pressed("strafe_left"):
        game.player.strafe(game.game_map, game.bots, right=False, speed=current_speed)
        moving = True
    if game.input_manager.is_action_pressed("strafe_right"):
        game.player.strafe(game.game_map, game.bots, right=True, speed=current_speed)
        moving = True

    game.player.is_moving = moving

    if game.input_manager.is_action_pressed("turn_left"):
        game.player.rotate(-0.05)
    if game.input_manager.is_action_pressed("turn_right"):
        game.player.rotate(0.05)
    if game.input_manager.is_action_pressed("look_up"):
        game.player.pitch_view(5)
    if game.input_manager.is_action_pressed("look_down"):
        game.player.pitch_view(-5)


def _resolve_weapon_pickup(game: Game, weapon_name: str) -> tuple[str, tuple[int, int, int]]:
    """Grant a weapon or ammo; return (message, color)."""
    if weapon_name not in game.unlocked_weapons:
        game.unlocked_weapons.add(weapon_name)
        game.player.switch_weapon(weapon_name)
        return f"{weapon_name.upper()} ACQUIRED!", C.CYAN
    if weapon_name in game.player.ammo:
        clip_size = int(C.WEAPONS[weapon_name]["clip_size"])
        game.player.ammo[weapon_name] += clip_size * 2
        return f"{weapon_name.upper()} AMMO", C.YELLOW
    return "", C.WHITE


def _apply_pickup_effect(game: Game, bot: object) -> str:
    """Apply the pickup effect for a bot and return the pickup message (or '')."""
    pickup_msg = ""
    color = C.GREEN
    enemy_type = getattr(bot, "enemy_type", "")
    if enemy_type == "health_pack":
        if game.player.health < 100:
            game.player.health = min(100, game.player.health + 50)
            pickup_msg = "HEALTH +50"
    elif enemy_type == "ammo_box":
        for weapon_name in game.player.ammo:
            game.player.ammo[weapon_name] += 20
        pickup_msg = "AMMO FOUND"
        color = C.YELLOW
    elif enemy_type == "bomb_item":
        game.player.bombs += 1
        pickup_msg = "BOMB +1"
        color = C.ORANGE
    elif enemy_type.startswith("pickup_"):
        weapon_name = enemy_type.replace("pickup_", "")
        pickup_msg, color = _resolve_weapon_pickup(game, weapon_name)

    if pickup_msg:
        bot.alive = False  # type: ignore[attr-defined]
        bot.removed = True  # type: ignore[attr-defined]
        game.damage_texts.append(
            {
                "x": C.SCREEN_WIDTH // 2,
                "y": C.SCREEN_HEIGHT // 2 - 50,
                "text": pickup_msg,
                "color": color,
                "timer": 60,
                "vy": -1,
            }
        )
    return pickup_msg


def check_item_pickups(game: Game) -> None:
    """Apply nearby pickup effects and announce successful pickups."""
    if not (game.player is not None):
        raise ValueError("DbC Blocked: Precondition failed.")

    for bot in game.bots:
        is_item = bot.enemy_type.startswith(("health", "ammo", "bomb", "pickup"))
        if not (bot.alive and is_item):
            continue

        dx = bot.x - game.player.x
        dy = bot.y - game.player.y
        if dx * dx + dy * dy >= PICKUP_RADIUS_SQ:
            continue

        _apply_pickup_effect(game, bot)


def update_game(game: Game) -> None:
    """Advance one active gameplay frame for Duum."""
    if game.paused:
        return
    if not (game.player is not None):
        raise ValueError("DbC Blocked: Precondition failed.")
