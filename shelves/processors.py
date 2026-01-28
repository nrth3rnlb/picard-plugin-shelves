"""
File processors for loading and saving shelf_name information.

Architecture:
- ProcessingContext: Holds file/track data and extracted shelf names
- ShelfStrategy (ABC): Base class for processing strategies
- Concrete strategies: KnownFromPath, KnownFromTagAndManual, etc.
- ShelfProcessors: Main processor facade with dependency injection support
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Sequence
from warnings import deprecated

from picard import log
from picard.file import File
from picard.track import Track

from .exceptions import ShelfNotFoundException
from .manager import ShelfManager
from .typings import ProcessingType, TagKey
from .workflow import WorkflowEngine


@dataclass
class ProcessingContext:
    """
    Context for shelf processing strategies.

    Contains all information needed to determine shelf assignment.
    """

    processing_type: ProcessingType
    album_id: str
    name_from_path: str
    name_from_tag: str
    is_locked: bool


class ShelfStrategy(ABC):
    """
    Base class for shelf processing strategies.

    Uses Template Method pattern: subclasses implement is_applicable() and resolve_shelf_name(),
    while the base class handles common logic.
    """

    def __init__(self, manager: ShelfManager):
        """
        Initialize strategy with ShelfManager.

        :param manager: ShelfManager instance for shelf operations.
        """
        self.manager = manager

    @abstractmethod
    def is_applicable(self, context: ProcessingContext) -> bool:
        """Check if this strategy should be applied."""
        pass

    @abstractmethod
    def resolve_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        """Get the shelf name to assign."""
        pass

    @staticmethod
    def should_lock() -> bool:
        """Whether this strategy should lock the shelf assignment."""
        return False

    @staticmethod
    def should_unlock() -> bool:
        """Whether this strategy should unlock the shelf assignment."""
        return False

    def should_upvote(self, context: ProcessingContext) -> bool:
        """Whether this strategy should vote."""
        current_type = self.manager.get_processing_type(album_id=context.album_id)
        return (
            context.processing_type == ProcessingType.LOAD
            or context.processing_type == ProcessingType.ADD
            and current_type != ProcessingType.LOAD
        )

    @staticmethod
    def should_downvote(context: ProcessingContext) -> bool:
        """Whether this strategy should downvote a shelf assignment."""
        return context.processing_type == ProcessingType.REMOVE

    def process(self, context: ProcessingContext) -> bool:
        """Process the shelf assignment based on the strategy."""

        # There are 4 responsibilities in process:
        # Activation, name resolution, voting, locking.

        if not self.is_applicable(context):
            return False
        log.debug("strategy: %s", self.__class__.__name__)

        shelf_name = self.resolve_shelf_name(context)
        if not shelf_name:
            return False

        log.debug("type: %s", context.processing_type.name)

        # WorkflowEngine.apply_transition() returns the original shelf name if no transition is needed
        # shelf_name = WorkflowEngine.apply_transition(shelf_name=shelf_name)

        self.apply_votes(context, shelf_name)
        self.apply_lock_state(context)

        return True

    def apply_lock_state(self, context: ProcessingContext):
        """Apply manual lock/unlock state to the shelf assignment."""
        if self.should_lock():
            self.manager.lock(album_id=context.album_id)
        if self.should_unlock():
            self.manager.unlock(album_id=context.album_id)

    def apply_votes(self, context: ProcessingContext, shelf_name: str):
        """Apply upvote/downvote to the shelf assignment."""
        if self.should_upvote(context):
            self.manager.upvote(
                album_id=context.album_id,
                shelf_name=shelf_name,
                processing_type=context.processing_type,
            )
        if self.should_downvote(context):
            self.manager.downvote(
                album_id=context.album_id,
                shelf_name=shelf_name,
                processing_type=context.processing_type,
            )


class StrategyKnownIdenticalNames(ShelfStrategy):
    """
    Strategy: Matching shelf names in path and tag.

    When the shelf name found in the file path is the same as the shelf name specified in the tag,
    no further action is required.
    """

    def is_applicable(self, context: ProcessingContext) -> bool:
        return (
            context.name_from_tag in self.manager.shelf_names
            and context.name_from_path in self.manager.shelf_names
            and context.name_from_tag == context.name_from_path
        )

    def resolve_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_tag


class StrategyKnownNameFromPathDiffersFromTag(ShelfStrategy):
    """
    Strategy: The shelf name detected in the file path does not match the shelf name indicated
    by the tag.

    The name of the shelf within the file's path is recognized and contrasts with the name present
    in the tag.

    This situation addresses the following scenario:
    The album has been relocated outside of the Picard application. This event warrants the
    utmost urgency.
    """

    def is_applicable(self, context: ProcessingContext) -> bool:
        return (
            context.name_from_path in self.manager.shelf_names
            and context.name_from_tag != context.name_from_path
        )

    def resolve_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path

    @staticmethod
    def should_lock() -> bool:
        return False


class StrategyUnknownNameFromPath(ShelfStrategy):
    """Strategy: Unknown shelf name from path."""

    def is_applicable(self, context: ProcessingContext) -> bool:
        return (
            context.name_from_path != ""
            and context.name_from_path not in self.manager.shelf_names
        )

    def resolve_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path


class ShelfProcessors:
    """
    File processors for loading and saving shelf name information.

    Supports dependency injection for testing. Uses strategy pattern
    for processing shelf assignments based on file paths and tags.
    """

    STRATEGY_ORDER: Sequence[type[ShelfStrategy]] = [
        StrategyKnownIdenticalNames,
        StrategyKnownNameFromPathDiffersFromTag,
        StrategyUnknownNameFromPath,
    ]

    def __init__(self, manager: Optional[ShelfManager] = None):
        """Initialize processors with optional ShelfManager injection."""

        self.manager = manager or ShelfManager()
        self.strategies = [cls(self.manager) for cls in self.STRATEGY_ORDER]

    def file_post_load_processor(self, file: File) -> None:
        """Process a file after Picard has scanned it."""
        context = ContextBuilder.build_processing_context_by_file(
            self.manager,
            processing_type=ProcessingType.LOAD,
            file=file,
        )
        if not context:
            return
        # Apply strategies in priority order
        for strategy in self.strategies:
            if strategy.process(context):
                # ShelfProcessors.track_metadata_processor(
                #         self, album=None, metadata=file.metadata, track=None, release=None
                # )
                break

    def file_post_addition_to_track_processor(
        self,
        track: Track,
        file: File,
    ) -> None:
        """Process a file after it has been added to a track."""
        context = ContextBuilder.build_processing_context_by_file(
            self.manager,
            processing_type=ProcessingType.ADD,
            file=file,
        )
        if not context:
            return
        # Apply strategies in priority order
        for strategy in self.strategies:
            if strategy.process(context):
                # ShelfProcessors.track_metadata_processor(
                #         self, album=None, metadata=file.metadata, track=track, release=None
                # )
                break

    def file_post_removal_from_track_processor(self, track: Track, file: File) -> None:
        """Process a file after it has been removed from a track."""
        context = ContextBuilder.build_processing_context_by_file(
            self.manager,
            processing_type=ProcessingType.REMOVE,
            file=file,
        )
        if not context:
            return
        # Apply strategies in priority order
        for strategy in self.strategies:
            if strategy.process(context):
                break

    def file_post_save_processor(self, file: File) -> None:
        """Process a file after it has been saved."""
        context = ContextBuilder.build_processing_context_by_file(
            self.manager,
            processing_type=ProcessingType.SAVE,
            file=file,
        )
        if not context:
            return
        # Apply strategies in priority order
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
        album_id = metadata.get(TagKey.MUSICBRAINZ_ALBUMID)
        if not album_id:
            return
        try:
            shelf_name = self.manager.get_shelf_name(album_id=album_id)
        except ShelfNotFoundException:
            log.warning("Failed to determine shelf name for album ID '%s'", album_id)
            return

        metadata[TagKey.SHELF] = WorkflowEngine.apply_transition(shelf_name=shelf_name)
        metadata[TagKey.SHELF_LOCKED] = self.manager.is_locked(album_id=album_id)

        log.debug(
            "shelf name: %s, locked: %s",
            metadata[TagKey.SHELF],
            metadata[TagKey.SHELF_LOCKED],
        )


class ContextBuilder:
    """Helper class for building processing contexts."""

    @staticmethod
    def build_processing_context_by_file(
        manager: ShelfManager,
        processing_type: ProcessingType,
        file: File,
    ) -> Optional[ProcessingContext]:
        """Build processing context from file"""
        from . import utils

        utils.debug_track(file)

        file_meta = getattr(file, "metadata", None)
        if not file_meta:
            return None

        album_id = file_meta.get(TagKey.MUSICBRAINZ_ALBUMID)
        if not album_id:
            return None

        # Extract shelf name from path
        name_from_path = utils.get_shelf_name_from_path(
            file_path=Path(file.filename),
            base_path=manager.base_path,
        )

        name_from_tag_file = file_meta.get(TagKey.SHELF, None)
        name_from_tag_file = utils.get_shelf_name_from_tag(name_from_tag_file)
        is_locked_file = file_meta.get(TagKey.SHELF_LOCKED, None)

        log.debug(
            f"file: {file.filename}, album_id: {album_id}, name_from_path: "
            f"{name_from_path}, name_from_tag: {name_from_tag_file}, is_locked: {is_locked_file}"
        )

        return ProcessingContext(
            processing_type=processing_type,
            album_id=album_id,
            name_from_path=name_from_path,
            name_from_tag=name_from_tag_file,
            is_locked=is_locked_file,
        )

    @staticmethod
    @deprecated(
        "I'm not quite sure yet, but I think we can ignore the files per track."
    )
    def build_processing_context_by_file_and_track(
        manager: ShelfManager,
        processing_type: ProcessingType,
        track: Track,
        _file: File,
    ) -> Optional[ProcessingContext]:
        """
        Build a processing context for a file based on its metadata and the track it belongs to.
        """
        from . import utils

        utils.debug_track(track)

        track_meta = getattr(track, "metadata", None)
        if not track_meta:
            return None

        album_id = track_meta.get(TagKey.MUSICBRAINZ_ALBUMID)
        if not album_id:
            return None

        names_from_path: set[str] = set()
        for file_by_track in track.files:
            log.debug(
                "file_by_track: %s", file_by_track.filename
            )  # Extract shelf name from path
            names_from_path.union(
                utils.get_shelf_name_from_path(
                    file_path=Path(file_by_track.filename),
                    base_path=manager.base_path,
                )
            )

        name_from_tag = track_meta.get(TagKey.SHELF, None)
        name_from_tag = utils.get_shelf_name_from_tag(name_from_tag)
        is_locked = track_meta.get(TagKey.SHELF_LOCKED, None)

        log.debug(
            f"Processing track: {track_meta['title']}, album_id: {album_id}, name_from_path: "
            f"{names_from_path}, name_from_tag: {name_from_tag}, is_locked: {is_locked}"
        )

        name_from_path = (
            set(names_from_path).pop() if len(names_from_path) == 1 else "multiple"
        )

        return ProcessingContext(
            processing_type=processing_type,
            album_id=album_id,
            name_from_path=name_from_path,
            name_from_tag=name_from_tag,
            is_locked=is_locked,
        )


# Global instance for lazy, shared access (avoids import-time config access).
_processors_singleton = None


def instance() -> ShelfProcessors:
    """Get the default global ShelfProcessors instance."""
    global _processors_singleton
    if _processors_singleton is None:
        _processors_singleton = ShelfProcessors()
    return _processors_singleton
