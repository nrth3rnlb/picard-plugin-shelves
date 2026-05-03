from __future__ import annotations

from typing import Optional

from picard import log
from PyQt5 import QtCore, QtWidgets

from ..ui.widgets import QShelvesWidget
from .constants import (
    MESSAGE_MOVE_SELECTED_ITEMS_DISABLED,
    MESSAGE_MOVE_SELECTED_ITEMS_ENABLED,
    NAME_WORKFLOW_STAGE_1,
    NAME_WORKFLOW_STAGE_2,
    NAME_WORKFLOW_STAGE_ALL,
)


class WorkflowOptionsMixin:
    shelves_for_stages: QShelvesWidget
    workflow_stage_1: QShelvesWidget
    workflow_stage_2: QShelvesWidget
    button_all_to_stage_1: QtWidgets.QPushButton
    button_all_to_stage_2: QtWidgets.QPushButton
    button_stage_1_to_all: QtWidgets.QPushButton
    button_stage_1_to_stage_2: QtWidgets.QPushButton
    button_stage_2_to_stage_1: QtWidgets.QPushButton
    label_workflow_stage_1: QtWidgets.QLabel
    label_workflow_stage_2: QtWidgets.QLabel
    workflow_enabled: QtWidgets.QCheckBox
    button_stage_2_to_all: QtWidgets.QPushButton
    button_stage_2_to_stage_1: QtWidgets.QPushButton
    go_down_icon: QtWidgets.QIcon
    go_previous_icon: QtWidgets.QIcon
    go_up_icon: QtWidgets.QIcon
    go_next_icon: QtWidgets.QIcon

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

        tooltip_to_all = self._workflow_tooltip_to_stage_is_full_or_not(
            NAME_WORKFLOW_STAGE_ALL
        )
        tooltip_to_stage_1 = self._workflow_tooltip_to_stage_is_full_or_not(
            NAME_WORKFLOW_STAGE_1,
        )
        tooltip_to_stage_2 = self._workflow_tooltip_to_stage_is_full_or_not(
            NAME_WORKFLOW_STAGE_2,
        )

        self.button_stage_1_to_stage_2.setToolTip(tooltip_to_stage_2)
        self.button_all_to_stage_1.setToolTip(tooltip_to_stage_1)
        self.button_all_to_stage_2.setToolTip(tooltip_to_stage_2)
        self.button_stage_1_to_all.setToolTip(tooltip_to_all)
        self.button_stage_2_to_all.setToolTip(tooltip_to_all)

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
        tooltip_to_stage_1 = self._workflow_tooltip_to_stage_is_full_or_not(
            NAME_WORKFLOW_STAGE_1,
            is_full=is_full_stage_1,
        )
        tooltip_to_stage_2 = self._workflow_tooltip_to_stage_is_full_or_not(
            NAME_WORKFLOW_STAGE_2,
            is_full=is_full_stage_2,
        )

        self.button_all_to_stage_1.setToolTip(tooltip_to_stage_1)
        self.button_stage_2_to_stage_1.setToolTip(tooltip_to_stage_1)

        self.button_all_to_stage_2.setToolTip(tooltip_to_stage_2)
        self.button_stage_1_to_stage_2.setToolTip(tooltip_to_stage_2)

    @staticmethod
    def _workflow_tooltip_to_stage_is_full_or_not(
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
