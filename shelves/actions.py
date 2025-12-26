# -*- coding: utf-8 -*-

"""
Context menu actions for the Shelves plugin.
"""

from __future__ import annotations

import os
from typing import Any, List, Optional

from picard import log
from picard.ui.itemviews import BaseAction
from PyQt5 import (
    QtWidgets,  # type: ignore # uic has no type stubs
    uic,
)
from PyQt5.QtWidgets import QDialog

from .constants import ShelfConstants
from .manager import ShelfManager
from .utils import ShelfUtils

LABEL_VALIDATION_NAME = "label_validation"
COMBO_SHELF_NAME = "combo_shelves"


class SetShelfAction(BaseAction):
    NAME = "Set shelf_name name..."

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

        is_valid, message = ShelfUtils.validate_shelf_name(shelf_name)
        if not is_valid:
            QtWidgets.QMessageBox.warning(
                self.tagger.window,
                "Invalid Shelf Name",
                f"Cannot use this shelf_name name: {message}",
            )
            return

        manual_shelf_tag = f"{shelf_name}{ShelfConstants.MANUAL_SHELF_SUFFIX}"
        for obj in objs:
            self._set_shelf_recursive(obj, shelf_name, manual_shelf_tag)

        ShelfManager().shelf_names.add(shelf_name)
        log.info(
            "Manually set shelf_name to '%s' for %d object(s)",
            shelf_name,
            len(objs),
        )

    @staticmethod
    def _set_shelf_recursive(obj: Any, shelf_name: str, shelf_tag: str) -> None:
        if hasattr(obj, "metadata"):
            album_id = obj.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
            if album_id:
                ShelfManager.set_album_shelf(
                    album_id=album_id,
                    shelf=shelf_name,
                    lock=True,
                )

            obj.metadata[ShelfConstants.TAG_KEY] = shelf_tag
            log.debug(
                "Set shelf_name tag '%s' on %s",
                shelf_tag,
                type(obj).__name__,
            )

        if hasattr(obj, "iterfiles"):
            for file in obj.iterfiles():
                file.metadata[ShelfConstants.TAG_KEY] = shelf_tag


class ResetShelfAction(BaseAction):
    NAME = "Restore automatic shelf_name"

    tagger: Any

    def callback(self, objs: List[Any]) -> None:
        for obj in objs:
            if hasattr(obj, "iterfiles"):
                files = list(obj.iterfiles())
                for file in files:
                    metadata = file.metadata
                    album_id = metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
                    print(f"DEBUG: Processing file {file}, album_id: {album_id}")

                    # Clear _lock in manager
                    if album_id:
                        ShelfManager.clear_manual_override(album_id)

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

        log.info("Reset shelf_name to automatic for %d object(s)", len(objs))


class SetShelfDialog(QDialog):
    NAME = "Set Shelf"

    def __init__(self) -> None:
        super().__init__()

        ui_file = os.path.join(os.path.dirname(__file__), "ui", "actions.ui")
        uic.loadUi(ui_file, self)

        self.validation_label: Optional[QtWidgets.QLabel] = self.findChild(
            QtWidgets.QLabel,
            LABEL_VALIDATION_NAME,
        )
        self.shelf_combo: Optional[QtWidgets.QComboBox] = self.findChild(
            QtWidgets.QComboBox,
            COMBO_SHELF_NAME,
        )

        if self.shelf_combo is not None:
            self.shelf_combo.currentTextChanged.connect(self._on_text_changed)

    def ask_for_shelf_name(self) -> str | None:
        """
        Ask for a shelf_name name.
        :return:
        :rtype:
        """
        if self.shelf_combo is not None:
            self.shelf_combo.clear()
            self.shelf_combo.addItems(ShelfManager().shelf_names)
            self.shelf_combo.sortItems()
            self.shelf_combo.setEditable(True)
            self.shelf_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)

        if self.validation_label is not None:
            self.validation_label.setText("")
            self.validation_label.setStyleSheet("QLabel { color: orange; }")

        if self.exec_() == QtWidgets.QDialog.Accepted:
            if self.shelf_combo is None:
                return None
            value = self.shelf_combo.currentText().strip()
            return value if value else None

        return None

    def _on_text_changed(self, text: str) -> None:
        valid, msg = ShelfUtils.validate_shelf_name(text)
        if self.validation_label is not None:
            if msg:
                self.validation_label.setText(msg)
                self.validation_label.setStyleSheet(
                    (
                        "QLabel { color: red; }"
                        if not valid
                        else "QLabel { color: orange; }"
                    ),
                )
            else:
                self.validation_label.setText("")


class DetermineShelfAction(BaseAction):
    """
    Determine shelf_name
    """

    NAME = "Determine shelf_name"

    tagger: Any

    def callback(self, objs: List[Any]) -> None:
        """
        Determine shelf_name
        :param objs:
        :type objs:
        :return:
        :rtype:
        """
        log.debug("DetermineShelfAction called with %d objects", len(objs))

        for obj in objs:
            self._determine_shelf_recursive(obj)

        log.info(
            "Determined shelf_name for %d object(s)",
            len(objs),
        )

    @staticmethod
    def _determine_shelf_recursive(obj: Any) -> None:
        if hasattr(obj, "iterfiles"):
            for file in obj.iterfiles():
                shelf_name, _ = ShelfUtils.get_shelf_name_from_path(
                    file_path_str=file.filename,
                )
                if shelf_name is not None:
                    file.metadata[ShelfConstants.TAG_KEY] = shelf_name
                    log.debug(
                        "Determined shelf_name '%s' for file: %s",
                        shelf_name,
                        file.filename,
                    )

                    ShelfManager().shelf_names.add(shelf_name)
