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
from .constants import ShelfConstants
from .dialogs import SetShelfDialog
from .manager import ShelfManager


class SetShelfAction(BaseAction):
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

        manual_shelf_tag = f"{shelf_name}{ShelfConstants.MANUAL_SHELF_SUFFIX}"
        for obj in objs:
            self._set_shelf_recursive(obj, shelf_name, manual_shelf_tag)

        ShelfManager().add_shelf_names(shelf_name)
        log.debug(
            "Manually set the shelf name to '%s' for %d object(s)",
            shelf_name,
            len(objs),
        )

    @staticmethod
    def _set_shelf_recursive(obj: Any, shelf_name: str, shelf_tag: str) -> None:
        if hasattr(obj, "metadata"):
            album_id = obj.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
            if album_id:
                ShelfManager().set_album_shelf(
                    album_id=album_id, shelf_name=shelf_name, lock=True
                )

            obj.metadata[ShelfConstants.TAG_KEY] = shelf_tag
            log.debug(
                "Set shelf name tag '%s' on %s",
                shelf_tag,
                type(obj).__name__,
            )

        if hasattr(obj, "iterfiles"):
            for file in obj.iterfiles():
                file.metadata[ShelfConstants.TAG_KEY] = shelf_tag


class ResetShelfAction(BaseAction):
    """
    Restore automatic shelf_name
    """

    # noinspection PyUnusedName
    NAME = "Clear manual shelf flag"

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
                files = list(obj.iterfiles())
                for file in files:
                    metadata = file.metadata
                    album_id = metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)

                    # Clear _lock in manager
                    if album_id:
                        ShelfManager().clear_manual_override(album_id)

                    # Clear tag in metadata
                    if ShelfConstants.TAG_KEY in metadata:
                        shelf_value = metadata.get(ShelfConstants.TAG_KEY, "")
                        if (
                            isinstance(shelf_value, str)
                            and ShelfConstants.MANUAL_SHELF_SUFFIX in shelf_value
                        ):
                            metadata[ShelfConstants.TAG_KEY] = shelf_value.replace(
                                ShelfConstants.MANUAL_SHELF_SUFFIX,
                                "",
                            )
                            log.debug(
                                "Cleared manual flag for file %s",
                                file.filename,
                            )

        # # Re-run the determination logic
        # determine_action = DetermineShelfAction()
        # determine_action.tagger = self.tagger
        # determine_action.callback(objs)

        log.debug("Clear manual flag for %d object(s)", len(objs))


class DetermineShelfAction(BaseAction):
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
                        file.metadata[ShelfConstants.TAG_KEY] = shelf_name
                        log.debug(
                            "Determined shelf name '%s' for file: %s",
                            shelf_name,
                            file.filename,
                        )
                        ShelfManager().add_shelf_names(shelf_name)
