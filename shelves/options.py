# -*- coding: utf-8 -*-

"""
Options page for the Shelves plugin.
"""

from __future__ import annotations

import os
from typing import Set, Optional

from PyQt5 import QtWidgets, uic, QtCore
from picard import log
from picard.config import BoolOption, ListOption, TextOption
from picard.ui.options import OptionsPage

from .manager import ShelfManager
from .constants import DEFAULT_SHELVES, ShelfConstants

class ShelvesOptionsPage(OptionsPage):
    """
    Options page for the Shelves plugin.
    """

    NAME = "shelves"
    TITLE = "Shelves"
    PARENT = "plugins"

    options = [
        ListOption(
            "setting",
            ShelfConstants.CONFIG_SHELVES_KEY,
            list(DEFAULT_SHELVES.values()),
        ),
        TextOption("setting", ShelfConstants.CONFIG_ALBUM_SHELF_KEY, ""),
        TextOption(
            "setting",
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY,
            DEFAULT_SHELVES[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY],
        ),
        TextOption(
            "setting",
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY,
            DEFAULT_SHELVES[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY],
        ),
        BoolOption("setting", ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY, True),
    ]

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        """
        Initialise the option page.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        ui_file = os.path.join(os.path.dirname(__file__), 'shelves_config.ui')
        uic.loadUi(ui_file, self)

        # Connect signals
        self.b_add_shelf.clicked.connect(self.add_shelf)
        self.b_remove_shelf.clicked.connect(self.remove_shelf)
        self.b_remove_unknown_shelves.clicked.connect(self.rebuild_shelf_list)

        self.b_scan_4_shelves.clicked.connect(self.scan_music_directory)
        self.shelf_list.itemSelectionChanged.connect(
            self.on_shelf_list_selection_changed
        )
        self.workflow_enabled.stateChanged.connect(self.on_workflow_enabled_changed)
        self.workflow_stage_1.currentTextChanged.connect(
            self.on_workflow_stage_changed
        )
        self.workflow_stage_2.currentTextChanged.connect(
            self.on_workflow_stage_changed
        )

    def set_shelf_manager(self, shelf_manager: ShelfManager) -> None:
        log.debug("%s: Setting ShelfManager in options page", shelf_manager.plugin_name)
        self.shelf_manager = shelf_manager
        self.utils = shelf_manager.utils
        self.validators = shelf_manager.validators

    def load(self) -> None:
        """Load already known shelves from config."""
        shelves = sorted(self.utils.get_known_shelves())
        self.shelf_list.clear()
        self.shelf_list.addItems(shelves)

        self.workflow_transitions.setEnabled(self.workflow_enabled.isChecked())
        self._rebuild_workflow_dropdowns()
        self.workflow_enabled.setChecked(
                self.config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY])  # type: ignore[index]
        # Update preview with current values
        snippet = self.get_rename_snippet()
        self.naming_script_code.setPlainText(snippet)

    def save(self) -> None:
        """Save shelves list to config."""
        shelves = []
        for i in range(self.shelf_list.count()):
            item_text = self.shelf_list.item(i).text()
            shelves.append(item_text)

        self.config.setting[ShelfConstants.CONFIG_SHELVES_KEY] = shelves  # type: ignore[index]
        self.config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY] = (  # type: ignore[index]
            self.workflow_stage_1.currentText()
        )
        self.config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY] = (  # type: ignore[index]
            self.workflow_stage_2.currentText()
        )
        self.config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY] = (  # type: ignore[index]
            self.workflow_enabled.isChecked()
        )

        log.debug("%s: Saved %d shelves to config", self.shelf_manager.plugin_name, len(shelves))

    def add_shelf(self) -> None:
        """Add a new shelf."""
        shelf_name, ok = QtWidgets.QInputDialog.getText(
            self, "Add Shelf", "Enter shelf name:"
        )

        if not ok or not shelf_name:
            return

        shelf_name = shelf_name.strip()
        is_valid, message = self.validators.validate_shelf_name(shelf_name)

        if not is_valid:
            QtWidgets.QMessageBox.warning(self, "Invalid Name", message)
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
        self.workflow_stage_1.addItem(shelf_name)
        self.workflow_stage_2.addItem(shelf_name)

    def remove_shelf(self) -> None:
        """Remove the selected shelf."""
        current_item = self.shelf_list.currentItem()
        if not current_item:
            return

        shelf_name = current_item.text()

        # Warn if it's a workflow shelf
        if shelf_name in [
            self.workflow_stage_1.currentText(),
            self.workflow_stage_2.currentText(),
        ]:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Remove Workflow Shelf?",
                f"'{shelf_name}' is a workflow stage shelf. "
                "Are you sure you want to remove it?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if reply == QtWidgets.QMessageBox.No:
                return

        self.shelf_list.takeItem(self.shelf_list.row(current_item))

    def rebuild_shelf_list(self) -> None:
        """Remove shelves that no longer exist in the music directory."""
        existing_shelves = self.utils.get_existing_dirs()
        items_to_remove = []

        # Identify shelves to remove
        for i in range(self.shelf_list.count()):
            item_text = self.shelf_list.item(i).text()
            log.debug("%s: Checking shelf '%s' for existence", self.shelf_manager.plugin_name, item_text)
            if item_text not in existing_shelves:
                items_to_remove.append(item_text)

        # Remove identified shelves
        for item_text in items_to_remove:
            # noinspection PyUnresolvedReferences
            matching_items = self.shelf_list.findItems(item_text, QtCore.Qt.MatchExactly)
            log.debug("%s: Removing shelf '%s' as it no longer exists", self.shelf_manager.plugin_name, item_text)
            for item in matching_items:
                self.shelf_list.takeItem(self.shelf_list.row(item))

        self._rebuild_workflow_dropdowns()

    def _rebuild_workflow_dropdowns(self) -> None:
        """Rebuild the workflow dropdowns based on current shelf list."""
        shelves = list(self.shelf_list.item(i).text() for i in range(self.shelf_list.count()))
        log.debug("%s: Rebuilding workflow dropdowns with shelves: %s", self.shelf_manager.plugin_name, shelves)
        self.workflow_stage_1.clear()
        self.workflow_stage_1.addItems(shelves)
        self.workflow_stage_1.setCurrentText(
            self.config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY])  # type: ignore[index]

        self.workflow_stage_2.clear()
        self.workflow_stage_2.addItems(shelves)
        self.workflow_stage_2.setCurrentText(
            self.config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY])  # type: ignore[index]

    def scan_music_directory(self) -> None:
        """Scan Picard's target directory for shelves."""
        try:
            # Load existing directories
            shelves_found = self.utils.get_existing_dirs()
            if not shelves_found:
                QtWidgets.QMessageBox.information(
                    self,
                    "No Shelves Found",
                    "No subdirectories found in the selected directory.",
                )
                log.debug("%s: No shelves found during scan in %s", self.shelf_manager.plugin_name,
                          self.config.setting["move_files_to"])  # type: ignore[index]
                return

            # Get currently configured shelves to avoid duplicates
            configured_shelves = self._get_configured_shelves()
            for shelf in shelves_found:
                if shelf not in configured_shelves:
                    is_valid, _ = self.validators.validate_shelf_name(shelf)
                    if is_valid:
                        self.shelf_list.addItem(shelf)
                        self.workflow_stage_1.addItem(shelf)
                        self.workflow_stage_2.addItem(shelf)

            self.shelf_list.sortItems()

        except (OSError, PermissionError) as e:
            log.error("%s: Error scanning directory: %s", self.shelf_manager.plugin_name, e)
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
        self.b_remove_shelf.setEnabled(
            self.shelf_list.currentItem() is not None
        )

    def on_workflow_enabled_changed(self) -> None:
        """ Handle workflow-enabled state change. """
        is_enabled = self.workflow_enabled.isChecked()
        log.debug("%s: on_workflow_enabled_changed: %s", self.shelf_manager.plugin_name, is_enabled)
        self.workflow_transitions.setEnabled(is_enabled)

        # Update preview when workflow is toggled
        snippet = self.get_rename_snippet()
        self.naming_script_code.setPlainText(snippet)

    def on_workflow_stage_changed(self) -> None:
        """Handle workflow stage change."""
        log.debug(
            "%s: on_workflow_stage_changed: stage_1='%s', stage_2='%s'",
            self.shelf_manager.plugin_name,
            self.workflow_stage_1.currentText(),
            self.workflow_stage_2.currentText(),
        )
        snippet = self.get_rename_snippet()
        self.naming_script_code.setPlainText(snippet)

    def _get_configured_shelves(self) -> Set[str]:
        """
        Get a set of currently listed shelves.

        Returns: Set of shelf names
        """
        return {
            self.shelf_list.item(i).text()
            for i in range(self.shelf_list.count())
        }
