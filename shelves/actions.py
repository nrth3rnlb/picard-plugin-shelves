"""
Context menu actions for the Shelves plugin.
"""

from __future__ import annotations

from typing import Any, List, Optional

from picard.album import Album, File, Track
from picard.ui.itemviews import BaseAction

from . import manager as manager_module
from .dialogs import SetShelfDialog
from .typings import TagKey


class ShelfActionUnset(BaseAction):
    # noinspection PyUnusedName
    NAME: str = "Unset shelf name"

    def callback(self, objs) -> None:
        from . import processors

        processors = processors.instance()
        albums: list[Album] = list(filter(lambda o: isinstance(o, Album), objs))
        for album in albums:
            track: Track
            for track in album.tracks:
                file: File
                for file in track.files:
                    processors.action_unset_processor(file=file)

        _set_album_metadata(albums=albums)


class ShelfActionSet(BaseAction):
    """Manually set shelf_name"""

    # noinspection PyUnusedName
    NAME: str = "Replace shelf name"

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
    """
    Restore automatic shelf_name
    """

    # noinspection PyUnusedName
    NAME = "Lock/Unlock album's shelf assignment."

    tagger: Any

    def callback(self, objs: List[Any]) -> None:
        """Toggle lock state of albums."""
        shelf_manager = manager.instance()
        _locked: dict[str, bool] = {}

        for obj in objs:
            if hasattr(obj, "iterfiles"):
                for file in list(obj.iterfiles()):
                    metadata = file.metadata
                    album_id = metadata.get(TagKey.MUSICBRAINZ_ALBUMID)
                    if not album_id:
                        continue
                    if album_id not in _locked:
                        _locked[album_id] = shelf_manager.is_locked(album_id)
                    if _locked[album_id]:
                        shelf_manager.unlock(album_id)
                    else:
                        shelf_manager.lock(album_id)
                    metadata[TagKey.SHELF_LOCKED] = shelf_manager.is_locked(album_id)

                    self.tagger.window.set_statusbar_message(
                        "Lock state of album %s is now %s."
                        % (
                            album_id,
                            (
                                "locked"
                                if shelf_manager.is_locked(album_id)
                                else "unlocked"
                            ),
                        )
                    )


# class ShelfActionDetermine(BaseAction):
#     """
#     Determine shelf_name
#     """
#
#     # noinspection PyUnusedName
#     NAME = "Determine shelf name"
#
#     tagger: Any
#
#     def callback(self, objs: List[Any]) -> None:
#         """
#         Determine the shelf name
#         :param objs:
#         :type objs:
#         :return:
#         :rtype:
#         """
#         for obj in objs:
#             if hasattr(obj, "iterfiles"):
#                 for file in obj.iterfiles():
#                     file_path = Path(file.filename).resolve()
#                     base_path = ShelfManager().base_path
#                     shelf_name = utils.get_shelf_name_from_path(
#                         file_path=file_path,
#                         base_path=base_path,
#                     )
#                     if shelf_name is not None:
#                         file.metadata[TagKey.SHELF] = shelf_name
#                         self.tagger.window.set_statusbar_message(
#                             f"Set shelf name to '{shelf_name}' for file '{file.filename}'"
#                         )
#
#                         ShelfManager().add_shelf_names(shelf_name)


def _set_album_metadata(albums: List[Album]):
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
