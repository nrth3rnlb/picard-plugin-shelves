"""
Dialogs for the Shelves plugin.
"""

from __future__ import annotations

import os
from typing import Optional

from PyQt5 import QtWidgets, uic

from . import utils
from .manager import ShelfManager

LABEL_VALIDATION_NAME = "label_validation"
COMBO_SHELF_NAME = "combo_shelves"


class SetShelfDialog(QtWidgets.QDialog):
    """
    Dialog to set or define a shelf name
    """

    # noinspection PyUnusedName
    NAME = "Set shelf names"

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
        Ask for a name.
        :return:
        :rtype:
        """
        if self.shelf_combo is not None:
            self.shelf_combo.clear()
            self.shelf_combo.addItems(ShelfManager().shelf_names)
            self.shelf_combo.setEditable(True)
            self.shelf_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)

        if self.validation_label is not None:
            self.validation_label.setText("")
            self.validation_label.setStyleSheet("QLabel { color: red; }")

        if self.exec_() == QtWidgets.QDialog.Accepted:
            if self.shelf_combo is None:
                return None
            value = self.shelf_combo.currentText().strip()
            return value if value else None

        return None

    def _on_text_changed(self, text: str) -> None:
        if not self.validation_label:
            return

        valid, msg = utils.validate_shelf_name(text)
        if valid:
            self.validation_label.setText("")
        else:
            self.validation_label.setText(msg)
