from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .game import Game
    from .player import Player
    from .ui_renderer import UIRenderer


def render_hud(renderer: UIRenderer, game: Game) -> None:
    """Render the full Zombie Survival gameplay HUD."""
    if not (game.player is not None):
        raise ValueError("DbC Blocked: Precondition failed.")
    if not (game.raycaster is not None):
        raise ValueError("DbC Blocked: Precondition failed.")

    renderer.overlay_surface.fill((0, 0, 0, 0))
    render_low_health_tint(renderer, game.player)
    render_damage_flash(renderer, game.damage_flash_timer)
    render_shield_effect(renderer, game.player)
    renderer.screen.blit(renderer.overlay_surface, (0, 0))

    render_crosshair(renderer)
    render_secondary_charge(renderer, game.player)

    render_messages(renderer, game)
    render_health_bar(renderer, game)
    render_ammo_display(renderer, game)
    render_weapon_slots(renderer, game)
    render_level_info(renderer, game)
    render_minimap(renderer, game)
    render_status_bars(renderer, game)
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

    w_state = game.player.weapon_state[game.player.current_weapon]
    w_name = C.WEAPONS[game.player.current_weapon]["name"]

    status_text = ""
    status_color = C.WHITE
    if w_state["reloading"]:
        status_text = "RELOADING..."
        status_color = C.YELLOW
    elif w_state["overheated"]:
        status_text = "OVERHEATED!"
        status_color = C.RED

    if status_text:
        txt = renderer.small_font.render(status_text, True, status_color)
        tr = txt.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 60))
        renderer.screen.blit(txt, tr)

    ammo_val = game.player.ammo[game.player.current_weapon]
    ammo_text = f"{w_name}: {w_state['clip']} / {ammo_val}"
    bomb_text = f"BOMBS: {game.player.bombs}"

    at = renderer.font.render(ammo_text, True, C.WHITE)
    bt = renderer.font.render(bomb_text, True, C.ORANGE)
    at_rect = at.get_rect(bottomright=(C.SCREEN_WIDTH - 20, hud_bottom + 25))
    bt_rect = bt.get_rect(bottomright=(C.SCREEN_WIDTH - 20, hud_bottom - 15))
    renderer.screen.blit(at, at_rect)
    renderer.screen.blit(bt, bt_rect)


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
        inv_txt = renderer.tiny_font.render(text_str, True, color)
        inv_rect = inv_txt.get_rect(bottomright=(C.SCREEN_WIDTH - 20, inv_y))
        renderer.screen.blit(inv_txt, inv_rect)
        inv_y -= 25


def _render_controls_hint(renderer: UIRenderer) -> None:
    """Render the controls hint bar with semi-transparent background."""
    controls_hint = renderer.tiny_font.render(
        "WASD:Move | 1-5:Wpn | R:Reload | F:Bomb | SPACE:Shield | M:Map | ESC:Menu",
        True,
        C.WHITE,
    )
    hint_rect = controls_hint.get_rect(topleft=(10, 10))
    bg = pygame.Surface(
        (hint_rect.width + C.HINT_BG_PADDING_H, hint_rect.height + C.HINT_BG_PADDING_V),
        pygame.SRCALPHA,
    )
    bg.fill(C.HINT_BG_COLOR)
    renderer.screen.blit(
        bg,
        (
            hint_rect.x - C.HINT_BG_PADDING_H // 2,
            hint_rect.y - C.HINT_BG_PADDING_V // 2,
        ),
    )
    renderer.screen.blit(controls_hint, hint_rect)


