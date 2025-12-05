# -*- coding: utf-8 -*-

"""
File processors for loading and saving shelf information.

The code in shelves/processors.py processes files after loading, adding or removing
them in Picard to assign shelves based on the file path, and avoids redundant calls
to get_known_shelves() by retrieving known_shelves once and
passing it to ShelfUtils.get_shelf_from_path. This reduces unnecessary calculations
and improves performance when processing multiple files.
The methods file_post_load_processor and file_post_addition_to_track_processor retrieve
known_shelves and use them directly.
"""

from __future__ import annotations

import traceback
from typing import Any, Dict, Optional

from picard import config, log

from . import clear_album, PLUGIN_NAME, vote_for_shelf, get_album_shelf
from .constants import ShelfConstants
from .utils import ShelfUtils


def _apply_workflow_transition(shelf: str) -> str:
    """
    Applies the workflow transition to a shelf name if the workflow is enabled.
    Returns the original shelf if it is None/empty, the workflow is disabled, keys are missing,
    or an error occurs while reading configuration.
    """
    # Guard: if the shelf is None or empty, leave it unchanged
    if not shelf:
        return shelf

    try:
        # Safely read config values using .get to avoid KeyError if keys are missing.
        workflow_stage_1 = config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY]
        workflow_stage_2 = config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY]

        # Determine whether the workflow feature is explicitly enabled.
        workflow_enabled = config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY]

        if workflow_enabled:
            # Apply the transition when the shelf matches stage 1 or when stage 1 is the wildcard.
            if shelf == workflow_stage_1 or workflow_stage_1 == ShelfConstants.WORKFLOW_STAGE_1_WILDCARD:
                log.debug(
                    "%s: Applying workflow transition: '%s' -> '%s'",
                    PLUGIN_NAME,
                    shelf,
                    workflow_stage_2,
                )
                return workflow_stage_2

        return shelf

    except Exception as e:
        # On any unexpected error reading config, leave the shelf unchanged and log details.
        log.debug("%s: Failed to evaluate workflow transition; leaving shelf unchanged: %s", PLUGIN_NAME, e)
        log.debug("%s: Traceback: %s", PLUGIN_NAME, traceback.format_exc())
        return shelf


def file_post_save_processor(file: Any) -> None:
    """
    Process a file after Picard has saved it.

    Args:
        file: Picard file object
    """
    try:
        log.debug("%s: Processing file: %s", PLUGIN_NAME, file.filename)

        album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
        if album_id:
            clear_album(album_id)

    except (KeyError, AttributeError, ValueError) as e:
        log.error("%s: Error in file processor: %s", PLUGIN_NAME, e)
        log.error("%s: Traceback: %s", PLUGIN_NAME, traceback.format_exc())


def _set_metadata(obj: Any, key: str, value: Any, label: str) -> None:
    meta = getattr(obj, "metadata", None)
    filename = getattr(obj, "filename", "<unknown>")
    if meta is None:
        log.debug("%s: %s metadata missing for: %s", PLUGIN_NAME, label, filename)
        return
    try:
        meta[key] = value
    except TypeError as e:
        log.debug("%s: Failed to set %s metadata (non-subscriptable) for: %s; %s", PLUGIN_NAME, label, filename, e)
        log.debug("%s: Traceback: %s", PLUGIN_NAME, traceback.format_exc())


def file_post_load_processor(file: Any) -> None:
    """
    Process a file after Picard has scanned it.
    Args:
        file: Picard file object
    """
    file_post_addition_to_track_processor(file=file, track=None)


def file_post_addition_to_track_processor(track: Optional[Any], file: Any) -> None:
    """
    Process a file after it has been added to a track.
    Args:
        track: Track object
        file: Picard file object
    """
    try:
        log.debug("%s: (file_post_addition_to_track_processor) Processing file: %s", PLUGIN_NAME,
                  file.filename)
        known_shelves = ShelfUtils.get_known_shelves()
        shelf = ShelfUtils.get_shelf_from_path(path=file.filename, known_shelves=known_shelves)

        # Apply workflow transition
        shelf = _apply_workflow_transition(shelf)

        ShelfUtils.add_known_shelf(shelf)
        log.debug("%s: Set shelf '%s' for: %s", PLUGIN_NAME, shelf, file.filename)

        # Preserve original behavior: surface missing metadata as an AttributeError
        file_meta = getattr(file, "metadata", None)
        if file_meta is None:
            raise AttributeError("file.metadata missing for: %s" % getattr(file, "filename", "<unknown>"))

        # Use the same safe metadata setter for file and track
        _set_metadata(file, ShelfConstants.TAG_KEY, shelf, "file")
        if track is not None:
            _set_metadata(track, ShelfConstants.TAG_KEY, shelf, "track")

        album_id = file_meta.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
        if album_id:
            vote_for_shelf(album_id, shelf)

    except (KeyError, AttributeError, ValueError) as e:
        log.error("%s: Error in file processor: %s", PLUGIN_NAME, e)
        log.error("%s: Traceback: %s", PLUGIN_NAME, traceback.format_exc())


def file_post_removal_from_track_processor(track: Any, file: Any) -> None:
    log.debug("%s: (file_post_removal_from_track_processor) Processing file: %s", PLUGIN_NAME,
              file.filename)
    album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
    if album_id:
        clear_album(album_id)


def set_shelf_in_metadata(
        _album: Any, metadata: Dict[str, Any], _track: Any, _release: Any
) -> None:
    """
    Set a shelf in track metadata from album assignment.

    Args:
        _album: Album object (unused, required by Picard API)
        metadata: Track metadata dictionary
        _track: Track object (unused, required by Picard API)
        _release: Release object (unused, required by Picard API)
    """
    album_id = metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
    if not album_id:
        return

    log.debug("%s: set_shelf_in_metadata '%s'", PLUGIN_NAME, album_id)

    shelf_name = get_album_shelf(album_id)
    if shelf_name is not None:
        metadata[ShelfConstants.TAG_KEY] = shelf_name
        log.debug("%s: Set shelf '%s' on track", PLUGIN_NAME, shelf_name)
