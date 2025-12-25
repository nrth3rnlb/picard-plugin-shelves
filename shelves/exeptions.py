from typing import Optional


class ShelfNotFoundException(Exception):
    """
    Represents an exception raised when a specific shelf cannot be found in a given context.

    This exception is used to indicate that an operation requiring access to or information about a shelf
    has failed because the shelf does not exist. Ensure that the shelf name or identifier provided
    corresponds to an existing shelf.
    """

    def __init__(
            self,
            album_id: Optional[str] = None,
            message: Optional[str] = None,
            *,
            cause: Optional[BaseException] = None, ) -> None:
        if message is None:
            if album_id:
                message = f"Shelf for album '{album_id}' not found."
            else:
                message = "Shelf not found."
        super().__init__(message)
        self.album_id = album_id
        self.cause = cause

    def __str__(self) -> str:
        base = super().__str__()
        if self.cause:
            return f"{base} (Cause: {self.cause!r})"
        return base

    def to_dict(self) -> dict:
        return {"message": str(self), "album_id": self.album_id, "cause": repr(self.cause) if self.cause else None, }
