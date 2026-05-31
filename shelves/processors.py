"""
File processors for loading and saving shelf_name information.

Architecture:
- Context: Holds file/track data and extracted shelf names
- Strategy (ABC): Base class for processing strategies
- Concrete strategies: KnownFromPath, KnownFromTagAndManual, etc.
- Processors: Main processor facade with dependency injection support
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Sequence

from picard import log
from picard.file import File
from picard.track import Track

from . import runtime
from .contexts import ProcessingContext, TransitionContext
from .manager import ShelfManager
from .typings import AlbumId, ShelfName
from .typings import TagKey


class Strategy(ABC):
    """ """

    def __init__(self, manager: Optional[ShelfManager] = None):
        self.manager = manager or runtime.manager_instance()

    @abstractmethod
    def is_applicable(self, context: ProcessingContext) -> bool:
        raise NotImplementedError

    @abstractmethod
    def shelf_name(self, context: ProcessingContext) -> ShelfName:
        raise NotImplementedError


class StrategyManualUnset(Strategy):
    def is_applicable(self, context: ProcessingContext) -> bool:
        return context.processing_type == ProcessingContext.ProcessingType.UNSET

    def shelf_name(self, context: ProcessingContext) -> ShelfName:
        return context.name_from_path


class StrategyManualSet(Strategy):
    def is_applicable(self, context: ProcessingContext) -> bool:
        if context.processing_type != ProcessingContext.ProcessingType.SET:
            return False
        return context.name_to_set in self.manager.registered_shelf_names

    def shelf_name(self, context: ProcessingContext) -> ShelfName:
        return context.name_to_set


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

    def shelf_name(self, context: ProcessingContext) -> ShelfName:
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

        return True

    def shelf_name(self, context: ProcessingContext) -> ShelfName:
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

    def shelf_name(self, context: ProcessingContext) -> ShelfName:
        return context.name_from_path


class Processors:
    """
    Handles the processing of file metadata and shelf assignments using various strategies.

    This class encapsulates the logic for updating, locking, unlocking, and applying shelf
    assignments to files and tracks based on metadata and predefined strategies. It facilitates
    managing metadata consistency between file paths, tags, and application's shelf naming rules.

    :ivar STRATEGY_ORDER: The ordered list of strategies used for processing files.
    :type STRATEGY_ORDER: Sequence[type[Strategy]]
    :ivar manager: Instance of ShelfManager used for managing shelf assignments.
    :type manager: ShelfManager
    :ivar strategies: List of strategy instances initialized using STRATEGY_ORDER and the ShelfManager.
    :type strategies: list[Strategy]
    """

    STRATEGY_ORDER: Sequence[type[Strategy]] = [
        StrategyManualUnset,
        StrategyManualSet,
        StrategyKnownIdenticalNames,
        StrategyKnownNameFromPathDiffersFromTag,
        StrategyUnknownNameFromPath,
    ]

    def __init__(self, manager: Optional[ShelfManager] = None):
        self.manager = manager or runtime.manager_instance()
        self.strategies = [cls(self.manager) for cls in self.STRATEGY_ORDER]

    def action_unset_processor(self, file: File) -> None:
        context = self.build_processing_context(
            file=file,
            processing_type=ProcessingContext.ProcessingType.UNSET,
        )
        log.debug("action_unset_processor: %s", context)
        for strategy in self.strategies:
            if strategy.is_applicable(context):
                self.manager.unset_name(album_id=context.album_id)
                break

    def action_set_processor(self, file: File, shelf_name: ShelfName) -> None:

        context = self.build_processing_context(
            file=file,
            name_to_set=shelf_name,
            processing_type=ProcessingContext.ProcessingType.SET,
        )
        log.debug("action_set_processor: %s", context)
        for strategy in self.strategies:
            if strategy.is_applicable(context):
                self.manager.set_name(
                    album_id=context.album_id,
                    shelf_name=strategy.shelf_name(context),
                )
                break

    def action_lock_processor(self, file: File) -> None:

        context = self.build_processing_context(
            file=file,
            processing_type=ProcessingContext.ProcessingType.LOCK,
        )
        log.debug("action_lock_processor: %s", context)
        for strategy in self.strategies:
            if strategy.is_applicable(context):
                self.manager.lock(
                    album_id=context.album_id,
                )
                break

    def action_unlock_processor(self, file: File) -> None:

        context = self.build_processing_context(
            file=file,
            processing_type=ProcessingContext.ProcessingType.UNLOCK,
        )
        log.debug("action_unlock_processor: %s", context)
        for strategy in self.strategies:
            if strategy.is_applicable(context):
                self.manager.unlock(
                    album_id=context.album_id,
                )
                break

    def file_post_load_processor(self, file: File) -> None:
        """
        A file has been loaded. From this, the following can be determined:

        Album ID
        Shelf from path
        Shelf from tag

        Then a decision should be made:
        If the album does not yet have a shelf name: set one.
        If the tag and path are consistent: set/confirm.
        If the path and tag are different: use a clear priority rule.
        If the assignment is locked: do not automatically overwrite.
        """

        context = self.build_processing_context(
            file=file,
            processing_type=ProcessingContext.ProcessingType.LOAD,
        )
        log.debug("file_post_load_processor: %s", context)
        self.process_context(context)

    def file_post_save_processor(self, file: File) -> None:
        """Process a file after it has been saved."""

        context = self.build_processing_context(
            file=file,
            processing_type=ProcessingContext.ProcessingType.SAVE,
        )
        log.debug("file_post_save_processor: %s", context)
        self.process_context(context)

    def apply_strategy(self, context: ProcessingContext, strategy: Strategy) -> None:
        shelf_name = strategy.shelf_name(context)

        if context.processing_type == ProcessingContext.ProcessingType.SET:
            self.manager.set_name(
                album_id=context.album_id,
                shelf_name=shelf_name,
            )
            return

        if context.processing_type == ProcessingContext.ProcessingType.UNSET:
            self.manager.unset_name(album_id=context.album_id)
            return

        if context.processing_type == ProcessingContext.ProcessingType.LOCK:
            self.manager.lock(album_id=context.album_id)
            return

        if context.processing_type == ProcessingContext.ProcessingType.UNLOCK:
            self.manager.unlock(album_id=context.album_id)
            return

        if context.processing_type in {
            ProcessingContext.ProcessingType.LOAD,
            ProcessingContext.ProcessingType.ADD,
            ProcessingContext.ProcessingType.SAVE,
        }:
            self.manager.set_name(
                album_id=context.album_id,
                shelf_name=shelf_name,
            )
            return

        if context.processing_type == ProcessingContext.ProcessingType.REMOVE:
            self.manager.unset_name(album_id=context.album_id)
            return

    # noinspection PyUnusedLocal
    def file_post_addition_to_track_processor(
        self,
        track: Track,
        file: File,
    ) -> None:
        """Process a file after it has been added to a track."""

        context = self.build_processing_context(
            file=file,
            processing_type=ProcessingContext.ProcessingType.ADD,
        )
        log.debug("file_post_addition_to_track_processor: %s", context)
        self.process_context(context)

    # noinspection PyUnusedLocal
    def file_post_removal_from_track_processor(self, track: Track, file: File) -> None:
        """Process a file after it has been removed from a track."""

        context = self.build_processing_context(
            file=file,
            processing_type=ProcessingContext.ProcessingType.REMOVE,
        )
        log.debug("file_post_removal_from_track_processor: %s", context)
        self.process_context(context)

    def process_context(self, context: ProcessingContext) -> None:
        for strategy in self.strategies:
            if strategy.is_applicable(context):
                self.apply_strategy(context=context, strategy=strategy)
                break

    def track_metadata_processor(
        self,
        _album: Optional[Any],
        metadata: dict[str, Any],
        _track: Optional[Any],
        _release: Optional[Any],
    ) -> None:
        """Set a shelf name in track metadata from album's shelf assignment."""
        album_id = metadata.get(TagKey.MUSICBRAINZ_ALBUM_ID, "")
        transition = runtime.transition_instance()

        context: TransitionContext = transition.transition_to(
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

    def build_processing_context(
        self,
        file: File,
        processing_type: ProcessingContext.ProcessingType,
        name_to_set: Optional[ShelfName] = ShelfName(),
    ) -> ProcessingContext:

        from . import utils

        # utils.debug_track(file)
        # Extract shelf name from path
        name_from_path: ShelfName = ShelfName(
            utils.get_name_from_path(
                file_path=Path(str(file.filename)),
                base_path=self.manager.base_path,
            )
        )
        album_id = AlbumId(file.metadata.get(TagKey.MUSICBRAINZ_ALBUM_ID))
        name_from_tag = ShelfName(file.metadata.get(TagKey.SHELF))

        return ProcessingContext(
            processing_type=processing_type,
            album_id=album_id,
            name_from_path=name_from_path,
            name_from_tag=name_from_tag,
            name_to_set=name_to_set or ShelfName(),
        )
