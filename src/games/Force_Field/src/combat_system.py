"""Backward-compatibility shim — implementation lives in systems/combat_system.py."""

from __future__ import annotations

from .systems.combat_system import CombatSystem as CombatSystem

__all__ = ["CombatSystem"]
