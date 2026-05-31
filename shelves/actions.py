"""
Context menu actions for the Shelves plugin.
"""

from typing import Any, Optional

from picard.album import Album, File, Track
from picard.ui.itemviews import BaseAction

from . import runtime
from .typings import ShelfName, TagKey
from .ui.dialogs import SetShelfDialog

__all__ = (
    "ShelfActionSet",
    "ShelfActionToggleLock",
    "ShelfActionUnset",
)


class ShelfActionSet(BaseAction):
    """Manually set shelf_name"""

    # noinspection PyUnusedName
    NAME: str = "Set album's shelf name"

    tagger: Any

    def callback(self, objs) -> None:
        name: Optional[str] = _ask_for_name()
        if name is None:
            return
        shelf_name = ShelfName(name)

        commands = runtime.command_instance()
        albums: list[Album] = list(filter(lambda o: isinstance(o, Album), objs))
        for album in albums:
            album_id = album.metadata[TagKey.MUSICBRAINZ_ALBUM_ID]
            commands.set_album_shelf(album_id=album_id, shelf_name=shelf_name)

        _set_album_metadata(albums)


class ShelfActionUnset(BaseAction):
    NAME = "Unset album's shelf name"

    tagger: Any

    def callback(self, objs: list[Any]) -> None:
        commands = runtime.command_instance()
        albums: list[Album] = list(filter(lambda o: isinstance(o, Album), objs))
        for album in albums:
            album_id = album.metadata[TagKey.MUSICBRAINZ_ALBUM_ID]
            commands.unset_album_shelf(album_id=album_id)

        _set_album_metadata(albums)


class ShelfActionToggleLock(BaseAction):
    # noinspection PyUnusedName
    NAME = "(Un-)Lock album's shelf assignment"

    tagger: Any

    def callback(self, objs: list[Any]) -> None:
        """Toggle lock state of albums."""

        commands = runtime.command_instance()
        albums: list[Album] = list(filter(lambda o: isinstance(o, Album), objs))
        for album in albums:
            album_id = album.metadata[TagKey.MUSICBRAINZ_ALBUM_ID]
            commands.toggle_album_shelf_lock(album_id=album_id)

        _set_album_metadata(albums)


def _ask_for_name() -> Optional[str]:
    dialog = SetShelfDialog()
    shelf_name = dialog.ask_for_shelf_name()
    return shelf_name


def _set_album_metadata(albums: list[Album]):
    manager = runtime.manager_instance()

    for album in albums:
        album_id = album.metadata[TagKey.MUSICBRAINZ_ALBUM_ID]
        shelf_name = manager.get_shelf_name(album_id)
        shelf_locked = manager.is_locked(album_id)

        track: Track
        for track in album.tracks:
            file: File
            for file in track.files:
                file.metadata[TagKey.SHELF] = shelf_name
                file.metadata[TagKey.SHELF_LOCKED] = shelf_locked
                file.update()
            track.update()
        album.update()
