# -*- coding: utf-8 -*-

"""
Script functions for the Shelves plugin.
"""

from __future__ import annotations

from typing import Any, Optional

from picard import config, log

from . import get_album_shelf
from .constants import ShelfConstants
from .exeptions import ShelfNotFoundException

PLUGIN_NAME = "Shelves"


def _resolve_shelf(context: Any) -> str:
    """
    Returns the shelf name, prioritizing manual overrides and otherwise applying workflow transition.
    """
    album_id = context.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
    shelf, shelf_source = get_album_shelf(context.get(ShelfConstants.MUSICBRAINZ_ALBUMID))
    if shelf is None:
        # Fallback
        shelf = context.metadata[ShelfConstants.TAG_KEY]
        shelf_source = ShelfConstants.SHELF_SOURCE_FALLBACK

    if shelf is None and shelf_source == ShelfConstants.SHELF_SOURCE_FALLBACK:
        raise ShelfNotFoundException(album_id=album_id, message="Shelf could not be determined.")

    log.debug("Shelf: %s, source: %s", shelf, shelf_source)

    # Workflow enabled?
    is_workflow = config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY]  # type: ignore[index]
    if not is_workflow:
        return shelf
    if shelf_source in (ShelfConstants.SHELF_SOURCE_MANUAL, ShelfConstants.SHELF_SOURCE_FALLBACK):
        return shelf

    workflow_stage_1 = config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY]  # type: ignore[index]
    workflow_stage_2 = config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY]  # type: ignore[index]

    # Apply transition only if not manually overridden and not fallback
    if shelf == workflow_stage_1 or workflow_stage_1 == ShelfConstants.WORKFLOW_STAGE_1_WILDCARD:
        log.debug(
            "%s: Applying workflow transition: '%s' -> '%s'",
            PLUGIN_NAME,
            workflow_stage_1,
            workflow_stage_2,
        )
        return workflow_stage_2

    return shelf


def func_shelf(parser: Any) -> Optional[str]:
    """
    Picard script function: `$shelf()`
    If the album ID cannot be determined, it is most likely because the Picard's settings
    dialog was open and the changes should be saved.
    This also triggers the functions, but they have no context to work with.
    """
    album_id = parser.context.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
    if album_id is not None:
        return _resolve_shelf(parser.context)
    return None
