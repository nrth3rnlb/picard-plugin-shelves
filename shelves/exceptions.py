"""Module containing custom exceptions for the shelves package."""

from gettext import gettext as _
from pathlib import Path
from typing import Optional


class ShelfNotFoundException(Exception):
    """Represents an exception raised when a specific shelf name cannot be found in a given context."""

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        album_id: Optional[str] = None,
        details: Optional[str] = None,
        cause: Optional[BaseException] = None,
    ) -> None:
        self.message = message
        self.album_id = album_id
        self.details = details
        self.cause = cause

        if message is None:
            message = "Shelf for the album cannot be determined."

        super().__init__(self.message, f"{album_id=!r}, {details=}")

    def __str__(self) -> str:
        base = super().__str__()
        if self.cause:
            return f"{base} (Cause: {self.cause!r})"
        return base


class ShelfNotDeterminableException(Exception):
    """Represents an exception raised when a shelf name cannot be determined from a given filepath."""

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        filepath: Optional[str | Path],
        details: Optional[str] = None,
        cause: Optional[BaseException] = None,
    ) -> None:
        self.message = message
        self.filepath = filepath
        self.cause = cause
        self.details = details

        if self.message is None:
            self.message = _("No shelf name can be determined from the file path.")

        super().__init__(self.message, f"{filepath=!r}, {details=}")

    def __str__(self) -> str:
        base = super().__str__()
        if self.cause:
            return f"{base} (Cause: {self.cause!r})"
        return base
