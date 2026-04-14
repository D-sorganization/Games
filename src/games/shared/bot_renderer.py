from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pygame

from .renderers import BotStyleRendererFactory

if TYPE_CHECKING:
    from .config import RaycasterConfig
    from .interfaces import Bot, EnemyData

Color3 = tuple[int, int, int]


class BotRenderer:
    """Handles rendering of bot sprites by delegating to style renderers."""

    @staticmethod
    def _get_render_dims(
        bot: Bot,
        screen: pygame.Surface,
        center_x: float,
        sprite_y: int,
        sprite_size: float,
        visual_style: str,
        base_color: Color3,
    ) -> tuple[int, float, float, Color3] | None:
        """Return (render_y, w, h, color) or None to skip the draw."""
        render_h = sprite_size
        render_w = (
            sprite_size * 0.55 if visual_style == "monster" else sprite_size * 0.7
        )
        if not bot.dead:
            return sprite_y, render_w, render_h, base_color
        return BotRenderer._render_death_animation(
            screen, bot, center_x, sprite_y, render_w, render_h, base_color
        )

    @staticmethod
    def render_sprite(
        screen: pygame.Surface,
        bot: Bot,
        sprite_x: int,
        sprite_y: int,
        sprite_size: float,
        config: RaycasterConfig,
    ) -> None:
        """Render sprite based on visual style to the given surface."""
        center_x = sprite_x + sprite_size / 2
        type_data: EnemyData = bot.type_data
        base_color = type_data["color"]
        visual_style = type_data.get("visual_style", "monster")
        if BotRenderer._render_item_sprite(
            screen, bot, center_x, sprite_y, sprite_size, base_color, config
        ):
            return
        result = BotRenderer._get_render_dims(
            bot, screen, center_x, sprite_y, sprite_size, visual_style, base_color
        )
        if result is None:
            return
        render_y, render_width, render_height, base_color = result
        renderer = BotStyleRendererFactory.get_renderer(visual_style)
        if renderer:
            renderer.render(
                screen,
                bot,
                center_x,
                render_y,
                render_width,
                render_height,
                base_color,
                config,
            )

    @staticmethod
    def _invoke_item_renderer(
        style_key: str,
        screen: pygame.Surface,
        bot: Bot,
        center_x: float,
        sprite_y: int,
        sprite_size: float,
        base_color: tuple[int, int, int],
        config: RaycasterConfig,
    ) -> None:
        """Look up and invoke an item-style renderer."""
        renderer = BotStyleRendererFactory.get_renderer(style_key)
        if renderer:
            renderer.render(
                screen,
                bot,
                center_x,
                sprite_y,
                sprite_size,
                sprite_size,
                base_color,
                config,
            )

    @staticmethod
    def _render_item_sprite(
        screen: pygame.Surface,
        bot: Bot,
        center_x: float,
        sprite_y: int,
        sprite_size: float,
        base_color: tuple[int, int, int],
        config: RaycasterConfig,
    ) -> bool:
        """Render item-type sprites; return True if handled."""
        if bot.enemy_type in ("health_pack", "ammo_box", "bomb_item"):
            BotRenderer._invoke_item_renderer(
                bot.enemy_type,
                screen,
                bot,
                center_x,
                sprite_y,
                sprite_size,
                base_color,
                config,
            )
            return True
        if bot.enemy_type.startswith("pickup_"):
            BotRenderer._invoke_item_renderer(
                "weapon_pickup",
                screen,
                bot,
                center_x,
                sprite_y,
                sprite_size,
                base_color,
                config,
            )
            return True
        return False

    @staticmethod
    def _compute_melt_transforms(
        sprite_y: int,
        render_width: float,
        render_height: float,
        base_color: Color3,
        death_timer: int,
    ) -> tuple[int, int, int, Color3]:
        """Return (render_y, w, h, color) after applying the melt animation."""
        melt_pct = min(1.0, death_timer / 60.0)
        goo_color = (50, 150, 50)
        blended = cast(
            Color3,
            tuple(
                int(c * (1 - melt_pct) + g * melt_pct)
                for c, g in zip(base_color, goo_color, strict=False)
            ),
        )
        current_h = render_height * (1.0 - melt_pct * 0.85)
        current_w = render_width * (1.0 + melt_pct * 0.8)
        offset_y = (render_height - current_h) + render_height * 0.05
        return int(sprite_y + offset_y), int(current_w), int(current_h), blended

    @staticmethod
    def _render_death_animation(
        screen: pygame.Surface,
        bot: Bot,
        center_x: float,
        sprite_y: int,
        render_width: float,
        render_height: float,
        base_color: tuple[int, int, int],
    ) -> tuple[int, int, int, tuple[int, int, int]] | None:
        """Calculate death animation transforms; return dims or None if not drawn."""
        render_y, render_width, render_height, base_color = (
            BotRenderer._compute_melt_transforms(
                sprite_y, render_width, render_height, base_color, bot.death_timer
            )
        )
        if bot.disintegrate_timer > 0:
            dis_pct = bot.disintegrate_timer / 100.0
            radius_mult = 1.0 - dis_pct
            if radius_mult <= 0:
                return None
            pygame.draw.ellipse(
                screen,
                base_color,
                (
                    int(center_x - render_width / 2 * radius_mult),
                    int(render_y + render_height - 10),
                    int(render_width * radius_mult),
                    int(20 * radius_mult),
                ),
            )
            return None
        return render_y, render_width, render_height, base_color
