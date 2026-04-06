"""Backward-compatibility shim — implementation lives in systems/spawn_manager.py."""

from __future__ import annotations

from .systems.spawn_manager import FFSpawnManager as FFSpawnManager

__all__ = ["FFSpawnManager"]
