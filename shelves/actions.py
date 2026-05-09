"""
Context menu actions for the Shelves plugin.
"""

from __future__ import annotations

from typing import Any, List, Optional

from picard import log
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


class ShelfActionLock(BaseAction):
    """Restore automatic shelf_name"""

    # noinspection PyUnusedName
    NAME = "(Un-)Lock album's shelf assignment"

    tagger: Any

    @staticmethod
    def _metadata_bool(value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

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
                    raw_shelf_locked = file.metadata.get(TagKey.SHELF_LOCKED, False)
                    shelf_locked: bool = self._metadata_bool(raw_shelf_locked)
                    log.debug("metadata locked raw: %r", raw_shelf_locked)
                    log.debug("metadata locked raw type: %s", type(raw_shelf_locked))
                    log.debug("shelf_locked: %s", shelf_locked)
                    if shelf_locked:
                        processors.action_unlock_processor(file=file)
                    else:
                        processors.action_lock_processor(file=file)

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
                file.metadata[TagKey.SHELF_LOCKED] = shelf_manager.get_shelf_locked(
                    album.metadata[TagKey.MUSICBRAINZ_ALBUMID]
                )
                file.update()
            track.update()
        album.update()
