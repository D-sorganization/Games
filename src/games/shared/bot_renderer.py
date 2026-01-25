from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from .renderers import BotStyleRendererFactory

if TYPE_CHECKING:
    from .config import RaycasterConfig
    from .interfaces import Bot, EnemyData


class BotRenderer:
    """Handles rendering of bot sprites by delegating to style renderers."""

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

        # Special handling for item types
        if bot.enemy_type in ("health_pack", "ammo_box", "bomb_item"):
            renderer = BotStyleRendererFactory.get_renderer(bot.enemy_type)
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
            return

        if bot.enemy_type.startswith("pickup_"):
            renderer = BotStyleRendererFactory.get_renderer("weapon_pickup")
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
            return

        render_height = sprite_size
        render_width = (
            sprite_size * 0.55 if visual_style == "monster" else sprite_size * 0.7
        )
        render_y = sprite_y

        if bot.dead:
            # Melting animation
            melt_pct = min(1.0, bot.death_timer / 60.0)
            goo_color = (50, 150, 50)
            base_color = tuple(
                int(c * (1 - melt_pct) + g * melt_pct)
                for c, g in zip(base_color, goo_color, strict=False)
            )  # type: ignore

            scale_y = 1.0 - (melt_pct * 0.85)
            scale_x = 1.0 + (melt_pct * 0.8)

            current_h = render_height * scale_y
            current_w = render_width * scale_x

            offset_y = (render_height - current_h) + (render_height * 0.05)
            render_y = int(sprite_y + offset_y)
            render_height = int(current_h)
            render_width = int(current_w)

            if bot.disintegrate_timer > 0:
                dis_pct = bot.disintegrate_timer / 100.0
                radius_mult = 1.0 - dis_pct
                if radius_mult <= 0:
                    return
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
                return

        # Delegate to specialized renderer
        BotStyleRendererFactory.render(
            screen,
            bot,
            center_x,
            render_y,
            render_width,
            render_height,
            base_color,
            config,
        )
