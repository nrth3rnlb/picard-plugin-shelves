from __future__ import annotations

from gettext import gettext as _

from picard import config
from PyQt5 import QtWidgets

from .. import manager as manager_module
from .. import utils
from ..typings import ConfigKey
from ..ui.widgets import QShelvesWidget
from .constants import (
    MESSAGE_INVALID_SHELF_NAME,
    MESSAGE_PROVIDE_SHELF_NAME,
    MESSAGE_USED_SHELF_NAME,
    TITLE_ADD_SHELF_NAME,
    TITLE_REMOVE_SHELF_NAMES,
)


class ManagementOptionsMixin:
    add_shelf_button: QtWidgets.QPushButton
    on_workflow_enabled: bool
    remove_shelves_button: QtWidgets.QPushButton
    remove_unknown_shelves_button: QtWidgets.QPushButton
    scan_for_shelf_names_button: QtWidgets.QPushButton
    shelf_management_shelves: QShelvesWidget
    shelves_for_stages: QShelvesWidget
    workflow_stage_1: QShelvesWidget
    workflow_stage_2: QShelvesWidget

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
        self._management_build_shelves_for_stages()

    def _management_on_list_selection_changed(self) -> None:
        """Enable / disable the remove button based on selection."""
        self.remove_shelves_button.setEnabled(
            len(self.shelf_management_shelves.selectedItems()) > 0,
        )

    # noinspection PyTypeHints
    def _management_build_shelves_for_stages(self) -> None:
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
            shelf_manager.registered_shelf_names.intersection(  # noqa: F821
                config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES]
            )
        )
