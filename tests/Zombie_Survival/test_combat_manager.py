"""Tests for games.Zombie_Survival.src.combat_manager."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from games.Zombie_Survival.src.combat_manager import ZSCombatManager


@pytest.fixture()
def zs_cm() -> ZSCombatManager:
    entity_manager = MagicMock()
    particle_system = MagicMock()
    sound_manager = MagicMock()
    return ZSCombatManager(entity_manager, particle_system, sound_manager)


class TestZSCombatManager:
    def test_init_creates_instance(self, zs_cm: ZSCombatManager) -> None:
        assert zs_cm is not None

    def test_inherits_from_base(self, zs_cm: ZSCombatManager) -> None:
        from games.shared.combat_manager import CombatManagerBase

        assert isinstance(zs_cm, CombatManagerBase)

    def test_init_with_on_kill_callback(self) -> None:
        on_kill = MagicMock()
        cm = ZSCombatManager(MagicMock(), MagicMock(), MagicMock(), on_kill=on_kill)
        assert cm is not None
