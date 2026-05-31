"""
Shelf manager for tracking album shelf name assignments.

The ShelfManager supports dependency injection for testing purposes.
"""

from dataclasses import dataclass
from gettext import gettext as _
from pathlib import Path
from typing import Optional, Union

from picard import log

from .typings import (
    ALBUM_INDICATORS,
    INVALID_SHELF_NAME_CHARS,
    INVALID_SHELF_NAMES,
    MAX_SHELF_NAME_LENGTH,
    AlbumId,
    ShelfName,
)

__all__ = [
    "ShelfManager",
    "ShelfNotFoundException",
    "ShelfManagerSettings",
]


@dataclass
class _ShelfAssignment:
    """Shelf assignment state for one album."""

    name: ShelfName = ShelfName()
    locked: bool = False


class _ShelfRegistry:
    """Registry for shelf names and base path configuration."""

    def __init__(self) -> None:
        """Initialize the shelf registry with empty names and the default base path."""
        self._shelf_names: set[ShelfName] = set()
        self._base_path: Path = Path(".")

    @property
    def shelf_names(self) -> set[ShelfName]:
        """Get the set of known shelf names."""
        return self._shelf_names

    @shelf_names.setter
    def shelf_names(self, names: set[ShelfName]) -> None:
        """Set the list of shelf names, filtering out invalid names."""
        self._shelf_names = names

    @property
    def base_path(self) -> Path:
        """Get the base path for shelf directories."""
        return self._base_path

    @base_path.setter
    def base_path(self, value: Union[str, Path]) -> None:
        """Set the base path for shelf directories."""
        if isinstance(value, str):
            self._base_path = Path(value).resolve()
        else:
            self._base_path = value.resolve()

    def add_shelf_names(self, names: Union[set[ShelfName], ShelfName]) -> None:
        """Add shelf names to the registry."""
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


class _ShelfNameManager:
    """Manage shelf assignments and lock state for albums."""

    DEFAULT_SHELF_NAME = ShelfName()

    def __init__(self) -> None:
        """Initialize an empty album-to-shelf assignment map."""
        self._assignments_by_album_id: dict[AlbumId, _ShelfAssignment] = {}
        # self._lock = threading.Lock()

    def _get_or_create_shelf(self, album_id: AlbumId) -> _ShelfAssignment:
        """Return the shelf assignment for an album, creating it if needed."""
        if album_id not in self._assignments_by_album_id:
            self._assignments_by_album_id[album_id] = _ShelfAssignment()
        return self._assignments_by_album_id[album_id]

    def _set_locked(self, album_id: AlbumId, locked: bool) -> None:
        """Set the manual override/lock state for an album's shelf assignment."""
        # with self._lock:
        shelf = self._get_or_create_shelf(album_id)
        shelf.locked = locked

    def set_name(
        self,
        album_id: AlbumId,
        shelf_name: ShelfName,
        locked: Optional[bool] = None,
    ) -> None:
        """Set the shelf name for an album, optionally updating its lock state."""
        shelf = self._get_or_create_shelf(album_id)
        if not self.is_locked(album_id):
            shelf.name = shelf_name
            if locked is not None:
                shelf.locked = locked

    def unset_name(self, album_id: AlbumId) -> None:
        """Reset the shelf name for an album while preserving its lock state."""
        shelf = self._get_or_create_shelf(album_id)
        if not self.is_locked(album_id):
            shelf.name = _ShelfNameManager.DEFAULT_SHELF_NAME

    def get_name(self, album_id: AlbumId) -> Optional[ShelfName]:
        """Return the shelf name assigned to an album."""
        shelf = self._get_or_create_shelf(album_id)
        return shelf.name

    def lock(self, album_id: AlbumId) -> None:
        """Set the manual override/lock for an album's shelf assignment."""
        self._set_locked(album_id, True)

    def unlock(self, album_id: AlbumId) -> None:
        """Clear the manual override/lock for an album's shelf assignment."""
        self._set_locked(album_id, False)

    def is_locked(self, album_id: AlbumId) -> bool:
        """Check if an album's shelf assignment is locked."""
        shelf = self._get_or_create_shelf(album_id)
        return shelf.locked


