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

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple
import threading

from picard import config, log

from . import constants, utils
from .exceptions import ShelfNotFoundException

SHELF_NAME = "shelf_name"
SHELF_LOCKED = "shelf_locked"


class ShelfRegistry:
    """
    Registry for shelf names and base path configuration.

    Manages the set of known shelf names and the base path for shelf directories.
    Provides validation when setting shelf names.
    """

    def __init__(self):
        """Initialize the shelf registry with empty names and default base path."""
        self._shelf_names: Set[str] = set()
        self._base_path: Path = Path(".")

    @property
    def shelf_names(self) -> Set[str]:
        """Get the set of known shelf names."""
        return self._shelf_names

    @shelf_names.setter
    def shelf_names(self, names: Set[str]):
        """
        Set the list of shelf names, filtering out invalid names.

        :param names: Set of shelf names to register.
        """
        self._shelf_names = set(
                filter(lambda name: utils.validate_shelf_name(name)[0], names),
        )

    @property
    def base_path(self) -> Path:
        """Get the base path for shelf directories."""
        return self._base_path

    @base_path.setter
    def base_path(self, value: str | Path):
        """
        Set the base path for shelf directories.

        :param value: Path as string or Path object.
        """
        if isinstance(value, str):
            self._base_path = Path(value).resolve()
        else:
            self._base_path = value.resolve()

    def add_shelf_names(self, names: Set[str] | str) -> None:
        """
        Add shelf names to the registry.

        :param names: Single shelf name or set of shelf names to add.
        """
        if isinstance(names, str):
            names = {names}
        self.shelf_names = self.shelf_names.union(names)
        log.debug("Added shelf names: %s", names)
        log.debug("Current shelf names: %s", self.shelf_names)

    def remove_shelf_names(self, names: Set[str] | str) -> None:
        """
        Remove shelf names from the registry.

        :param names: Single shelf name or set of shelf names to remove.
        """
        if isinstance(names, str):
            names = {names}
        self.shelf_names = self.shelf_names.difference(names)
        log.debug("Removed shelf names: %s", names)
        log.debug("Current shelf names: %s", self.shelf_names)

    def intersect_shelf_names(self, names: Set[str] | str) -> None:
        """
        Intersect shelf names with the provided set.

        :param names: Single shelf name or set of shelf names to intersect.
        """
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
        """
        Initialize the assignment engine.

        :param registry: ShelfRegistry instance for accessing shelf names.
        """
        self.registry = registry
        self._shelf_votes: Dict[str, Counter] = {}
        self._shelf_processor: Dict[str, int] = {}
        self._lock = threading.Lock()

    def upvote(self, album_id: str, shelf_name: str, processor_type: int) -> None:
        """ Register a vote for a shelf assignment. """
        with self._lock:
            # Counter for majority decisions
            if album_id not in self._shelf_votes:
                self._shelf_votes[album_id] = Counter()
            self._shelf_votes[album_id][shelf_name] += 1
            self._shelf_processor[album_id] = processor_type

        log.debug(
                "album=%s, shelf=%s, votes=%s",
                album_id, shelf_name, dict(self._shelf_votes[album_id])
        )

    def downvote(self, album_id: str, shelf_name: str, processor_type: int) -> None:
        """ Unregister a vote for a shelf assignment. """
        with self._lock:
            if album_id in self._shelf_votes and shelf_name in self._shelf_votes[album_id]:
                self._shelf_votes[album_id][shelf_name] -= 1
            self._shelf_processor[album_id] = processor_type

        log.debug(
                "album=%s, shelf=%s, votes=%s",
                album_id, shelf_name, dict(self._shelf_votes[album_id])
        )

    def get_shelf_name_by_votes(self, album_id) -> Optional[str]:
        """ Determine the winning shelf based on vote counts. """
        votes: Counter = self._shelf_votes.get(album_id, Counter())
        if not votes:
            return None
        result = votes.most_common(1)
        log.debug("%s, %s", album_id, result)
        return result[0][0]

    def get_processor_type(self, album_id) -> Optional[int]:
        """ Determine the processor type based on vote counts. """
        return self._shelf_processor.get(album_id, None)

    def get_shelf_name(
            self, album_id: str, lock_manager: "ShelfLockManager",
    ) -> str:
        """
        Retrieves the shelf name for a given album.

        This method determines the shelf name for an album based on the weighted or counted shelf
        name computation. If neither a weighted nor counted shelf name can be identified, the method raises
        a `ShelfNotFoundException`.
        """
        with self._lock:
            if shelf_name := self.get_shelf_name_by_votes(album_id):
                return shelf_name

        raise ShelfNotFoundException(album_id=album_id)

    def clear_album(self, album_id: str) -> None:
        """ Clear all votes and assignments for an album. """
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
        self._shelf_state: Dict[str, Dict[str, Any]] = defaultdict(dict)

    def set_shelf_name(self, album_id: str, shelf_name: str, lock: bool = False, vote: bool = False) -> None:
        """ Set the shelf for an album with optional locking. """
        state = self._shelf_state.setdefault(album_id, {})

        # Manually locked => can only be overwritten manually
        if state.get(SHELF_LOCKED):
            log.warning("Album %s is locked, skipping shelf assignment", album_id)
            return

        state[SHELF_NAME] = shelf_name
        if lock:
            self.lock(album_id)
        else:
            self.unlock(album_id)

    def lock(self, album_id: str) -> None:
        """ Set the manual override/lock for an album's shelf assignment. """
        state = self._shelf_state.setdefault(album_id, {})
        state[SHELF_LOCKED] = True

    def unlock(self, album_id: str) -> None:
        """ Clear the manual override/lock for an album's shelf assignment. """
        state = self._shelf_state.setdefault(album_id, {})
        state[SHELF_LOCKED] = False

    def is_locked(self, album_id: str) -> bool:
        """Check if an album's shelf assignment is locked."""
        state = self._shelf_state.get(album_id, {})
        if state is None:
            return False
        return state.get(SHELF_LOCKED, False)


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

    def is_likely_shelf_name(self, name: str) -> Tuple[bool, Optional[str]]:
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
        if len(name) > constants.MAX_SHELF_NAME_LENGTH:
            suspicious_reasons.append(f"too long ({len(name)} chars)")

        # Too many words
        word_count = len(name.split())
        if word_count > constants.MAX_WORD_COUNT:
            suspicious_reasons.append(f"too many words ({word_count})")

        # Contains album indicators
        if any(indicator in name for indicator in constants.ALBUM_INDICATORS):
            suspicious_reasons.append("contains album indicator (Vol., Disc, etc.)")

        if suspicious_reasons:
            return False, "; ".join(suspicious_reasons)

        return True, None


