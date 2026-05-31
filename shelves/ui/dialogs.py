"""
Dialogs for the Shelves plugin.
"""

from pathlib import Path
from typing import Optional

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt

from .. typings import ShelfName
from .. import runtime

LABEL_VALIDATION_NAME = "label_validation"
COMBO_SHELF_NAME = "combo_shelves"


class SetShelfDialog(QtWidgets.QDialog):
    """
    Dialog to set or define a shelf name
    """

    # noinspection PyUnusedName
    NAME = "Set shelf names"

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        ui_dir: Path = Path(__file__).parent.parent
        ui_file = ui_dir / "ui" / "actions.ui"
        uic.loadUi(ui_file, self)

        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self.validation_label: Optional[QtWidgets.QLabel] = self.findChild(
            QtWidgets.QLabel,
            LABEL_VALIDATION_NAME,
        )
        if self.validation_label is not None:
            self.validation_label.setText("")
            self.validation_label.setStyleSheet("QLabel { color: red; }")

        self.shelf_combo: Optional[QtWidgets.QComboBox] = self.findChild(
            QtWidgets.QComboBox,
            COMBO_SHELF_NAME,
        )
        if self.shelf_combo is not None:
            self.shelf_combo.currentTextChanged.connect(self._on_text_changed)

    def ask_for_shelf_name(self) -> Optional[str]:
        """Ask for a name."""
        shelf_manager = runtime.manager_instance()

        if self.shelf_combo is not None:
            self.shelf_combo.clear()
            self.shelf_combo.addItems(sorted(shelf_manager.registered_shelf_names))
            self.shelf_combo.setEditable(False)
            self.shelf_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)

        if self.exec_() != QtWidgets.QDialog.Accepted:
            return None

        if self.shelf_combo is None:
            return None

        shelf_name = ShelfName(self.shelf_combo.currentText().strip())
        valid, msg = shelf_manager.validate_likely_shelf_name(shelf_name)
        if not valid:
            return None
        return shelf_name

    def _on_text_changed(self, text: str) -> None:
        if not self.validation_label:
            return

        shelf_manager = runtime.manager_instance()
        shelf_name = ShelfName(text)
        valid, msg = shelf_manager.validate_likely_shelf_name(shelf_name)
        if valid:
            self.validation_label.setText("")
        else:
            self.validation_label.setText(msg)
