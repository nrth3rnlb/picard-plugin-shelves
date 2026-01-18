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

import threading
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from picard import config, log

from . import constants, utils
from .exceptions import ShelfNotFoundException

SHELF_NAME = "shelf_name"
SHELF_SOURCE = "shelf_source"
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

        self._shelf_votes_weighted: Dict[str, List[Tuple[str, float, str]]] = (
            defaultdict(list)
        )
        self._shelf_votes_counted: Dict[str, Counter] = {}
        self._lock = threading.Lock()

    def vote_for_shelf(
            self,
            album_id: str,
            shelf_name: str,
            weight: float = 0.0,
            reason: str = "",
    ) -> None:
        """ Register a vote for a shelf assignment. """
        if not shelf_name:
            return

        shelf_name = shelf_name.strip()

        with self._lock:
            # Counter for majority decisions
            if album_id not in self._shelf_votes_counted:
                self._shelf_votes_counted[album_id] = Counter()
            self._shelf_votes_counted[album_id][shelf_name] += 1

            # For weighted decisions
            self._shelf_votes_weighted[album_id].append((shelf_name, weight, reason))

    def _get_weighted_shelf_name(self, album_id) -> Optional[str]:
        """ Determine the winning shelf based on weighted votes. """
        votes = self._shelf_votes_weighted.get(album_id, [])
        agg: Dict[str, float] = {}
        for shelf, weight, _ in votes:
            agg[shelf] = agg.get(shelf, 0.0) + float(weight)
        return max(agg.items(), key=lambda kv: kv[1])[0]

    def _get_counted_shelf_name(self, album_id) -> Optional[str]:
        """ Determine the winning shelf based on vote counts. """
        votes = self._shelf_votes_counted.get(album_id, Counter())
        return votes.most_common(1)[0][0]

    def get_album_shelf(
            self, album_id: str, lock_manager: "ShelfLockManager",
    ) -> Tuple[str, str]:
        """
        Retrieves the shelf name and its source type for a given album.

        This method determines the shelf name for an album based on the weighted or counted shelf
        name computation. If a weighted shelf name exists and the album is locked using the given
        lock manager, the shelf is classified as a manual shelf. Otherwise, it checks for a counted
        shelf name. If neither a weighted nor counted shelf name can be identified, the method raises
        a `ShelfNotFoundException`.
        """
        if shelf_name := self._get_weighted_shelf_name(album_id):
            if lock_manager.is_locked(album_id):
                return shelf_name, constants.SHELF_SOURCE_MANUAL
            return shelf_name, constants.SHELF_SOURCE_VOTES

        # with self._lock:
        if shelf_name := self._get_counted_shelf_name(album_id):
            return shelf_name, constants.SHELF_SOURCE_QUANTITY

        raise ShelfNotFoundException(message=f"Album ID '{album_id}' has no shelf name.")

    def clear_album(self, album_id: str) -> None:
        """ Clear all votes and assignments for an album. """
        self._shelf_votes_weighted.pop(album_id, None)
        self._shelf_votes_counted.pop(album_id, None)

    @property
    def shelf_votes(self):
        """Get the weighted votes dictionary."""
        return self._shelf_votes_weighted


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

    def set_album_shelf(
            self,
            album_id: str,
            shelf_name: str,
            source: str = constants.SHELF_SOURCE_MANUAL,
            lock: Optional[bool] = None,
    ) -> None:
        """ Set the shelf for an album with optional locking. """
        state = self._shelf_state.setdefault(album_id, {})
        if lock is None:
            lock = source == constants.SHELF_SOURCE_MANUAL

        # Manually locked => can only be overwritten manually
        if state.get(SHELF_LOCKED) and source != constants.SHELF_SOURCE_MANUAL:
            return

        state[SHELF_NAME] = shelf_name
        state[SHELF_SOURCE] = source
        state[SHELF_LOCKED] = bool(lock)

        if source == constants.SHELF_SOURCE_MANUAL:
            # Register dominant decision (∞ weight)
            self.assignment_engine.vote_for_shelf(
                    album_id=album_id,
                    shelf_name=shelf_name,
                    weight=float("inf"),
                    reason=constants.SHELF_SOURCE_MANUAL,
            )

    def lock(self, album_id: str) -> None:
        """
        Set the manual override/lock for an album's shelf assignment.
        """
        state = self._shelf_state.setdefault(album_id, {})
        state[SHELF_LOCKED] = True
        state[SHELF_SOURCE] = constants.SHELF_SOURCE_MANUAL

    def unlock(self, album_id: str) -> None:
        """
        Clear the manual override/lock for an album's shelf assignment.
        """
        state = self._shelf_state.setdefault(album_id, {})
        state[SHELF_LOCKED] = False
        state[SHELF_SOURCE] = constants.SHELF_SOURCE_VOTES

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
    def shelf_votes(self):
        """Get the weighted votes."""
        return self._assignment_engine.shelf_votes

    @property
    def test_value(self):
        """Test value for testing purposes."""
        return self._test_value

    @test_value.setter
    def test_value(self, value):
        """Set test value."""
        self._test_value = value

    # ===== Static/Class Methods =====

    @classmethod
    def destroy(cls):
        """Destroy the singleton instance."""
        cls._instance = None

    # ===== Delegation Methods =====

    def vote_for_shelf(
            self,
            album_id: str,
            shelf_name: str,
            weight: float = 0.0,
            reason: str = "",
    ) -> None:
        """Register a vote for a shelf assignment - delegates to assignment engine."""
        self._assignment_engine.vote_for_shelf(album_id, shelf_name, weight, reason)

    def get_album_shelf(self, album_id: str) -> Tuple[str, str]:
        """
        Determine the shelf for an album.

        :param album_id: The album identifier.
        :return: Tuple of (shelf_name, source).
        :raises ShelfNotFoundException: If no shelf can be determined.
        """
        try:
            return self._assignment_engine.get_album_shelf(album_id, self._lock_manager)
        except ShelfNotFoundException as e:
            raise

    def clear_album(self, album_id: str) -> None:
        """Clear all votes and assignments for an album."""
        self._assignment_engine.clear_album(album_id)

    def set_album_shelf(
            self,
            album_id: str,
            shelf_name: str,
            source: str = constants.SHELF_SOURCE_MANUAL,
            lock: Optional[bool] = None,
    ) -> None:
        """
        Set the shelf for an album with optional locking.
        """
        self._lock_manager.set_album_shelf(album_id, shelf_name, source, lock)

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
