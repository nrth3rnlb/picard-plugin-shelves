"""
Constants for the Shelves plugin.
"""

from __future__ import annotations

from enum import StrEnum

# Validation limits
# TODO Make configurable
MAX_SHELF_NAME_LENGTH: int = 30
MAX_WORD_COUNT: int = 3
INVALID_SHELF_NAME_CHARS: set[str] = set()
INVALID_SHELF_NAMES: frozenset[str] = frozenset([".", ".."])
ALBUM_INDICATORS: frozenset[str] = frozenset(["Vol.", "Volume", "Disc", "CD", "Part"])

# noinspection SpellCheckingInspection
RENAME_SNIPPET: str = """$set(_shelffolder,$shelf())
$set(_shelffolder,$if($not($eq(%_shelffolder%,)),%_shelffolder%/))

%_shelffolder%
$if2(%albumartist%,%artist%)/%album%/%title%"""


class ConfigKey(StrEnum):
    """Configuration keys for the Shelves plugin."""

    MOVE_FILES_TO = "move_files_to"
    CONFIG_ACTIVE_TAB = "shelves_active_tab"
    ALBUM_SHELF = "shelves_album_shelf"
    KNOWN_SHELVES = "shelves_known_shelves"
    STAGE_1_INCLUDES_NON_SHELVES = "shelves_stage_1_includes_non_shelves"
    WORKFLOW_ENABLED = "shelves_workflow_enabled"
    WORKFLOW_STAGE_1_SHELVES = "shelves_workflow_stage_1_shelves"
    WORKFLOW_STAGE_2_SHELVES = "shelves_workflow_stage_2_shelves"


class TagKey(StrEnum):
    """Tag keys for the Shelves plugin."""

    MUSICBRAINZ_ALBUMID = "musicbrainz_albumid"
    SHELF = "shelf"
    SHELF_LOCKED = "shelf_locked"
