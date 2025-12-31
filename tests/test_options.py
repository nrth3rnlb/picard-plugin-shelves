"""
Tests for the options options_page logic.
"""

import sys
import unittest
from copy import deepcopy
from unittest.mock import MagicMock, PropertyMock, patch

from PyQt5.QtWidgets import QApplication

from shelves.constants import ShelfConstants
from shelves.ui.options import OptionsPage


class OptionsPageTest(unittest.TestCase):
    """
    Tests for the OptionsPage logic.
    """

    UI_ATTRS = list(OptionsPage.__annotations__.keys())

    @classmethod
    def setUpClass(cls):
        if QApplication.instance() is None:
            cls._app = QApplication(sys.argv)

    def setUp(self):
        """Set up a mock OptionsPage _instance."""
        self.options_page = OptionsPage()

        # Manually mock all UI elements that might be touched.
        for attr in self.UI_ATTRS:
            setattr(self.options_page, attr, MagicMock())

        self.test_known_shelves = ["Incoming", "Standard", "Soundtracks", "Favorites"]
        self.test_number_known_shelves = len(self.test_known_shelves)
        self.test_configuration = {
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
            ShelfConstants.CONFIG_MOVE_FILES_TO_KEY: "/music",
        }

        # Mapping zwischen Config-Keys und Attributnamen der OptionsPage
        self.mapping = {
            ShelfConstants.CONFIG_ACTIVE_TAB: self.options_page.plugin_configuration,
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: self.options_page.shelf_management_shelves,
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: self.options_page.stage_1_includes_non_shelves,
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: self.options_page.workflow_enabled,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: self.options_page.workflow_stage_1,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: self.options_page.workflow_stage_2,
        }

        # Create a config mock and patch the module-level `shelves.ui.options.config`
        self.config = MagicMock()
        # Share the same dict so tests that mutate config.setting see the changes
        self.config.setting = self.test_configuration
        self._config_patcher = patch("shelves.ui.options.config", new=self.config)
        self._config_patcher.start()
        self.addCleanup(self._config_patcher.stop)

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
        for option in OptionsPage.options:
            with self.subTest(option=option.name):
                self.assertIn(option.name, self.test_configuration)

    @patch("shelves.ui.options.config")
    def test_save_writes_to_config(self, mock_config):
        """Test if the save method correctly writes UI state to config."""
        # Arrange
        mock_config.setting = {}

        for option in OptionsPage.options:
            if option.name in self.mapping:
                widget = self.mapping[option.name]
                self.setup_ui_mock(widget, self.test_configuration[option.name])

        # We patch the property of the OptionsPage that is read in the save()
        with patch.object(
            OptionsPage, "shelf_names", new_callable=PropertyMock
        ) as mock_prop:
            mock_prop.return_value = set(self.test_known_shelves)

            # Act
            self.options_page.save()

        # Assert
        for key in self.mapping.keys():
            with self.subTest(key=key):
                actual = mock_config.setting.get(key)
                expected_value = self.test_configuration[key]
                if isinstance(expected_value, (list, set)):
                    self.assertSetEqual(set(actual), set(expected_value))
                else:
                    self.assertEqual(actual, expected_value)

    @patch("shelves.ui.options.ShelfManager")
    def test_load_populates_ui_from_config(self, mock_shelf_manager):
        """Test if the load method correctly populates UI from config."""
        # Act
        self.options_page.load()

        # Assert
        for key in self.mapping.keys():
            with self.subTest(key=key):
                actual = self.config.setting[key]
                expected_value = self.test_configuration[key]
                if isinstance(expected_value, (list, set)):
                    self.assertSetEqual(set(actual), set(expected_value))
                else:
                    self.assertEqual(actual, expected_value)

    @patch(
        "shelves.ui.options.QtWidgets.QInputDialog.getText",
    )
    @patch("shelves.ui.options.ShelfManager.shelf_names", new_callable=PropertyMock)
    def test_add_shelf(self, mock_shelf_names, mock_get_text):
        """Test adding a new, valid shelf_name."""
        # Arrange
        mock_shelf_names.return_value = deepcopy(self.test_known_shelves)
        popped = mock_shelf_names.return_value.pop()
        mock_get_text.return_value = (popped, True)

        # Act
        self.options_page._add_shelf()

        # Assert
        expected_shelves = deepcopy(self.test_known_shelves)
        mock_shelf_names.assert_called_with(set(expected_shelves))

    @patch("shelves.ui.options.ShelfManager.shelf_names", new_callable=PropertyMock)
    def test_remove_shelf(self, mock_shelf_names):
        """Test removing a selected shelf_name."""
        # Arrange
        mock_shelf_names.return_value = deepcopy(self.test_known_shelves)
        possible_selections_text = deepcopy(self.test_known_shelves)
        selected_text = possible_selections_text.pop()
        mock_item = MagicMock()
        mock_item.text.return_value = selected_text
        self.options_page.shelf_management_shelves.selectedItems.return_value = [
            mock_item
        ]

        # Act
        self.options_page._remove_shelf()

        # Assert
        expected_shelves = possible_selections_text
        mock_shelf_names.assert_called_with(set(expected_shelves))

    @patch("shelves.ui.options.ShelfManager.shelf_names", new_callable=PropertyMock)
    @patch("shelves.utils.ShelfUtils.get_shelf_dirs")
    def test_remove_unknown_shelves(self, mock_get_shelf_dirs, mock_shelf_names):
        """Test removing unknown shelves."""
        # Arrange
        mock_shelf_names.return_value = deepcopy(self.test_known_shelves)
        mock_items = {}
        for name in mock_shelf_names.return_value:
            mock_item = MagicMock()
            mock_item.text.return_value = name
            mock_items[name] = [mock_item]

        mock_get_shelf_dirs.return_value = deepcopy(self.test_known_shelves)
        popped = mock_get_shelf_dirs.return_value.pop()

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

        # Act
        self.options_page._remove_unknown_shelves()

        # Assert
        expected_shelves = mock_get_shelf_dirs.return_value
        mock_shelf_names.assert_called_with(set(expected_shelves))

    @patch("shelves.ui.options.ShelfManager.shelf_names", new_callable=PropertyMock)
    @patch("shelves.utils.ShelfUtils.get_shelf_dirs")
    def test_scan_for_shelves(self, mock_get_shelf_dirs, mock_shelf_names):
        """Test scanning for shelves adds them to the shelf management list."""
        # Arrange
        mock_get_shelf_dirs.return_value = deepcopy(self.test_known_shelves)
        mock_shelf_names.return_value = deepcopy(self.test_known_shelves)
        popped = mock_shelf_names.return_value.pop()
        mock_items = {}
        for name in mock_shelf_names.return_value:
            mock_item = MagicMock()
            mock_item.text.return_value = name
            mock_items[name] = [mock_item]
        self.options_page._get_configured_shelves = MagicMock(return_value={"Incoming"})

        # Act
        self.options_page._scan_for_shelves()

        # Assert
        expected_shelves = deepcopy(self.test_known_shelves)
        mock_shelf_names.assert_called_with(set(expected_shelves))


if __name__ == "__main__":
    unittest.main()
