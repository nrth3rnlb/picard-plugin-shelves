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
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, Optional
from warnings import deprecated

from picard import log
from picard.file import File
from picard.track import Track

from . import utils
from .constants import TagKey
from .exceptions import ShelfNotFoundException
from .manager import ShelfManager
from .workflow import WorkflowEngine


@dataclass
class ProcessingContext:
    """
    Context for shelf processing strategies.

    Contains all information needed to determine shelf assignment.
    """

    # TODO tidy up
    # metadata: Dict[str, Any]
    processing_type: ProcessingType
    # trigger: str
    album_id: str
    # file: Any
    # track: Optional[Any]
    name_from_path: str
    name_from_tag: str
    is_locked: bool

    def is_known_name_from_path(self, shelf_names: set) -> bool:
        """Check if path contains a known shelf name."""
        return self.name_from_path in shelf_names

    def is_known_name_from_tag(self, shelf_names: set) -> bool:
        """Check if tag contains a known shelf name."""
        return self.name_from_tag in shelf_names

    def is_unknown_name_from_path(self, shelf_names: set) -> bool:
        """Check if path contains an unknown shelf name."""
        return self.name_from_path not in shelf_names

    def is_unknown_name_from_tag(self, shelf_names: set) -> bool:
        """Check if tag contains an unknown shelf name."""
        return self.name_from_tag not in shelf_names


@dataclass
class ProcessingType(IntEnum):
    """Processing types for shelf processing strategies."""

    REMOVE = 10
    ADD = 20
    SAVE = 30
    LOAD = 40


class ShelfStrategy(ABC):
    """
    Base class for shelf processing strategies.

    Uses Template Method pattern: subclasses implement should_apply() and get_shelf_name(),
    while the base class handles common logic.
    """

    def __init__(self, manager: ShelfManager):
        """
        Initialize strategy with ShelfManager.

        :param manager: ShelfManager instance for shelf operations.
        """
        self.manager = manager

    @abstractmethod
    def should_apply(self, context: ProcessingContext) -> bool:
        """Check if this strategy should be applied."""
        pass

    @abstractmethod
    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
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

    @staticmethod
    def should_upvote() -> bool:
        """Whether this strategy should vote."""
        return False

    @staticmethod
    def should_downvote() -> bool:
        """Whether this strategy should downvote a shelf assignment."""
        return False

    def process(self, context: ProcessingContext) -> bool:
        """Process the shelf assignment if this strategy applies."""

        if not self.should_apply(context):
            return False
        log.debug("strategy: %s", self.__class__.__name__)

        shelf_name = self.get_shelf_name(context)
        if not shelf_name:
            return False

        log.debug("type: %s", context.processing_type)

        # WorkflowEngine.apply_transition() returns the original shelf name if no transition is needed
        shelf_name = WorkflowEngine.apply_transition(shelf_name=shelf_name)
        processing_type = self.manager.get_processing_type(album_id=context.album_id)
        if context.processing_type == ProcessingType.LOAD:
            self.manager.upvote(
                album_id=context.album_id,
                shelf_name=shelf_name,
                processing_type=context.processing_type,
            )
        if (
            context.processing_type == ProcessingType.ADD
            and processing_type != ProcessingType.LOAD
        ):
            self.manager.upvote(
                album_id=context.album_id,
                shelf_name=shelf_name,
                processing_type=context.processing_type,
            )
        if context.processing_type == ProcessingType.REMOVE:
            self.manager.downvote(
                album_id=context.album_id,
                shelf_name=shelf_name,
                processing_type=context.processing_type,
            )
        if self.should_lock():
            self.manager.lock(album_id=context.album_id)

        return True


class KnownIdenticalNames(ShelfStrategy):
    """
    Strategy: Matching shelf names in path and tag.

    When the shelf name found in the file path is the same as the shelf name specified in the tag,
    no further action is required.
    """

    def should_apply(self, context: ProcessingContext) -> bool:
        return (
            context.is_known_name_from_tag(self.manager.shelf_names)
            and context.is_known_name_from_path(self.manager.shelf_names)
            and context.name_from_tag == context.name_from_path
        )

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_tag


