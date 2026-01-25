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
from typing import Any, Dict, Optional

from picard import log
from picard.file import File
from picard.track import Track

from . import constants, utils
from .workflow import WorkflowEngine
from .manager import ShelfManager
from .exceptions import ShelfNotFoundException

REMOVE = 10
ADD = 20
SAVE = 30
LOAD = 40

_type_to_name = {
    REMOVE: 'REMOVE',
    ADD   : 'ADD',
    SAVE  : 'SAVE',
    LOAD  : 'LOAD',
}
_name_to_type = {
    'REMOVE': REMOVE,
    'ADD'   : ADD,
    'SAVE'  : SAVE,
    'LOAD'  : LOAD,
}


@dataclass
class ProcessingContext:
    """
    Context for shelf processing strategies.

    Contains all information needed to determine shelf assignment.
    """
    # TODO tidy up
    # metadata: Dict[str, Any]
    processor_type: int
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

    def should_unlock(self) -> bool:
        """Whether this strategy should unlock the shelf assignment."""
        return False

    def should_upvote(self) -> bool:
        """Whether this strategy should vote."""
        return False

    def should_downvote(self) -> bool:
        """Whether this strategy should downvote a shelf assignment."""
        return False

    def process(self, context: ProcessingContext) -> bool:
        """
        Process the shelf assignment if this strategy applies.

        :param context: Processing context with file/track data.
        :return: True if strategy was applied, False otherwise.
        """

        if not self.should_apply(context):
            return False
        log.debug("strategy: %s", self.__class__.__name__)

        shelf_name = self.get_shelf_name(context)
        if not shelf_name:
            return False

        # Avoid duplicate votes:
        # When adding, '.file_post_load_processor' and '.file_post_addition_to_track_processor' run
        # run one after the other, which leads to a doubling of the votes.
        # However, we must take both processors into account.
        # log.debug(
        #         "Trigger: %s, %s.%s", context.trigger, ShelfProcessors.__name__,
        #         ShelfProcessors.file_post_load_processor.__name__
        # )
        log.debug('type: %s', _type_to_name[context.processor_type])

        # disable_voting = False
        # if context.trigger != (f'{ShelfProcessors.__name__}.'
        #                        f'{ShelfProcessors.file_post_load_processor.__name__}'):
        #     disable_voting = True

        # WorkflowEngine.apply_transition() returns the original shelf name if no transition is needed
        shelf_name = WorkflowEngine.apply_transition(shelf_name=shelf_name)
        processor_type = self.manager.get_processor_type(album_id=context.album_id)
        if context.processor_type == LOAD:
            self.manager.upvote(
                    album_id=context.album_id,
                    shelf_name=shelf_name,
                    type=context.processor_type
            )
        if context.processor_type == ADD and processor_type != LOAD:
            self.manager.upvote(
                    album_id=context.album_id,
                    shelf_name=shelf_name,
                    type=context.processor_type
            )
        if context.processor_type == REMOVE:
            self.manager.downvote(
                    album_id=context.album_id,
                    shelf_name=shelf_name,
                    type=context.processor_type
            )
        if self.should_lock():
            self.manager.lock(album_id=context.album_id)

        return True


class KnownNameFromPathStrategy(ShelfStrategy):
    """Strategy: Known shelf name found in file path (highest priority)."""

    def should_apply(self, context: ProcessingContext) -> bool:
        return context.is_known_name_from_path(self.manager.shelf_names)

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path

    def should_lock(self) -> bool:
        return True


class IdenticalNameAndPathStrategy(ShelfStrategy):
    """
    Strategy: Known and identical shelf name from path and tag.

    Der Name des Regals im Pfad und der Name des Regals im Tag sind identisch.
    Wen das der Fall ist, dann muss nichts weiter entschieden werden.
    """

    def should_apply(self, context: ProcessingContext) -> bool:
        return (
                context.is_known_name_from_tag(self.manager.shelf_names) and
                context.is_known_name_from_path(self.manager.shelf_names)
                and context.name_from_tag == context.name_from_path
        )

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_tag

    def should_lock(self) -> bool:
        return False


class KnownNameFromTagAndLockedStrategy(ShelfStrategy):
    """Strategy: Known shelf name from tag with manual suffix."""

    def should_apply(self, context: ProcessingContext) -> bool:
        return (
                context.is_known_name_from_tag(self.manager.shelf_names)
                and context.is_locked
        )

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_tag


class KnownNameFromTagStrategy(ShelfStrategy):
    """Strategy: Known shelf name from tag (without manual suffix)."""

    def should_apply(self, context: ProcessingContext) -> bool:
        return context.is_known_name_from_tag(self.manager.shelf_names)

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_tag


class UnknownNameFromTagStrategy(ShelfStrategy):
    """Strategy: Unknown shelf name from tag, use path instead."""

    def should_apply(self, context: ProcessingContext) -> bool:
        return context.is_unknown_name_from_tag(self.manager.shelf_names)

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path

    def should_upvote(self) -> bool:
        return True


