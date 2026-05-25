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
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from picard import log

from . import utils

MAX_SHELF_NAME_LENGTH: int = 30
MAX_WORD_COUNT: int = 3
ALBUM_INDICATORS: frozenset[str] = frozenset(["Vol.", "Volume", "Disc", "CD", "Part"])
INVALID_SHELF_NAME_CHARS: set[str] = set()
INVALID_SHELF_NAMES: frozenset[str] = frozenset([".", ".."])


@dataclass(frozen=True)
class AlbumId(str):
    """ """

    # ToDo: Validator integrieren
    id: str = ""


@dataclass(frozen=True)
class ShelfName(str):
    """ """

    # ToDo: Validator integrieren
    name: str = ""


class Shelf:
    name: ShelfName = ShelfName()
    locked: bool = False


class ShelfRegistry:
    """
    Registry for shelf names and base path configuration.

    Manages the set of known shelf names and the base path for shelf directories.
    Provides validation when setting shelf names.
    """

    def __init__(self) -> None:
        """Initialize the shelf registry with empty names and default base path."""
        self._shelf_names: set[ShelfName] = set()
        self._base_path: Path = Path(".")

    @property
    def shelf_names(self) -> set[ShelfName]:
        """Get the set of known shelf names."""
        return self._shelf_names

    @shelf_names.setter
    def shelf_names(self, names: set[ShelfName]) -> None:
        """
        Set the list of shelf names, filtering out invalid names.
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
    def base_path(self, value: Union[str, Path]) -> None:
        """
        Set the base path for shelf directories.
        """
        if isinstance(value, str):
            self._base_path = Path(value).resolve()
        else:
            self._base_path = value.resolve()

    def add_shelf_names(self, names: Union[set[ShelfName], ShelfName]) -> None:
        """
        Add shelf names to the registry.
        """
        if isinstance(names, ShelfName):
            names = {names}
        self.shelf_names = self.shelf_names.union(names)
        log.debug("Added shelf names: %s", names)
        log.debug("Current shelf names: %s", self.shelf_names)

    def remove_shelf_names(self, names: Union[set[ShelfName], ShelfName]) -> None:
        """Remove shelf names from the registry."""
        if isinstance(names, ShelfName):
            names = {names}
        self.shelf_names = self.shelf_names.difference(names)
        log.debug("Removed shelf names: %s", names)
        log.debug("Current shelf names: %s", self.shelf_names)

    def intersect_shelf_names(self, names: Union[set[ShelfName], ShelfName]) -> None:
        """Intersect shelf names with the provided set."""
        if isinstance(names, ShelfName):
            names = {names}
        self.shelf_names = self.shelf_names.intersection(names)
        log.debug("Intersected shelf names: %s", names)
        log.debug("Current shelf names: %s", self.shelf_names)


class ShelfNameManager:
    """ """

    def __init__(self):
        """ """
        self._shelf_names: dict[AlbumId, Shelf] = {}
        # self._lock = threading.Lock()

    def set_name(
        self,
        album_id: AlbumId,
        shelf_name: ShelfName,
        locked: Optional[bool] = None,
    ) -> None:
        """ """
        shelf = self._shelf_names.get(album_id, Shelf())
        shelf.name = shelf_name
        if locked is not None:
            shelf.locked = locked
        self._shelf_names[album_id] = shelf

    def unset_name(self, album_id: AlbumId) -> None:
        """ """
        shelf = self._shelf_names.get(album_id, Shelf())
        shelf.name = ShelfName()
        self._shelf_names[album_id] = shelf

    def get_name(
        self,
        album_id: AlbumId,
    ) -> Optional[ShelfName]:
        """ """
        shelf = self._shelf_names.get(album_id, Shelf())
        return shelf.name

    def lock(self, album_id: AlbumId) -> None:
        """Set the manual override/lock for an album's shelf assignment."""
        # with self._lock:
        shelf = self._shelf_names.get(album_id, Shelf())
        shelf.locked = True
        self._shelf_names[album_id] = shelf
        log.debug("Locking album %s to shelf %s", album_id, shelf.name)

    def unlock(self, album_id: AlbumId) -> None:
        """Clear the manual override/lock for an album's shelf assignment."""
        # with self._lock:
        shelf = self._shelf_names.get(album_id, Shelf())
        shelf.locked = False
        self._shelf_names[album_id] = shelf

    def is_locked(self, album_id: AlbumId) -> bool:
        """Check if an album's shelf assignment is locked."""
        shelf = self._shelf_names.get(album_id, Shelf())
        log.debug(
            "Lock status for album %s: %s",
            album_id,
            shelf.locked,
        )
        return shelf.locked


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
    shelf_names: set[ShelfName]


class ShelfManager:
    """
    Facade for shelf management, delegating to specialized components.
    """

    def __init__(
        self,
        registry: Optional[ShelfRegistry] = None,
        name_manager: Optional[ShelfNameManager] = None,
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

        self._name_manager = name_manager or ShelfNameManager()
        self._validator = validator or ShelfValidator(self._registry)

    @property
    def registered_shelf_names(self) -> set[ShelfName]:
        """Get the list of shelf names."""
        return self._registry.shelf_names

    @property
    def base_path(self) -> Path:
        """Get the base path."""
        return self._registry.base_path

    def set_name(
        self, album_id: AlbumId, shelf_name: ShelfName, locked: Optional[bool] = None
    ):
        """ """
        self._name_manager.set_name(
            album_id=album_id, shelf_name=shelf_name, locked=locked
        )

    def unset_name(self, album_id: AlbumId):
        """ """
        self._name_manager.unset_name(album_id)

    def get_shelf_name(self, album_id: AlbumId) -> Optional[ShelfName]:
        """Determine the shelf for an album."""
        shelf_name = self._name_manager.get_name(album_id)
        if shelf_name is None:
            return None
        return shelf_name

    def lock(self, album_id: AlbumId) -> None:
        """Set the manual lock for an album's shelf assignment."""
        self._name_manager.lock(album_id)

    def unlock(self, album_id: AlbumId) -> None:
        """Clear the manual lock for an album's shelf assignment."""
        self._name_manager.unlock(album_id)

    def get_shelf_locked(self, album_id: AlbumId) -> bool:
        """Check if an album's shelf assignment is locked."""
        return self._name_manager.is_locked(album_id)

    def is_likely_shelf_name(self, name: str) -> tuple[bool, Optional[str]]:
        """Check if a name is likely a valid shelf name."""
        # Note: known_shelves parameter kept for backward compatibility but not used
        return self._validator.is_likely_shelf_name(name)

    def add_shelf_names(self, names: Union[set[ShelfName], ShelfName]) -> None:
        """Add shelf names to the registry."""
        self._registry.add_shelf_names(names)

    def remove_shelf_names(self, names: Union[set[ShelfName], ShelfName]) -> None:
        """Remove shelf names from the registry."""
        self._registry.remove_shelf_names(names)

    def intersect_shelf_names(self, names: Union[set[ShelfName], ShelfName]) -> None:
        """Intersect shelf names with the provided set."""
        self._registry.intersect_shelf_names(names)


class ShelfNotFoundException(Exception):
    """Represents an exception raised when a specific shelf name cannot be found in a given context."""

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        album_id: Optional[AlbumId] = None,
        details: Optional[str] = "",
        cause: Optional[BaseException] = None,
    ) -> None:
        if album_id is None:
            album_id = AlbumId()

        self.message = message
        self.album_id = album_id
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