class KnownNameFromPath(ShelfStrategy):
    """
    Strategy: The shelf name detected in the file path does not match the shelf name indicated
    by the tag.

    The name of the shelf within the file's path is recognized and contrasts with the name present
    in the tag.

    This situation addresses the following scenario:
    The album has been relocated outside of the Picard application. This event warrants the
    utmost urgency.
    """

    def should_apply(self, context: ProcessingContext) -> bool:
        return (
            context.is_known_name_from_path(self.manager.shelf_names)
            and context.name_from_tag != context.name_from_path
        )

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path


class UnknownNameFromTag(ShelfStrategy):
    """Strategy: Unknown shelf name from tag, use path instead."""

    def should_apply(self, context: ProcessingContext) -> bool:
        return context.name_from_tag != "" and context.is_unknown_name_from_tag(
            self.manager.shelf_names
        )

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path


class UnknownNameFromPath(ShelfStrategy):
    """Strategy: Unknown shelf name from path."""

    def should_apply(self, context: ProcessingContext) -> bool:
        return context.name_from_path != "" and context.is_unknown_name_from_path(
            self.manager.shelf_names
        )

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path


class ShelfProcessors:
    """
    File processors for loading and saving shelf name information.

    Supports dependency injection for testing. Uses strategy pattern
    for processing shelf assignments based on file paths and tags.
    """

    def __init__(self, manager: Optional[ShelfManager] = None):
        """
        Initialize processors with optional ShelfManager injection.

        :param manager: ShelfManager instance (created if None).
        """
        self.manager = manager or ShelfManager()
        self.strategies = [
            KnownIdenticalNames(self.manager),
            KnownNameFromPath(self.manager),
            UnknownNameFromTag(self.manager),
            UnknownNameFromPath(self.manager),
        ]

    def file_post_load_processor(self, file: File) -> None:
        """Process a file after Picard has scanned it."""
        context = self.build_processing_context_by_file(
            processing_type=ProcessingType.LOAD, file=file
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
        context = self.build_processing_context_by_file(
            processing_type=ProcessingType.ADD, file=file
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
        context = self.build_processing_context_by_file(
            processing_type=ProcessingType.REMOVE, file=file
        )
        if not context:
            return
        # Apply strategies in priority order
        for strategy in self.strategies:
            if strategy.process(context):
                break

    def file_post_save_processor(self, file: File) -> None:
        """Process a file after it has been saved."""
        context = self.build_processing_context_by_file(
            processing_type=ProcessingType.SAVE, file=file
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

    def build_processing_context_by_file(
        self, processing_type: ProcessingType, file: File
    ) -> Optional[ProcessingContext]:
        """Build processing context from file"""
        utils.debug_file(file)

        file_meta = getattr(file, "metadata", None)
        if not file_meta:
            return None

        album_id = file_meta.get(TagKey.MUSICBRAINZ_ALBUMID)
        if not album_id:
            return None

        # Extract shelf name from path
        name_from_path = utils.get_shelf_name_from_path(
            file_path=Path(file.filename),
            base_path=self.manager.base_path,
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

    @deprecated(
        "I'm not quite sure yet, but I think we can ignore the files per track."
    )
    def build_processing_context_by_file_and_track(
        self, processing_type: ProcessingType, track: Track, _file: File
    ) -> Optional[ProcessingContext]:
        """
        Build a processing context for a file based on its metadata and the track it belongs to.
        """
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
                    base_path=self.manager.base_path,
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


# Global instance for backward compatibility with static method calls
# Created lazily to avoid import-time config access

_default_processors = None


def get_default_processors() -> ShelfProcessors:
    """Get the default global ShelfProcessors instance."""
    global _default_processors
    if _default_processors is None:
        _default_processors = ShelfProcessors()
    return _default_processors
