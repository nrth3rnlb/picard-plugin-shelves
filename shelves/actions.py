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

from . import constants, utils
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
                    album_id = metadata.get(constants.MUSICBRAINZ_ALBUMID)

                    if not album_id:
                        continue

                    ShelfManager().set_album_shelf(
                            album_id=album_id, shelf_name=shelf_name, lock=True,
                    )
                    # Set shelf name in metadata
                    shelf_name = ShelfManager().get_album_shelf(album_id)[0]
                    log.debug("Set shelf name: %s", shelf_name)

                    metadata[constants.TAG_KEY] = shelf_name
                    metadata[constants.TAG_LOCKED_KEY] = ShelfManager().is_locked(album_id)

                    self.tagger.window.set_statusbar_message(
                            f"Set shelf name to '{shelf_name}' for album"
                            f" {album_id}"
                    )

        # # Re-run the determination logic
        # determine_action = ShelfActionDetermine()
        # determine_action.tagger = self.tagger


class ShelfActionLock(BaseAction):
    """ Lock album's shelf assignment """

    # noinspection PyUnusedName
    NAME = "Lock album's shelf assignment"

    tagger: Any

    def callback(self, objs: List[Any]) -> None:
        for obj in objs:
            if hasattr(obj, "iterfiles"):
                for file in list(obj.iterfiles()):
                    metadata = file.metadata
                    album_id = metadata.get(constants.MUSICBRAINZ_ALBUMID)
                    if not album_id:
                        continue
                    ShelfManager().set_album_shelf(album_id, metadata[constants.TAG_KEY], lock=True)
                    metadata[constants.TAG_LOCKED_KEY] = ShelfManager().is_locked(album_id)
                    self.tagger.window.set_statusbar_message(f"Lock album's shelf assignment {album_id}")

        # # Re-run the determination logic
        # determine_action = ShelfActionDetermine()
        # determine_action.tagger = self.tagger
        # determine_action.callback(objs)


class ShelfActionUnlock(BaseAction):
    """
    Restore automatic shelf_name
    """

    # noinspection PyUnusedName
    NAME = "Unlock album's shelf assignment"

    tagger: Any

    def callback(self, objs: List[Any]) -> None:
        """
        Processes a list of objects to perform metadata cleanup operations. Specifically,
        clears manually set metadata flags in music file metadata and optionally re-runs
        determination logic.

        :param objs: A list of objects, each potentially containing music files with
        metadata to be processed.
        :type objs: List[Any]

        :return: This method does not return any value.
        :rtype: None
        """
        for obj in objs:
            if hasattr(obj, "iterfiles"):
                for file in list(obj.iterfiles()):
                    metadata = file.metadata
                    album_id = metadata.get(constants.MUSICBRAINZ_ALBUMID)
                    if not album_id:
                        continue

                    ShelfManager().unlock(album_id)
                    metadata[constants.TAG_LOCKED_KEY] = ShelfManager().is_locked(album_id)

                    self.tagger.window.set_statusbar_message(f"Cleared manual shelf override for album {album_id}")

        # # Re-run the determination logic
        # determine_action = ShelfActionDetermine()
        # determine_action.tagger = self.tagger
        # determine_action.callback(objs)


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
                        file.metadata[constants.TAG_KEY] = shelf_name
                        self.tagger.window.set_statusbar_message(
                                f"Set shelf name to '{shelf_name}' for file '{file.filename}'"
                        )

                        ShelfManager().add_shelf_names(shelf_name)
