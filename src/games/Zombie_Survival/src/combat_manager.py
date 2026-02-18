"""Zombie Survival-specific combat manager."""

from __future__ import annotations

from typing import Any

from games.shared.combat_manager import CombatManagerBase

from . import constants as C  # noqa: N812


class ZSCombatManager(CombatManagerBase):
    """Combat manager configured for Zombie Survival."""

    def __init__(
        self,
        entity_manager: Any,
        particle_system: Any,
        sound_manager: Any,
        on_kill: Any | None = None,
    ) -> None:
        super().__init__(
            entity_manager, particle_system, sound_manager, C, on_kill=on_kill
        )
