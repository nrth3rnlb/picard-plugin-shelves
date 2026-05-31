from typing import Optional

from . import runtime
from .manager import ShelfManager
from .typings import AlbumId, ShelfName


class ShelfCommands:
    """Handle explicit user commands for album shelf assignments."""

    def __init__(self, manager: Optional[ShelfManager] = None) -> None:
        self.manager = manager or runtime.manager_instance()

    def set_album_shelf(self, album_id: AlbumId, shelf_name: ShelfName) -> None:
        """Set the shelf assignment for an album."""
        self.manager.set_name(album_id=album_id, shelf_name=shelf_name)

    def unset_album_shelf(self, album_id: AlbumId) -> None:
        """Unset the shelf assignment for an album."""
        self.manager.unset_name(album_id=album_id)

    def lock_album_shelf(self, album_id: AlbumId) -> None:
        """Lock the shelf assignment for an album."""
        self.manager.lock(album_id=album_id)

    def unlock_album_shelf(self, album_id: AlbumId) -> None:
        """Unlock the shelf assignment for an album."""
        self.manager.unlock(album_id=album_id)

    def toggle_album_shelf_lock(self, album_id: AlbumId) -> None:
        """Toggle the shelf assignment lock for an album."""
        if self.manager.is_locked(album_id=album_id):
            self.unlock_album_shelf(album_id=album_id)
        else:
            self.lock_album_shelf(album_id=album_id)
