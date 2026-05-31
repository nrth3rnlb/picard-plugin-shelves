"""Typings for the Shelves plugin."""

from enum import Enum

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


MAX_SHELF_NAME_LENGTH: int = 30
MAX_WORD_COUNT: int = 3
ALBUM_INDICATORS: frozenset[str] = frozenset(["Vol.", "Volume", "Disc", "CD", "Part"])
INVALID_SHELF_NAME_CHARS: frozenset[str] = frozenset(["-"])
INVALID_SHELF_NAMES: frozenset[str] = frozenset([".", ".."])


class AlbumId(str):
    """Album identifier (MusicBrainz albumid)."""

    def __new__(cls, value: object) -> "AlbumId":
        if value is None:
            raise ValueError("AlbumId value cannot be None")
        return str.__new__(cls, str(value))


class ShelfName(str):
    """Name of a shelf."""

    def __new__(cls, value: object = "") -> "ShelfName":
        return str.__new__(cls, "" if value is None else str(value))
