"""
Options page for the Shelves plugin.
"""

from __future__ import annotations

import sys
from gettext import gettext as _
from pathlib import Path
from typing import Optional

from picard import config, log
from picard.config import BoolOption, IntOption, ListOption, Option
from picard.ui.options import OptionsPage as PicardOptions
from PyQt5 import QtCore, QtGui, QtWidgets, uic

from . import constants, utils
from . import manager as manager_module
from .typings import ConfigKey
from .widgets import QShelvesWidget

MESSAGE_INVALID_SHELF_NAME: str = _("Shelf name is not valid.")
MESSAGE_MOVE_SELECTED_ITEMS_ENABLED: str = _(
    "Move selected shelf names to the list of the {name_of_target_stage}.",
)
MESSAGE_MOVE_SELECTED_ITEMS_DISABLED: str = _(
    "The list of {name_of_target_stage} is full, no further elements possible.",
)
NAME_WORKFLOW_STAGE_ALL: str = _("Available shelf names")
MESSAGE_PROVIDE_SHELF_NAME: str = _("Provide a name for the new shelf:")
MESSAGE_USED_SHELF_NAME: str = _(
    "The shelf names '{list_of_shelf_names}' are used in your workflow. Are you sure you want to remove them?",
)
NAME_WORKFLOW_STAGE_1: str = _("origin shelves")
NAME_WORKFLOW_STAGE_2: str = _("target shelves")
TITLE_ADD_SHELF_NAME: str = _("Add a shelf name.")
TITLE_REMOVE_SHELF_NAMES: str = _("Remove shelf names?")


