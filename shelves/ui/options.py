"""
Options options_page for the Shelves plugin.
"""

from __future__ import annotations

import os
import sys
from gettext import gettext as _
from typing import Optional

from picard import config
from picard.config import BoolOption, IntOption, ListOption, Option, TextOption
from picard.ui.options import OptionsPage as PicardOptions
from PyQt5 import (
    QtGui,
    QtWidgets,
    uic,
)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QListWidget

from ..constants import ShelfConstants
from ..manager import ShelfManager
from ..utils import ShelfUtils
from .widgets import MaxItemsDropListWidget


class OptionsPage(PicardOptions):
    """
    Options options_page for the Shelves plugin.
    """

    # ============================================================================
    # Class attributes
    # ============================================================================
    NAME = "shelves"
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
            [],
        ),
        ListOption(
            "setting",
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY,
            [],
        ),
        BoolOption("setting", ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY, True),
        BoolOption(
            "setting",
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY,
            False,
        ),
        IntOption("setting", ShelfConstants.CONFIG_ACTIVE_TAB, 0),
    ]

    # UI widget type hints
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
    remove_shelves_button: QtWidgets.QPushButton
    remove_unknown_shelves_button: QtWidgets.QPushButton
    scan_for_shelf_names_button: QtWidgets.QPushButton
    shelf_management_shelves: QtWidgets.QListWidget
    shelves_for_stages: MaxItemsDropListWidget
    stage_1_includes_non_shelves: QtWidgets.QCheckBox
    workflow_enabled: QtWidgets.QCheckBox
    workflow_stage_1: MaxItemsDropListWidget
    workflow_stage_2: MaxItemsDropListWidget
    workflow_transitions: QtWidgets.QWidget

    # Picard Icons
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
        ui_dir = os.path.dirname(__file__)
        ui_file = os.path.join(ui_dir, "options.ui")

        # We briefly add the directory to the path so that uic can find the custom widgets
        sys.path.insert(0, ui_dir)
        try:
            uic.loadUi(ui_file, self)
        finally:
            sys.path.pop(0)

    # ============================================================================
    # Load/Save methods
    # ============================================================================
    # noinspection PyTypeHints
    def load(self) -> None:
        """
        Load configuration.
        :return:
        :rtype:
        """
        self.shelf_management_shelves.addItems(
            config.setting[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY]
        )
        self.shelf_management_shelves.sortItems()

        self.workflow_stage_1.addItems(
            config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY]
        )
        self.workflow_stage_1.sortItems()

        self.workflow_stage_2.addItems(
            config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY]
        )
        self.workflow_stage_2.sortItems()

        self.naming_script_code.setPlainText(ShelfConstants.RENAME_SNIPPET)

        self.plugin_configuration.setCurrentIndex(
            config.setting[ShelfConstants.CONFIG_ACTIVE_TAB],
        )
        self.workflow_enabled.setChecked(
            config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY],
        )
        self.stage_1_includes_non_shelves.setChecked(
            config.setting[ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY],
        )

        self._setup_shelf_management()
        self._setup_workflow_configuration()

    # noinspection PyTypeHints
    def save(self) -> None:
        """Save shelf_names list to config."""
        config.setting[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY] = (
            item.text()
            for i in range(self.self.shelf_management_shelves.count())
            if (item := self.self.shelf_management_shelves.item(i)) is not None
        )
        config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY] = [
            item.text()
            for i in range(self.workflow_stage_1.count())
            if (item := self.workflow_stage_1.item(i)) is not None
        ]

        config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY] = [
            item.text()
            for i in range(self.workflow_stage_2.count())
            if (item := self.workflow_stage_2.item(i)) is not None
        ]

        config.setting[ShelfConstants.CONFIG_ALBUM_SHELF_KEY] = ShelfConstants.TAG_KEY
        config.setting[ShelfConstants.CONFIG_ACTIVE_TAB] = (
            self.plugin_configuration.currentIndex()
        )

        config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY] = (
            self.workflow_enabled.isChecked()
        )
        config.setting[ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY] = (
            self.stage_1_includes_non_shelves.isChecked()
        )

    def _action_add_shelf(self) -> None:
        """
        Add a new shelf name and update the UI.

        :return: None
        :rtype: None
        """
        shelf_name, ok = QtWidgets.QInputDialog.getText(
            self,
            _("Add Shelf"),
            _("Enter shelf name name:"),
        )
        if not ok or not shelf_name:
            return

        is_valid, message = ShelfUtils.validate_shelf_name(shelf_name)
        if not is_valid:
            QtWidgets.QMessageBox.warning(
                self,
                _("Invalid Name"),
                message if message is not None else "",
            )
            return

        ShelfManager().add_shelf_names(shelf_name)

    def _action_remove_shelves(self) -> None:
        """
        Remove the selected shelf names and update the UI.

        :return: None
        :rtype: None
        """
        selected_items = self.shelf_management_shelves.selectedItems()
        if not selected_items:
            return
        selected_names: set[str] = set(item.text() for item in selected_items)

        workflow_items_stage_1 = [
            self.workflow_stage_1.item(i) for i in range(self.workflow_stage_1.count())
        ]
        workflow_items_stage_2 = [
            self.workflow_stage_2.item(i) for i in range(self.workflow_stage_2.count())
        ]
        workflow_shelves: set[str] = set(
            item.text() for item in workflow_items_stage_1 if item
        ).union(set(item.text() for item in workflow_items_stage_2 if item))

        conflicting_shelves: set[str] = selected_names.intersection(workflow_shelves)

        if conflicting_shelves:
            hr_conflicting_shelves = (
                f"{', '.join(repr(c) for c in set(conflicting_shelves))}"
            )
            reply = QtWidgets.QMessageBox.question(
                self,
                _("Remove Workflow Shelves?"),
                _(
                    f"The shelf name(s) {hr_conflicting_shelves} are used in your workflow. "
                    "Are you sure you want to remove them?"
                ),
                buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if reply == QtWidgets.QMessageBox.No:
                return

        self._remove_shelf_names(selected_names)

    def _action_scan_for_shelf_names(self) -> None:
        """
        Scan Picard's target directory for shelf names and update the UI.

        :return: None
        :rtype: None
        """
        shelf_names: set[str] = ShelfUtils.get_shelf_dirs(
            base_path=ShelfManager().base_path
        )

        self._add_shelf_names(shelf_names)

    def _action_intersect_shelves(self) -> None:
        """
        Remove shelf_names that no longer exist in the music directory.

        :return: None
        :rtype: None
        """
        shelf_names: set[str] = ShelfUtils.get_shelf_dirs(
            base_path=ShelfManager().base_path
        )

        self._intersect_shelf_names(shelf_names)

    # ============================================================================
    # Workflow - Move actions
    # ============================================================================
    def _action_move_item_all_to_stage_1(self):
        """Move selected item from all shelves to stage 1."""
        self._move_item(self.shelves_for_stages, self.workflow_stage_1)

    def _action_move_item_all_to_stage_2(self):
        """Move selected item from all shelves to stage 2."""
        self._move_to_stage_2(self.shelves_for_stages)

    def _action_move_item_stage_1_to_all(self):
        """Move selected item from stage 1 to all shelves."""
        self._move_item(self.workflow_stage_1, self.shelves_for_stages)

    def _action_move_item_stage_1_to_stage_2(self):
        """Move selected item from stage 1 to stage 2."""
        self._move_to_stage_2(self.workflow_stage_1)

    def _action_move_item_stage_2_to_all(self):
        """Move selected item from stage 2 to all shelves."""
        self._move_item(self.workflow_stage_2, self.shelves_for_stages)

    def _action_move_item_stage_2_to_stage_1(self):
        """Move selected item from stage 2 to stage 1."""
        self._move_item(self.workflow_stage_2, self.workflow_stage_1)

    # ============================================================================
    # Configuration setup
    # ============================================================================
    def _setup_workflow_configuration(self) -> None:
        """Setup workflow configuration UI components and connect signals."""
        # noinspection PyTypeHints
        remaining_shelves = (
            ShelfManager()
            .shelf_names.difference(
                config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY]
            )
            .difference(
                config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY]
            )
        )
        self._build_workflow_list_widget(remaining_shelves, "", self.shelves_for_stages)

        self.shelves_for_stages.setMaximumItemCount()
        self.shelves_for_stages.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # Workflow stage 1
        self.label_workflow_stage_1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.workflow_stage_1.setMaximumItemCount()
        self.workflow_stage_1.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.workflow_stage_1.itemSelectionChanged.connect(
            self._on_workflow_stage_changed,
        )

        # Workflow stage 2
        self.workflow_stage_2.setMaximumItemCount(1)
        self.workflow_stage_2.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.workflow_stage_2.itemSelectionChanged.connect(
            self._on_workflow_stage_changed,
        )

        # Button icons
        self.button_all_to_stage_1.setIcon(self.go_down_icon)
        self.button_all_to_stage_2.setIcon(self.go_down_icon)
        self.button_stage_1_to_all.setIcon(self.go_up_icon)
        self.button_stage_1_to_stage_2.setIcon(self.go_next_icon)
        self.button_stage_2_to_all.setIcon(self.go_up_icon)
        self.button_stage_2_to_stage_1.setIcon(self.go_previous_icon)

        # Button connections
        self.button_all_to_stage_1.clicked.connect(
            self._action_move_item_all_to_stage_1
        )
        self.button_all_to_stage_2.clicked.connect(
            self._action_move_item_all_to_stage_2
        )
        self.button_stage_1_to_all.clicked.connect(
            self._action_move_item_stage_1_to_all
        )
        self.button_stage_1_to_stage_2.clicked.connect(
            self._action_move_item_stage_1_to_stage_2,
        )
        self.button_stage_2_to_all.clicked.connect(
            self._action_move_item_stage_2_to_all
        )
        self.button_stage_2_to_stage_1.clicked.connect(
            self._action_move_item_stage_2_to_stage_1,
        )

    def _setup_shelf_management(self) -> None:
        """Setup shelf management UI components and connect signals."""
        self.shelf_management_shelves.setSelectionMode(
            QAbstractItemView.ExtendedSelection,
        )
        self.add_shelf_button.clicked.connect(self._action_add_shelf)
        self.remove_shelves_button.clicked.connect(self._action_remove_shelves)
        self.remove_unknown_shelves_button.clicked.connect(
            self._action_intersect_shelves
        )
        self.scan_for_shelf_names_button.clicked.connect(
            self._action_scan_for_shelf_names
        )
        self.shelf_management_shelves.itemSelectionChanged.connect(
            self._on_shelf_management_shelves_selection_changed,
        )
        if (model := self.shelf_management_shelves.model()) is not None:
            model.rowsInserted.connect(
                self._on_shelf_management_shelves_rows_changed,
            )
            model.rowsRemoved.connect(
                self._on_shelf_management_shelves_rows_changed,
            )

    # ============================================================================
    # Workflow - Helper methods
    # ============================================================================
    @staticmethod
    def _move_item(
        source: QtWidgets.QListWidget,
        target: QtWidgets.QListWidget,
    ) -> None:
        """
        Move current item from source to target list widget.

        :param source: Source list widget.
        :param target: Target list widget.
        """
        item = source.currentItem()
        if not item:
            return

        target.addItem(item.clone())
        source.takeItem(source.currentRow())

    def _move_to_stage_2(self, source: QtWidgets.QListWidget) -> None:
        """
        Move item from source to stage 2 (only if stage 2 is empty).

        :param source: Source list widget.
        """
        if self.workflow_stage_2.count() > 0:
            return

        row = source.currentRow()
        if row < 0:
            return

        incoming = source.takeItem(row)
        if incoming is None:
            return

        self.workflow_stage_2.addItem(incoming)

    @staticmethod
    def _build_workflow_list_widget(
        possible_shelves: set[str],
        config_key: str,
        widget: QListWidget,
    ) -> set[str]:
        """
        Build workflow list widgets based on possible shelves and config.

        :param possible_shelves: Set of possible shelf names.
        :type possible_shelves: set[str]
        :param config_key: Configuration key for shelf settings.
        :type config_key: str
        :param widget: QListWidget to display the workflow stage.
        :type widget: QListWidget
        :return: Set of shelves not included in the workflow stage.
        :rtype: set[str]
        """
        to_use = possible_shelves
        if config_key:
            # noinspection PyTypeHints
            to_use = set(config.setting[config_key])

        widget.clear()
        widget.addItems(possible_shelves.intersection(to_use))
        widget.sortItems()

        return possible_shelves.difference(to_use)

    # ============================================================================
    # Event handlers
    # ============================================================================
    def _on_shelf_management_shelves_rows_changed(self) -> None:
        """
        Rebuild shelf_names for stages.
        Normally linked to an event, an explicit call should not be necessary.

        :return: None
        :rtype: None
        """
        possible_shelves_stage_2 = ShelfManager().shelf_names
        possible_shelves_stage_1 = self._build_workflow_list_widget(
            possible_shelves_stage_2,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY,
            self.workflow_stage_2,
        )

        remaining_shelves = self._build_workflow_list_widget(
            possible_shelves_stage_1,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY,
            self.workflow_stage_1,
        )
        self._build_workflow_list_widget(remaining_shelves, "", self.shelves_for_stages)

    def _on_shelf_management_shelves_selection_changed(self) -> None:
        """
        Enable / disable the remove button based on selection.

        :return: None
        :rtype: None
        """
        self.remove_shelves_button.setEnabled(
            len(self.shelf_management_shelves.selectedItems()) > 0,
        )

    def _on_workflow_stage_changed(self) -> None:
        """
        Handle workflow stage change and update naming script code.

        :return: None
        :rtype: None
        """
        self.naming_script_code.setPlainText(ShelfConstants.RENAME_SNIPPET)
