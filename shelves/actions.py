# -*- coding: utf-8 -*-

"""
Context menu actions for the Shelves plugin.
"""

from __future__ import annotations

import os
from typing import Any, List, Optional

from PyQt5 import QtWidgets
from PyQt5 import uic  # type: ignore # uic has no type stubs
from PyQt5.QtWidgets import QDialog
from picard import log
from picard.ui.itemviews import BaseAction

from .constants import ShelfConstants
from .utils import ShelfUtils

LABEL_VALIDATION_NAME = "label_validation"
COMBO_SHELF_NAME = "combo_shelves"


class SetShelfAction(BaseAction):
    NAME = "Set shelf name..."

    tagger: Any

    @property
    def shelf_manager(self):
        from . import manager

        return manager.SHELF_MANAGER

    def __init__(self) -> None:
        super().__init__()

    def callback(self, objs: List[Any]) -> None:
        log.debug("SetShelfAction called with %d objects", len(objs))

        known_shelves = ShelfUtils.get_configured_shelves()

        dialog = SetShelfDialog(self.tagger)
        shelf_name = dialog.ask_for_shelf_name(known_shelves)
        if not shelf_name:
            return

        is_valid, message = ShelfUtils.validate_shelf_name(shelf_name)
        if not is_valid:
            QtWidgets.QMessageBox.warning(
                self.tagger.window,
                "Invalid Shelf Name",
                f"Cannot use this shelf name: {message}",
            )
            return

        manual_shelf_tag = f"{shelf_name}{ShelfConstants.MANUAL_SHELF_SUFFIX}"
        for obj in objs:
            self._set_shelf_recursive(obj, shelf_name, manual_shelf_tag)

        ShelfUtils.add_known_shelf(shelf_name)
        log.info(
            "Manually set shelf to '%s' for %d object(s)",
            shelf_name,
            len(objs),
        )

    def _set_shelf_recursive(self, obj: Any, shelf_name: str, shelf_tag: str) -> None:
        if hasattr(obj, "metadata"):
            album_id = obj.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
            if album_id:
                self.shelf_manager.set_album_shelf(
                    album_id,
                    shelf_name,
                    source=ShelfConstants.SHELF_SOURCE_MANUAL,
                    lock=True,
                )

            obj.metadata[ShelfConstants.TAG_KEY] = shelf_tag
            log.debug(
                "Set shelf tag '%s' on %s",
                shelf_tag,
                type(obj).__name__,
            )

        if hasattr(obj, "iterfiles"):
            for file in obj.iterfiles():
                file.metadata[ShelfConstants.TAG_KEY] = shelf_tag


class ResetShelfAction(BaseAction):
    NAME = "Restore automatic shelf"

    tagger: Any

    @property
    def shelf_manager(self):
        from . import manager

        return manager.SHELF_MANAGER

    def callback(self, objs: List[Any]) -> None:
        for obj in objs:
            if hasattr(obj, "iterfiles"):
                for file in obj.iterfiles():
                    metadata = file.metadata
                    album_id = metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)

                    # Clear lock in manager
                    if album_id:
                        self.shelf_manager.clear_manual_override(album_id)

                    # Clear tag in metadata
                    if ShelfConstants.TAG_KEY in metadata:
                        shelf_value = metadata.get(ShelfConstants.TAG_KEY, "")
                        if (
                            isinstance(shelf_value, str)
                            and ShelfConstants.MANUAL_SHELF_SUFFIX in shelf_value
                        ):
                            metadata[ShelfConstants.TAG_KEY] = ""
                            log.debug(
                                "Cleared manual flag for file %s",
                                file.filename,
                            )

        # # Re-run the determination logic
        # determine_action = DetermineShelfAction()
        # determine_action.tagger = self.tagger
        # determine_action.callback(objs)

        log.info("Reset shelf to automatic for %d object(s)", len(objs))


class SetShelfDialog(QDialog):
    NAME = "Set Shelf"

    # @property
    # def shelf_manager(self):
    #     from . import manager
    #
    #     return manager.SHELF_MANAGER

    def __init__(self) -> None:
        super().__init__()

        ui_file = os.path.join(os.path.dirname(__file__), "ui", "actions.ui")
        uic.loadUi(ui_file, self)

        self.validation_label: Optional[QtWidgets.QLabel] = self.findChild(
            QtWidgets.QLabel, LABEL_VALIDATION_NAME
        )
        self.shelf_combo: Optional[QtWidgets.QComboBox] = self.findChild(
            QtWidgets.QComboBox, COMBO_SHELF_NAME
        )

        if self.shelf_combo is not None:
            self.shelf_combo.currentTextChanged.connect(self._on_text_changed)

    def ask_for_shelf_name(self, known_shelves: list[str]) -> str | None:
        if self.shelf_combo is not None:
            self.shelf_combo.clear()
            self.shelf_combo.addItems(known_shelves)
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
                    "QLabel { color: red; }"
                    if not valid
                    else "QLabel { color: orange; }"
                )
            else:
                self.validation_label.setText("")


class DetermineShelfAction(BaseAction):
    NAME = "Determine shelf"

    tagger: Any

    def __init__(self) -> None:
        super().__init__()

    @property
    def shelf_manager(self):
        from . import manager

        return manager.SHELF_MANAGER

    def callback(self, objs: List[Any]) -> None:
        log.debug("DetermineShelfAction called with %d objects", len(objs))

        for obj in objs:
            self._determine_shelf_recursive(obj)

        log.info(
            "Determined shelf for %d object(s)",
            len(objs),
        )

    @staticmethod
    def _determine_shelf_recursive(obj: Any) -> None:
        if hasattr(obj, "iterfiles"):
            for file in obj.iterfiles():
                known_shelves = ShelfUtils.get_configured_shelves()
                shelf_name, _ = ShelfUtils.get_shelf_from_path(
                    path=file.filename, known_shelves=known_shelves
                )
                if shelf_name is not None:
                    file.metadata[ShelfConstants.TAG_KEY] = shelf_name
                    log.debug(
                        "Determined shelf '%s' for file: %s",
                        shelf_name,
                        file.filename,
                    )
                    ShelfUtils.add_known_shelf(shelf_name)
