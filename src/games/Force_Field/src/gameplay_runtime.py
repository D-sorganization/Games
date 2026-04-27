"""Per-frame gameplay runtime for Force Field."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Protocol

import pygame

from games.shared.constants import (
    BEAST_TIMER_MAX,
    BEAST_TIMER_MIN,
    FOG_REVEAL_RADIUS,
    GROAN_TIMER_DELAY,
    PICKUP_RADIUS_SQ,
    PORTAL_RADIUS_SQ,
    GameState,
)

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .bot import Bot
    from .game import Game
    from .map import Map
    from .player import Player


KILL_COMBO_PHRASES = (
    "DAMN, I'M GOOD!",
    "COME GET SOME!",
    "HAIL TO THE KING!",
    "GROOVY!",
    "PIECE OF CAKE!",
    "WHO WANTS SOME?",
    "EAT THIS!",
    "SHAKE IT BABY!",
    "NOBODY STEALS OUR CHICKS!",
    "IT'S TIME TO KICK ASS!",
    "DAMN, THOSE ALIEN BASTARDS!",
    "YOUR FACE, YOUR ASS!",
    "WHAT'S THE DIFFERENCE?",
    "HOLY COW!",
    "TERMINATED!",
    "WASTED!",
    "OWNED!",
    "DOMINATING!",
    "UNSTOPPABLE!",
    "RAMPAGE!",
    "GODLIKE!",
    "BOOM BABY!",
)
ITEM_PREFIXES = ("health", "ammo", "bomb", "pickup")
PLAYER_HEALTH_PACK_VALUE = 50
AMMO_BOX_AMOUNT = 20
BOMB_ITEM_AMOUNT = 1
SCREEN_SHAKE_DAMPING = 0.9
SCREEN_SHAKE_MINIMUM = 0.5
FOG_RADIUS_SQ = 16
FOG_RADIUS_RANGE = range(-4, 5)


class KeyState(Protocol):
    """Minimal protocol for pygame's pressed-key state container."""

    def __getitem__(self, key: int, /) -> bool: ...


class JoystickLike(Protocol):
    """Minimal protocol for the joystick methods used by the runtime."""

    def get_axis(self, axis: int) -> float: ...

    def get_numaxes(self) -> int: ...

    def get_numbuttons(self) -> int: ...

    def get_button(self, button: int) -> bool: ...

    def get_numhats(self) -> int: ...

    def get_hat(self, hat: int) -> tuple[float, float]: ...


def check_game_over(game: Game) -> bool:
    """Handle death, respawn, and game-over transitions."""
    player = _require_player(game)
    if player.alive:
        return False
    if game.lives > 1:
        game.lives -= 1
        game.respawn_player()
        return True
    level_time = (
        pygame.time.get_ticks() - game.level_start_time - game.total_paused_time
    ) / 1000.0
    game.level_times.append(level_time)
    game.lives = 0
    game.state = GameState.GAME_OVER
    game.game_over_timer = 0
    game.sound_manager.play_sound("game_over1")
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)
    return True


def update_screen_shake(game: Game) -> None:
    """Decay the transient screen shake over time."""
    if game.screen_shake <= 0:
        return
    game.screen_shake *= SCREEN_SHAKE_DAMPING
    if game.screen_shake < SCREEN_SHAKE_MINIMUM:
        game.screen_shake = 0.0


def check_portal_completion(game: Game) -> bool:
    """Spawn the exit portal and detect when the player reaches it."""
    player = _require_player(game)
    if not game.entity_manager.get_active_enemies() and game.portal is None:
        game.spawn_portal()
        game.damage_texts.append(
            {
                "x": C.SCREEN_WIDTH // 2,
                "y": C.SCREEN_HEIGHT // 2,
                "text": "PORTAL OPENED!",
                "color": C.CYAN,
                "timer": 180,
                "vy": 0,
            }
        )
    if game.portal is None:
        return False
    dx = game.portal["x"] - player.x
    dy = game.portal["y"] - player.y
    if dx * dx + dy * dy >= PORTAL_RADIUS_SQ:
        return False
    level_time = (
        pygame.time.get_ticks() - game.level_start_time - game.total_paused_time
    ) / 1000.0
    game.level_times.append(level_time)
    game.state = GameState.LEVEL_COMPLETE
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)
    return True


