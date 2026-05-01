"""
File processors for loading and saving shelf_name information.

Architecture:
- Context: Holds file/track data and extracted shelf names
- Strategy (ABC): Base class for processing strategies
- Concrete strategies: KnownFromPath, KnownFromTagAndManual, etc.
- Processors: Main processor facade with dependency injection support
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from picard import log, config
from picard.file import File
from picard.track import Track

from . import transitions
from . import manager as manager_module
from .contexts import ProcessingContext, TransitionContext
from .manager import ShelfManager
from .typings import TagKey, VotingType, ConfigKey


class Strategy(ABC):
    """
    Base class for shelf processing strategies.

    Uses Template Method pattern: subclasses implement is_applicable() and shelf_name(),
    while the base class handles common logic.
    """

    def __init__(self, manager: ShelfManager):
        """Initialize with ShelfManager."""
        self.manager = manager

    @abstractmethod
    def is_applicable(self, context: ProcessingContext) -> bool:
        """Check if this strategy should be applied."""
        raise NotImplementedError

    @abstractmethod
    def shelf_name(self, context: ProcessingContext) -> str:
        """Get the shelf name to assign."""
        raise NotImplementedError

    def upvote_shelf_names(self, context: ProcessingContext) -> List[str]:
        if (
            context.processing_type == ProcessingContext.ProcessingType.ADD
            or context.processing_type == ProcessingContext.ProcessingType.SET
        ):
            return [context.name_from_path]
        if (
            context.processing_type == ProcessingContext.ProcessingType.REMOVE
            or context.processing_type == ProcessingContext.ProcessingType.UNSET
        ):
            return []
        return []

    def downvote_shelf_names(self, context: ProcessingContext) -> List[str]:
        if (
            context.processing_type == ProcessingContext.ProcessingType.ADD
            or context.processing_type == ProcessingContext.ProcessingType.SET
        ):
            return list(
                self.manager.registered_shelf_names.difference([context.name_from_path])
            )
        if (
            context.processing_type == ProcessingContext.ProcessingType.REMOVE
            or context.processing_type == ProcessingContext.ProcessingType.UNSET
        ):
            return [context.name_from_path]

        return []

    @staticmethod
    def should_lock(context: ProcessingContext) -> bool:
        """Whether this strategy should lock the shelf assignment."""
        decision = context.processing_type == ProcessingContext.ProcessingType.SET
        return decision

    @staticmethod
    def should_unlock(context: ProcessingContext) -> bool:
        """Whether this strategy should unlock the shelf assignment."""
        decision = context.processing_type == ProcessingContext.ProcessingType.UNSET
        return decision

    @staticmethod
    def decide_voting(context: ProcessingContext) -> VotingType:
        """Whether this strategy should initialize the shelf assignment."""
        if (
            context.processing_type == ProcessingContext.ProcessingType.REMOVE
            or context.processing_type == ProcessingContext.ProcessingType.UNSET
        ):
            return VotingType.DOWN
        if (
            context.processing_type == ProcessingContext.ProcessingType.ADD
            or context.processing_type == ProcessingContext.ProcessingType.SET
        ):
            return VotingType.UP
        return VotingType.INITIAL

    def apply_lock_state(self, context: ProcessingContext):
        """Apply manual lock/unlock state to the shelf assignment."""
        if self.should_lock(context):
            self.manager.lock(album_id=context.album_id)
        if self.should_unlock(context):
            self.manager.unlock(album_id=context.album_id)

    def apply_votes(
        self, voting_type: VotingType, album_id: str, shelf_names: str | List[str]
    ):
        """Initialize voting, apply upvote/downvote to the shelf assignment."""
        if isinstance(shelf_names, str):
            shelf_names = [shelf_names]

        for shelf_name in shelf_names:
            self.manager.vote(
                voting_type=voting_type, album_id=album_id, shelf_name=shelf_name
            )

    def process(self, context: ProcessingContext) -> bool:
        """Process the shelf assignment based on the strategy."""

        if not self.is_applicable(context):
            return False
        log.debug("Strategy: %s, Context: %s", self.__class__.__name__, context)
        if context.processing_type == ProcessingContext.ProcessingType.LOAD:
            log.debug("INITIAL: %s", self.shelf_name(context))
            self.apply_votes(
                voting_type=VotingType.INITIAL,
                album_id=context.album_id,
                shelf_names=self.shelf_name(context),
            )
        else:
            log.debug("UP: %s", self.upvote_shelf_names(context))
            self.apply_votes(
                voting_type=VotingType.UP,
                album_id=context.album_id,
                shelf_names=self.upvote_shelf_names(context),
            )
            log.debug("DOWN: %s", self.downvote_shelf_names(context))
            self.apply_votes(
                voting_type=VotingType.DOWN,
                album_id=context.album_id,
                shelf_names=self.downvote_shelf_names(context),
            )

        return True


class StrategyManualUnset(Strategy):
    def is_applicable(self, context: ProcessingContext) -> bool:
        return context.processing_type == ProcessingContext.ProcessingType.UNSET

    def shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path

    def upvote_shelf_names(self, context: ProcessingContext) -> List[str]:
        return [context.name_from_path]

    def downvote_shelf_names(self, context: ProcessingContext) -> List[str]:
        return list(
            self.manager.registered_shelf_names.difference([context.name_from_path])
        )


class StrategyManualSet(Strategy):
    def shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.processing_name

    def is_applicable(self, context: ProcessingContext) -> bool:
        if context.processing_type != ProcessingContext.ProcessingType.SET:
            return False

        return context.processing_name in self.manager.registered_shelf_names

    def upvote_shelf_names(self, context: ProcessingContext) -> List[str]:
        return [context.processing_name]

    def downvote_shelf_names(self, context: ProcessingContext) -> List[str]:
        return list(
            self.manager.registered_shelf_names.difference([context.processing_name])
        )


class StrategyKnownIdenticalNames(Strategy):
    """
    Strategy: Matching shelf names in path and tag.

    When the shelf name found in the file path is the same as the shelf name specified in the tag,
    no further action is required.
    """

    def is_applicable(self, context: ProcessingContext) -> bool:
        processing_type = context.processing_type
        name_from_path = context.name_from_path
        name_from_tag = context.name_from_tag
        if processing_type in {
            ProcessingContext.ProcessingType.SET,
            ProcessingContext.ProcessingType.UNSET,
        }:
            return False

        if name_from_path != name_from_tag:
            return False

        return name_from_path in self.manager.registered_shelf_names

    def shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path


class StrategyKnownNameFromPathDiffersFromTag(Strategy):
    """
    Strategy: The shelf name detected in the file path does not match the shelf name indicated
    by the tag.

    The name of the shelf within the file's path is recognized and contrasts with the name present
    in the tag.

    This situation addresses the following scenario:
    The album has been relocated outside the Picard application. This event warrants the
    utmost urgency.
    """

    def is_applicable(self, context: ProcessingContext) -> bool:
        # Early return for manual operations
        if context.processing_type in (
            ProcessingContext.ProcessingType.SET,
            ProcessingContext.ProcessingType.UNSET,
        ):
            return False

        name_from_path = context.name_from_path

        # Early return if names match
        if name_from_path == context.name_from_tag:
            return False

        # Check if it's a registered shelf name first (likely cheaper than config lookup)
        if name_from_path not in self.manager.registered_shelf_names:
            return False

        # Final check: exclude workflow stage 1 shelves
        return name_from_path not in config.setting[ConfigKey.WORKFLOW_STAGE_1_SHELVES]

    def shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path


class StrategyUnknownNameFromPath(Strategy):
    """Strategy: Unknown shelf name from path."""

    def is_applicable(self, context: ProcessingContext) -> bool:
        # Early return if it's a manual operation
        if context.processing_type in {
            ProcessingContext.ProcessingType.SET,
            ProcessingContext.ProcessingType.UNSET,
        }:
            return False

        # Early return if no name from path
        name_from_path = context.name_from_path
        if not name_from_path:
            return False

        # Check if it's NOT a registered shelf name (single membership test)
        return name_from_path not in self.manager.registered_shelf_names

    def shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path


class Processors:
    """
    Manages and orchestrates the processing strategies for shelf-related operations
    on files and tracks. Provides mechanisms to handle file post-loading, addition,
    removal, saving processes, as well as track metadata processing, applying
    various shelf strategies for their resolution.

    The purpose of this class is to encapsulate the application of various shelf
    strategies in a prioritized manner to manage shelf assignments and metadata
    within a music processing context. Operations performed by this class include
    post-loading, addition, and removal of files from tracks, as well as processing
    of metadata. Strategies are applied sequentially according to the defined order.
    """

    STRATEGY_ORDER: Sequence[type[Strategy]] = [
        StrategyManualUnset,
        StrategyManualSet,
        StrategyKnownIdenticalNames,
        StrategyKnownNameFromPathDiffersFromTag,
        StrategyUnknownNameFromPath,
    ]

    def __init__(self, manager: Optional[ShelfManager] = None):
        """Initialize processors with optional ShelfManager injection."""
        self.manager = manager or manager_module.instance()
        self.strategies = [cls(self.manager) for cls in self.STRATEGY_ORDER]

    def action_unset_processor(self, file: File) -> None:
        context = ContextBuilder.build(
            self.manager,
            file=file,
            processing_type=ProcessingContext.ProcessingType.UNSET,
        )
        for strategy in self.strategies:
            if strategy.process(context):
                break

    def action_set_processor(self, file: File, shelf_name: str) -> None:
        context = ContextBuilder.build(
            self.manager,
            file=file,
            processing_type=ProcessingContext.ProcessingType.SET,
            processing_name=shelf_name,
        )
        for strategy in self.strategies:
            if strategy.process(context):
                break

    def file_post_load_processor(self, file: File) -> None:
        """Process a file after it has been loaded."""
        context = ContextBuilder.build(
            self.manager,
            file=file,
            processing_type=ProcessingContext.ProcessingType.LOAD,
        )
        for strategy in self.strategies:
            if strategy.process(context):
                break

    def file_post_save_processor(self, file: File) -> None:
        """Process a file after it has been saved."""
        context = ContextBuilder.build(
            self.manager,
            file=file,
            processing_type=ProcessingContext.ProcessingType.SAVE,
        )
        for strategy in self.strategies:
            if strategy.process(context):
                break

    # noinspection PyUnusedLocal
    def file_post_addition_to_track_processor(
        self,
        track: Track,
        file: File,
    ) -> None:
        """Process a file after it has been added to a track."""
        context = ContextBuilder.build(
            self.manager,
            file=file,
            processing_type=ProcessingContext.ProcessingType.ADD,
        )
        for strategy in self.strategies:
            if strategy.process(context):
                break

    # noinspection PyUnusedLocal
    def file_post_removal_from_track_processor(self, track: Track, file: File) -> None:
        """Process a file after it has been removed from a track."""
        context = ContextBuilder.build(
            self.manager,
            file=file,
            processing_type=ProcessingContext.ProcessingType.REMOVE,
        )
        for strategy in self.strategies:
            if strategy.process(context):
                break

    def track_metadata_processor(
        self,
        _album: Optional[Any],
        metadata: Dict[str, Any],
        _track: Optional[Any],
        _release: Optional[Any],
    ) -> None:
        """Set a shelf name in track metadata from album's shelf assignment."""
        album_id = metadata.get(TagKey.MUSICBRAINZ_ALBUMID, "")
        context: TransitionContext = transitions.instance().transition_to(
            album_id=album_id,
            transition_type=TransitionContext.TransitionType.TO_STAGE_2,
        )
        metadata[TagKey.SHELF] = context.shelf_name
        metadata[TagKey.SHELF_LOCKED] = self.manager.is_locked(album_id=album_id)

        log.debug(
            "shelf name: %s, locked: %s",
            metadata[TagKey.SHELF],
            metadata[TagKey.SHELF_LOCKED],
        )


