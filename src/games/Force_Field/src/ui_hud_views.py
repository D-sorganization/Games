"""HUD rendering helpers for Force_Field, extracted from UIRenderer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

from . import constants as C  # noqa: N812

if TYPE_CHECKING:
    from .player import Player
    from .ui_renderer import UIRenderer


def render_hud(renderer: UIRenderer, game: Any) -> None:
    """Render the full Force_Field gameplay HUD."""
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
    render_status_bars(renderer, game)
    render_controls_hint(renderer)

    if game.paused:
        render_pause_overlay(renderer, game)


def render_health_bar(renderer: UIRenderer, game: Any) -> None:
    """Render the player health bar at the bottom of the HUD."""
    player = game.player
    bar_height = 12
    bar_width = 150
    start_x = 20
    start_y = C.SCREEN_HEIGHT - 40

    render_bar(
        renderer,
        start_x,
        start_y,
        bar_width,
        bar_height,
        player.health / player.max_health,
        C.RED if player.health <= 50 else C.GREEN,
        "HP",
    )


def _draw_shield_bar(
    renderer: UIRenderer,
    player: Player,
    start_x: int,
    health_y: int,
    bar_width: int,
    bar_height: int,
    bar_spacing: int,
) -> int:
    """Render the shield bar and return its y position."""
    shield_y = health_y - (bar_height + bar_spacing)
    render_bar(
        renderer,
        start_x,
        shield_y,
        bar_width,
        bar_height,
        player.shield_timer / C.SHIELD_MAX_DURATION,
        C.CYAN,
        "SHLD",
    )
    if player.shield_recharge_delay > 0:
        status = "RECHRG" if player.shield_active else "COOL"
        txt = renderer.tiny_font.render(status, True, C.GRAY)
        renderer.screen.blit(txt, (start_x + bar_width + 5, shield_y - 2))
    return shield_y


def _draw_charge_and_stamina_bars(
    renderer: UIRenderer,
    player: Player,
    start_x: int,
    shield_y: int,
    bar_width: int,
    bar_height: int,
    bar_spacing: int,
) -> None:
    """Render secondary charge and stamina bars below the shield bar."""
    charge_y = shield_y - (bar_height + bar_spacing)
    charge_pct = 1.0 - (player.secondary_cooldown / C.SECONDARY_COOLDOWN)
    render_bar(
        renderer,
        start_x,
        charge_y,
        bar_width,
        bar_height,
        max(0, min(1, charge_pct)),
        (255, 100, 100),
        "CHRG",
    )
    stamina_y = charge_y - (bar_height + bar_spacing)
    render_bar(
        renderer,
        start_x,
        stamina_y,
        bar_width,
        bar_height,
        player.stamina / player.max_stamina,
        C.YELLOW,
        "STM",
    )


def render_status_bars(renderer: UIRenderer, game: Any) -> None:
    """Render shield bar, secondary charge bar, and stamina bar."""
    player = game.player
    bar_height = 12
    bar_spacing = 8
    bar_width = 150
    start_x = 20
    start_y = C.SCREEN_HEIGHT - 40

    shield_y = _draw_shield_bar(
        renderer, player, start_x, start_y, bar_width, bar_height, bar_spacing
    )
    _draw_charge_and_stamina_bars(
        renderer, player, start_x, shield_y, bar_width, bar_height, bar_spacing
    )


def render_messages(renderer: UIRenderer, game: Any) -> None:
    """Render floating damage texts and messages."""
    render_damage_texts(renderer, game.damage_texts)


def render_pause_overlay(renderer: UIRenderer, game: Any) -> None:
    """Render the pause menu overlay (delegates to ui_overlay_views)."""
    from . import ui_overlay_views

    ui_overlay_views.render_pause_menu(renderer, game)


def render_controls_hint(renderer: UIRenderer) -> None:
    """Render the controls hint bar at the top of the screen."""
    msg = "WASD:Move|1-7:Wpn|R:Rel|Ctrl+C:Cheat|SPACE:Shield|M:Map|ESC:Menu"
    controls_hint = renderer.tiny_font.render(msg, True, C.WHITE)
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


def render_damage_texts(renderer: UIRenderer, texts: list[dict[str, Any]]) -> None:
    """Render floating damage text indicators with enhanced effects."""
    for t in texts:
        is_large = t.get("size") == "large"
        has_glow = t.get("effect") == "glow"
        font = renderer.subtitle_font if is_large else renderer.small_font
        text_surf = font.render(t["text"], True, t["color"])

        if has_glow:
            glow_surf = font.render(t["text"], True, (255, 255, 255))
            glow_positions = [
                (-2, -2),
                (-2, 2),
                (2, -2),
                (2, 2),
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1),
            ]
            for gx, gy in glow_positions:
                glow_rect = glow_surf.get_rect(
                    center=(int(t["x"]) + gx, int(t["y"]) + gy)
                )
                glow_surf.set_alpha(50)
                renderer.screen.blit(glow_surf, glow_rect)

        rect = text_surf.get_rect(center=(int(t["x"]), int(t["y"])))
        renderer.screen.blit(text_surf, rect)


def render_damage_flash(renderer: UIRenderer, timer: int) -> None:
    """Render red screen flash effect when player takes damage."""
    if timer > 0:
        alpha = int(100 * (timer / 10.0))
        renderer.overlay_surface.fill(
            (255, 0, 0, alpha), special_flags=pygame.BLEND_RGBA_ADD
        )


def _draw_shield_active(renderer: UIRenderer, player: Player) -> None:
    """Render shield overlay, text, and timer when the shield is active."""
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
        shield_text,
        (C.SCREEN_WIDTH // 2 - shield_text.get_width() // 2, 100),
    )
    time_left = player.shield_timer / 60.0
    timer_text = renderer.small_font.render(f"{time_left:.1f}s", True, C.WHITE)
    renderer.screen.blit(
        timer_text,
        (C.SCREEN_WIDTH // 2 - timer_text.get_width() // 2, 160),
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
        _draw_shield_active(renderer, player)
    elif (
        player.shield_timer == C.SHIELD_MAX_DURATION
        and player.shield_recharge_delay <= 0
    ):
        ready_text = renderer.tiny_font.render("SHIELD READY", True, C.CYAN)
        renderer.screen.blit(ready_text, (20, C.SCREEN_HEIGHT - 160))


def render_bar(
    renderer: UIRenderer,
    x: int,
    y: int,
    w: int,
    h: int,
    pct: float,
    color: tuple[int, int, int],
    label: str,
) -> None:
    """Render a labeled HUD bar."""
    pygame.draw.rect(renderer.screen, C.DARK_GRAY, (x, y, w, h))
    fill_w = int(w * max(0.0, min(1.0, pct)))
    if fill_w > 0:
        pygame.draw.rect(renderer.screen, color, (x, y, fill_w, h))
    pygame.draw.rect(renderer.screen, C.WHITE, (x, y, w, h), 1)
    lbl = renderer.tiny_font.render(label, True, C.WHITE)
    renderer.screen.blit(lbl, (x + w + 5, y - 2))


def render_low_health_tint(renderer: UIRenderer, player: Player) -> None:
    """Render red screen tint when health is low."""
    if player.health < 50:
        alpha = int(100 * (1.0 - (player.health / 50.0)))
        renderer.overlay_surface.fill(
            (255, 0, 0, alpha), special_flags=pygame.BLEND_RGBA_ADD
        )


def render_crosshair(renderer: UIRenderer) -> None:
    """Render the aiming crosshair at the center of the screen."""
    cx = C.SCREEN_WIDTH // 2
    cy = C.SCREEN_HEIGHT // 2
    size = 12
    pygame.draw.line(renderer.screen, C.RED, (cx - size, cy), (cx + size, cy), 2)
    pygame.draw.line(renderer.screen, C.RED, (cx, cy - size), (cx, cy + size), 2)
    pygame.draw.circle(renderer.screen, C.RED, (cx, cy), 2)


def render_secondary_charge(renderer: UIRenderer, player: Player) -> None:
    """Render secondary weapon charge bar."""
    charge_pct = 1.0 - (player.secondary_cooldown / C.SECONDARY_COOLDOWN)
    if charge_pct < 1.0:
        bar_w = 40
        bar_h = 4
        cx, cy = C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2 + 30
        pygame.draw.rect(
            renderer.screen, C.DARK_GRAY, (cx - bar_w // 2, cy, bar_w, bar_h)
        )
        pygame.draw.rect(
            renderer.screen,
            C.CYAN,
            (cx - bar_w // 2, cy, int(bar_w * charge_pct), bar_h),
        )
