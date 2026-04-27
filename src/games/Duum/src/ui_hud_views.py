from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from . import constants as C  # noqa: N812
from .custom_types import DamageText

if TYPE_CHECKING:
    from .game import Game
    from .player import Player
    from .ui_renderer import UIRenderer


def render_hud(renderer: UIRenderer, game: Game) -> None:
    """Render the full Duum gameplay HUD."""
    if not (game.player is not None):
        raise ValueError("DbC Blocked: Precondition failed.")
    if not (game.raycaster is not None):
        raise ValueError("DbC Blocked: Precondition failed.")

    renderer.overlay_surface.fill((0, 0, 0, 0))
    render_low_health_tint(renderer, game.player)
    render_damage_flash(renderer, game.damage_flash_timer)
    render_shield_effect(renderer, game.player)
    renderer.screen.blit(renderer.overlay_surface, (0, 0))

    renderer.screen.blit(renderer.vignette, (0, 0))

    render_crosshair(renderer)
    render_secondary_charge(renderer, game.player)

    render_messages(renderer, game)
    render_health_bar(renderer, game)
    render_ammo_display(renderer, game)
    render_weapon_slots(renderer, game)
    render_level_info(renderer, game)
    render_minimap(renderer, game)
    render_status_bars(renderer, game)
    render_controls_hint(renderer)
    render_pause_overlay(renderer, game)


def render_health_bar(renderer: UIRenderer, game: Game) -> None:
    """Render the player health bar."""
    hud_bottom = C.SCREEN_HEIGHT - 80
    health_width = 150
    health_height = 25
    health_x = 20
    health_y = hud_bottom

    pygame.draw.rect(
        renderer.screen,
        C.DARK_GRAY,
        (health_x, health_y, health_width, health_height),
    )
    health_percent = max(0, game.player.health / game.player.max_health)
    fill_width = int(health_width * health_percent)
    health_color = C.RED
    if health_percent > 0.5:
        health_color = C.GREEN
    elif health_percent > 0.25:
        health_color = C.ORANGE
    health_rect = (health_x, health_y, fill_width, health_height)
    pygame.draw.rect(renderer.screen, health_color, health_rect)
    pygame.draw.rect(
        renderer.screen,
        C.WHITE,
        (health_x, health_y, health_width, health_height),
        2,
    )


def render_ammo_display(renderer: UIRenderer, game: Game) -> None:
    """Render the ammo counter and weapon name."""
    hud_bottom = C.SCREEN_HEIGHT - 80

    weapon_state = game.player.weapon_state[game.player.current_weapon]
    weapon_name = C.WEAPONS[game.player.current_weapon]["name"]

    status_text = ""
    status_color = C.WHITE
    if weapon_state["reloading"]:
        status_text = "RELOADING..."
        status_color = C.YELLOW
    elif weapon_state["overheated"]:
        status_text = "OVERHEATED!"
        status_color = C.RED

    if status_text:
        text = renderer.small_font.render(status_text, True, status_color)
        text_rect = text.get_rect(
            center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 60)
        )
        renderer.screen.blit(text, text_rect)

    ammo_val = game.player.ammo[game.player.current_weapon]
    ammo_text = f"{weapon_name}: {weapon_state['clip']} / {ammo_val}"
    bomb_text = f"BOMBS: {game.player.bombs}"

    ammo_surface = renderer.font.render(ammo_text, True, C.WHITE)
    bomb_surface = renderer.font.render(bomb_text, True, C.ORANGE)
    ammo_rect = ammo_surface.get_rect(
        bottomright=(C.SCREEN_WIDTH - 20, hud_bottom + 25)
    )
    bomb_rect = bomb_surface.get_rect(
        bottomright=(C.SCREEN_WIDTH - 20, hud_bottom - 15)
    )
    renderer.screen.blit(ammo_surface, ammo_rect)
    renderer.screen.blit(bomb_surface, bomb_rect)


def render_weapon_slots(renderer: UIRenderer, game: Game) -> None:
    """Render the weapon inventory slots."""
    hud_bottom = C.SCREEN_HEIGHT - 80
    inv_y = hud_bottom - 80

    for weapon_name in (
        "pistol",
        "rifle",
        "shotgun",
        "laser",
        "plasma",
        "rocket",
        "minigun",
    ):
        color = C.GRAY
        if weapon_name in game.unlocked_weapons:
            color = C.GREEN if weapon_name == game.player.current_weapon else C.WHITE

        key_display = C.WEAPONS[weapon_name]["key"]
        text_str = f"[{key_display}] {C.WEAPONS[weapon_name]['name']}"
        inv_text = renderer.tiny_font.render(text_str, True, color)
        inv_rect = inv_text.get_rect(bottomright=(C.SCREEN_WIDTH - 20, inv_y))
        renderer.screen.blit(inv_text, inv_rect)
        inv_y -= 25


