"""
Context menu actions for the Shelves plugin.
"""

from __future__ import annotations

from typing import Any, List, Optional

from picard.album import Album, File, Track
from picard.ui.itemviews import BaseAction

from .ui.dialogs import SetShelfDialog
from .typings import TagKey


class ShelfActionSet(BaseAction):
    """Manually set shelf_name"""

    # noinspection PyUnusedName
    NAME: str = "Set album's shelf name"

    tagger: Any

    def callback(self, objs) -> None:
        shelf_name = self._ask_for_shelf_name()
        if not shelf_name:
            return
        from . import processors

        processors = processors.instance()
        albums: list[Album] = list(filter(lambda o: isinstance(o, Album), objs))
        for album in albums:
            track: Track
            for track in album.tracks:
                file: File
                for file in track.files:
                    processors.action_set_processor(file=file, shelf_name=shelf_name)

        _set_album_metadata(albums)

    @staticmethod
    def _ask_for_shelf_name() -> Optional[str]:
        dialog = SetShelfDialog()
        shelf_name = dialog.ask_for_shelf_name()
        return shelf_name


class ShelfActionToggleLock(BaseAction):
    """Restore automatic shelf_name"""

    # noinspection PyUnusedName
    NAME = "Lock/Unlock album's shelf assignment"

    tagger: Any

    def callback(self, objs: List[Any]) -> None:
        """Toggle lock state of albums."""
        from . import processors

        processors = processors.instance()
        albums: list[Album] = list(filter(lambda o: isinstance(o, Album), objs))
        for album in albums:
            track: Track
            for track in album.tracks:
                file: File
                for file in track.files:
                    processors.action_toggle_lock_processor(file=file)

        _set_album_metadata(albums)


def _set_album_metadata(albums: List[Album]):
    from . import manager as manager_module

    shelf_manager = manager_module.instance()

    for album in albums:
        track: Track
        for track in album.tracks:
            file: File
            for file in track.files:
                file.metadata[TagKey.SHELF] = shelf_manager.get_shelf_name(
                    album.metadata[TagKey.MUSICBRAINZ_ALBUMID]
                )
                file.update()
            track.update()
        album.update()
