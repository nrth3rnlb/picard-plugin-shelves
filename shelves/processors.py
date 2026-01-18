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
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

from picard import log

from .workflow import WorkflowEngine
from . import constants, utils
from .manager import ShelfManager
from .exceptions import ShelfNotFoundException


@dataclass
class ProcessingContext:
    """
    Context for shelf processing strategies.

    Contains all information needed to determine shelf assignment.
    """
    album_id: str
    file: Any
    track: Optional[Any]
    name_from_path: str
    name_from_tag: str
    is_manual: bool

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
        """
        Check if this strategy should be applied.

        :param context: Processing context with file/track data.
        :return: True if strategy should be applied.
        """
        pass

    @abstractmethod
    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        """
        Get the shelf name to assign.

        :param context: Processing context with file/track data.
        :return: Shelf name or None.
        """
        pass

    def should_lock(self) -> bool:
        """Whether this strategy should lock the shelf assignment."""
        return False

    def should_vote(self) -> bool:
        """Whether this strategy should vote instead of directly assigning."""
        return False

    def process(self, context: ProcessingContext) -> bool:
        """
        Process the shelf assignment if this strategy applies.

        :param context: Processing context with file/track data.
        :return: True if strategy was applied, False otherwise.
        """

        if not self.should_apply(context):
            log.debug("Skipping strategy: %s", self.__class__.__name__)
            return False
        log.debug("Applying strategy: %s", self.__class__.__name__)

        shelf_name = self.get_shelf_name(context)
        if not shelf_name:
            log.debug("No shelf name found for strategy: %s", self.__class__.__name__)
            return False
        log.debug("Shelf name found: %s", shelf_name)

        # WorkflowEngine.apply_transition() returns the original shelf name if no transition is needed
        shelf_name = WorkflowEngine.apply_transition(shelf_name=shelf_name)
        log.debug("Transition applied, new shelf name: %s", shelf_name)

        # Set metadata
        obj = context.file if context.file else context.track
        label = "file" if context.file else "track"
        ShelfProcessors.set_metadata(obj, constants.TAG_KEY, shelf_name, label)

        # Assign or vote
        if self.should_vote():
            self.manager.vote_for_shelf(
                    album_id=context.album_id,
                    shelf_name=shelf_name,
            )
        else:
            self.manager.set_album_shelf(
                    album_id=context.album_id,
                    shelf_name=shelf_name,
                    lock=self.should_lock(),
            )

        return True


class KnownNameFromPathStrategy(ShelfStrategy):
    """Strategy: Known shelf name found in file path (highest priority)."""

    def should_apply(self, context: ProcessingContext) -> bool:
        return context.is_known_name_from_path(self.manager.shelf_names)

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path

    def should_lock(self) -> bool:
        return True


class KnownNameFromTagAndManualStrategy(ShelfStrategy):
    """Strategy: Known shelf name from tag with manual suffix."""

    def should_apply(self, context: ProcessingContext) -> bool:
        return (
                context.is_known_name_from_tag(self.manager.shelf_names)
                and context.is_manual
        )

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_tag

    def should_lock(self) -> bool:
        return True


class KnownNameFromTagStrategy(ShelfStrategy):
    """Strategy: Known shelf name from tag (without manual suffix)."""

    def should_apply(self, context: ProcessingContext) -> bool:
        return context.is_known_name_from_tag(self.manager.shelf_names)

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_tag

    def should_lock(self) -> bool:
        return True


class UnknownNameFromTagStrategy(ShelfStrategy):
    """Strategy: Unknown shelf name from tag, use path instead."""

    def should_apply(self, context: ProcessingContext) -> bool:
        return context.is_unknown_name_from_tag(self.manager.shelf_names)

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path

    def should_vote(self) -> bool:
        return True