def render_level_info(renderer: UIRenderer, game: Game) -> None:
    """Render level number, enemy count, and score."""
    level_text = renderer.small_font.render(f"Level: {game.level}", True, C.YELLOW)
    level_rect = level_text.get_rect(topright=(C.SCREEN_WIDTH - 20, 20))
    renderer.screen.blit(level_text, level_rect)

    bots_alive = sum(
        1
        for bot in game.bots
        if bot.alive
        and bot.enemy_type != "health_pack"
        and C.ENEMY_TYPES[bot.enemy_type].get("visual_style") != "item"
    )
    kills_text = renderer.small_font.render(f"Enemies: {bots_alive}", True, C.RED)
    kills_rect = kills_text.get_rect(topright=(C.SCREEN_WIDTH - 20, 50))
    renderer.screen.blit(kills_text, kills_rect)

    score = game.kills * 100
    score_text = renderer.small_font.render(f"Score: {score}", True, C.YELLOW)
    score_rect = score_text.get_rect(topright=(C.SCREEN_WIDTH - 20, 80))
    renderer.screen.blit(score_text, score_rect)


def render_minimap(renderer: UIRenderer, game: Game) -> None:
    """Render the minimap when enabled."""
    if game.show_minimap:
        game.raycaster.render_minimap(
            renderer.screen,
            game.player,
            game.bots,
            game.visited_cells,
            game.portal,
        )


def _render_shield_bar(
    renderer: UIRenderer,
    game: Game,
    shield_x: int,
    shield_y: int,
    shield_width: int,
    shield_height: int,
) -> None:
    """Render the shield percentage bar with recharge/cooldown label."""
    shield_pct = game.player.shield_timer / C.SHIELD_MAX_DURATION
    pygame.draw.rect(
        renderer.screen, C.DARK_GRAY, (shield_x, shield_y, shield_width, shield_height)
    )
    pygame.draw.rect(
        renderer.screen,
        C.CYAN,
        (shield_x, shield_y, int(shield_width * shield_pct), shield_height),
    )
    pygame.draw.rect(
        renderer.screen, C.WHITE, (shield_x, shield_y, shield_width, shield_height), 1
    )
    if game.player.shield_recharge_delay > 0:
        status_text = "RECHARGING" if game.player.shield_active else "COOLDOWN"
        status_surf = renderer.tiny_font.render(status_text, True, C.WHITE)
        renderer.screen.blit(status_surf, (shield_x + shield_width + 5, shield_y - 2))


def render_status_bars(renderer: UIRenderer, game: Game) -> None:
    """Render shield, laser cooldown, and stamina bars."""
    hud_bottom = C.SCREEN_HEIGHT - 80
    shield_x = 20
    shield_y = hud_bottom - 20
    shield_width = 150
    shield_height = 10

    _render_shield_bar(renderer, game, shield_x, shield_y, shield_width, shield_height)

    laser_y = shield_y - 15
    laser_pct = max(
        0, min(1, 1.0 - (game.player.secondary_cooldown / C.SECONDARY_COOLDOWN))
    )
    pygame.draw.rect(
        renderer.screen, C.DARK_GRAY, (shield_x, laser_y, shield_width, shield_height)
    )
    pygame.draw.rect(
        renderer.screen,
        (255, 50, 50),
        (shield_x, laser_y, int(shield_width * laser_pct), shield_height),
    )

    stamina_y = laser_y - 15
    stamina_pct = game.player.stamina / game.player.max_stamina
    pygame.draw.rect(
        renderer.screen, C.DARK_GRAY, (shield_x, stamina_y, shield_width, shield_height)
    )
    pygame.draw.rect(
        renderer.screen,
        (255, 255, 0),
        (shield_x, stamina_y, int(shield_width * stamina_pct), shield_height),
    )
    if stamina_pct < 1.0:
        stamina_text = renderer.tiny_font.render("STAMINA", True, C.WHITE)
        renderer.screen.blit(stamina_text, (shield_x + shield_width + 5, stamina_y - 2))


def render_messages(renderer: UIRenderer, game: Game) -> None:
    """Render floating damage texts and messages."""
    render_damage_texts(renderer, game.damage_texts)


def render_controls_hint(renderer: UIRenderer) -> None:
    """Render the controls hint text at the top of the screen."""
    controls_hint = renderer.tiny_font.render(
        "WASD:Move | 1-5:Wpn | R:Reload | F:Bomb | SPACE:Shield | M:Map | ESC:Menu",
        True,
        C.WHITE,
    )
    controls_hint_rect = controls_hint.get_rect(topleft=(10, 10))
    bg_surface = pygame.Surface(
        (
            controls_hint_rect.width + C.HINT_BG_PADDING_H,
            controls_hint_rect.height + C.HINT_BG_PADDING_V,
        ),
        pygame.SRCALPHA,
    )
    bg_surface.fill(C.HINT_BG_COLOR)
    renderer.screen.blit(
        bg_surface,
        (
            controls_hint_rect.x - C.HINT_BG_PADDING_H // 2,
            controls_hint_rect.y - C.HINT_BG_PADDING_V // 2,
        ),
    )
    renderer.screen.blit(controls_hint, controls_hint_rect)


def render_pause_overlay(renderer: UIRenderer, game: Game) -> None:
    """Render the pause menu overlay when the game is paused."""
    if game.paused:
        renderer._render_pause_menu()


