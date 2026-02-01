"""
Module providing classes and logic for managing shelf workflow transitions.

This module defines the base classes and implementation for handling
transitions within the workflow of a shelving system. It includes strategies
for determining the appropriate shelf transitions based on the context and
applies a sequence of predefined transitions to handle different scenarios.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Sequence

from picard import config

from .manager import ShelfManager
from .typings import ConfigKey, TransitionType


@dataclass
class TransitionContext:
    """Context for shelf workflow transitions."""

    transition_type: TransitionType
    album_id: str
    shelf_name: str


class TransitionStrategy(ABC):
    """Base class for shelf workflow transitions."""

    def __init__(self, manager: ShelfManager):
        """Initialize with ShelfManager."""
        self.manager = manager

    @abstractmethod
    def is_applicable(self, context: TransitionContext) -> bool:
        """Check if this transition should be applied."""
        pass

    def resolve_shelf_name(self, context: TransitionContext) -> Optional[str]:
        """The shelf name to which the transition should be applied."""
        shelf_name = self.manager.get_shelf_name(album_id=context.album_id)
        return shelf_name

    # noinspection PyTypeHints
    def process(self, context: TransitionContext) -> bool:
        """Process the shelf transition."""
        if not config.setting[ConfigKey.WORKFLOW_ENABLED]:
            return False

        if not self.is_applicable(context):
            return False

        shelf_name = self.resolve_shelf_name(context)
        if not shelf_name:
            return False

        self.manager.set_shelf_name(
            album_id=context.album_id,
            shelf_name=config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES][0],
        )
        return True


class TransitionUnknownNameToStage2(TransitionStrategy):
    """TransitionStrategy of an unknown shelf name."""

    def is_applicable(self, context: TransitionContext) -> bool:
        # noinspection PyTypeHints
        return (
            context.transition_type == TransitionType.TO_STAGE_2
            and config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES]
            and config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES]
            and context.shelf_name not in self.manager.shelf_names
        )


class TransitionsKnownNameToStage2(TransitionStrategy):
    """TransitionStrategy of a known shelf name."""

    def is_applicable(self, context: TransitionContext) -> bool:
        # noinspection PyTypeHints
        return (
            context.transition_type == TransitionType.TO_STAGE_2
            and config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES]
            and context.shelf_name in self.manager.shelf_names
        )


class Transitions:
    """
    Represents a workflow transition handler.

    This class is responsible for managing a sequence of transition processes
    in a predefined order. It optionally accepts a `ShelfManager` for managing
    the workflow state. If no `ShelfManager` is provided, a default one is
    initialized internally. Each transition in the workflow is instantiated with
    its own copy of the manager.
    """

    TRANSITION_ORDER: Sequence[type[TransitionStrategy]] = [
        TransitionUnknownNameToStage2,
        TransitionsKnownNameToStage2,
    ]

    def __init__(self, manager: Optional[ShelfManager] = None):
        """Initialize workflow with optional ShelfManager injection."""
        self.manager = manager or ShelfManager()
        self.transitions = [cls(self.manager) for cls in self.TRANSITION_ORDER]

    def transition_to(self, album_id: str, transition_type: TransitionType) -> None:
        """
        Handles the transition process for given album IDs based on the context and
        available transitions. Each transition is evaluated in sequence until a
        successful one processes the context.
        """
        context = ContextBuilder.build_context(
            manager=self.manager,
            album_id=album_id,
            transition_type=transition_type,
        )
        if not context:
            return
        for transition in self.transitions:
            if transition.process(context):
                break


class ContextBuilder:
    """Helper class for building transition contexts."""

    @staticmethod
    def build_context(
        manager: ShelfManager, album_id: str, transition_type: TransitionType
    ) -> TransitionContext:
        """Build transition context from album_id."""
        shelf_name = manager.get_shelf_name(album_id=album_id)
        return TransitionContext(
            album_id=album_id,
            shelf_name=shelf_name,
            transition_type=transition_type,
        )


# Global instance for lazy, shared access (avoids import-time config access).
_workflow_singleton = None


def instance() -> Transitions:
    """Get the default global Transitions instance."""
    global _workflow_singleton
    if _workflow_singleton is None:
        _workflow_singleton = Transitions()
    return _workflow_singleton
