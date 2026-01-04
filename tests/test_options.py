"""
Tests for the options options_page logic.
"""

import sys
import unittest
from copy import deepcopy
from unittest.mock import MagicMock, patch

from picard.config import BoolOption, IntOption, ListOption
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication

from shelves.constants import ShelfConstants
from shelves.ui.options import OptionsPage


class OptionsPageTest(unittest.TestCase):
    """
    Tests for the OptionsPage logic.
    """

    # ============================================================================
    # Class attributes
    # ============================================================================
    UI_ATTRS = list(OptionsPage.__annotations__.keys())

    # ============================================================================
    # Setup and teardown
    # ============================================================================
    @classmethod
    def setUpClass(cls):
        """Set up QApplication once for all tests."""
        if QApplication.instance() is None:
            cls._app = QApplication(sys.argv)

    def setUp(self):
        """Set up test fixtures."""
        self.options_page = OptionsPage()

        # Manually mock all UI elements that might be touched.
        for attr in self.UI_ATTRS:
            setattr(self.options_page, attr, MagicMock())

        self.test_known_shelves = [
            "Incoming",
            "Standard",
            "Soundtracks",
            "Favorites",
            "Soundtracks: Games",
            "Soundtracks - Movies",
        ]
        self.test_number_known_shelves = len(self.test_known_shelves)
        self.test_configuration: dict[
            str,
            str | list[str] | bool | int,
        ] = {
            ShelfConstants.CONFIG_ACTIVE_TAB: 1,
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: self.test_known_shelves,
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: self.test_known_shelves[
                : self.test_number_known_shelves - 2
            ],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: self.test_known_shelves[
                self.test_number_known_shelves - 1 :
            ],
            ShelfConstants.CONFIG_ALBUM_SHELF_KEY: ShelfConstants.TAG_KEY,
            ShelfConstants.CONFIG_MOVE_FILES_TO_KEY: "/music",
        }

        self.widget_config = {
            ShelfConstants.CONFIG_ACTIVE_TAB: {
                "option_class": IntOption,
                "widget": self.options_page.plugin_configuration,
                "setter": "setCurrentIndex",
                "getter": "currentIndex",
            },
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: {
                "option_class": ListOption,
                "widget": self.options_page.shelf_management_shelves,
                "setter": "addItems",
                "getter": None,
            },
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: {
                "option_class": BoolOption,
                "widget": self.options_page.stage_1_includes_non_shelves,
                "setter": "setChecked",
                "getter": "isChecked",
            },
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: {
                "option_class": BoolOption,
                "widget": self.options_page.workflow_enabled,
                "setter": "setChecked",
                "getter": "isChecked",
            },
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: {
                "option_class": ListOption,
                "widget": self.options_page.workflow_stage_1,
                "setter": "addItems",
                "getter": None,
            },
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: {
                "option_class": ListOption,
                "widget": self.options_page.workflow_stage_2,
                "setter": "addItems",
                "getter": None,
            },
        }

        # Create a config mock and patch the module-level `shelves.ui.options.config`
        self.config = MagicMock()
        # Share the same dict so tests that mutate config.setting see the changes
        self.config.setting = self.test_configuration
        self._config_patcher = patch("shelves.ui.options.config", new=self.config)
        self._config_patcher.start()
        self.addCleanup(self._config_patcher.stop)

    # ============================================================================
    # Helper methods
    # ============================================================================
    @staticmethod
    def setup_ui_mock(widget, value):
        """Configures a mock based on the data type of the value."""
        if isinstance(value, (list, set)):
            items = []
            for text in value:
                item = MagicMock()
                item.text.return_value = text
                items.append(item)
            widget.count.return_value = len(items)
            widget.item.side_effect = items
        elif isinstance(value, bool):
            widget.isChecked.return_value = value
        elif isinstance(value, int):
            widget.currentIndex.return_value = value
        return value

    # ============================================================================
    # Configuration tests
    # ============================================================================
    def test_options_use_correct_namespace(self):
        """Test that all options use the correct namespace 'setting'."""
        for option in OptionsPage.options:
            with self.subTest(option=option.name):
                self.assertEqual(
                    option.section,
                    "setting",
                    f"Option '{option.name}' uses incorrect namespace '{option.section}' instead of 'setting'",
                )

    def test_all_options_used(self):
        """Test that all options are present in test configuration."""
        for option in OptionsPage.options:
            with self.subTest(option=option.name):
                self.assertIn(option.name, self.test_configuration)

    # ============================================================================
    # Load/Save tests
    # ============================================================================
    @patch("shelves.ui.options.config")
    def test_save_writes_to_config_empty_shelves(self, mock_config):
        """Test if the save method correctly writes UI state to config with empty shelves."""
        # Arrange
        _test_configuration = deepcopy(self.test_configuration)
        _test_configuration[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY] = []
        _test_configuration[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY] = []
        _test_configuration[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY] = []

        mock_config.setting = {}

        for option in OptionsPage.options:
            if option.name in self.widget_config:
                widget = self.widget_config[option.name]["widget"]
                self.setup_ui_mock(widget, _test_configuration[option.name])

        # We patch the property of the OptionsPage that is read in the save()
        with patch.object(
            OptionsPage, "registered_shelf_names"
        ) as mock_registered_shelf_names:
            mock_registered_shelf_names.return_value = _test_configuration[
                ShelfConstants.CONFIG_KNOWN_SHELVES_KEY
            ]

            # Act
            self.options_page.save()

        # Assert
        for key in self.widget_config.keys():
            with self.subTest(key=key):
                actual = mock_config.setting.get(key)
                expected_value = _test_configuration[key]
                if isinstance(expected_value, (list, set)):
                    self.assertSetEqual(set(actual), set(expected_value))
                else:
                    self.assertEqual(actual, expected_value)

    @patch("shelves.ui.options.config")
    def test_save_writes_to_config_with_shelves(self, mock_config):
        """Test if the save method correctly writes UI state to config with shelves."""
        # Arrange
        _test_configuration = deepcopy(self.test_configuration)

        mock_config.setting = {}
        for option in OptionsPage.options:
            if option.name in self.widget_config:
                widget = self.widget_config[option.name]["widget"]
                self.setup_ui_mock(widget, _test_configuration[option.name])

        # We patch the property of the OptionsPage that is read in the save()
        with patch.object(
            OptionsPage, "registered_shelf_names"
        ) as mock_registered_shelf_names:
            mock_registered_shelf_names.return_value = set(self.test_known_shelves)
            # Act
            self.options_page.save()

        # Assert
        for key in self.widget_config.keys():
            with self.subTest(key=key):
                actual = mock_config.setting.get(key)
                expected_value = _test_configuration[key]
                if isinstance(expected_value, (list, set)):
                    self.assertSetEqual(set(actual), set(expected_value))
                else:
                    self.assertEqual(actual, expected_value)

    @patch("shelves.ui.options.config")
    def test_load_populates_ui_from_config(self, mock_config: MagicMock) -> None:
        """Test if the load method correctly populates UI from config."""
        # Arrange
        mock_config.setting = self.test_configuration

        # Act
        self.options_page.load()

        # Assert - Check whether the widgets have been given the correct values
        for key, config in self.widget_config.items():
            with self.subTest(key=key):
                option_class = config["option_class"]
                widget = config["widget"]
                setter = config["setter"]

                if option_class == BoolOption:
                    expected_bool_option: bool = self.test_configuration[key]
                    getattr(widget, setter).assert_called_with(expected_bool_option)
                elif option_class == IntOption:
                    expected_int_option: int = self.test_configuration[key]
                    getattr(widget, setter).assert_called_with(expected_int_option)
                elif option_class == ListOption:
                    expected_list_option: list[str] = self.test_configuration[key]
                    # Verify the method was called
                    self.assertTrue(getattr(widget, setter).called)
                    # Get the actual argument and compare as sets
                    actual_arg = getattr(widget, setter).call_args[0][0]
                    self.assertEqual(set(actual_arg), set(expected_list_option))
                else:
                    raise ValueError(f"Unsupported option type: {option_class}")

    # ============================================================================
    # Shelf management tests - Add
    # ============================================================================
    @patch(
        "shelves.ui.options.QtWidgets.QInputDialog.getText",
    )
    @patch.object(OptionsPage, "_register_shelf_names")
    def test_add_valid_shelf(self, mock_register_shelf_names, mock_get_text):
        """Test adding a new, valid shelf_name."""
        # Arrange
        shelf_names = deepcopy(self.test_known_shelves)
        popped = shelf_names.pop()
        mock_get_text.return_value = (popped, True)

        with patch.object(
            OptionsPage, "registered_shelf_names"
        ) as mock_get_registered_shelf_names:
            mock_get_registered_shelf_names.return_value = set(self.test_known_shelves)
            # Act
            self.options_page._action_add_shelf()

            # Assert
            expected_shelves = set(self.test_known_shelves)
            actual = set(mock_register_shelf_names.call_args[0][0])
            self.assertSetEqual(actual, expected_shelves)

    @patch(
        "shelves.ui.options.QtWidgets.QInputDialog.getText",
    )
    @patch(
        "shelves.ui.options.QtWidgets.QMessageBox.warning",
    )
    @patch.object(OptionsPage, "_register_shelf_names")
    @unittest.skipUnless(
        ShelfConstants.INVALID_SHELF_NAME_CHARS,
        "No INVALID_SHELF_NAME_CHARS defined",
    )
    def test_add_invalid_shelf(
        self, mock_register_shelf_names, mock_warning, mock_get_text
    ):
        """Test adding an invalid shelf name shows warning dialog."""
        # Arrange
        _test_known_shelves = deepcopy(self.test_known_shelves)
        popped = _test_known_shelves.pop()
        mock_get_text.return_value = (
            f"{popped}{ShelfConstants.INVALID_SHELF_NAME_CHARS.pop()}",
            True,
        )

        with patch.object(
            OptionsPage, "registered_shelf_names"
        ) as mock_registered_shelf_names:
            mock_registered_shelf_names.return_value = set(self.test_known_shelves)
            # Act
            self.options_page._action_add_shelf()

        # Assert - The warning dialog should have been called
        mock_warning.assert_called_once()
        call_args = mock_warning.call_args
        self.assertEqual(call_args[1]["title"], "Invalid Name")

    # ============================================================================
    # Shelf management tests - Remove
    # ============================================================================
    @patch.object(OptionsPage, "_register_shelf_names")
    def test_remove_shelf(self, mock_register_shelf_names):
        """Test removing a selected shelf_name without conflicts."""
        # Arrange
        possible_selections_text = deepcopy(self.test_known_shelves)
        selected_text = possible_selections_text.pop()
        mock_item = MagicMock()
        mock_item.text.return_value = selected_text
        self.options_page.shelf_management_shelves.selectedItems.return_value = [
            mock_item
        ]

        with patch.object(
            OptionsPage, "registered_shelf_names"
        ) as mock_registered_shelf_names:
            mock_registered_shelf_names.return_value = set(self.test_known_shelves)
            # Act
            self.options_page._action_remove_shelves()

        # Assert
        expected_shelves = set(possible_selections_text)
        actual = set(mock_register_shelf_names.call_args[0][0])
        self.assertSetEqual(actual, expected_shelves)

    @patch(
        "shelves.ui.options.QtWidgets.QMessageBox.question",
    )
    @patch.object(OptionsPage, "_register_shelf_names")
    def test_remove_shelves_with_conflicts(
        self, mock_register_shelf_names, mock_question
    ):
        """Test removing shelves that are used in workflow shows confirmation dialog."""
        # Arrange
        _test_configuration = deepcopy(self.test_configuration)
        _test_known_shelves = deepcopy(self.test_known_shelves)

        _mock_selected_item = MagicMock()
        _selected_item_text = _test_known_shelves.pop()
        _mock_selected_item.text.return_value = _selected_item_text
        self.options_page.shelf_management_shelves.selectedItems.return_value = [
            _mock_selected_item
        ]

        _stage_1_items = []
        for _name in _test_known_shelves:
            _mock = MagicMock()
            _mock.text.return_value = _name
            _stage_1_items.append(_mock)
        self.options_page.workflow_stage_1.count.return_value = len(_stage_1_items)
        self.options_page.workflow_stage_1.item.side_effect = lambda i: (
            _stage_1_items[i] if i < len(_stage_1_items) else None
        )

        _stage_2_items = [_mock_selected_item]
        self.options_page.workflow_stage_2.count.return_value = len(_stage_2_items)
        self.options_page.workflow_stage_2.item.side_effect = lambda i: (
            _stage_2_items[i] if i < len(_stage_2_items) else None
        )

        with patch.object(
            OptionsPage, "registered_shelf_names"
        ) as _mock_registered_shelf_names:
            _mock_registered_shelf_names.return_value = set(self.test_known_shelves)

            # Act
            self.options_page._action_remove_shelves()

        # Assert - The dialog should have been called because there's a conflict
        mock_question.assert_called_once()
        call_args = mock_question.call_args
        self.assertEqual(call_args[1]["title"], "Remove Workflow Shelves?")
        self.assertEqual(
            call_args[1]["text"],
            f"The shelf name(s) '{_selected_item_text}' are used in your workflow. Are you sure you want to remove "
            f"them?",
        )
        self.assertEqual(
            call_args[1]["buttons"],
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )

    @patch("shelves.utils.ShelfUtils.get_shelf_dirs")
    @patch("shelves.ui.options.ShelfManager")
    @patch.object(OptionsPage, "_register_shelf_names")
    def test_remove_unknown_shelves(
        self, mock_register_shelf_names, mock_shelf_manager, mock_get_shelf_dirs
    ):
        """Test removing unknown shelves that no longer exist in filesystem."""
        # Arrange
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance
        mock_manager_instance.shelf_names = deepcopy(self.test_known_shelves)

        mock_items = {}
        for name in self.test_known_shelves:
            mock_item = MagicMock()
            mock_item.text.return_value = name
            mock_items[name] = [mock_item]

        shelf_dirs = set(deepcopy(self.test_known_shelves))
        popped = shelf_dirs.pop()
        mock_get_shelf_dirs.return_value = shelf_dirs

        self.options_page.shelf_management_shelves.takeItem = MagicMock()

        def find_items_side_effect(text, flags):
            """Mock findItems method"""
            _flags = flags
            return mock_items.get(text, [])

        self.options_page.shelf_management_shelves.findItems.side_effect = (
            find_items_side_effect
        )
        self.options_page.shelf_management_shelves.row.side_effect = lambda item: list(
            mock_items.keys()
        ).index(item.text())

        with patch.object(
            OptionsPage, "registered_shelf_names"
        ) as mock_registered_shelf_names:
            mock_registered_shelf_names.return_value = set(self.test_known_shelves)
            # Act
            self.options_page._action_intersect_shelves()

        # Assert
        expected_shelves = shelf_dirs
        actual = set(mock_register_shelf_names.call_args[0][0])
        self.assertSetEqual(actual, expected_shelves)

    # ============================================================================
    # Shelf management tests - Scan
    # ============================================================================
    @patch("shelves.utils.ShelfUtils.get_shelf_dirs")
    @patch.object(OptionsPage, "_add_shelf_names")
    def test_scan_for_shelves(self, mock_add_shelf_names, mock_get_shelf_dirs):
        """Test scanning for shelves adds them to the shelf management list."""
        # Arrange
        mock_get_shelf_dirs.return_value = deepcopy(self.test_known_shelves)

        # Act
        self.options_page._action_scan_for_shelf_names()

        # Assert
        expected_shelves = deepcopy(self.test_known_shelves)
        mock_add_shelf_names.assert_called_with(expected_shelves)


if __name__ == "__main__":
    unittest.main()
