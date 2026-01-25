"""
Context menu actions for the Shelves plugin.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

from picard import log
from picard.ui.itemviews import BaseAction
from PyQt5 import (
    QtWidgets,
)

from . import utils
from .constants import TagKey
from .dialogs import SetShelfDialog
from .manager import ShelfManager


class ShelfActionSet(BaseAction):
    """
    Manually set shelf_name
    """

    # noinspection PyUnusedName
    NAME: str = "Define/Set shelf name..."

    tagger: Any

    def callback(self, objs: List[Any]) -> None:
        """

        :param objs:
        :type objs:
        :return:
        :rtype:
        """
        dialog = SetShelfDialog()
        shelf_name = dialog.ask_for_shelf_name()
        if not shelf_name:
            return

        is_valid, message = utils.validate_shelf_name(shelf_name)
        if not is_valid:
            QtWidgets.QMessageBox.warning(
                self.tagger.window,
                "Invalid shelf name",
                f"Cannot use this name as a shelf name: {message}",
            )
            return

        for obj in objs:
            log.debug("Processing object: %s", obj)
            if hasattr(obj, "iterfiles"):
                log.debug("Processing files in object: %s", obj)
                for file in list(obj.iterfiles()):
                    log.debug("Processing file: %s", file.filename)
                    metadata = file.metadata
                    album_id = metadata.get(TagKey.MUSICBRAINZ_ALBUMID)

                    if not album_id:
                        continue

                    ShelfManager().set_shelf_name(
                        album_id=album_id,
                        shelf_name=shelf_name,
                        lock=True,
                    )
                    # Set shelf name in metadata
                    shelf_name = ShelfManager().get_shelf_name(album_id)[0]
                    log.debug("Set shelf name: %s", shelf_name)

                    metadata[TagKey.SHELF] = shelf_name
                    metadata[TagKey.SHELF_LOCKED] = ShelfManager().is_locked(album_id)

                    self.tagger.window.set_statusbar_message(
                        f"Set shelf name to '{shelf_name}' for album {album_id}"
                    )

        # # Re-run the determination logic
        determine_action = ShelfActionDetermine()
        determine_action.tagger = self.tagger
        determine_action.callback(objs)


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

        # # Re-run the determination logic
        determine_action = ShelfActionDetermine()
        determine_action.tagger = self.tagger
        determine_action.callback(objs)


class ShelfActionDetermine(BaseAction):
    """
    Determine shelf_name
    """

    # noinspection PyUnusedName
    NAME = "Determine shelf name"

    tagger: Any

    def callback(self, objs: List[Any]) -> None:
        """
        Determine the shelf name
        :param objs:
        :type objs:
        :return:
        :rtype:
        """
        for obj in objs:
            if hasattr(obj, "iterfiles"):
                for file in obj.iterfiles():
                    file_path = Path(file.filename).resolve()
                    base_path = ShelfManager().base_path
                    shelf_name = utils.get_shelf_name_from_path(
                        file_path=file_path,
                        base_path=base_path,
                    )
                    if shelf_name is not None:
                        file.metadata[TagKey.SHELF] = shelf_name
                        self.tagger.window.set_statusbar_message(
                            f"Set shelf name to '{shelf_name}' for file '{file.filename}'"
                        )

                        ShelfManager().add_shelf_names(shelf_name)