class UnknownNameFromPathStrategy(ShelfStrategy):
    """Strategy: Unknown shelf name from path (voting mode)."""

    def should_apply(self, context: ProcessingContext) -> bool:
        return context.is_unknown_name_from_path(self.manager.shelf_names)

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path

    def should_vote(self) -> bool:
        return True


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
            KnownNameFromPathStrategy(self.manager),
            KnownNameFromTagAndManualStrategy(self.manager),
            KnownNameFromTagStrategy(self.manager),
            UnknownNameFromTagStrategy(self.manager),
            UnknownNameFromPathStrategy(self.manager),
        ]

    @staticmethod
    def set_metadata(obj: Any, key: str, value: Any, label: str) -> None:
        """Safely sets metadata on a Picard object."""
        meta = getattr(obj, "metadata", None)
        filename = getattr(obj, "filename", "")
        if meta is None:
            log.debug("%s metadata missing for: %s", label, filename)
            return
        try:
            meta[key] = value
        except TypeError as e:
            log.debug("Failed to set %s metadata for: %s; %s", label, filename, e)

    def file_post_removal_from_track_processor(self, _track: Any, file: Any) -> None:
        """Process a file after it has been removed from a track."""
        log.debug(
                "(file_post_removal_from_track_processor) Processing file: %s",
                file.filename,
        )
        album_id = file.metadata.get(constants.MUSICBRAINZ_ALBUMID)
        if album_id:
            self.manager.clear_album(album_id)

    def file_post_addition_to_track_processor(
            self, track: Optional[Any], file: Any,
    ) -> None:
        """Process a file after it has been added to a track."""
        context = self.build_processing_context(file, track)
        if not context:
            return

        log.debug("Processing file: %s", file.filename)
        # Apply strategies in priority order
        for strategy in self.strategies:
            if strategy.process(context):
                break

    def build_processing_context(
            self, file: Any, track: Optional[Any],
    ) -> Optional[ProcessingContext]:
        """
        Build processing context from file/track metadata.

        :param file: File object with metadata.
        :param track: Optional track object.
        :return: ProcessingContext or None if missing required data.
        """
        file_meta = getattr(file, "metadata", None)
        if not file_meta:
            return None

        album_id = file_meta.get(constants.MUSICBRAINZ_ALBUMID)
        if not album_id:
            return None

        # Extract shelf name from path
        name_from_path = utils.get_shelf_name_from_path(
                file_path=Path(file.filename), base_path=self.manager.base_path,
        )
        name_from_path = name_from_path.strip()

        # Extract shelf name from tag
        name_from_tag = file_meta.get(constants.TAG_KEY, "").strip()
        name_from_tag = utils.get_shelf_name_from_tag(name_from_tag)

        is_manual = file_meta.get(constants.TAG_LOCKED_KEY, False)

        # TODO: Hier geht es weiter
        log.debug(
                f"Processing file: {file.filename}, album_id: {album_id}, track: {track}, name_from_path: "
                f"{name_from_path}, name_from_tag: {name_from_tag}, is_manual: {is_manual}"
        )

        return ProcessingContext(
                file=file,
                album_id=album_id,
                track=track,
                name_from_path=name_from_path,
                name_from_tag=name_from_tag,
                is_manual=is_manual,
        )

    def file_post_save_processor(self, file: Any) -> None:
        """Process a file after it has been saved."""
        try:
            log.debug("Processing file: %s", file.filename)
            album_id = file.metadata.get(constants.MUSICBRAINZ_ALBUMID)
            if album_id:
                self.manager.clear_album(album_id)
        except (KeyError, AttributeError, ValueError) as e:
            log.error("Error in file processor: %s", e)
            log.error("Traceback: %s", traceback.format_exc())

    def file_post_load_processor(self, file: Any) -> None:
        """Process a file after Picard has scanned it."""
        self.file_post_addition_to_track_processor(file=file, track=None)

    def set_shelf_in_metadata(
            self,
            _album: Any,
            metadata: Dict[str, Any],
            _track: Any,
            _release: Any,
    ) -> None:
        """Set a shelf name in track metadata from album's shelf assignment."""
        album_id = metadata.get(constants.MUSICBRAINZ_ALBUMID)
        if not album_id:
            return

        try:
            shelf_name = self.manager.get_album_shelf(album_id=album_id)
        except ShelfNotFoundException as e:
            log.warning("Failed to determine shelf name for album ID '%s'", album_id)
            return

        metadata[constants.TAG_KEY] = WorkflowEngine.apply_transition(shelf_name=shelf_name)
        metadata[constants.TAG_LOCKED_KEY] = self.manager.is_locked(album_id=album_id)


# Global instance for backward compatibility with static method calls
# Created lazily to avoid import-time config access
_default_processors = None


def get_default_processors() -> ShelfProcessors:
    """Get the default global ShelfProcessors instance."""
    global _default_processors
    if _default_processors is None:
        _default_processors = ShelfProcessors()
    return _default_processors