class ShelfManager:
    """
    Facade for shelf management, delegating to specialized components.

    This class maintains backward compatibility while internally using:
    - ShelfRegistry: Manages shelf names and base path
    - ShelfAssignmentEngine: Handles voting and shelf determination
    - ShelfLockManager: Manages manual overrides and locks
    - ShelfValidator: Validates shelf names
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
            self,
            registry: Optional[ShelfRegistry] = None,
            assignment_engine: Optional[ShelfAssignmentEngine] = None,
            lock_manager: Optional[ShelfLockManager] = None,
            validator: Optional[ShelfValidator] = None,
    ):
        """
        Initialize ShelfManager with optional dependency injection.

        :param registry: Optional ShelfRegistry instance (created if None)
        :param assignment_engine: Optional ShelfAssignmentEngine instance (created if None)
        :param lock_manager: Optional ShelfLockManager instance (created if None)
        :param validator: Optional ShelfValidator instance (created if None)
        """
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._test_value = None

            # Initialize component hierarchy (use injected or create new)
            self._registry = registry or ShelfRegistry()
            self._assignment_engine = assignment_engine or ShelfAssignmentEngine(
                    self._registry,
            )
            self._lock_manager = lock_manager or ShelfLockManager(
                    self._assignment_engine,
            )
            self._validator = validator or ShelfValidator(self._registry)

            # Initialize from config only if using default components
            if registry is None:
                self._registry.base_path = Path(
                        config.setting[constants.CONFIG_MOVE_FILES_TO_KEY],
                )
                self._registry.shelf_names = set(
                        config.setting[constants.CONFIG_KNOWN_SHELVES_KEY],
                )

    # ===== Properties (delegate to components) =====

    @property
    def shelf_names(self) -> Set[str]:
        """Get the list of shelf names."""
        return self._registry.shelf_names

    @shelf_names.setter
    def shelf_names(self, names: Set[str]):
        """Set the list of shelf names."""
        self._registry.shelf_names = names

    @property
    def base_path(self) -> Path:
        """Get the base path."""
        return self._registry.base_path

    @base_path.setter
    def base_path(self, value: str | Path):
        """Set the base path."""
        self._registry.base_path = value

    @property
    def test_value(self):
        """Test value for testing purposes."""
        return self._test_value

    @test_value.setter
    def test_value(self, value):
        """Set test value."""
        self._test_value = value

    # ===== Delegation Methods =====

    def downvote(
            self,
            album_id: str,
            shelf_name: str,
            type: int,
    ) -> None:
        """Register a vote for a shelf assignment - delegates to assignment engine."""
        self._assignment_engine.downvote(album_id, shelf_name, type)

    def upvote(
            self,
            album_id: str,
            shelf_name: str,
            type: int,
            weight: float = 0.0,
            reason: str = "",
    ) -> None:
        """Register a vote for a shelf assignment - delegates to assignment engine."""
        self._assignment_engine.upvote(album_id, shelf_name, type)

    def get_shelf_name(self, album_id: str) -> str:
        """ Determine the shelf for an album. """
        try:
            return self._assignment_engine.get_shelf_name(album_id, self._lock_manager)
        except ShelfNotFoundException:
            raise

    def clear_album(self, album_id: str) -> None:
        """Clear all votes and assignments for an album."""
        self._assignment_engine.clear_album(album_id)

    def get_processor_type(self, album_id) -> Optional[int]:
        """ Determine the processor type based on vote counts. """
        return self._assignment_engine.get_processor_type(album_id)

    def set_shelf_name(
            self,
            album_id: str,
            shelf_name: str,
            lock: bool = False,
            vote: bool = False,
    ) -> None:
        """
        Set the shelf for an album with optional locking.
        """
        self._lock_manager.set_shelf_name(album_id, shelf_name, lock, vote)

    def lock(self, album_id: str) -> None:
        """Set the manual lock for an album's shelf assignment."""
        self._lock_manager.lock(album_id)

    def unlock(self, album_id: str) -> None:
        """Clear the manual lock for an album's shelf assignment."""
        self._lock_manager.unlock(album_id)

    def is_locked(self, album_id: str) -> bool:
        """Check if an album's shelf assignment is locked."""
        return self._lock_manager.is_locked(album_id)

    def is_likely_shelf_name(
            self,
            name: str,
            known_shelves: Set[str],
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a name is likely a valid shelf name.

        :param name: The name to validate.
        :param known_shelves: Set of known shelf names (ignored, uses registry).
        :return: Tuple of (is_valid, reason_if_invalid).
        """
        # Note: known_shelves parameter kept for backward compatibility but not used
        return self._validator.is_likely_shelf_name(name)

    def add_shelf_names(self, names: Set[str] | str) -> None:
        """Add shelf names to the registry."""
        self._registry.add_shelf_names(names)

    def remove_shelf_names(self, names: Set[str] | str) -> None:
        """Remove shelf names from the registry."""
        self._registry.remove_shelf_names(names)

    def intersect_shelf_names(self, names: Set[str] | str) -> None:
        """Intersect shelf names with the provided set."""
        self._registry.intersect_shelf_names(names)