class UnknownNameFromPathStrategy(ShelfStrategy):
    """Strategy: Unknown shelf name from path (voting mode)."""

    def should_apply(self, context: ProcessingContext) -> bool:
        # Since an empty name is not a name, it is neither known nor unknown.
        return self.manager.shelf_names != "" and context.is_unknown_name_from_path(self.manager.shelf_names)

    def get_shelf_name(self, context: ProcessingContext) -> Optional[str]:
        return context.name_from_path

    def should_upvote(self) -> bool:
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
            IdenticalNameAndPathStrategy(self.manager),
            KnownNameFromPathStrategy(self.manager),
            KnownNameFromTagAndLockedStrategy(self.manager),
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

    def file_post_load_processor(self, file: File) -> None:
        """Process a file after Picard has scanned it."""
        context = self.build_processing_context_by_file(processor_type=LOAD, file=file)
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
            self, track: Track, file: File,
    ) -> None:
        """Process a file after it has been added to a track."""
        context = self.build_processing_context_by_file_and_track(processor_type=ADD, track=track, file=file)
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
        context = self.build_processing_context_by_file_and_track(processor_type=REMOVE, track=track, file=file)
        if not context:
            return
        # Apply strategies in priority order
        for strategy in self.strategies:
            if strategy.process(context):
                break

    def file_post_save_processor(self, file: File) -> None:
        """Process a file after it has been saved."""
        context = self.build_processing_context_by_file(processor_type=SAVE, file=file)
        if not context:
            return
        # Apply strategies in priority order
        for strategy in self.strategies:
            if strategy.process(context):
                break

    def track_metadata_processor(
            self,
            album: Optional[Any],
            metadata: Dict[str, Any],
            track: Optional[Any],
            release: Optional[Any],
    ) -> None:
        """Set a shelf name in track metadata from album's shelf assignment."""
        album_id = metadata.get(constants.MUSICBRAINZ_ALBUMID)
        if not album_id:
            return
        try:
            shelf_name = self.manager.get_shelf_name(album_id=album_id)
        except ShelfNotFoundException:
            log.warning("Failed to determine shelf name for album ID '%s'", album_id)
            return

        metadata[constants.TAG_KEY] = WorkflowEngine.apply_transition(shelf_name=shelf_name)
        metadata[constants.TAG_LOCKED_KEY] = self.manager.is_locked(album_id=album_id)

        log.debug("shelf name: %s, locked: %s", metadata[constants.TAG_KEY], metadata[constants.TAG_LOCKED_KEY])

    def build_processing_context_by_file(self, processor_type: int, file: File) -> Optional[ProcessingContext]:
        """ Build processing context from file """
        # utils.debug_file(file)

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

        name_from_tag_file = file_meta.get(constants.TAG_KEY, None)
        name_from_tag_file = utils.get_shelf_name_from_tag(name_from_tag_file)
        is_locked_file = file_meta.get(constants.TAG_LOCKED_KEY, None)

        log.debug(
                f"file: {file.filename}, album_id: {album_id}, name_from_path: "
                f"{name_from_path}, name_from_tag: {name_from_tag_file}, is_locked: {is_locked_file}"
        )

        return ProcessingContext(
                processor_type=processor_type,
                album_id=album_id,
                name_from_path=name_from_path,
                name_from_tag=name_from_tag_file,
                is_locked=is_locked_file
        )

    def build_processing_context_by_file_and_track(self, processor_type: int, track: Track, file: File) -> Optional[
        ProcessingContext]:
        """
        Build a processing context for a file based on its metadata and the track it belongs to.
        """
        processing_context_file = self.build_processing_context_by_file(processor_type=processor_type, file=file)
        if processing_context_file:
            return processing_context_file

        # TODO: I'm not quite sure yet, but I think we can ignore the files per track. Wenn dem so ist, dann
        # utils.debug_track(track)
        track_meta = getattr(track, "metadata", None)
        if not track_meta:
            return None

        album_id = track_meta.get(constants.MUSICBRAINZ_ALBUMID)
        if not album_id:
            return None

        names_from_path: set[str] = set()
        for file_by_track in track.files:
            log.debug('file_by_track: %s', file_by_track.filename)  # Extract shelf name from path
            names_from_path.union(
                    utils.get_shelf_name_from_path(
                            file_path=Path(file_by_track.filename), base_path=self.manager.base_path,
                    )
            )

        name_from_tag = track_meta.get(constants.TAG_KEY, None)
        name_from_tag = utils.get_shelf_name_from_tag(name_from_tag)
        is_locked = track_meta.get(constants.TAG_LOCKED_KEY, None)

        log.debug(
                f"Processing track: {track_meta['title']}, album_id: {album_id}, name_from_path: "
                f"{names_from_path}, name_from_tag: {name_from_tag}, is_locked: {is_locked}"
        )

        name_from_path = set(names_from_path).pop() if len(names_from_path) == 1 else "multiple"

        return ProcessingContext(
                processor_type=processor_type,
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
