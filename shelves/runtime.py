from __future__ import annotations

from typing import Optional

from .manager import ShelfManager
from .processors import Processors
from .transitions import Transitions

_manager_singleton: Optional[ShelfManager] = None

__all__ = ["manager_instance", "processor_instance", "transition_instance"]


def manager_instance() -> ShelfManager:
    """Get the default global ShelfManager instance."""
    global _manager_singleton
    if _manager_singleton is None:
        from .settings import shelf_manager_settings_from_picard_config

        _manager_singleton = ShelfManager(
            settings=shelf_manager_settings_from_picard_config(),
        )
    if _manager_singleton is None:
        raise RuntimeError("ShelfManager instance could not be initialized")
    return _manager_singleton


_processors_singleton: Optional[Processors] = None


def processor_instance() -> Processors:
    """Get the default global Processors instance."""
    global _processors_singleton
    if _processors_singleton is None:
        _processors_singleton = Processors()
    if _processors_singleton is None:
        raise RuntimeError("Processors instance could not be initialized")
    return _processors_singleton


_transition_singleton: Optional[Transitions] = None


def transition_instance() -> Transitions:
    """Get the default global Transitions instance."""
    global _transition_singleton
    if _transition_singleton is None:
        _transition_singleton = Transitions()
    if _transition_singleton is None:
        raise RuntimeError("Transitions instance could not be initialized")
    return _transition_singleton


def _reset_all_instances():
    """Reset all global singleton instances to None.
    Intended for tests only.
    """
    global _manager_singleton, _processors_singleton, _transition_singleton
    _manager_singleton = None
    _processors_singleton = None
    _transition_singleton = None
