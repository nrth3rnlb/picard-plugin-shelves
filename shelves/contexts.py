from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .typings import ProcessingType, TransitionType


@dataclass
class ProcessingContext:
    """Context for shelf processing strategies."""

    processing_type: ProcessingType
    album_id: str
    name_from_path: str
    name_from_tag: str
    processing_name: Optional[str]
    is_locked: bool


@dataclass
class TransitionContext:
    """Context for shelf workflow transitions."""

    transition_type: TransitionType
    strategy: str
    album_id: str
    shelf_name: str