class OptionsPage(PicardOptions):
    """Options options_page for the Shelves plugin."""

    # noinspection PyUnusedName
    NAME = "shelves"
    # noinspection PyUnusedName
    TITLE = "Shelves"
    # noinspection PyUnusedName
    PARENT = "plugins"

    options: list[Option] = [
        ListOption(
            "setting",
            ConfigKey.KNOWN_SHELVES,
            [],
        ),
        ListOption(
            "setting",
            ConfigKey.WORKFLOW_STAGE_1_SHELVES,
            [],
        ),
        ListOption(
            "setting",
            ConfigKey.WORKFLOW_STAGE_2_SHELVES,
            [],
        ),
        BoolOption("setting", ConfigKey.WORKFLOW_ENABLED, True),
        BoolOption(
            "setting",
            ConfigKey.STAGE_1_INCLUDES_NON_SHELVES,
            False,
        ),
        IntOption("setting", ConfigKey.ACTIVE_TAB, 0),
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
    shelf_management_shelves: QShelvesWidget
    shelves_for_stages: QShelvesWidget
    stage_1_includes_non_shelves: QtWidgets.QCheckBox
    workflow_enabled: QtWidgets.QCheckBox
    workflow_stage_1: QShelvesWidget
    workflow_stage_2: QShelvesWidget
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
        ui_dir: Path = Path(__file__).parent
        ui_file = ui_dir / "ui" / "options.ui"

        # We briefly add the directory to the path so that uic can find the custom widgets
        sys.path.insert(0, str(ui_dir))
        try:
            uic.loadUi(ui_file, self)
        finally:
            sys.path.pop(0)

        self._management_setup_connections()
        self._workflow_setup_connections()
        self._workflow_customize_buttons()

    # ============================================================================
    # Load/Save methods
    # ============================================================================
    # noinspection PyTypeHints
    def load(self) -> None:
        """Load configuration."""

        # The widgets "workflow_stage_1" and "workflow_stage_2," and of course "shelves_for_stages," are indirectly
        # populated by filling the widget "shelf_management_shelves." Therefore, we first add the shelf names to that
        # widget.
        self.shelf_management_shelves.addItems(
            config.setting[ConfigKey.KNOWN_SHELVES],
        )

        self.stage_1_includes_non_shelves.setChecked(
            config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES],
        )

        self.workflow_enabled.setChecked(
            config.setting[ConfigKey.WORKFLOW_ENABLED],
        )

        self.naming_script_code.setPlainText(constants.RENAME_SNIPPET)

        self.plugin_configuration.setCurrentIndex(
            config.setting[ConfigKey.ACTIVE_TAB],
        )

    # noinspection PyTypeHints
    def save(self) -> None:
        """Save configuration."""
        shelf_manager = manager_module.instance()

        config.setting[ConfigKey.KNOWN_SHELVES] = [
            item.text()
            for i in range(self.shelf_management_shelves.count())
            if (item := self.shelf_management_shelves.item(i)) is not None
            and item.text() in shelf_manager.registered_shelf_names
        ]

        config.setting[ConfigKey.WORKFLOW_STAGE_1_SHELVES] = [
            item.text()
            for i in range(self.workflow_stage_1.count())
            if (item := self.workflow_stage_1.item(i)) is not None
            and item.text() in shelf_manager.registered_shelf_names
        ]

        config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES] = [
            item.text()
            for i in range(self.workflow_stage_2.count())
            if (item := self.workflow_stage_2.item(i)) is not None
            and item.text() in shelf_manager.registered_shelf_names
        ]

        config.setting[ConfigKey.ACTIVE_TAB] = self.plugin_configuration.currentIndex()

        config.setting[ConfigKey.WORKFLOW_ENABLED] = self.workflow_enabled.isChecked()
        config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = (
            self.stage_1_includes_non_shelves.isChecked()
        )

    def _management_action_add(self) -> None:
        """Add a new shelf name and update the UI."""
        shelf_manager = manager_module.instance()
        shelf_name, ok = QtWidgets.QInputDialog.getText(
            self,
            _(TITLE_ADD_SHELF_NAME),
            _(MESSAGE_PROVIDE_SHELF_NAME),
        )
        if not ok or not shelf_name:
            return

        is_valid, message = utils.validate_shelf_name(shelf_name)
        if not is_valid:
            QtWidgets.QMessageBox.warning(
                self,
                _(MESSAGE_INVALID_SHELF_NAME),
                message if message is not None else "",
            )
            return

        shelf_manager.add_shelf_names(shelf_name)
        self._management_build_list()

    def _management_action_remove(self) -> None:
        """Remove the selected shelf names and update the UI."""
        selected_items = self.shelf_management_shelves.selectedItems()
        shelf_manager = manager_module.instance()
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
                TITLE_REMOVE_SHELF_NAMES,
                MESSAGE_USED_SHELF_NAME.format(
                    list_of_shelf_names=hr_conflicting_shelves,
                ),
                buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if reply == QtWidgets.QMessageBox.No:
                return

        shelf_manager.remove_shelf_names(selected_names)
        self._management_build_list()

    def _management_action_scan(self) -> None:
        """Scan Picard's target directory for shelf names and update the UI."""
        shelf_manager = manager_module.instance()
        shelf_names: set[str] = utils.get_shelf_dirs(base_path=shelf_manager.base_path)

        shelf_manager.add_shelf_names(shelf_names)
        self._management_build_list()

    def _management_action_intersect(self) -> None:
        """Remove shelf_names that no longer exist in the music directory."""
        shelf_manager = manager_module.instance()
        shelf_names: set[str] = utils.get_shelf_dirs(base_path=shelf_manager.base_path)

        shelf_manager.intersect_shelf_names(shelf_names)
        self._management_build_list()

    # ============================================================================
    # Workflow - Move actions
    # ============================================================================
    def _workflow_action_move_item_all_to_stage_1(self):
        """Move selected item from all shelves to stage 1."""
        self._workflow_move_selected_items(
            self.shelves_for_stages,
            self.workflow_stage_1,
        )

    def _workflow_action_move_item_all_to_stage_2(self):
        """Move selected item from all shelves to stage 2."""
        self._workflow_move_selected_items(
            self.shelves_for_stages,
            self.workflow_stage_2,
        )

    def _workflow_action_move_item_stage_1_to_all(self):
        """Move selected item from stage 1 to all shelves."""
        self._workflow_move_selected_items(
            self.workflow_stage_1,
            self.shelves_for_stages,
        )

    def _workflow_action_move_item_stage_1_to_stage_2(self):
        """Move selected item from stage 1 to stage 2."""
        self._workflow_move_selected_items(self.workflow_stage_1, self.workflow_stage_2)

    def _workflow_action_move_item_stage_2_to_all(self):
        """Move selected item from stage 2 to all shelves."""
        self._workflow_move_selected_items(
            self.workflow_stage_2,
            self.shelves_for_stages,
        )

    def _workflow_action_move_item_stage_2_to_stage_1(self):
        """Move selected item from stage 2 to stage 1."""
        self._workflow_move_selected_items(self.workflow_stage_2, self.workflow_stage_1)

    # ============================================================================
    # Configuration setup
    # ============================================================================

    def _management_setup_connections(self) -> None:
        """Setup shelf management UI components and connect signals."""
        self.shelf_management_shelves.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection,
        )
        self.add_shelf_button.clicked.connect(self._management_action_add)
        self.remove_shelves_button.clicked.connect(self._management_action_remove)
        self.remove_unknown_shelves_button.clicked.connect(
            self._management_action_intersect,
        )
        self.scan_for_shelf_names_button.clicked.connect(self._management_action_scan)
        self.shelf_management_shelves.itemSelectionChanged.connect(
            self._management_on_list_selection_changed,
        )
        if (model := self.shelf_management_shelves.model()) is not None:
            model.rowsInserted.connect(
                self._management_on_list_rows_changed,
            )
            model.rowsRemoved.connect(
                self._management_on_list_rows_changed,
            )

    def _workflow_setup_connections(self) -> None:
        """Setup workflow configuration UI components and connect signals."""

        # Shelves for stages connections
        self.shelves_for_stages.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection,
        )
        self.shelves_for_stages.itemSelectionChanged.connect(
            self._workflow_on_lists_changed,
        )
        if (model := self.shelves_for_stages.model()) is not None:
            model.rowsInserted.connect(
                self._workflow_on_lists_changed,
            )
            model.rowsRemoved.connect(
                self._workflow_on_lists_changed,
            )

        # Stage 1 connections
        self.label_workflow_stage_1.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
        )
        self.workflow_stage_1.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection,
        )
        self.workflow_stage_1.itemSelectionChanged.connect(
            self._workflow_on_lists_changed,
        )
        if (model := self.workflow_stage_1.model()) is not None:
            model.rowsInserted.connect(
                self._workflow_on_lists_changed,
            )
            model.rowsRemoved.connect(
                self._workflow_on_lists_changed,
            )

        # Stage 2 connections
        self.workflow_stage_2.max_item_count = 1
        log.debug(f"Max item count: {self.workflow_stage_2.max_item_count}")
        self.workflow_stage_2.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection,
        )
        self.workflow_stage_2.itemSelectionChanged.connect(
            self._workflow_on_lists_changed,
        )
        if (model := self.workflow_stage_2.model()) is not None:
            model.rowsInserted.connect(
                self._workflow_on_lists_changed,
            )
            model.rowsRemoved.connect(
                self._workflow_on_lists_changed,
            )

        # Button connections
        self.button_all_to_stage_1.clicked.connect(
            self._workflow_action_move_item_all_to_stage_1,
        )
        self.button_all_to_stage_2.clicked.connect(
            self._workflow_action_move_item_all_to_stage_2,
        )
        self.button_stage_1_to_all.clicked.connect(
            self._workflow_action_move_item_stage_1_to_all,
        )
        self.button_stage_1_to_stage_2.clicked.connect(
            self._workflow_action_move_item_stage_1_to_stage_2,
        )
        self.button_stage_2_to_all.clicked.connect(
            self._workflow_action_move_item_stage_2_to_all,
        )
        self.button_stage_2_to_stage_1.clicked.connect(
            self._workflow_action_move_item_stage_2_to_stage_1,
        )

    def _workflow_customize_buttons(self) -> None:
        # Button icons
        self.button_all_to_stage_1.setIcon(self.go_down_icon)
        self.button_all_to_stage_2.setIcon(self.go_down_icon)
        self.button_stage_1_to_all.setIcon(self.go_up_icon)
        self.button_stage_1_to_stage_2.setIcon(self.go_next_icon)
        self.button_stage_2_to_all.setIcon(self.go_up_icon)
        self.button_stage_2_to_stage_1.setIcon(self.go_previous_icon)

        tooltip_to_all = self._tooltip_to_stage_is_full_or_not(NAME_WORKFLOW_STAGE_ALL)
        tooltip_to_stage_1 = self._tooltip_to_stage_is_full_or_not(
            NAME_WORKFLOW_STAGE_1,
        )
        tooltip_to_stage_2 = self._tooltip_to_stage_is_full_or_not(
            NAME_WORKFLOW_STAGE_2,
        )

        self.button_stage_1_to_stage_2.setToolTip(tooltip_to_stage_2)
        self.button_all_to_stage_1.setToolTip(tooltip_to_stage_1)
        self.button_all_to_stage_2.setToolTip(tooltip_to_stage_2)
        self.button_stage_1_to_all.setToolTip(tooltip_to_all)
        self.button_stage_2_to_all.setToolTip(tooltip_to_all)

    # noinspection PyTypeHints
    def _workflow_build_shelves_for_stages(self) -> None:
        # Build shelves for stages and trigger an initial state change
        shelf_manager = manager_module.instance()

        self.shelves_for_stages.clear()
        self.shelves_for_stages.addItems(
            shelf_manager.registered_shelf_names.difference(
                config.setting[ConfigKey.WORKFLOW_STAGE_1_SHELVES]
            ).difference(
                config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES],
            )
        )
        self.workflow_stage_1.clear()
        self.workflow_stage_1.addItems(
            shelf_manager.registered_shelf_names.intersection(
                config.setting[ConfigKey.WORKFLOW_STAGE_1_SHELVES]
            )
        )
        self.workflow_stage_2.clear()
        self.workflow_stage_2.addItems(
            shelf_manager.registered_shelf_names.intersection(
                config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES]
            )
        )

    # ============================================================================
    # Workflow - Helper methods
    # ============================================================================

    @staticmethod
    def _workflow_move_selected_items(
        source: QShelvesWidget,
        target: QShelvesWidget,
    ) -> None:
        """Move current item from source to target list widget."""
        items = source.selectedItems()
        for item in items:
            is_full = (
                max_count := target.max_item_count
            ) != QShelvesWidget.UNLIMITED and max_count <= target.count()
            if is_full:
                return
            target.addItem(source.takeItem(source.row(item)))

    def _management_build_list(self):
        """Refresh the shelves widget with the current shelf names."""
        shelf_manager = manager_module.instance()
        self.shelf_management_shelves.clear()
        self.shelf_management_shelves.addItems(shelf_manager.registered_shelf_names)

    # ============================================================================
    # Event handlers
    # ============================================================================
    def _management_on_list_rows_changed(self) -> None:
        """
        Rebuild shelf names for stages.
        Normally linked to an event, an explicit call should not be necessary.
        """
        self._workflow_build_shelves_for_stages()

    def _management_on_list_selection_changed(self) -> None:
        """Enable / disable the remove button based on selection."""
        self.remove_shelves_button.setEnabled(
            len(self.shelf_management_shelves.selectedItems()) > 0,
        )

    def _workflow_on_lists_changed(self) -> None:
        """Handles the state change for shelves available for workflow stages."""
        # Check for items
        has_items_shelves_for_stages = self.shelves_for_stages.count() > 0
        has_items_stage_1 = self.workflow_stage_1.count() > 0
        has_items_stage_2 = self.workflow_stage_2.count() > 0

        # Check for selected items
        has_selected_items_shelves_for_stages = (
            has_items_shelves_for_stages
            and len(self.shelves_for_stages.selectedItems()) > 0
        )
        has_selected_items_stage_1 = (
            has_items_stage_1 and len(self.workflow_stage_1.selectedItems()) > 0
        )
        has_selected_items_stage_2 = (
            has_items_stage_2 and len(self.workflow_stage_2.selectedItems()) > 0
        )

        # Check for full lists
        is_full_shelves_for_stages = (
            (max_count := self.shelves_for_stages.max_item_count)
            != QShelvesWidget.UNLIMITED
            and max_count <= self.shelves_for_stages.count()
        )
        is_full_stage_1 = (
            max_count := self.workflow_stage_1.max_item_count
        ) != QShelvesWidget.UNLIMITED and max_count <= self.workflow_stage_1.count()
        is_full_stage_2 = (
            max_count := self.workflow_stage_2.max_item_count
        ) != QShelvesWidget.UNLIMITED and max_count <= self.workflow_stage_2.count()

        # Update buttons accordingly
        self.button_all_to_stage_1.setEnabled(
            has_selected_items_shelves_for_stages and not is_full_stage_1,
        )
        self.button_all_to_stage_2.setEnabled(
            has_selected_items_shelves_for_stages and not is_full_stage_2,
        )

        self.button_stage_1_to_all.setEnabled(
            has_selected_items_stage_1 and not is_full_shelves_for_stages,
        )
        self.button_stage_1_to_stage_2.setEnabled(
            has_selected_items_stage_1 and not is_full_stage_2,
        )

        self.button_stage_2_to_all.setEnabled(
            has_selected_items_stage_2 and not is_full_shelves_for_stages,
        )

        self.button_stage_2_to_stage_1.setEnabled(
            has_selected_items_stage_2 and not is_full_stage_1,
        )

        # Update tooltips
        tooltip_to_stage_1 = self._tooltip_to_stage_is_full_or_not(
            NAME_WORKFLOW_STAGE_1,
            is_full=is_full_stage_1,
        )
        tooltip_to_stage_2 = self._tooltip_to_stage_is_full_or_not(
            NAME_WORKFLOW_STAGE_2,
            is_full=is_full_stage_2,
        )

        self.button_all_to_stage_1.setToolTip(tooltip_to_stage_1)
        self.button_stage_2_to_stage_1.setToolTip(tooltip_to_stage_1)

        self.button_all_to_stage_2.setToolTip(tooltip_to_stage_2)
        self.button_stage_1_to_stage_2.setToolTip(tooltip_to_stage_2)

    @staticmethod
    def _tooltip_to_stage_is_full_or_not(
        stage_name: str,
        is_full: Optional[bool] = False,
    ) -> str:
        """Generates a tooltip message based on the state of the target."""
        if is_full:
            return MESSAGE_MOVE_SELECTED_ITEMS_DISABLED.format(
                name_of_target_stage=stage_name,
            )
        return MESSAGE_MOVE_SELECTED_ITEMS_ENABLED.format(
            name_of_target_stage=stage_name,
        )
