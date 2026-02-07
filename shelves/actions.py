"""
Context menu actions for the Shelves plugin.
"""

from __future__ import annotations

from typing import Any, List, Optional

from picard.album import Album, File, Track
from picard.ui.itemviews import BaseAction
from PyQt5 import (
    QtWidgets,
)

from . import utils
from .dialogs import SetShelfDialog
from .manager import ShelfManager
from .processors import ContextBuilder
from .typings import ProcessingType, TagKey


class ShelfActionSet(BaseAction):
    """Manually set shelf_name"""

    # noinspection PyUnusedName
    NAME: str = "Define/Set shelf name..."

    tagger: Any

    def callback(self, objs) -> None:
        shelf_name = self._ask_for_shelf_name()
        if not shelf_name:
            return

        manager = ShelfManager()

        albums: list[Album] = list(filter(lambda o: isinstance(o, Album), objs))
        for album in albums:
            track: Track
            for track in album.tracks:
                file: File
                for file in track.files:
                    context = ContextBuilder.build(
                        file=file,
                        processing_type=ProcessingType.SET,
                        manager=manager,
                    )
                    if not context:
                        continue
                    context.processing_name = shelf_name
                    manager.upvote(context=context)
                    file.metadata[TagKey.SHELF] = shelf_name
                    file.metadata[TagKey.SHELF_LOCKED] = manager.is_locked(
                        file.metadata.get(TagKey.MUSICBRAINZ_ALBUMID)
                    )
                    file.update()
                track.update()
            album.update()
            self.tagger.window.set_statusbar_message(
                f'Successfully set shelf name "{shelf_name}" for "{album.metadata["album"]}"'
            )

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
        _locked: dict[str, bool] = {}

        for obj in objs:
            if hasattr(obj, "iterfiles"):
                for file in list(obj.iterfiles()):
                    metadata = file.metadata
                    album_id = metadata.get(TagKey.MUSICBRAINZ_ALBUMID)
                    if not album_id:
                        continue
                    if album_id not in _locked:
                        _locked[album_id] = ShelfManager().is_locked(album_id)
                    if _locked[album_id]:
                        ShelfManager().unlock(album_id)
                    else:
                        ShelfManager().lock(album_id)
                    metadata[TagKey.SHELF_LOCKED] = ShelfManager().is_locked(album_id)

                    self.tagger.window.set_statusbar_message(
                        "Lock state of album %s is now %s."
                        % (
                            album_id,
                            "locked"
                            if ShelfManager().is_locked(album_id)
                            else "unlocked",
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
