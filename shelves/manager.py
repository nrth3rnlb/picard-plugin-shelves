"""
Shelf manager for tracking album shelf name assignments.

This module provides a component-based architecture for managing shelf assignments:
- ShelfRegistry: Manages shelf names and base path configuration
- ShelfAssignmentEngine: Handles voting logic and shelf determination
- ShelfLockManager: Manages manual overrides and locks
- ShelfValidator: Validates shelf names using heuristics
- ShelfManager: Facade pattern providing a unified interface (singleton)

The ShelfManager supports dependency injection for testing purposes.
"""

import threading
from collections import Counter
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Optional, Union

from picard import log

from . import utils
from .contexts import ProcessingContext
from .typings import VotingType

MAX_SHELF_NAME_LENGTH: int = 30
MAX_WORD_COUNT: int = 3
ALBUM_INDICATORS: frozenset[str] = frozenset(["Vol.", "Volume", "Disc", "CD", "Part"])
INVALID_SHELF_NAME_CHARS: set[str] = set()
INVALID_SHELF_NAMES: frozenset[str] = frozenset([".", ".."])


class ShelfRegistry:
    """
    Registry for shelf names and base path configuration.

    Manages the set of known shelf names and the base path for shelf directories.
    Provides validation when setting shelf names.
    """

    def __init__(self):
        """Initialize the shelf registry with empty names and default base path."""
        self._shelf_names: set[str] = set()
        self._base_path: Path = Path(".")

    @property
    def shelf_names(self) -> set[str]:
        """Get the set of known shelf names."""
        return self._shelf_names

    @shelf_names.setter
    def shelf_names(self, names: set[str]):
        """
        Set the list of shelf names, filtering out invalid names.

        :param names: Set of shelf names to register.
        """
        self._shelf_names = set(
            filter(
                lambda name: utils.validate_shelf_name(
                    name,
                    ALBUM_INDICATORS,
                    INVALID_SHELF_NAMES,
                    INVALID_SHELF_NAME_CHARS,
                )[0],
                names,
            ),
        )

    @property
    def base_path(self) -> Path:
        """Get the base path for shelf directories."""
        return self._base_path

    @base_path.setter
    def base_path(self, value: Union[str, Path]):
        """
        Set the base path for shelf directories.

        :param value: Path as string or Path object.
        """
        if isinstance(value, str):
            self._base_path = Path(value).resolve()
        else:
            self._base_path = value.resolve()

    def add_shelf_names(self, names: Union[set[str], str]) -> None:
        """
        Add shelf names to the registry.

        :param names: Single shelf name or set of shelf names to add.
        """
        if isinstance(names, str):
            names = {names}
        self.shelf_names = self.shelf_names.union(names)
        log.debug("Added shelf names: %s", names)
        log.debug("Current shelf names: %s", self.shelf_names)

    def remove_shelf_names(self, names: Union[set[str], str]) -> None:
        """Remove shelf names from the registry."""
        if isinstance(names, str):
            names = {names}
        self.shelf_names = self.shelf_names.difference(names)
        log.debug("Removed shelf names: %s", names)
        log.debug("Current shelf names: %s", self.shelf_names)

    def intersect_shelf_names(self, names: Union[set[str], str]) -> None:
        """Intersect shelf names with the provided set."""
        if isinstance(names, str):
            names = {names}
        self.shelf_names = self.shelf_names.intersection(names)
        log.debug("Intersected shelf names: %s", names)
        log.debug("Current shelf names: %s", self.shelf_names)


