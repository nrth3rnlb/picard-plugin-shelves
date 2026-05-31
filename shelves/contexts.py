from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

from .typings import AlbumId, ShelfName


@dataclass
class ProcessingContext:
    """Context for shelf processing strategies."""

    class ProcessingType(IntEnum):
        """Processing types for shelf processing strategies."""

        LOAD = 1
        ADD = 2
        SET = 4
        SAVE = 8
        REMOVE = 16
        UNSET = 32
        LOCK = 64
        UNLOCK = 128

    processing_type: ProcessingType
    album_id: AlbumId
    name_from_path: ShelfName
    name_from_tag: ShelfName
    name_to_set: ShelfName


@dataclass
class TransitionContext:
    """Context for shelf workflow transitions."""

    class TransitionType(IntEnum):
        """Transition types for shelf workflow."""

        TO_STAGE_1 = 1
        TO_STAGE_2 = 2

    transition_type: TransitionType
    strategy: Optional[str]
    album_id: AlbumId
    shelf_name: ShelfName