class ContextBuilder:
    """Helper class for building processing contexts."""

    @staticmethod
    def build(
        manager: ShelfManager,
        file: File,
        processing_type: ProcessingContext.ProcessingType,
        processing_name: Optional[str] = "",
    ) -> ProcessingContext:
        """Build processing context from file"""

        from . import utils

        # utils.debug_track(file)
        # Extract shelf name from path
        name_from_path = utils.get_shelf_name_from_path(
            file_path=Path(file.filename),
            base_path=manager.base_path,
        )

        return ProcessingContext(
            processing_type=processing_type,
            album_id=file.metadata[TagKey.MUSICBRAINZ_ALBUMID],
            name_from_path=name_from_path,
            name_from_tag=file.metadata[TagKey.SHELF],
            processing_name=processing_name or "",
            is_locked=file.metadata[TagKey.SHELF_LOCKED],
        )

    # @staticmethod
    # @deprecated(
    #     "I'm not quite sure yet, but I think we can ignore the files per track."
    # )
    # def build_processing_context_by_file_and_track(
    #     manager: ShelfManager,  #     processing_type: ProcessingContext.ProcessingType,
    #     track: Track,
    #     _file: File,
    # ) -> Optional[ProcessingContext]:
    #     """
    #     Build a processing context for a file based on its metadata and the track it belongs to.
    #     """
    #     from . import utils
    #
    #     # utils.debug_track(track)
    #
    #     track_meta = getattr(track, "metadata", None)
    #     if not track_meta:
    #         return None
    #
    #     album_id = track_meta.get(TagKey.MUSICBRAINZ_ALBUMID)
    #     if not album_id:
    #         return None
    #
    #     names_from_path: set[str] = set()
    #     for file_by_track in track.files:
    #         log.debug(
    #             "file_by_track: %s", file_by_track.filename
    #         )  # Extract shelf name from path
    #         names_from_path.union(
    #             utils.get_shelf_name_from_path(
    #                 file_path=Path(file_by_track.filename),
    #                 base_path=manager.base_path,
    #             )
    #         )
    #
    #     name_from_tag = track_meta.get(TagKey.SHELF, None)
    #     name_from_tag = utils.get_shelf_name_from_tag(name_from_tag)
    #     is_locked = track_meta.get(TagKey.SHELF_LOCKED, None)
    #
    #     # log.debug(
    #     #     f"Processing track: {track_meta['title']}, album_id: {album_id}, name_from_path: "
    #     #     f"{names_from_path}, name_from_tag: {name_from_tag}, is_locked: {is_locked}"
    #     # )
    #
    #     name_from_path = (
    #         set(names_from_path).pop() if len(names_from_path) == 1 else "multiple"
    #     )
    #
    #     return ProcessingContext(
    #         processing_type=processing_type,
    #         album_id=album_id,
    #         name_from_path=name_from_path,
    #         name_from_tag=name_from_tag,
    #         is_locked=is_locked,
    #     )


# Global instance for lazy, shared access (avoids import-time config access).
_processors_singleton = None


def instance() -> Processors:
    """Get the default global Processors instance."""
    global _processors_singleton
    if _processors_singleton is None:
        _processors_singleton = Processors()
    return _processors_singleton