class ShelfAssignmentEngine:
    """
    Engine for voting-based shelf assignment.

    Manages weighted votes from different sources (file paths, tags, etc.)
    and determines the winning shelf for each album based on vote counts.
    Detects conflicts when files from the same album suggest different shelves.
    """

    def __init__(self, registry: ShelfRegistry):
        """Initialize the assignment engine."""
        self.registry = registry
        self._shelf_votes: dict[str, Counter] = {}
        self._shelf_processor: dict[str, ProcessingContext.ProcessingType] = {}
        self._lock = threading.Lock()

    def vote(
        self,
        album_id: str,
        shelf_name: str,
        voting_type: VotingType = VotingType.INITIAL,
        shelf_locked: bool = False,
    ):
        """
        Executes a specific voting operation (upvote, downvote, or initial vote) for a given album on a specified shelf.
        The operation is determined based on the `voting_type` parameter.
        """
        if shelf_locked:
            log.debug(
                "Shelf %s is locked, fallback to initial voting: %s",
                shelf_name,
                album_id,
            )
            voting_type = VotingType.INITIAL

        dispatch = {
            VotingType.DOWN: partial(
                self._downvote, album_id=album_id, shelf_name=shelf_name
            ),
            VotingType.UP: partial(
                self._upvote, album_id=album_id, shelf_name=shelf_name
            ),
            VotingType.INITIAL: partial(
                self._init_voting, album_id=album_id, shelf_name=shelf_name
            ),
            VotingType.LOCK: partial(
                self._init_voting, album_id=album_id, shelf_name=shelf_name
            ),
            VotingType.UNLOCK: partial(
                self._init_voting, album_id=album_id, shelf_name=shelf_name
            ),
        }
        dispatch[voting_type]()

    def _init_voting(self, album_id, shelf_name) -> None:
        """
        Initializes the voting system for a specific album and shelf. If the album
        ID does not exist in the voting structure, or if the shelf name has
        not been registered under that album, it initializes the corresponding
        entry to track votes.

        :param album_id: The unique identifier for the album.
        :param shelf_name: The name of the shelf associated with the album.
        :return: This method does not return a value.
        """
        if album_id not in self._shelf_votes:
            log.debug("Initializing voting data for album %s", album_id)
            self._shelf_votes[album_id] = Counter()
        if shelf_name not in self._shelf_votes[album_id]:
            log.debug("Initializing vote count for shelf %s", shelf_name)
            self._shelf_votes[album_id][shelf_name] = 0

    def _upvote(self, album_id, shelf_name) -> None:
        """
        Handles the upvoting of a specific album by its ID associated with a specified shelf.

        This method processes the voting action by initializing the voting operation for
        the specified album and shelf name. The vote is then registered within the internal
        data structure that tracks shelf votes. Designed to work with internal components
        only.
        """
        self._init_voting(album_id=album_id, shelf_name=shelf_name)
        log.debug("Incrementing vote count for %s", shelf_name)
        self._shelf_votes[album_id].update({shelf_name})

    def _downvote(self, album_id, shelf_name) -> None:
        """
        Reduces the vote count for a specific shelf associated with an album. This method
        ensures that the initialization of voting data is done before attempting the
        vote decrement. If the specified shelf exists within the album's recorded
        vote data, the vote count for that shelf will be decreased.

        The number of votes for a shelf cannot be less than 0.

        This function assumes that votes are managed through a data structure
        in which each album is linked to its associated shelves and their respective
        vote counts.
        """
        self._init_voting(album_id=album_id, shelf_name=shelf_name)
        if shelf_name in self._shelf_votes[album_id].elements():
            log.debug("Decrementing vote count for %s", shelf_name)
            self._shelf_votes[album_id].subtract({shelf_name})

    def get_shelf_name_by_votes(self, album_id) -> Optional[str]:
        """
        Get the most commonly voted shelf name for a given album.

        This method retrieves the most frequently voted shelf name associated with the
        provided album ID. If no votes are present for the album, the method returns None.
        It also logs the album ID, the selected shelf name, and the current vote counts
        for the album for debugging purposes.
        """
        if album_id not in self._shelf_votes:
            return None
        most_common = self._shelf_votes[album_id].most_common(1)
        if not most_common:
            return None
        shelf_name, count = most_common[0]
        log.debug("%s, %s, %s", album_id, shelf_name, self._shelf_votes[album_id])
        return shelf_name

    def get_processing_type(
        self, album_id
    ) -> Optional[ProcessingContext.ProcessingType]:
        """Determine the processor type based on vote counts."""
        return self._shelf_processor.get(album_id, None)

    def get_shelf_name(
        self,
        album_id: str,
    ) -> Optional[str]:
        """
        Retrieves the shelf name corresponding to a given album ID. The method first tries to
        fetch the shelf name based on votes associated with the given album. If no shelf name
        can be determined, it returns None.
        """
        with self._lock:
            if shelf_name := self.get_shelf_name_by_votes(album_id):
                return shelf_name

        return None

    def clear_album(self, album_id: str) -> None:
        """Clear all votes and assignments for an album."""
        self._shelf_votes.pop(album_id, None)


