from __future__ import annotations

from .baby_renderer import BabyStyleRenderer
from .ball_renderer import BallStyleRenderer
from .beast_renderer import BeastStyleRenderer
from .cyber_demon_renderer import CyberDemonStyleRenderer
from .factory import BotStyleRendererFactory
from .ghost_renderer import GhostStyleRenderer
from .item_renderer import ItemRenderer
from .minigunner_renderer import MinigunnerStyleRenderer
from .monster_renderer import MonsterStyleRenderer
from .weapon_pickup_renderer import WeaponPickupRenderer

# Register all renderers
BotStyleRendererFactory.register_renderer("monster", MonsterStyleRenderer())
BotStyleRendererFactory.register_renderer("beast", BeastStyleRenderer())
BotStyleRendererFactory.register_renderer("ghost", GhostStyleRenderer())
BotStyleRendererFactory.register_renderer("baby", BabyStyleRenderer())
BotStyleRendererFactory.register_renderer("ball", BallStyleRenderer())
BotStyleRendererFactory.register_renderer("minigunner", MinigunnerStyleRenderer())
BotStyleRendererFactory.register_renderer("cyber_demon", CyberDemonStyleRenderer())
BotStyleRendererFactory.register_renderer("item", ItemRenderer())
BotStyleRendererFactory.register_renderer("health_pack", ItemRenderer())
BotStyleRendererFactory.register_renderer("ammo_box", ItemRenderer())
BotStyleRendererFactory.register_renderer("bomb_item", ItemRenderer())
BotStyleRendererFactory.register_renderer("weapon_pickup", WeaponPickupRenderer())
BotStyleRendererFactory.register_renderer("pickup_rifle", WeaponPickupRenderer())
BotStyleRendererFactory.register_renderer("pickup_shotgun", WeaponPickupRenderer())
BotStyleRendererFactory.register_renderer("pickup_plasma", WeaponPickupRenderer())
BotStyleRendererFactory.register_renderer("pickup_minigun", WeaponPickupRenderer())
BotStyleRendererFactory.register_renderer("pickup_rocket", WeaponPickupRenderer())