def handle_combat_input(game: Game) -> None:
    """Drive automatic-fire combat while the shoot input is held."""
    player = _require_player(game)
    is_firing = (
        game.input_manager.is_action_pressed("shoot") or pygame.mouse.get_pressed()[0]
    )
    if not is_firing:
        return
    weapon_data = C.WEAPONS.get(player.current_weapon, {})
    if weapon_data.get("automatic", False) and player.shoot():
        game.combat_system.fire_weapon()


def handle_joystick_input(game: Game, shield_active: bool) -> bool:
    """Apply joystick movement, look, firing, and weapon switching."""
    joystick = _require_joystick(game)
    player = _require_player(game)
    _move_from_joystick(game, player, joystick)
    _look_from_joystick(player, joystick)
    if joystick.get_numbuttons() > 0 and joystick.get_button(0):
        shield_active = True
    if joystick.get_numbuttons() > 2 and joystick.get_button(2):
        player.reload()
    if joystick.get_numbuttons() > 5 and joystick.get_button(5):
        if player.shoot():
            game.combat_system.fire_weapon()
    if joystick.get_numbuttons() > 4 and joystick.get_button(4):
        if player.fire_secondary():
            game.combat_system.fire_weapon(is_secondary=True)
    if joystick.get_numhats() > 0:
        _handle_hat_switching(game, joystick)
    return shield_active


def update_damage_texts(game: Game) -> None:
    """Advance floating combat text and discard expired entries."""
    for text in game.damage_texts:
        text["y"] += text["vy"]
        text["timer"] -= 1
    game.damage_texts = [text for text in game.damage_texts if text["timer"] > 0]


def handle_keyboard_movement(game: Game, keys: KeyState) -> None:
    """Apply keyboard movement and look input for the current frame."""
    player = _require_player(game)
    current_speed = _resolve_player_speed(game, player, keys)
    moving = False
    moving |= _move_if_pressed(game, "move_forward", True, current_speed)
    moving |= _move_if_pressed(game, "move_backward", False, current_speed)
    moving |= _strafe_if_pressed(game, "strafe_left", False, current_speed)
    moving |= _strafe_if_pressed(game, "strafe_right", True, current_speed)
    player.is_moving = moving
    if game.input_manager.is_action_pressed("turn_left"):
        player.rotate(-0.05)
    if game.input_manager.is_action_pressed("turn_right"):
        player.rotate(0.05)
    if game.input_manager.is_action_pressed("look_up"):
        player.pitch_view(5)
    if game.input_manager.is_action_pressed("look_down"):
        player.pitch_view(-5)


def update_fog_of_war(game: Game) -> None:
    """Reveal nearby visited cells around the player."""
    player = _require_player(game)
    player_x, player_y = int(player.x), int(player.y)
    for dy in FOG_RADIUS_RANGE:
        for dx in FOG_RADIUS_RANGE:
            if dx * dx + dy * dy > FOG_RADIUS_SQ:
                continue
            cell_x, cell_y = player_x + dx, player_y + dy
            if _in_map_bounds(game, cell_x, cell_y):
                game.visited_cells.add((cell_x, cell_y))


def check_item_pickups(game: Game) -> None:
    """Resolve pickup collisions and apply their inventory effects."""
    player = _require_player(game)
    for bot in game.bots:
        if not bot.alive or not bot.enemy_type.startswith(ITEM_PREFIXES):
            continue
        dx = bot.x - player.x
        dy = bot.y - player.y
        if dx * dx + dy * dy >= PICKUP_RADIUS_SQ:
            continue
        pickup_message, color = _apply_pickup_effect(game, bot)
        if not pickup_message:
            continue
        bot.alive = False
        bot.removed = True
        game.damage_texts.append(
            {
                "x": C.SCREEN_WIDTH // 2,
                "y": C.SCREEN_HEIGHT // 2 - 50,
                "text": pickup_message,
                "color": color,
                "timer": 60,
                "vy": -1,
            }
        )


def update_large_fog_reveal(game: Game) -> None:
    """Reveal the larger minimap halo around the player."""
    player = _require_player(game)
    center_x, center_y = int(player.x), int(player.y)
    radius = FOG_REVEAL_RADIUS
    for row_offset in range(-radius, radius + 1):
        for col_offset in range(-radius, radius + 1):
            if row_offset * row_offset + col_offset * col_offset <= radius * radius:
                game.visited_cells.add((center_x + col_offset, center_y + row_offset))


