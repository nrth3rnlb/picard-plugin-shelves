# -*- coding: utf-8 -*-

"""
Constants for the Shelves plugin.
"""

from __future__ import annotations


class ShelfConstants:
    """Central constants for the Shelves plugin."""

    # noinspection SpellCheckingInspection
    MUSICBRAINZ_ALBUMID = "musicbrainz_albumid"
    # noinspection SpellCheckingInspection
    TAG_KEY = "shelf"

    # Validation limits
    # TODO Make configurable
    MAX_SHELF_NAME_LENGTH = 30
    MAX_WORD_COUNT = 3
    INVALID_PATH_CHARS = frozenset(["<", ">", "|", ":", "*", "?", '"', "/", "\\", "'"])
    ALBUM_INDICATORS = frozenset(["Vol.", "Volume", "Disc", "CD", "Part"])

    # Config keys
    CONFIG_MOVE_FILES_TO_KEY = "move_files_to"
    CONFIG_ACTIVE_TAB = "shelves_active_tab"
    CONFIG_ALBUM_SHELF_KEY = "shelves_album_shelf"
    CONFIG_KNOWN_SHELVES_KEY = "shelves_known_shelves"
    CONFIG_RENAME_SNIPPET_SKELETON_KEY = "shelves_rename_snippet_skeleton"
    CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY = "shelves_stage_1_includes_non_shelves"
    CONFIG_WORKFLOW_ENABLED_KEY = "shelves_workflow_enabled"
    CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY = "shelves_workflow_stage_1_shelves"
    CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY = "shelves_workflow_stage_2_shelves"

    # The value set manually by the user is used
    SHELF_SOURCE_MANUAL = "manual"
    MANUAL_SHELF_SUFFIX = f"; {SHELF_SOURCE_MANUAL}"
    # Value determined by voting is used
    SHELF_SOURCE_VOTES = "_votes"
    # If nothing else works, use the value in TAG_KEY
    SHELF_SOURCE_FALLBACK = "fallback"


# Default configuration values
DEFAULT_SHELVES = {
    ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: "",
    ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: "",
}
