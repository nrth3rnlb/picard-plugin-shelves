"""
Options page for the Shelves plugin.
"""

from __future__ import annotations

import os
from typing import Set, Optional

from PyQt5 import QtWidgets, QtCore
from PyQt5 import uic  # type: ignore # uic has no type stubs
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView
from picard import log
from picard.config import BoolOption, ListOption, TextOption, IntOption
from picard.ui.options import OptionsPage

from . import PLUGIN_NAME, ShelfUtils
from .constants import DEFAULT_SHELVES, ShelfConstants
from .manager import ShelfManager


class ShelvesOptionsPage(OptionsPage):
    """
    Options page for the Shelves plugin.
    """
    NAME = "shelves"
    TITLE = "Shelves"
    PARENT = "plugins"

    add_shelf_button: QtWidgets.QPushButton
    label_workflow_stage_1: QtWidgets.QLabel
    label_workflow_stage_2: QtWidgets.QLabel
    naming_script_code: QtWidgets.QPlainTextEdit
    remove_shelf_button: QtWidgets.QPushButton
    remove_unknown_shelves_button: QtWidgets.QPushButton
    scan_for_shelves_button: QtWidgets.QPushButton
    shelf_list: QtWidgets.QListWidget
    tabWidget: QtWidgets.QTabWidget
    workflow_enabled: QtWidgets.QCheckBox
    workflow_stage_1: QtWidgets.QListWidget
    workflow_stage_2: QtWidgets.QListWidget
    workflow_transitions: QtWidgets.QWidget

    options = [
        ListOption(
            "setting",
            ShelfConstants.CONFIG_SHELVES_KEY,
            list(DEFAULT_SHELVES.values()),
        ),
        TextOption("setting", ShelfConstants.CONFIG_ALBUM_SHELF_KEY, ""),
        ListOption(
            "setting",
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY,
            DEFAULT_SHELVES[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY],
        ),
        ListOption(
            "setting",
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY,
            DEFAULT_SHELVES[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY],
        ),
        BoolOption("setting", ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY, True),
        IntOption("setting", ShelfConstants.CONFIG_ACTIVE_TAB, 0)
    ]

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        """
        Initialize the option page.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        ui_file = os.path.join(os.path.dirname(__file__), 'ui', 'shelves.ui')
        uic.loadUi(ui_file, self)

        # Allow multi-selection
        self.shelf_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.plugin_configuration.setCurrentIndex(
            self.config.setting[ShelfConstants.CONFIG_ACTIVE_TAB])  # type: ignore[index]

        # Connect signals
        self.add_shelf_button.clicked.connect(self.add_shelf)
        self.remove_shelf_button.clicked.connect(self.remove_shelf)
        self.remove_unknown_shelves_button.clicked.connect(self.rebuild_shelf_list)

        self.scan_for_shelves_button.clicked.connect(self.populate_shelf_list)
        self.shelf_list.itemSelectionChanged.connect(
            self.on_shelf_list_selection_changed
        )

        # 😠 Since uic cannot handle valid XML
        # <set>
        #     Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter
        # </set>
        self.label_workflow_stage_1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.workflow_stage_1.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.workflow_stage_2.setSelectionMode(QAbstractItemView.SingleSelection)
        self.workflow_stage_1.itemSelectionChanged.connect(
            self.on_workflow_stage_changed
        )
        self.workflow_stage_2.itemSelectionChanged.connect(
            self.on_workflow_stage_changed
        )

    def load(self) -> None:
        """Load already known shelves from config."""
        shelves = sorted(ShelfManager.get_configured_shelves())
        self.shelf_list.clear()
        self.shelf_list.addItems(shelves)

        self._rebuild_shelves_for_stages()

        self.workflow_enabled.setChecked(
            self.config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY])  # type: ignore[index]
        # Update preview with current values
        snippet = self.get_rename_snippet()
        self.naming_script_code.setPlainText(snippet)

        # Automatically scan for shelves if the list is empty
        if self.shelf_list.count() == 0:
            log.debug("%s: Shelf list is empty, auto-scanning for shelves.", PLUGIN_NAME)
            self.populate_shelf_list()

    def save(self) -> None:
        """Save shelves list to config."""
        shelves = []
        for i in range(self.shelf_list.count()):
            item = self.shelf_list.item(i)
            if item is not None:
                shelves.append(item.text())

        self.config.setting[ShelfConstants.CONFIG_SHELVES_KEY] = shelves  # type: ignore[index]

        self.config.setting[  # type: ignore[index]
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY] = self.get_selected_shelves_stage_1()
        self.config.setting[  # type: ignore[index]
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY] = self.get_selected_shelves_stage_2()

        self.config.setting[  # type: ignore[index]
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY] = self.workflow_enabled.isChecked()
        self.config.setting[  # type: ignore[index]
            ShelfConstants.CONFIG_ACTIVE_TAB] = self.tabWidget.currentIndex()
        log.debug("%s: Saved %d shelves to config", PLUGIN_NAME, len(shelves))

    def get_selected_shelves_stage_1(self) -> list[str]:
        selected_shelves_stage_1: list[str] = []
        for i in range(self.workflow_stage_1.count()):
            element = self.workflow_stage_1.item(i)
            if element and element.isSelected():
                selected_shelves_stage_1.append(element.text())
        return selected_shelves_stage_1

    def get_selected_shelves_stage_2(self) -> list[str]:
        selected_shelves_stage_2: list[str] = []
        for i in range(self.workflow_stage_2.count()):
            element = self.workflow_stage_2.item(i)
            if element and element.isSelected():
                selected_shelves_stage_2.append(element.text())
        return selected_shelves_stage_2

    def add_shelf(self) -> None:
        """Add a new shelf."""
        shelf_name, ok = QtWidgets.QInputDialog.getText(
            self, "Add Shelf", "Enter shelf name:"
        )

        if not ok or not shelf_name:
            return

        shelf_name = shelf_name.strip()
        is_valid, message = ShelfUtils.validate_shelf_name(shelf_name)

        if not is_valid:
            QtWidgets.QMessageBox.warning(self, title="Invalid Name", text=message)
            return

        # Check if already exists
        existing_shelves = self._get_configured_shelves()
        if shelf_name in existing_shelves:
            QtWidgets.QMessageBox.information(
                self, "Already Exists", f"Shelf '{shelf_name}' already exists."
            )
            return

        self.shelf_list.addItem(shelf_name)
        self.shelf_list.sortItems()
        self._rebuild_shelves_for_stages()

    def remove_shelf(self) -> None:
        """Remove the selected shelves."""
        selected_items = self.shelf_list.selectedItems()
        if not selected_items:
            return

        shelves_to_remove = [item.text() for item in selected_items]
        workflow_shelves = set(self.get_selected_shelves_stage_1() + self.get_selected_shelves_stage_2())
        conflicting_shelves = [shelf for shelf in shelves_to_remove if shelf in workflow_shelves]

        if conflicting_shelves:
            shelf_list_str = ", ".join(f"'{s}'" for s in conflicting_shelves)
            if len(conflicting_shelves) == 1:
                title = "Remove Workflow Shelf?"
                message = (
                    f"'{conflicting_shelves[0]}' is a workflow stage shelf. "
                    "Are you sure you want to remove it?"
                )
            else:
                title = "Remove Workflow Shelves?"
                message = (
                    f"The shelves {shelf_list_str} are used in your workflow. "
                    "Are you sure you want to remove them?"
                )

            reply = QtWidgets.QMessageBox.question(
                self,
                title,
                message,
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if reply == QtWidgets.QMessageBox.No:
                return

        for item in selected_items:
            self.shelf_list.takeItem(self.shelf_list.row(item))

        self._rebuild_shelves_for_stages()

    def rebuild_shelf_list(self) -> None:
        """Remove shelves that no longer exist in the music directory."""
        existing_shelves = ShelfUtils.get_existing_dirs()
        items_to_remove = []

        # Identify shelves to remove
        for i in range(self.shelf_list.count()):
            item = self.shelf_list.item(i)
            if item is not None:
                item_text = item.text()
                log.debug("%s: Checking shelf '%s' for existence", PLUGIN_NAME, item_text)
                if item_text not in existing_shelves:
                    items_to_remove.append(item_text)

        # Remove identified shelves
        for item_text in items_to_remove:
            # noinspection PyUnresolvedReferences
            matching_items = self.shelf_list.findItems(item_text, QtCore.Qt.MatchExactly)
            log.debug("%s: Removing shelf '%s' as it no longer exists", PLUGIN_NAME, item_text)
            for item in matching_items:
                self.shelf_list.takeItem(self.shelf_list.row(item))

        self._rebuild_shelves_for_stages()

    def _rebuild_shelves_for_stages(self) -> None:
        shelves = []
        for i in range(self.shelf_list.count()):
            item = self.shelf_list.item(i)
            if item is not None:
                shelves.append(item.text())

        self.build_workflow_stage_1(shelves)
        self.build_workflow_stage_2(shelves)

    def build_workflow_stage_1(self, shelves: list[str]):
        self.workflow_stage_1.clear()
        # Add wildcard option first
        self.workflow_stage_1.addItem(ShelfConstants.WORKFLOW_STAGE_1_WILDCARD)
        selected_shelves = self.config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY]
        for selected_shelf in selected_shelves:
            self.workflow_stage_1.addItem(selected_shelf)

    def build_workflow_stage_2(self, shelves: list[str]):
        self.workflow_stage_2.clear()
        self.workflow_stage_2.addItems(shelves)

        selected_shelves = self.config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY]
        for i in range(self.workflow_stage_2.count()):
            element = self.workflow_stage_2.item(i)
            if element and element.text() in selected_shelves:
                element.setSelected(True)

    def populate_shelf_list(self) -> None:
        """Scan Picard's target directory for shelves."""
        try:
            # Load existing directories
            shelves_found = ShelfUtils.get_existing_dirs()
            if not shelves_found:
                QtWidgets.QMessageBox.information(
                    self,
                    "No Shelves Found",
                    "No subdirectories found in the selected directory.",
                )
                log.debug("%s: No shelves found during scan in %s", PLUGIN_NAME,
                          self.config.setting["move_files_to"])  # type: ignore[index]
                return

            # Get currently configured shelves to avoid duplicates
            configured_shelves = self._get_configured_shelves()
            new_shelves_added = False
            for shelf in shelves_found:
                if shelf not in configured_shelves:
                    is_valid, _ = ShelfUtils.validate_shelf_name(shelf)
                    if is_valid:
                        self.shelf_list.addItem(shelf)
                        new_shelves_added = True

            if new_shelves_added:
                self.shelf_list.sortItems()
                self._rebuild_shelves_for_stages()

        except (OSError, PermissionError) as e:
            log.error("%s: Error scanning directory: %s", PLUGIN_NAME, e)
            QtWidgets.QMessageBox.critical(
                self, "Scan Error", f"Error scanning directory: {e}"
            )

    @staticmethod
    def get_rename_snippet() -> str:
        """ Get the renaming script snippet. """
        # noinspection SpellCheckingInspection
        return """$set(_shelffolder,$shelf())
$set(_shelffolder,$if($not($eq(%_shelffolder%,)),%_shelffolder%/))

%_shelffolder%
$if2(%albumartist%,%artist%)/%album%/%title%"""

    def on_shelf_list_selection_changed(self) -> None:
        """ Enable / disable the remove button based on selection. """
        self.remove_shelf_button.setEnabled(
            len(self.shelf_list.selectedItems()) > 0
        )

    def on_workflow_stage_changed(self) -> None:
        """Handle workflow stage change."""
        snippet = self.get_rename_snippet()
        self.naming_script_code.setPlainText(snippet)

    def _get_configured_shelves(self) -> Set[str]:
        """
        Get a set of currently listed shelves.

        Returns: Set of shelf names
        """
        shelves = set()
        for i in range(self.shelf_list.count()):
            item = self.shelf_list.item(i)
            if item is not None:
                shelves.add(item.text())
        return shelves
