"""
Options page for the Shelves plugin.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Protocol

from picard import config
from picard.config import BoolOption, IntOption, ListOption, Option
from picard.ui.options import OptionsPage as PicardOptions
from PyQt5 import QtGui, QtWidgets, uic

from .. import runtime
from ..typings import ConfigKey
from ..ui.widgets import QShelvesWidget
from . import constants
from .management import ManagementOptionsMixin
from .releasetype import ReleaseTypeOptionsMixin
from .workflow import WorkflowOptionsMixin


def _shelf_names_from_widget(
    widget: QShelvesWidget, allowed_names: set[str]
) -> list[str]:
    result = []
    for i in range(widget.count()):
        item = widget.item(i)
        if item is not None and item.text() in allowed_names:
            result.append(item.text())
    return result


class ManagementOptionsPageProtocol(Protocol):
    shelf_management_shelves: QShelvesWidget
    add_shelf_button: QtWidgets.QPushButton
    remove_shelves_button: QtWidgets.QPushButton


class OptionsPage(
    ManagementOptionsMixin, WorkflowOptionsMixin, ReleaseTypeOptionsMixin, PicardOptions
):
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
        super().__init__(parent)
        ui_dir: Path = Path(__file__).parent.parent
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
        self._releasetype_setup_connections()

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
        shelf_manager = runtime.manager_instance()
        registered = shelf_manager.registered_shelf_names

        config.setting[ConfigKey.KNOWN_SHELVES] = _shelf_names_from_widget(
            self.shelf_management_shelves,
            registered,
        )
        config.setting[ConfigKey.WORKFLOW_STAGE_1_SHELVES] = _shelf_names_from_widget(
            self.workflow_stage_1,
            registered,
        )
        config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES] = _shelf_names_from_widget(
            self.workflow_stage_2,
            registered,
        )

        config.setting[ConfigKey.ACTIVE_TAB] = self.plugin_configuration.currentIndex()

        config.setting[ConfigKey.WORKFLOW_ENABLED] = self.workflow_enabled.isChecked()
        config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = (
            self.stage_1_includes_non_shelves.isChecked()
        )