def render_damage_texts(renderer: UIRenderer, texts: list[DamageText]) -> None:
    """Render floating damage text indicators."""
    for text in texts:
        surf = renderer.small_font.render(text["text"], True, text["color"])
        rect = surf.get_rect(center=(int(text["x"]), int(text["y"])))
        renderer.screen.blit(surf, rect)


def render_damage_flash(renderer: UIRenderer, timer: int) -> None:
    """Render red screen flash effect when player takes damage."""
    if timer > 0:
        alpha = int(100 * (timer / 10.0))
        renderer.overlay_surface.fill(
            (255, 0, 0, alpha),
            special_flags=pygame.BLEND_RGBA_ADD,
        )


def _render_active_shield(renderer: UIRenderer, player: Player) -> None:
    """Render overlay, label, timer, and low-time warning for active shield."""
    pygame.draw.rect(
        renderer.overlay_surface,
        (*C.SHIELD_COLOR, C.SHIELD_ALPHA),
        (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT),
    )
    pygame.draw.rect(
        renderer.overlay_surface,
        C.SHIELD_COLOR,
        (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT),
        10,
    )
    shield_text = renderer.title_font.render("SHIELD ACTIVE", True, C.SHIELD_COLOR)
    renderer.screen.blit(
        shield_text, (C.SCREEN_WIDTH // 2 - shield_text.get_width() // 2, 100)
    )
    time_left = player.shield_timer / 60.0
    timer_text = renderer.small_font.render(f"{time_left:.1f}s", True, C.WHITE)
    renderer.screen.blit(
        timer_text, (C.SCREEN_WIDTH // 2 - timer_text.get_width() // 2, 160)
    )
    if player.shield_timer < 120 and (player.shield_timer // 10) % 2 == 0:
        pygame.draw.rect(
            renderer.overlay_surface,
            (255, 0, 0, 50),
            (0, 0, C.SCREEN_WIDTH, C.SCREEN_HEIGHT),
        )


def render_shield_effect(renderer: UIRenderer, player: Player) -> None:
    """Render shield activation visual effects and status."""
    if player.shield_active:
        _render_active_shield(renderer, player)
    elif (
        player.shield_timer == C.SHIELD_MAX_DURATION
        and player.shield_recharge_delay <= 0
    ):
        ready_text = renderer.tiny_font.render("SHIELD READY", True, C.CYAN)
        renderer.screen.blit(ready_text, (20, C.SCREEN_HEIGHT - 120))


def render_low_health_tint(renderer: UIRenderer, player: Player) -> None:
    """Render red screen tint when health is low."""
    if player.health < 50:
        alpha = int(100 * (1.0 - (player.health / 50.0)))
        renderer.overlay_surface.fill(
            (255, 0, 0, alpha),
            special_flags=pygame.BLEND_RGBA_ADD,
        )


def _draw_crosshair_arms(
    screen: pygame.Surface,
    cx: int,
    cy: int,
    gap: int,
    length: int,
    color: tuple[int, int, int],
    width: int,
) -> None:
    """Draw the four arm lines of the crosshair at the given colour and width."""
    pygame.draw.line(screen, color, (cx - length, cy), (cx - gap, cy), width)
    pygame.draw.line(screen, color, (cx + gap, cy), (cx + length, cy), width)
    pygame.draw.line(screen, color, (cx, cy - length), (cx, cy - gap), width)
    pygame.draw.line(screen, color, (cx, cy + gap), (cx, cy + length), width)


def render_crosshair(renderer: UIRenderer) -> None:
    """Render the enhanced aiming crosshair at the center of the screen."""
    center_x = C.SCREEN_WIDTH // 2
    center_y = C.SCREEN_HEIGHT // 2
    gap = 5
    length = 10
    _draw_crosshair_arms(
        renderer.screen, center_x, center_y, gap - 2, length + 2, (0, 0, 0), 4
    )
    _draw_crosshair_arms(
        renderer.screen, center_x, center_y, gap, length, (255, 255, 255), 2
    )
    pygame.draw.circle(renderer.screen, (0, 0, 0), (center_x, center_y), 3)
    pygame.draw.circle(renderer.screen, (255, 255, 255), (center_x, center_y), 1)


def render_secondary_charge(renderer: UIRenderer, player: Player) -> None:
    """Render the secondary weapon charge bar."""
    charge_pct = 1.0 - (player.secondary_cooldown / C.SECONDARY_COOLDOWN)
    if charge_pct < 1.0:
        bar_width = 40
        bar_height = 4
        center_x = C.SCREEN_WIDTH // 2
        center_y = C.SCREEN_HEIGHT // 2 + 30
        pygame.draw.rect(
            renderer.screen,
            C.DARK_GRAY,
            (center_x - bar_width // 2, center_y, bar_width, bar_height),
        )
        pygame.draw.rect(
            renderer.screen,
            C.CYAN,
            (
                center_x - bar_width // 2,
                center_y,
                int(bar_width * charge_pct),
                bar_height,
            ),
        )
