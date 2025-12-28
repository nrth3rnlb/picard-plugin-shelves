"""
Options options_page for the Shelves plugin.
"""

from __future__ import annotations

import os
import sys
from typing import Optional, Set

from picard import config, log
from picard.config import BoolOption, IntOption, ListOption, Option, TextOption
from picard.ui.options import OptionsPage as PicardOptions
from PyQt5 import (
    QtGui,  # type: ignore # uic has no type stubs
    QtWidgets,
    uic,
)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QListWidget

from ..constants import DEFAULT_SHELVES, ShelfConstants
from ..manager import ShelfManager
from ..utils import ShelfUtils
from .widgets import MaxItemsDropListWidget


class OptionsPage(PicardOptions):
    """
    Options options_page for the Shelves plugin.
    """

    NAME = "shelf_names"
    TITLE = "Shelves"
    PARENT = "plugins"

    options: list[Option] = [
        ListOption(
            "setting",
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY,
            [],
        ),
        TextOption(
            "setting", ShelfConstants.CONFIG_ALBUM_SHELF_KEY, ShelfConstants.TAG_KEY
        ),
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
            "setting",
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY,
            False,
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
        Initialize the option options_page.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # ui_dir = Path(__file__).parent / "ui"

        ui_dir = os.path.join(os.path.dirname(__file__), "")
        sys.path.insert(0, str(ui_dir))

        ui_file = os.path.join(os.path.dirname(__file__), "", "options.ui")
        uic.loadUi(ui_file, self)

        # Shelf Management
        self.shelf_management_shelves.setSelectionMode(
            QAbstractItemView.ExtendedSelection,
        )
        self.add_shelf_button.clicked.connect(self._add_shelf)
        self.remove_shelf_button.clicked.connect(self._remove_shelf)
        self.remove_unknown_shelves_button.clicked.connect(self._remove_unknown_shelves)
        self.scan_for_shelves_button.clicked.connect(OptionsPage._scan_for_shelves)
        self.shelf_management_shelves.itemSelectionChanged.connect(
            self._on_shelf_list_selection_changed,
        )
        self.shelf_management_shelves.model().rowsInserted.connect(
            self._rebuild_shelves_for_stages,
        )
        self.shelf_management_shelves.model().rowsRemoved.connect(
            self._rebuild_shelves_for_stages,
        )

        # Workflow Configuration
        self.shelves_for_stages.setMaximumItemCount()
        self.shelves_for_stages.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.label_workflow_stage_1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.workflow_stage_1.setMaximumItemCount()
        self.workflow_stage_1.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.workflow_stage_1.itemSelectionChanged.connect(
            self._on_workflow_stage_changed,
        )

        self.workflow_stage_2.setMaximumItemCount(1)
        self.workflow_stage_2.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.workflow_stage_2.itemSelectionChanged.connect(
            self._on_workflow_stage_changed,
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
        self.button_stage_1_to_stage_2.clicked.connect(
            self._move_item_stage_1_to_stage_2,
        )
        self.button_stage_2_to_all.clicked.connect(self._move_item_stage_2_to_all)
        self.button_stage_2_to_stage_1.clicked.connect(
            self._move_item_stage_2_to_stage_1,
        )

    @staticmethod
    def _move_item(
        source: QtWidgets.QListWidget,
        target: QtWidgets.QListWidget,
    ) -> None:
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
        """
        Rebuild shelf_names for stages.
        Normally linked to an event, an explicit call should not be necessary.

        :return:
        """
        log.debug("Rebuilding shelf_names for stages")
        possible_shelves_stage_2 = self.shelf_names
        possible_shelves_stage_1 = self._build_workflow_stage_2(
            possible_shelves_stage_2,
        )
        remaining_shelves = self._build_workflow_stage_1(possible_shelves_stage_1)
        self._build_workflow_shelves_stages(remaining_shelves)

    def _build_workflow_shelves_stages(self, remaining_shelves: set[str]) -> None:
        self.shelves_for_stages.clear()
        self.shelves_for_stages.addItems(remaining_shelves)

    @staticmethod
    def _build_workflow_stage(
        possible_shelves: set[str],
        config_key: str,
        widget: QListWidget,
    ) -> set[str]:
        widget.clear()

        selected_shelves = set(config.setting[config_key])  # type: ignore[index]
        remaining: set[str] = set()

        for shelf in possible_shelves:
            if shelf in selected_shelves:
                widget.addItem(shelf)
            else:
                remaining.add(shelf)

        return remaining

    def _build_workflow_stage_2(self, possible_shelves: set[str]) -> set[str]:
        return self._build_workflow_stage(
            possible_shelves,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY,
            self.workflow_stage_2,
        )

    def _build_workflow_stage_1(self, possible_shelves: set[str]) -> set[str]:
        return self._build_workflow_stage(
            possible_shelves,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY,
            self.workflow_stage_1,
        )

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

    def _add_shelf(self) -> None:
        """Add a new shelf name."""
        shelf_name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Add Shelf",
            "Enter shelf name name:",
        )
        if not ok or not shelf_name:
            return

        shelf_name = shelf_name.strip()
        is_valid, message = ShelfUtils.validate_shelf_name(shelf_name)
        if not is_valid:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Name",
                message if message is not None else "",
            )
            return

        shelf_names = self.shelf_names
        shelf_names.add(shelf_name)
        self.shelf_names = shelf_names

    def _remove_shelf(self) -> None:
        """Remove the selected shelf_names."""
        selected_items = self.shelf_management_shelves.selectedItems()
        if not selected_items:
            return

        shelves_to_remove: set[str] = set(item.text() for item in selected_items)
        workflow_shelves: set[str] = set(self._get_selected_shelves_stage_1()).union(
            set(self._get_selected_shelves_stage_2())
        )
        conflicting_shelves: set[str] = set(
            shelf for shelf in shelves_to_remove if shelf in workflow_shelves
        )

        if conflicting_shelves:
            if len(conflicting_shelves) == 1:
                title = "Remove Workflow Shelf?"
                message = (
                    f"'{conflicting_shelves.pop()}' is a workflow stage shelf name. "
                    "Are you sure you want to remove it?"
                )
            else:
                title = "Remove Workflow Shelves?"
                message = (
                    f"The shelf names {', '.join(conflicting_shelves)} are used in your workflow. "
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

        shelf_names = self.shelf_names
        shelf_names = shelf_names.difference(shelves_to_remove)
        self.shelf_names = shelf_names

    def _remove_unknown_shelves(self) -> None:
        """Remove shelf_names that no longer exist in the music directory."""
        shelf_sub_dirs: set[str] = ShelfUtils.get_shelf_dirs(
            base_path=ShelfManager().base_path
        )

        shelf_names = self.shelf_names
        shelf_names = shelf_names.intersection(shelf_sub_dirs)
        self.shelf_names = shelf_names

    def _scan_for_shelves(self) -> None:
        """Scan Picard's target directory for shelf names."""
        shelf_sub_dirs: set[str] = ShelfUtils.get_shelf_dirs(
            base_path=ShelfManager().base_path
        )

        shelf_names = self.shelf_names
        shelf_names = shelf_names.union(shelf_sub_dirs)
        self.shelf_names = shelf_names

    def _on_shelf_list_selection_changed(self) -> None:
        """Enable / disable the remove button based on selection."""
        self.remove_shelf_button.setEnabled(
            len(self.shelf_management_shelves.selectedItems()) > 0,
        )

    def _on_workflow_stage_changed(self) -> None:
        """Handle workflow stage change."""
        self.naming_script_code.setPlainText(self.rename_snippet)

    def load(self) -> None:
        """
        Load configuration into the options_page.
        :return:
        :rtype:
        """
        # Set the base file_path_str in the manager to prevent access to the configuration.
        ShelfManager().base_path = config.setting[ShelfConstants.CONFIG_MOVE_FILES_TO_KEY]  # type: ignore[index] # noqa""
        # Load known shelf_names from config
        shelves: set[str] = set(config.setting[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY])  # type: ignore[index]
        # Update ShelfManager shelf_names
        self.shelf_names = shelves
        if len(self.shelf_names) == 0:
            log.debug("Shelf list is empty, auto-scanning for shelf_names.")
            self._scan_for_shelves()
        if len(self.shelf_names) == 0:
            log.error("No shelves found during scan.")

        self.plugin_configuration.setCurrentIndex(
            config.setting[ShelfConstants.CONFIG_ACTIVE_TAB],  # type: ignore[index]
        )

        self.workflow_enabled.setChecked(
            config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY],  # type: ignore[index]
        )
        # Update preview with current values
        self.naming_script_code.setPlainText(ShelfConstants.RENAME_SNIPPET)

        self.stage_1_includes_non_shelves.setChecked(
            config.setting[ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY],  # type: ignore[index] # noqa
        )

    def save(self) -> None:
        """Save shelf_names list to config."""
        config.setting[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY] = self.shelf_names  # type: ignore[index]

        config.setting[ShelfConstants.CONFIG_ACTIVE_TAB] = (  # type: ignore[index]
            self.plugin_configuration.currentIndex()
        )

        shelves_stage_1 = []
        for i in range(self.workflow_stage_1.count()):
            element = self.workflow_stage_1.item(i)
            if element is not None:
                shelves_stage_1.append(element.text())
        config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY] = (
            shelves_stage_1  # type: ignore[index]
        )

        shelves_stage_2 = []
        for i in range(self.workflow_stage_2.count()):
            element = self.workflow_stage_2.item(i)
            if element is not None:
                shelves_stage_2.append(element.text())
        config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY] = (
            shelves_stage_2  # type: ignore[index]
        )

        config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY] = (  # type: ignore[index]
            self.workflow_enabled.isChecked()
        )

        config.setting[ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY] = (  # type: ignore[index]
            self.stage_1_includes_non_shelves.isChecked()
        )

    @property
    def shelf_names(self) -> Set[str]:
        """

        :return:
        :rtype:
        """
        valid_names = set(
            filter(
                lambda name: ShelfUtils.validate_shelf_name(name)[0],
                ShelfManager().shelf_names,
            )
        )
        return valid_names

    @shelf_names.setter
    def shelf_names(self, names: Set[str]):
        """

        :param names:
        :type names:
        :return:
        :rtype:
        """
        self.shelf_management_shelves.clear()
        valid_names = set(
            filter(lambda name: ShelfUtils.validate_shelf_name(name)[0], names)
        )
        self.shelf_management_shelves.addItems(valid_names)
        self.shelf_management_shelves.sortItems()
        ShelfManager().shelf_names = valid_names