class ShelfLockManager:
    """
    Manager for manual shelf overrides and locks.

    Handles user-initiated shelf assignments and locked shelf states.
    Locked shelves prevent automatic reassignment through voting.
    Maintains shelf state including source and lock status for each album.
    """

    def __init__(self, assignment_engine: ShelfAssignmentEngine):
        """
        Initialize the lock manager.

        :param assignment_engine: ShelfAssignmentEngine instance for vote clearing.
        """
        self.assignment_engine = assignment_engine
        self._shelf_locked: Dict[str, bool] = {}

    def lock(self, album_id: str, shelf_name: str) -> None:
        """Set the manual override/lock for an album's shelf assignment."""
        self._shelf_locked[album_id] = True
        log.debug("Locking album %s to shelf %s", album_id, shelf_name)
        self.assignment_engine.vote(
            album_id=album_id, shelf_name=shelf_name, voting_type=VotingType.LOCK
        )

    def unlock(self, album_id: str, shelf_name: str) -> None:
        """Clear the manual override/lock for an album's shelf assignment."""
        self._shelf_locked[album_id] = False
        log.debug("Unlocking album %s from shelf %s", album_id, shelf_name)
        self.assignment_engine.vote(
            album_id=album_id, shelf_name=shelf_name, voting_type=VotingType.UNLOCK
        )

    def is_locked(self, album_id: str) -> bool:
        """Check if an album's shelf assignment is locked."""
        log.debug(
            "Lock status for album %s: %s",
            album_id,
            self._shelf_locked.get(album_id, False),
        )
        return self._shelf_locked.get(album_id, False)


class ShelfValidator:
    """
    Validator for shelf names using heuristics.

    Applies heuristics to detect whether a string is likely a valid shelf name
    or an accidental album/artist name. Checks against known shelf names,
    length limits, word counts, and suspicious patterns.
    """

    def __init__(self, registry: "ShelfRegistry"):
        """
        Initialize the validator.

        :param registry: ShelfRegistry instance for checking known shelf names.
        """
        self.registry = registry

    def is_likely_shelf_name(self, name: str) -> tuple[bool, Optional[str]]:
        """
        Check if a name is likely to be a valid shelf name using heuristics.

        :param name: The name to validate.
        :return: Tuple of (is_valid, reason_if_invalid)
        """
        if not name:
            return False, "Empty name"

        if name in self.registry.shelf_names:
            return True, None

        # Heuristics for suspicious names
        suspicious_reasons = []

        # Contains ` - ` (typical for "Artist - Album")
        if " - " in name:
            suspicious_reasons.append(
                "contains ' - ' (typical for 'Artist - Album' format)",
            )

        # Too long
        if len(name) > MAX_SHELF_NAME_LENGTH:
            suspicious_reasons.append(f"too long ({len(name)} chars)")

        # Too many words
        word_count = len(name.split())
        if word_count > MAX_WORD_COUNT:
            suspicious_reasons.append(f"too many words ({word_count})")

        # Contains album indicators
        if any(indicator in name for indicator in ALBUM_INDICATORS):
            suspicious_reasons.append("contains album indicator (Vol., Disc, etc.)")

        if suspicious_reasons:
            return False, "; ".join(suspicious_reasons)

        return True, None


@dataclass(frozen=True)
class ShelfManagerSettings:
    """Configuration required to initialize shelf management."""

    base_path: Path
    shelf_names: set[str]


