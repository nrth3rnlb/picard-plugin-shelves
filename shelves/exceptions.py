"""Module containing custom exceptions for the shelves package."""

from pathlib import Path
from typing import Optional


class ShelfNotFoundException(Exception):
    """Represents an exception raised when a specific shelf name cannot be found in a given context."""

    def __init__(
        self,
        album_id: Optional[str] = None,
        message: Optional[str] = None,
        *,
        cause: Optional[BaseException] = None,
    ) -> None:
        if message is None:
            message = (
                "Shelf for the album%s cannot be determined." % f" '{album_id}'"
                if album_id
                else ""
            )
        super().__init__(message)
        self.album_id = album_id
        self.cause = cause

    def __str__(self) -> str:
        base = super().__str__()
        if self.cause:
            return f"{base} (Cause: {self.cause!r})"
        return base


class ShelfNotDeterminableException(Exception):
    """Represents an exception raised when a shelf name cannot be determined from a given filepath."""

    def __init__(
        self,
        filepath: Optional[str | Path] = None,
        message: Optional[str] = None,
        *,
        cause: Optional[BaseException] = None,
    ) -> None:
        if message is None:
            message = (
                "No name for a shelf can be derived from the path%s." % f" '{filepath}'"
                if filepath
                else ""
            )
        super().__init__(message)
        self.filepath = filepath
        self.cause = cause

    def __str__(self) -> str:
        base = super().__str__()
        if self.cause:
            return f"{base} (Cause: {self.cause!r})"
        return base