def update_atmosphere(game: Game) -> None:
    """Drive ambient audio cues based on enemy proximity and player health."""
    player = _require_player(game)
    min_distance = game.entity_manager.get_nearest_enemy_distance(
        player.x,
        player.y,
    )
    if min_distance < 15:
        game.beast_timer -= 1
        if game.beast_timer <= 0:
            game.sound_manager.play_sound("beast")
            game.beast_timer = random.randint(BEAST_TIMER_MIN, BEAST_TIMER_MAX)
    if min_distance < 20:
        beat_delay = int(min(1.5, max(0.4, min_distance / 10.0)) * C.FPS)  # type: ignore
        game.heartbeat_timer -= 1
        if game.heartbeat_timer <= 0:
            game.sound_manager.play_sound("heartbeat")
            game.sound_manager.play_sound("breath")
            game.heartbeat_timer = beat_delay
    if player.health < 50:
        game.groan_timer -= 1
        if game.groan_timer <= 0:
            game.sound_manager.play_sound("groan")
            game.groan_timer = GROAN_TIMER_DELAY


def check_kill_combo(game: Game) -> None:
    """Expire kill combos and surface their celebratory HUD message."""
    if game.kill_combo_timer <= 0:
        return
    game.kill_combo_timer -= 1
    if game.kill_combo_timer > 0:
        return
    if game.kill_combo_count >= 3:
        game.sound_manager.play_sound("phrase_cool")
        game.damage_texts.append(
            {
                "x": C.SCREEN_WIDTH // 2,
                "y": C.SCREEN_HEIGHT // 2 - 150,
                "text": random.choice(KILL_COMBO_PHRASES),
                "color": C.YELLOW,
                "timer": 180,
                "vy": -0.2,
                "size": "large",
                "effect": "glow",
            }
        )
    game.kill_combo_count = 0


def update_game(game: Game) -> None:
    """Run one gameplay tick when the game is in the active state."""
    if game.paused:
        return
    player = _require_player(game)
    game_map = _require_map(game)
    if check_game_over(game):
        return
    update_screen_shake(game)
    if check_portal_completion(game):
        return
    keys = pygame.key.get_pressed()
    shield_active = game.input_manager.is_action_pressed("shield")
    if player.alive:
        handle_combat_input(game)
    if game.joystick and player.alive:
        shield_active = handle_joystick_input(game, shield_active)
    player.set_shield(shield_active)
    game.particle_system.update()
    update_damage_texts(game)
    handle_keyboard_movement(game, keys)
    player.update()
    update_fog_of_war(game)
    game.entity_manager.update_bots(game_map, player, game)
    check_item_pickups(game)
    game.entity_manager.update_projectiles(game_map, player, game)
    update_large_fog_reveal(game)
    update_atmosphere(game)
    check_kill_combo(game)


def _move_from_joystick(
    game: Game,
    player: Player,
    joystick: JoystickLike,
) -> None:
    """Translate left-stick input into movement and strafing."""
    game_map = _require_map(game)
    axis_x = joystick.get_axis(0)
    axis_y = joystick.get_axis(1)
    if abs(axis_x) > C.JOYSTICK_DEADZONE:
        player.strafe(
            game_map,
            game.bots,
            right=(axis_x > 0),
            speed=abs(axis_x) * C.PLAYER_SPEED * game.movement_speed_multiplier,
        )
        player.is_moving = True
    if abs(axis_y) > C.JOYSTICK_DEADZONE:
        player.move(
            game_map,
            game.bots,
            forward=(axis_y < 0),
            speed=abs(axis_y) * C.PLAYER_SPEED * game.movement_speed_multiplier,
        )
        player.is_moving = True


def _look_from_joystick(player: Player, joystick: JoystickLike) -> None:
    """Apply right-stick look input when the controller exposes it."""
    look_x = 0.0
    look_y = 0.0
    if joystick.get_numaxes() >= 4:
        look_x = joystick.get_axis(2)
        look_y = joystick.get_axis(3)
    if abs(look_x) > C.JOYSTICK_DEADZONE:
        player.rotate(look_x * C.PLAYER_ROT_SPEED * 15 * C.SENSITIVITY_X)  # type: ignore
    if abs(look_y) > C.JOYSTICK_DEADZONE:
        player.pitch_view(-look_y * 10 * C.SENSITIVITY_Y)