def render_level_info(renderer: UIRenderer, game: Game) -> None:
    """Render the level number, enemy count, kills, and controls hint."""
    level_text = renderer.small_font.render(f"Level: {game.level}", True, C.YELLOW)
    renderer.screen.blit(
        level_text, level_text.get_rect(topright=(C.SCREEN_WIDTH - 20, 20))
    )
    bots_alive = sum(
        1
        for bot in game.bots
        if bot.alive
        and bot.enemy_type != "health_pack"
        and C.ENEMY_TYPES[bot.enemy_type].get("visual_style") != "item"
    )
    kills_text = renderer.small_font.render(f"Enemies: {bots_alive}", True, C.RED)
    renderer.screen.blit(
        kills_text,
        kills_text.get_rect(topright=(C.SCREEN_WIDTH - 20, 50)),
    )
    score_text = renderer.small_font.render(
        f"Score: {int(game.kills) * 100}", True, C.YELLOW  # type: ignore[has-type]
    )
    renderer.screen.blit(
        score_text, score_text.get_rect(topright=(C.SCREEN_WIDTH - 20, 80))
    )
    _render_controls_hint(renderer)


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
    player: Any,
    bar_x: int,
    bar_y: int,
    bar_w: int,
    bar_h: int,
) -> None:
    """Draw shield percentage bar and recharge status label."""
    shield_pct = player.shield_timer / C.SHIELD_MAX_DURATION
    pygame.draw.rect(renderer.screen, C.DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
    pygame.draw.rect(
        renderer.screen, C.CYAN, (bar_x, bar_y, int(bar_w * shield_pct), bar_h)
    )
    pygame.draw.rect(renderer.screen, C.WHITE, (bar_x, bar_y, bar_w, bar_h), 1)
    if player.shield_recharge_delay > 0:
        label = "RECHARGING" if player.shield_active else "COOLDOWN"
        renderer.screen.blit(
            renderer.tiny_font.render(label, True, C.WHITE),
            (bar_x + bar_w + 5, bar_y - 2),
        )


def render_status_bars(renderer: UIRenderer, game: Game) -> None:
    """Render the shield, laser cooldown, and stamina bars."""
    bar_x, bar_w, bar_h = 20, 150, 10
    shield_y = C.SCREEN_HEIGHT - 80 - 20
    _render_shield_bar(renderer, game.player, bar_x, shield_y, bar_w, bar_h)
    laser_y = shield_y - 15
    laser_pct = max(
        0, min(1, 1.0 - (game.player.secondary_cooldown / C.SECONDARY_COOLDOWN))
    )
    pygame.draw.rect(renderer.screen, C.DARK_GRAY, (bar_x, laser_y, bar_w, bar_h))
    pygame.draw.rect(
        renderer.screen,
        (255, 50, 50),
        (bar_x, laser_y, int(bar_w * laser_pct), bar_h),
    )
    stamina_y = laser_y - 15
    stamina_pct = game.player.stamina / game.player.max_stamina
    pygame.draw.rect(renderer.screen, C.DARK_GRAY, (bar_x, stamina_y, bar_w, bar_h))
    pygame.draw.rect(
        renderer.screen,
        (255, 255, 0),
        (bar_x, stamina_y, int(bar_w * stamina_pct), bar_h),
    )
    if stamina_pct < 1.0:
        renderer.screen.blit(
            renderer.tiny_font.render("STAMINA", True, C.WHITE),
            (bar_x + bar_w + 5, stamina_y - 2),
        )


def render_messages(renderer: UIRenderer, game: Game) -> None:
    """Render floating damage texts and messages."""
    render_damage_texts(renderer, game.damage_texts)


def render_pause_overlay(renderer: UIRenderer, game: Game) -> None:
    """Render the pause menu overlay when the game is paused."""
    if game.paused:
        renderer._render_pause_menu()


def render_damage_texts(renderer: UIRenderer, texts: list[dict[str, Any]]) -> None:
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
    """Render the active shield overlay, label, timer, and low-shield warning."""
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
    cx = C.SCREEN_WIDTH // 2
    st = renderer.title_font.render("SHIELD ACTIVE", True, C.SHIELD_COLOR)
    renderer.screen.blit(st, (cx - st.get_width() // 2, 100))
    tt = renderer.small_font.render(f"{player.shield_timer / 60.0:.1f}s", True, C.WHITE)
    renderer.screen.blit(tt, (cx - tt.get_width() // 2, 160))
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


def render_crosshair(renderer: UIRenderer) -> None:
    """Render the aiming crosshair at the center of the screen."""
    center_x = C.SCREEN_WIDTH // 2
    center_y = C.SCREEN_HEIGHT // 2
    size = 12
    pygame.draw.line(
        renderer.screen,
        C.RED,
        (center_x - size, center_y),
        (center_x + size, center_y),
        2,
    )
    pygame.draw.line(
        renderer.screen,
        C.RED,
        (center_x, center_y - size),
        (center_x, center_y + size),
        2,
    )
    pygame.draw.circle(renderer.screen, C.RED, (center_x, center_y), 2)


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
