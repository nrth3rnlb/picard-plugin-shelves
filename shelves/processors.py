# -*- coding: utf-8 -*-

"""
File processors for loading and saving shelf information.
"""

from __future__ import annotations

import traceback
from typing import Any, Dict

from picard import log

from .constants import ShelfConstants

def file_post_save_processor(file: Any, shelf_manager: Any) -> None:
    """
    Process a file after Picard has saved it.

    Args:
        file: Picard file object
        shelf_manager: ShelfManager instance
    """
    try:
        log.debug("%s: Processing file: %s", shelf_manager.plugin_name, file.filename)

        album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
        if album_id:
            shelf_manager.clear_album(album_id)

    except (KeyError, AttributeError, ValueError) as e:
        log.error("%s: Error in file processor: %s", shelf_manager.plugin_name, e)
        log.error("%s: Traceback: %s", shelf_manager.plugin_name, traceback.format_exc())


def file_post_load_processor(file: Any, shelf_manager: Any) -> None:
    """
    Process a file after Picard has scanned it.
    Args:
        file: Picard file object
        shelf_manager: ShelfManager instance
    """
    try:
        log.debug("%s: Processing file: %s", shelf_manager.plugin_name, file.filename)
        known_shelves = shelf_manager.utils.get_known_shelves()
        shelf = shelf_manager.utils.get_shelf_from_path(path=file.filename, known_shelves=known_shelves)

        # file.metadata[ShelfConstants.TAG_KEY] = file_shelf
        shelf_manager.add_known_shelf(shelf)
        log.debug("%s: Set shelf '%s' for: %s", shelf_manager.plugin_name, shelf, file.filename)

        album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
        if album_id:
            shelf_manager.vote_for_shelf(album_id, shelf)

    except (KeyError, AttributeError, ValueError) as e:
        log.error("%s: Error in file processor: %s", shelf_manager.plugin_name, e)
        log.error("%s: Traceback: %s", shelf_manager.plugin_name, traceback.format_exc())

def file_post_addition_to_track_processor(track, file, shelf_manager: Any) -> None:
    """
    Process a file after it has been added to a track.
    :param track:
    :param file:
    :param shelf_manager:
    :return:
    """
    try:

        log.debug("%s: (file_post_addition_to_track_processor) Processing file: %s", shelf_manager.plugin_name,
                  file.filename)
        known_shelves = shelf_manager.utils.get_known_shelves()
        shelf = shelf_manager.get_shelf_from_path(path=file.filename, known_shelves=known_shelves)

        shelf_manager.add_known_shelf(shelf)
        log.debug("%s: Set shelf '%s' for: %s", shelf_manager.plugin_name, shelf, file.filename)

        album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
        if album_id:
            shelf_manager.vote_for_shelf(album_id, shelf)
            file.metadata[ShelfConstants.TAG_KEY] = shelf
            track.metadata[ShelfConstants.TAG_KEY] = shelf

    except (KeyError, AttributeError, ValueError) as e:
        log.error("%s: Error in file processor: %s", shelf_manager.plugin_name, e)
        log.error("%s: Traceback: %s", shelf_manager.plugin_name, traceback.format_exc())

def file_post_removal_from_track_processor(track, file, shelf_manager: Any) -> None:
    """
    Process a file after it has been removed from a track.

    Args:
        track: Track object
        file: Picard file object
        shelf_manager: ShelfManager instance
    """
    log.debug("%s: (file_post_removal_from_track_processor) Processing file: %s", shelf_manager.plugin_name,
              file.filename)
    album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
    if album_id:
        shelf_manager.clear_album(album_id)


def set_shelf_in_metadata(
        _album: Any, metadata: Dict[str, Any], _track: Any, _release: Any, shelf_manager: Any
) -> None:
    """
    Set a shelf in track metadata from album assignment.

    Args:
        _album: Album object (unused, required by Picard API)
        metadata: Track metadata dictionary
        _track: Track object (unused, required by Picard API)
        _release: Release object (unused, required by Picard API)
        shelf_manager: ShelfManager instance
    """
    album_id = metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
    if not album_id:
        return

    log.debug("%s: set_shelf_in_metadata '%s'", shelf_manager.plugin_name, album_id)

    shelf_name = shelf_manager.get_album_shelf(album_id)
    if shelf_name is not None:
        metadata[ShelfConstants.TAG_KEY] = shelf_name
        log.debug("%s: Set shelf '%s' on track", shelf_manager.plugin_name, shelf_name)