class ShelfManager:
    """
    Facade for shelf management, delegating to specialized components.
    """

    def __init__(
        self,
        registry: Optional[ShelfRegistry] = None,
        assignment_engine: Optional[ShelfAssignmentEngine] = None,
        lock_manager: Optional[ShelfLockManager] = None,
        validator: Optional[ShelfValidator] = None,
        settings: Optional[ShelfManagerSettings] = None,
    ):
        """
        Initialize ShelfManager with optional dependency injection.
        """

        self._registry = registry or ShelfRegistry()

        if settings is not None:
            self._registry.base_path = settings.base_path
            self._registry.shelf_names = set(settings.shelf_names)

        self._assignment_engine = assignment_engine or ShelfAssignmentEngine(
            self._registry,
        )
        self._lock_manager = lock_manager or ShelfLockManager(
            self._assignment_engine,
        )
        self._validator = validator or ShelfValidator(self._registry)

    @property
    def registered_shelf_names(self) -> set[str]:
        """Get the list of shelf names."""
        return self._registry.shelf_names

    @property
    def base_path(self) -> Path:
        """Get the base path."""
        return self._registry.base_path

    def vote(
        self,
        album_id: str,
        shelf_name: str,
        voting_type: VotingType = VotingType.INITIAL,
        shelf_locked: bool = False,
    ):
        """
        Registers a voting action for the specified album within the given shelf. This function allows
        the system to handle voting operations based on the provided album identifier, shelf name,
        and voting type.
        """

        self._assignment_engine.vote(
            album_id=album_id,
            shelf_name=shelf_name,
            voting_type=voting_type,
            shelf_locked=shelf_locked,
        )

    def get_shelf_name(self, album_id: str) -> Optional[str]:
        """Determine the shelf for an album."""
        return self._assignment_engine.get_shelf_name(album_id)

    def get_processing_type(
        self, album_id
    ) -> Optional[ProcessingContext.ProcessingType]:
        """Determine the processor type based on vote counts."""
        return self._assignment_engine.get_processing_type(album_id)

    def lock(self, album_id: str, shelf_name: str = "") -> None:
        """Set the manual lock for an album's shelf assignment."""
        self._lock_manager.lock(album_id, shelf_name)

    def unlock(self, album_id: str, shelf_name: str = "") -> None:
        """Clear the manual lock for an album's shelf assignment."""
        self._lock_manager.unlock(album_id, shelf_name)

    def get_shelf_locked(self, album_id: str) -> bool:
        """Check if an album's shelf assignment is locked."""
        return self._lock_manager.is_locked(album_id)

    def is_likely_shelf_name(self, name: str) -> tuple[bool, Optional[str]]:
        """Check if a name is likely a valid shelf name."""
        # Note: known_shelves parameter kept for backward compatibility but not used
        return self._validator.is_likely_shelf_name(name)

    def add_shelf_names(self, names: Union[set[str], str]) -> None:
        """Add shelf names to the registry."""
        self._registry.add_shelf_names(names)

    def remove_shelf_names(self, names: Union[set[str], str]) -> None:
        """Remove shelf names from the registry."""
        self._registry.remove_shelf_names(names)

    def intersect_shelf_names(self, names: Union[set[str], str]) -> None:
        """Intersect shelf names with the provided set."""
        self._registry.intersect_shelf_names(names)


class ShelfNotFoundException(Exception):
    """Represents an exception raised when a specific shelf name cannot be found in a given context."""

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        album_id: Optional[str] = "",
        details: Optional[str] = "",
        cause: Optional[BaseException] = None,
    ) -> None:
        self.message = message
        self.album_id = album_id or ""
        self.details = details or ""
        self.cause = cause

        if self.message is None:
            self.message = "Shelf for the album cannot be determined."

        super().__init__(self.message, f"{self.album_id=!r}, {self.details=!r}")

    def __str__(self) -> str:
        base = super().__str__()
        if self.cause:
            return f"{base} (Cause: {self.cause!r})"
        return base
