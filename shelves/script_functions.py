"""
Script functions for the Shelves plugin.
"""

from __future__ import annotations

from typing import Any, Optional

from picard import log

from . import constants
from .exceptions import ShelfNotFoundException
from .manager import ShelfManager


def shelf(parser: Any) -> str:
    """
    Picard script function: `$shelf()`
    Returns the clean shelf name from the file's metadata, removing any internal suffixes.
    """
    album_id = parser.value_for_key(constants.MUSICBRAINZ_ALBUMID)
    if album_id is None:
        return ""

    try:
        shelf_info = ShelfManager().get_album_shelf(album_id=album_id)
        return shelf_info[0]
    except ShelfNotFoundException as e:
        log.error("Error retrieving shelf name for album id '%s': %s", album_id, e)
        return ""
