"""
Module providing classes and logic for managing shelf workflow transitions.

This module defines the base classes and implementation for handling
transitions within the workflow of a shelving system. It includes strategies
for determining the appropriate shelf transitions based on the context and
applies a sequence of predefined transitions to handle different scenarios.
"""

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from picard import config, log

from . import manager as manager_module
from .contexts import TransitionContext
from .manager import ShelfManager
from .typings import ConfigKey


class Strategy(ABC):
    """Base class for shelf workflow transitions."""

    def __init__(self, manager: ShelfManager):
        """Initialize with ShelfManager."""
        self.manager = manager

    @abstractmethod
    def is_applicable(self, context: TransitionContext) -> bool:
        """Check if this strategy is applicable."""
        pass

    @abstractmethod
    def apply_transition(self, context: TransitionContext) -> bool:
        """Check if this transition should be applied."""
        pass

    # noinspection PyTypeHints
    def process(self, context: TransitionContext) -> bool:
        """Process the shelf transition."""
        if not config.setting[ConfigKey.WORKFLOW_ENABLED]:
            return False

        if not self.is_applicable(context):
            return False

        log.debug("Strategy: %s, Context: %s", self.__class__.__name__, context)
        if self.apply_transition(context):
            context.shelf_name = config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES][0]
        return True


class StrategyEmptyNameToStage2(Strategy):
    """Strategy of an empty shelf name."""

    def is_applicable(self, context: TransitionContext) -> bool:
        # noinspection PyTypeHints
        decision = (
            context.transition_type == TransitionContext.TransitionType.TO_STAGE_2
            and config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES]
            and context.shelf_name == ""
        )
        return decision

    def apply_transition(self, context: TransitionContext) -> bool:
        # An album is being loaded from MusicBrainz. It doesn't know about the files in the folder.
        return True


class StrategyUnknownNameToStage2(Strategy):
    """Strategy of an unknown shelf name."""

    def is_applicable(self, context: TransitionContext) -> bool:
        # noinspection PyTypeHints
        decision = (
            context.transition_type == TransitionContext.TransitionType.TO_STAGE_2
            and config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES]
            and config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES]
            and context.shelf_name not in self.manager.registered_shelf_names
        )
        return decision

    def apply_transition(self, context: TransitionContext) -> bool:
        # noinspection PyTypeHints
        decision = (
            config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES]
            and context.shelf_name not in self.manager.registered_shelf_names
        )
        return decision


class StrategyKnownNameToStage2(Strategy):
    """Strategy of a known shelf name."""

    def is_applicable(self, context: TransitionContext) -> bool:
        # noinspection PyTypeHints

        decision = (
            context.transition_type == TransitionContext.TransitionType.TO_STAGE_2
            and config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES]
            and context.shelf_name in self.manager.registered_shelf_names
            and context.shelf_name in config.setting[ConfigKey.WORKFLOW_STAGE_1_SHELVES]
        )
        return decision

    def apply_transition(self, context: TransitionContext) -> bool:
        decision = context.shelf_name in self.manager.registered_shelf_names
        return decision


class Transitions:
    """
    Represents a workflow transition handler.

    This class is responsible for managing a sequence of transition processes
    in a predefined order. It optionally accepts a `ShelfManager` for managing
    the workflow state. If no `ShelfManager` is provided, a default one is
    initialized internally. Each transition in the workflow is instantiated with
    its own copy of the manager.
    """

    STRATEGY_ORDER: Sequence[type[Strategy]] = [
        StrategyEmptyNameToStage2,
        StrategyUnknownNameToStage2,
        StrategyKnownNameToStage2,
    ]

    def __init__(self, manager: Optional[ShelfManager] = None):
        """Initialize workflow with optional ShelfManager injection."""
        self.manager = manager or manager_module.instance()
        self.strategies = [cls(self.manager) for cls in self.STRATEGY_ORDER]

    def transition_to(
        self, album_id: str, transition_type: TransitionContext.TransitionType
    ) -> TransitionContext:
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
        for strategy in self.strategies:
            if strategy.process(context):
                context.strategy = strategy.__class__.__name__
                break
        return context


class ContextBuilder:
    """Helper class for building transition contexts."""

    @staticmethod
    def build_context(
        manager: ShelfManager,
        album_id: str,
        transition_type: TransitionContext.TransitionType,
    ) -> TransitionContext:
        """Build transition context from album_id."""
        shelf_name = manager.get_shelf_name(album_id=album_id)

        return TransitionContext(
            album_id=album_id,
            shelf_name=shelf_name,
            transition_type=transition_type,
            strategy=None,
        )


# Global instance for lazy, shared access (avoids import-time config access).
_workflow_singleton = None


def instance() -> Transitions:
    """Get the default global Transitions instance."""
    global _workflow_singleton
    if _workflow_singleton is None:
        _workflow_singleton = Transitions()
    return _workflow_singleton