def _handle_hat_switching(game: Game, joystick: JoystickLike) -> None:
    """Map D-pad hat input to the quick weapon shortcuts."""
    hat = joystick.get_hat(0)
    if hat[0] == -1:
        game.switch_weapon_with_message("pistol")
    if hat[0] == 1:
        game.switch_weapon_with_message("rifle")
    if hat[1] == 1:
        game.switch_weapon_with_message("shotgun")
    if hat[1] == -1:
        game.switch_weapon_with_message("plasma")


def _resolve_player_speed(game: Game, player: Player, keys: KeyState) -> float:
    """Return the player's current movement speed based on sprint state."""
    sprint_key = keys[pygame.K_RSHIFT]
    is_sprinting = game.input_manager.is_action_pressed("sprint") or sprint_key
    if is_sprinting and player.stamina > 0:
        player.stamina -= 1
        player.stamina_recharge_delay = 60
        return C.PLAYER_SPRINT_SPEED * game.movement_speed_multiplier
    return C.PLAYER_SPEED * game.movement_speed_multiplier


def _move_if_pressed(
    game: Game,
    action: str,
    forward: bool,
    speed: float,
) -> bool:
    """Move the player forward/backward when the bound action is active."""
    if not game.input_manager.is_action_pressed(action):
        return False
    player = _require_player(game)
    game_map = _require_map(game)
    player.move(game_map, game.bots, forward=forward, speed=speed)
    return True


def _strafe_if_pressed(
    game: Game,
    action: str,
    right: bool,
    speed: float,
) -> bool:
    """Strafe the player when the bound action is active."""
    if not game.input_manager.is_action_pressed(action):
        return False
    player = _require_player(game)
    game_map = _require_map(game)
    player.strafe(game_map, game.bots, right=right, speed=speed)
    return True


def _in_map_bounds(game: Game, cell_x: int, cell_y: int) -> bool:
    """Return whether a grid coordinate falls inside the current map."""
    return bool(
        game.game_map
        and 0 <= cell_x < game.game_map.width
        and 0 <= cell_y < game.game_map.height
    )


def _apply_pickup_effect(game: Game, bot: Bot) -> tuple[str, tuple[int, int, int]]:
    """Apply a pickup to the player and return its HUD message."""
    player = _require_player(game)
    if bot.enemy_type == "health_pack":
        if player.health >= C.PLAYER_HEALTH:
            return "", C.GREEN
        player.health = min(
            C.PLAYER_HEALTH,
            player.health + PLAYER_HEALTH_PACK_VALUE,
        )
        return "HEALTH +50", C.GREEN
    if bot.enemy_type == "ammo_box":
        for weapon_name in player.ammo:
            player.ammo[weapon_name] += AMMO_BOX_AMOUNT
        return "AMMO FOUND", C.YELLOW
    if bot.enemy_type == "bomb_item":
        player.bombs += BOMB_ITEM_AMOUNT
        return "BOMB +1", C.ORANGE
    return _apply_weapon_pickup(game, bot.enemy_type.replace("pickup_", ""))


def _apply_weapon_pickup(
    game: Game,
    weapon_name: str,
) -> tuple[str, tuple[int, int, int]]:
    """Unlock a weapon or top up its ammo if already unlocked."""
    player = _require_player(game)
    if weapon_name not in game.unlocked_weapons:
        game.unlocked_weapons.add(weapon_name)
        player.switch_weapon(weapon_name)
        return f"{weapon_name.upper()} ACQUIRED!", C.CYAN
    if weapon_name not in player.ammo:
        return "", C.YELLOW
    clip_size = int(C.WEAPONS[weapon_name]["clip_size"])
    player.ammo[weapon_name] += clip_size * 2
    return f"{weapon_name.upper()} AMMO", C.YELLOW


def _require_player(game: Game) -> Player:
    """Return the current player or raise when gameplay state is incomplete."""
    if game.player is None:
        raise ValueError("DbC Blocked: Precondition failed.")
    return game.player


def _require_map(game: Game) -> Map:
    """Return the current map or raise when gameplay state is incomplete."""
    if game.game_map is None:
        raise ValueError("DbC Blocked: Precondition failed.")
    return game.game_map


def _require_joystick(game: Game) -> JoystickLike:
    """Return the active joystick or raise when controller input is unavailable."""
    if game.joystick is None:
        raise ValueError("DbC Blocked: Precondition failed.")
    return game.joystick