class _ShelfValidator:
    """Validator for shelf names using heuristics."""

    def __init__(self, registry: "_ShelfRegistry") -> None:
        """Initialize the validator."""
        self.registry = registry

    @staticmethod
    def is_likely_shelf_name(name: ShelfName) -> bool:
        """Return whether a name is likely to be a shelf name."""
        is_likely, _reason = _ShelfValidator.validate_likely_shelf_name(name)
        return is_likely

    @staticmethod
    def filter_valid_shelf_names(names: set[ShelfName]) -> set[ShelfName]:
        """Filter out invalid shelf names from the provided set."""
        return set(
            filter(
                lambda name: _ShelfValidator.validate_likely_shelf_name(
                    name,
                )[0],
                names,
            ),
        )

    @staticmethod
    def validate_likely_shelf_name(name: ShelfName) -> tuple[bool, Optional[str]]:
        """Validate a shelf name."""
        if not isinstance(name, str) or not name.strip():
            return False, _("Shelf name cannot be empty")

        shelf_name: ShelfName = ShelfName(name.strip())

        invalid_names_used = [
            name_used
            for name_used in shelf_name.split()
            if name_used in INVALID_SHELF_NAMES
        ]
        if invalid_names_used:
            hr_invalid_names_used = (
                f"{', '.join(repr(c) for c in set(invalid_names_used))}"
            )
            hr_invalid_names = f"{', '.join(repr(c) for c in INVALID_SHELF_NAMES)}"
            return (
                False,
                f"Cannot use '{shelf_name}' as shelf name."
                f" The name is an invalid name: {hr_invalid_names_used}."
                f" Not allowed are: {hr_invalid_names}.",
            )

        invalid_chars_used = [
            char_used
            for char_used in shelf_name
            if char_used in INVALID_SHELF_NAME_CHARS
        ]
        if invalid_chars_used:
            hr_invalid_chars_used = (
                f"{', '.join(repr(c) for c in set(invalid_chars_used))}"
            )
            hr_invalid_name_chars = (
                f"{', '.join(repr(c) for c in INVALID_SHELF_NAME_CHARS)}"
            )
            return (
                False,
                f"Cannot use '{shelf_name}' as shelf name."
                f" The name contains invalid character(s): {hr_invalid_chars_used}."
                f" Not allowed are: {hr_invalid_name_chars}.",
            )

        invalid_tokens_used = [
            token_used
            for token_used in shelf_name.split()
            if token_used.lower() in [token.lower() for token in ALBUM_INDICATORS]
        ]

        if invalid_tokens_used:
            hr_invalid_tokens_used = (
                f"{', '.join(repr(c) for c in set(invalid_tokens_used))}"
            )
            hr_invalid_name_tokens = f"{', '.join(repr(c) for c in ALBUM_INDICATORS)}"
            return (
                False,
                f"Cannot use '{shelf_name}' as shelf name."
                f" The name contains album indicator(s): {hr_invalid_tokens_used}."
                f" Not allowed are: {hr_invalid_name_tokens}.",
            )

        # TODO(#15): Decide if max length validation should be enforced
        # if len(shelf_name) > MAX_SHELF_NAME_LENGTH:
        #     return (
        #         False,
        #         f"Cannot use '{shelf_name}' as shelf name."
        #         f" The name is too long with {len(shelf_name)} characters."
        #         f" Maximum allowed is {MAX_SHELF_NAME_LENGTH}.",
        #     )

        # TODO(#16): Decide if max word count validation should be enforced
        # if len(shelf_name.split()) > MAX_WORD_COUNT:
        #     return (
        #         False,
        #         f"Cannot use '{shelf_name}' as shelf name."
        #         f" Shelf name is too long with {len(shelf_name.split())} words."
        #         f" Maximum allowed is {MAX_WORD_COUNT}.",
        #     )

        return True, "Valid shelf name"

    def _looks_like_artist_album_name(self, name: str) -> bool:
        """Return whether the name looks like an 'Artist - Album' title."""
        return " - " in name

    def _is_too_long(self, name: str) -> bool:
        """Return whether the name exceeds the recommended shelf name length."""
        return len(name) > MAX_SHELF_NAME_LENGTH

    def _word_count(self, name: str) -> int:
        """Return the number of words in the name."""
        return len(name.split())

    def _contains_album_indicator(self, name: str) -> bool:
        """Return whether the name contains typical album part indicators."""
        return any(indicator in name for indicator in ALBUM_INDICATORS)


@dataclass(frozen=True)
class ShelfManagerSettings:
    """Configuration required to initialize shelf management."""

    base_path: Path
    shelf_names: set[ShelfName]


class ShelfManager:
    """Facade for shelf management, delegating to specialized components."""

    def __init__(
        self,
        registry: Optional[_ShelfRegistry] = None,
        name_manager: Optional[_ShelfNameManager] = None,
        validator: Optional[_ShelfValidator] = None,
        settings: Optional[ShelfManagerSettings] = None,
    ):
        """Initialize ShelfManager with optional dependency injection."""

        self._registry = registry or _ShelfRegistry()

        if settings is not None:
            self._registry.base_path = settings.base_path
            self._registry.shelf_names = set(settings.shelf_names)

        self._name_manager = name_manager or _ShelfNameManager()
        self._validator = validator or _ShelfValidator(self._registry)

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
        """Set the shelf name for an album."""
        self._name_manager.set_name(
            album_id=album_id, shelf_name=shelf_name, locked=locked
        )

    def unset_name(self, album_id: AlbumId):
        """Clear the shelf name for an album."""
        self._name_manager.unset_name(album_id)

    def get_shelf_name(self, album_id: AlbumId) -> Optional[ShelfName]:
        """Determine the shelf for an album."""
        return self._name_manager.get_name(album_id)

    def lock(self, album_id: AlbumId) -> None:
        """Set the manual lock for an album's shelf assignment."""
        self._name_manager.lock(album_id)

    def unlock(self, album_id: AlbumId) -> None:
        """Clear the manual lock for an album's shelf assignment."""
        self._name_manager.unlock(album_id)

    def is_locked(self, album_id: AlbumId) -> bool:
        """Check if an album's shelf assignment is locked."""
        return self._name_manager.is_locked(album_id)

    def add_shelf_names(self, names: Union[set[ShelfName], ShelfName]) -> None:
        """Add shelf names to the registry."""
        self._registry.add_shelf_names(names)

    def remove_shelf_names(self, names: Union[set[ShelfName], ShelfName]) -> None:
        """Remove shelf names from the registry."""
        self._registry.remove_shelf_names(names)

    def intersect_shelf_names(self, names: Union[set[ShelfName], ShelfName]) -> None:
        """Intersect shelf names with the provided set."""
        self._registry.intersect_shelf_names(names)

    def is_likely_shelf_name(self, name: ShelfName) -> bool:
        """Return whether a name is likely to be a valid shelf name."""
        return self._validator.is_likely_shelf_name(name)

    def validate_likely_shelf_name(self, name: ShelfName) -> tuple[bool, Optional[str]]:
        """Check whether a name is likely valid and return an optional reason."""
        return self._validator.validate_likely_shelf_name(name)


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
