"""
Options page for the Shelves plugin.
"""

from __future__ import annotations

import os
import sys
from typing import Optional, Set

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
    uic,  # type: ignore # uic has no type stubs
)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView
# Imported to trigger inclusion of N_() in builtins
from picard import (
    # noqa: F401,E402 # pylint: disable=unused-import
    log,
)
from picard.config import BoolOption, IntOption, ListOption, TextOption
from picard.ui.options import OptionsPage

from . import PLUGIN_NAME, ShelfUtils
from .constants import DEFAULT_SHELVES, ShelfConstants
from .manager import ShelfManager
from .ui.widgets import MaxItemsDropListWidget


class ShelvesOptionsPage(OptionsPage):
    """
    Options page for the Shelves plugin.
    """

    NAME = "shelves"
    TITLE = N_("Shelves")
    PARENT = "plugins"

    options = [
        ListOption(
            "setting",
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY,
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
        BoolOption(
            "setting", ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY, False
        ),
        IntOption("setting", ShelfConstants.CONFIG_ACTIVE_TAB, 0),
    ]

    add_shelf_button: QtWidgets.QPushButton
    button_all_to_stage_1: QtWidgets.QToolButton
    button_all_to_stage_2: QtWidgets.QToolButton
    button_stage_1_to_all: QtWidgets.QToolButton
    button_stage_1_to_stage_2: QtWidgets.QToolButton
    button_stage_2_to_all: QtWidgets.QToolButton
    button_stage_2_to_stage_1: QtWidgets.QToolButton
    label_workflow_stage_1: QtWidgets.QLabel
    label_workflow_stage_2: QtWidgets.QLabel
    naming_script_code: QtWidgets.QPlainTextEdit
    plugin_configuration: QtWidgets.QTabWidget
    remove_shelf_button: QtWidgets.QPushButton
    remove_unknown_shelves_button: QtWidgets.QPushButton
    scan_for_shelves_button: QtWidgets.QPushButton
    shelf_management_shelves: QtWidgets.QListWidget
    shelves_for_stages: MaxItemsDropListWidget
    stage_1_includes_non_shelves: QtWidgets.QCheckBox
    workflow_enabled: QtWidgets.QCheckBox
    workflow_stage_1: MaxItemsDropListWidget
    workflow_stage_2: MaxItemsDropListWidget
    workflow_transitions: QtWidgets.QWidget

    go_next_icon = QtGui.QIcon.fromTheme(":/images/16x16/go-next.png")
    go_previous_icon = QtGui.QIcon.fromTheme(":/images/16x16/go-previous.png")
    go_up_icon = QtGui.QIcon.fromTheme(":/images/16x16/go-up.png")
    go_down_icon = QtGui.QIcon.fromTheme(":/images/16x16/go-down.png")

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        """
        Initialize the option page.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # ui_dir = Path(__file__).parent / "ui"
        ui_dir = os.path.join(os.path.dirname(__file__), "ui")
        sys.path.insert(0, str(ui_dir))

        ui_file = os.path.join(os.path.dirname(__file__), "ui", "shelves.ui")
        uic.loadUi(ui_file, self)

        # Shelf Management
        self.shelf_management_shelves.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )
        self.add_shelf_button.clicked.connect(self.add_shelf)
        self.remove_shelf_button.clicked.connect(self.remove_shelf)
        self.remove_unknown_shelves_button.clicked.connect(self._rebuild_shelf_list)
        self.scan_for_shelves_button.clicked.connect(self._populate_shelf_list)
        self.shelf_management_shelves.itemSelectionChanged.connect(
            self._on_shelf_list_selection_changed
        )

        # Workflow Configuration
        self.shelves_for_stages.setMaximumItemCount(MaxItemsDropListWidget.UNLIMITED)
        self.shelves_for_stages.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.label_workflow_stage_1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.workflow_stage_1.setMaximumItemCount(MaxItemsDropListWidget.UNLIMITED)
        self.workflow_stage_1.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.workflow_stage_1.itemSelectionChanged.connect(
            self._on_workflow_stage_changed
        )

        self.workflow_stage_2.setMaximumItemCount(1)
        self.workflow_stage_2.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.workflow_stage_2.itemSelectionChanged.connect(
            self._on_workflow_stage_changed
        )

        # self.add_countries.setIcon(icon)
        self.button_all_to_stage_1.setIcon(self.go_down_icon)
        self.button_all_to_stage_2.setIcon(self.go_down_icon)
        self.button_stage_1_to_all.setIcon(self.go_up_icon)
        self.button_stage_1_to_stage_2.setIcon(self.go_next_icon)
        self.button_stage_2_to_all.setIcon(self.go_up_icon)
        self.button_stage_2_to_stage_1.setIcon(self.go_previous_icon)

        self.button_all_to_stage_1.clicked.connect(self._move_item_all_to_stage_1)
        self.button_all_to_stage_2.clicked.connect(self._move_item_all_to_stage_2)
        self.button_stage_1_to_all.clicked.connect(self._move_item_stage_1_to_all)
        self.button_stage_1_to_stage_2.clicked.connect(self._move_item_stage_1_to_stage_2)
        self.button_stage_2_to_all.clicked.connect(self._move_item_stage_2_to_all)
        self.button_stage_2_to_stage_1.clicked.connect(self._move_item_stage_2_to_stage_1)

    @staticmethod
    def _move_item(source: QtWidgets.QListWidget, target: QtWidgets.QListWidget) -> None:

        item = source.currentItem()
        if not item:
            return

        target.addItem(item.clone())
        source.takeItem(source.currentRow())

    def _move_to_stage_2(self, source: QtWidgets.QListWidget) -> None:
        if self.workflow_stage_2.count() > 0:
            return

        row = source.currentRow()
        if row < 0:
            return

        incoming = source.takeItem(row)
        if incoming is None:
            return

        self.workflow_stage_2.addItem(incoming)

    def _move_item_all_to_stage_1(self):
        self._move_item(self.shelves_for_stages, self.workflow_stage_1)

    def _move_item_all_to_stage_2(self):
        self._move_to_stage_2(self.shelves_for_stages)

    def _move_item_stage_1_to_stage_2(self):
        self._move_to_stage_2(self.workflow_stage_1)

    def _move_item_stage_1_to_all(self):
        self._move_item(self.workflow_stage_1, self.shelves_for_stages)

    def _move_item_stage_2_to_all(self):
        self._move_item(self.workflow_stage_2, self.shelves_for_stages)

    def _move_item_stage_2_to_stage_1(self):
        self._move_item(self.workflow_stage_2, self.workflow_stage_1)

    def _rebuild_shelves_for_stages(self) -> None:
        possible_shelves_stage_2 = self.config.setting[
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY
        ]
        possible_shelves_stage_1 = self._build_workflow_stage_2(possible_shelves_stage_2)
        remaining_shelves = self._build_workflow_stage_1(possible_shelves_stage_1)
        self._build_workflow_shelves_stages(remaining_shelves)

    def _build_workflow_shelves_stages(self, remaining_shelves: list[str]) -> None:
        self.shelves_for_stages.clear()
        self.shelves_for_stages.addItems(remaining_shelves)

    def _build_workflow_stage_2(self, possible_shelves: list[str]) -> list[str]:
        self.workflow_stage_2.clear()

        selected_shelves = set(
            self.config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY]
        )
        remaining: list[str] = []

        for shelf in possible_shelves:
            if shelf in selected_shelves:
                self.workflow_stage_2.addItem(shelf)
            else:
                remaining.append(shelf)

        return remaining

    def _build_workflow_stage_1(self, possible_shelves: list[str]) -> list[str]:
        self.workflow_stage_1.clear()

        selected_shelves = set(
            self.config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY]
        )
        remaining: list[str] = []

        for shelf in possible_shelves:
            if shelf in selected_shelves:
                self.workflow_stage_1.addItem(shelf)
            else:
                remaining.append(shelf)

        return remaining

    def load(self) -> None:
        """Load already known shelves from config."""
        shelves = sorted(ShelfManager.get_configured_shelves())
        self.shelf_management_shelves.clear()
        self.shelf_management_shelves.addItems(shelves)

        self._rebuild_shelves_for_stages()

        self.plugin_configuration.setCurrentIndex(
            self.config.setting[ShelfConstants.CONFIG_ACTIVE_TAB]
        )  # type: ignore[index]

        self.workflow_enabled.setChecked(
            self.config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY]
        )  # type: ignore[index]
        # Update preview with current values
        snippet = self._get_rename_snippet()
        self.naming_script_code.setPlainText(snippet)

        self.stage_1_includes_non_shelves.setChecked(
            self.config.setting[ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY]
        )  # type: ignore[index]

        # Automatically scan for shelves if the list is empty
        if self.shelf_management_shelves.count() == 0:
            log.debug(
                "%s: Shelf list is empty, auto-scanning for shelves.", PLUGIN_NAME
            )
            self._populate_shelf_list ()

    def save(self) -> None:
        """Save shelves list to config."""
        shelves = []
        for i in range(self.shelf_management_shelves.count()):
            item = self.shelf_management_shelves.item(i)
            if item is not None:
                shelves.append(item.text())
        self.config.setting[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY] = (
            shelves  # type: ignore[index]
        )

        shelves_stage_1 = []
        for i in range(self.workflow_stage_1.count()):
            element = self.workflow_stage_1.item(i)
            if element is not None:
                shelves_stage_1.append(element.text())
        self.config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY] = (
            shelves_stage_1  # type: ignore[index]
        )

        shelves_stage_2 = []
        for i in range(self.workflow_stage_2.count()):
            element = self.workflow_stage_2.item(i)
            if element is not None:
                shelves_stage_2.append(element.text())
        self.config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY] = (
            shelves_stage_2  # type: ignore[index]
        )

        self.config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY] = (
            self.workflow_enabled.isChecked()
        )  # type: ignore[index]
        self.config.setting[ShelfConstants.CONFIG_ACTIVE_TAB] = (
            self.plugin_configuration.currentIndex()
        )  # type: ignore[index]
        log.debug("%s: Saved %d shelves to config", PLUGIN_NAME, len(shelves))

        self.config.setting[ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY] = (
            self.stage_1_includes_non_shelves.isChecked()
        )  # type: ignore[index]

    def _get_selected_shelves_stage_1(self) -> list[str]:
        selected_shelves_stage_1: list[str] = []
        for i in range(self.workflow_stage_1.count()):
            element = self.workflow_stage_1.item(i)
            if element and element.isSelected():
                selected_shelves_stage_1.append(element.text())
        return selected_shelves_stage_1

    def _get_selected_shelves_stage_2(self) -> list[str]:
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
            # Stelle sicher, dass `text` ein `str` ist (kein `None`)
            QtWidgets.QMessageBox.warning(
                self, "Invalid Name", message if message is not None else ""
            )
            return

        existing_shelves = self._get_configured_shelves()
        if shelf_name in existing_shelves:
            QtWidgets.QMessageBox.information(
                self, "Already Exists", f"Shelf '{shelf_name}' already exists."
            )
            return

        self.shelf_management_shelves.addItem(shelf_name)
        self.shelf_management_shelves.sortItems()
        self._rebuild_shelves_for_stages()

    def remove_shelf(self) -> None:
        """Remove the selected shelves."""
        selected_items = self.shelf_management_shelves.selectedItems()
        if not selected_items:
            return

        shelves_to_remove = [item.text() for item in selected_items]
        workflow_shelves = set(
            self._get_selected_shelves_stage_1() + self._get_selected_shelves_stage_2()
        )
        conflicting_shelves = [
            shelf for shelf in shelves_to_remove if shelf in workflow_shelves
        ]

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
            self.shelf_management_shelves.takeItem(
                self.shelf_management_shelves.row(item)
            )

        self._rebuild_shelves_for_stages()

    def _rebuild_shelf_list(self) -> None:
        """Remove shelves that no longer exist in the music directory."""
        existing_shelves = ShelfUtils.get_existing_dirs()
        items_to_remove = []

        # Identify shelves to remove
        for i in range(self.shelf_management_shelves.count()):
            item = self.shelf_management_shelves.item(i)
            if item is not None:
                item_text = item.text()
                log.debug(
                    "%s: Checking shelf '%s' for existence", PLUGIN_NAME, item_text
                )
                if item_text not in existing_shelves:
                    items_to_remove.append(item_text)

        # Remove identified shelves
        for item_text in items_to_remove:
            # noinspection PyUnresolvedReferences
            matching_items = self.shelf_management_shelves.findItems(
                item_text, QtCore.Qt.MatchExactly
            )
            log.debug(
                "%s: Removing shelf '%s' as it no longer exists", PLUGIN_NAME, item_text
            )
            for item in matching_items:
                self.shelf_management_shelves.takeItem(
                    self.shelf_management_shelves.row(item)
                )

        self._rebuild_shelves_for_stages()

    def _populate_shelf_list (self) -> None:
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
                log.debug(
                    "%s: No shelves found during scan in %s",
                    PLUGIN_NAME,
                    self.config.setting["move_files_to"],
                )  # type: ignore[index]
                return

            # Get currently configured shelves to avoid duplicates
            configured_shelves = self._get_configured_shelves()
            new_shelves_added = False
            for shelf in shelves_found:
                if shelf not in configured_shelves:
                    is_valid, _ = ShelfUtils.validate_shelf_name(shelf)
                    if is_valid:
                        self.shelf_management_shelves.addItem(shelf)
                        new_shelves_added = True

            if new_shelves_added:
                self.shelf_management_shelves.sortItems()
                self._rebuild_shelves_for_stages()

        except (OSError, PermissionError) as e:
            log.error("%s: Error scanning directory: %s", PLUGIN_NAME, e)
            QtWidgets.QMessageBox.critical(
                self, "Scan Error", f"Error scanning directory: {e}"
            )

    @staticmethod
    def _get_rename_snippet() -> str:
        """Get the renaming script snippet."""
        # noinspection SpellCheckingInspection
        return """$set(_shelffolder,$shelf())
$set(_shelffolder,$if($not($eq(%_shelffolder%,)),%_shelffolder%/))

%_shelffolder%
$if2(%albumartist%,%artist%)/%album%/%title%"""

    def _on_shelf_list_selection_changed(self) -> None:
        """Enable / disable the remove button based on selection."""
        self.remove_shelf_button.setEnabled(
            len(self.shelf_management_shelves.selectedItems()) > 0
        )

    def _on_workflow_stage_changed(self) -> None:
        """Handle workflow stage change."""
        snippet = self._get_rename_snippet()
        self.naming_script_code.setPlainText(snippet)

    def _get_configured_shelves(self) -> Set[str]:
        """
        Get a set of currently listed shelves.

        Returns: Set of shelf names
        """
        shelves = set()
        for i in range(self.shelf_management_shelves.count()):
            item = self.shelf_management_shelves.item(i)
            if item is not None:
                shelves.add(item.text())
        return shelves
