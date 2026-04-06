"""Backward-compatibility shim — implementation lives in systems/entity_manager.py."""

from __future__ import annotations

from .systems.entity_manager import EntityManager as EntityManager

__all__ = ["EntityManager"]
