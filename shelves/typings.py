"""Typings for the Shelves plugin."""

from enum import Enum, IntEnum


class VotingType(IntEnum):
    """Voting types for the Shelves plugin."""

    UP = 1
    DOWN = 2
    INITIAL = UP | DOWN
    LOCK = 4
    UNLOCK = 8


class ConfigKey(str, Enum):
    """Configuration keys for the Shelves plugin."""

    MOVE_FILES_TO = "move_files_to"
    ACTIVE_TAB = "shelves_active_tab"
    ALBUM_SHELF = "shelves_album_shelf"
    KNOWN_SHELVES = "shelves_known_shelves"
    STAGE_1_INCLUDES_NON_SHELVES = "shelves_stage_1_includes_non_shelves"
    WORKFLOW_ENABLED = "shelves_workflow_enabled"
    WORKFLOW_STAGE_1_SHELVES = "shelves_workflow_stage_1_shelves"
    WORKFLOW_STAGE_2_SHELVES = "shelves_workflow_stage_2_shelves"


class TagKey(str, Enum):
    """Tag keys for the Shelves plugin."""

    MUSICBRAINZ_ALBUM_ID = "musicbrainz_albumid"
    SHELF = "shelf"
    SHELF_LOCKED = "shelf_locked"
