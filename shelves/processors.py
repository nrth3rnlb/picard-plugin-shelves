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

from picard import config, log
from picard.file import File
from picard.track import Track

from . import runtime
from .contexts import ProcessingContext, TransitionContext
from .manager import AlbumId, ShelfManager, ShelfName
from .typings import ConfigKey, TagKey


class Strategy(ABC):
    """ """

    def __init__(self, manager: Optional[runtime.ShelfManager] = None):
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
        """Process a file after it has been loaded."""

        context = self.build_processing_context(
            file=file,
            processing_type=ProcessingContext.ProcessingType.LOAD,
        )
        log.debug("file_post_load_processor: %s", context)
        for strategy in self.strategies:
            if strategy.is_applicable(context):
                break

    def file_post_save_processor(self, file: File) -> None:
        """Process a file after it has been saved."""

        context = self.build_processing_context(
            file=file,
            processing_type=ProcessingContext.ProcessingType.SAVE,
        )
        log.debug("file_post_save_processor: %s", context)
        for strategy in self.strategies:
            if strategy.is_applicable(context):
                break

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
        for strategy in self.strategies:
            if strategy.is_applicable(context):
                break

    # noinspection PyUnusedLocal
    def file_post_removal_from_track_processor(self, track: Track, file: File) -> None:
        """Process a file after it has been removed from a track."""

        context = self.build_processing_context(
            file=file,
            processing_type=ProcessingContext.ProcessingType.REMOVE,
        )
        log.debug("file_post_removal_from_track_processor: %s", context)
        for strategy in self.strategies:
            if strategy.is_applicable(context):
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
        metadata[TagKey.SHELF_LOCKED] = self.manager.get_shelf_locked(album_id=album_id)

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
            utils.get_shelf_name_from_path(
                file_path=Path(str(file.filename)),
                base_path=self.manager.base_path,
            )
        )
        album_id: AlbumId = AlbumId(file.metadata.get(TagKey.MUSICBRAINZ_ALBUM_ID, ""))
        name_from_tag: ShelfName = ShelfName(
            file.metadata.get(TagKey.SHELF, ShelfName())
        )

        return ProcessingContext(
            processing_type=processing_type,
            album_id=album_id,
            name_from_path=name_from_path,
            name_from_tag=name_from_tag,
            name_to_set=name_to_set or ShelfName(),
        )
