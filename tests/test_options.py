"""
Tests for the options options_page logic.
"""

import copy
import sys
import unittest
from unittest.mock import MagicMock, PropertyMock, call, patch

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

        self.known_shelves = {"Incoming", "Standard", "Soundtracks", "Favorites"}
        self.config_setting = {
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: False,
            ShelfConstants.CONFIG_MOVE_FILES_TO_KEY: "/music",
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: self.known_shelves,
        }

        # Create a config mock and patch the module-level `shelves.ui.options.config`
        self.config = MagicMock()
        # Share the same dict so tests that mutate config.setting see the changes
        self.config.setting = self.config_setting
        self._config_patcher = patch("shelves.ui.options.config", new=self.config)
        self._config_patcher.start()
        self.addCleanup(self._config_patcher.stop)

    def test_options_use_correct_namespace(self):
        """Test that all options use the correct namespace 'setting'."""
        for option in OptionsPage.options:
            with self.subTest(option=option.name):
                self.assertEqual(
                    option.section,
                    "setting",
                    f"Option '{option.name}' uses incorrect namespace '{option.section}' instead of 'setting'",
                )

    @patch("shelves.ui.options.config")
    def test_save_writes_to_config(self, mock_config):
        """Test if the save method correctly writes UI _state to config."""
        # Arrange
        mock_config.setting = self.config_setting
        mock_config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY] = False

        # Because I simply can't or don't want to remember it:
        # MagicMock(ret_value=...), this sets the return value when the mock is called, NOT for item.text()
        # mock_item.text.return_value sets the return value for item.text()
        mock_item_1 = MagicMock()
        mock_item_1.text.return_value = "Incoming"
        mock_item_2 = MagicMock()
        mock_item_2.text.return_value = "Standard"

        self.options_page.plugin_configuration.currentIndex.return_value = (
            0  # CONFIG_ACTIVE_TAB
        )
        self.options_page.shelf_management_shelves.item.side_effect = [
            mock_item_1,
            mock_item_2,
        ]
        self.options_page.shelf_management_shelves.count.return_value = 2
        self.options_page.workflow_enabled.isChecked.return_value = (
            True  # CONFIG_WORKFLOW_ENABLED_KEY
        )
        self.options_page.workflow_stage_1.item.side_effect = [
            mock_item_1
        ]  # CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY
        self.options_page.workflow_stage_2.item.side_effect = [
            mock_item_2
        ]  # CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY

        # Act
        self.options_page.save()

        # Assert
        self.assertSetEqual(
            set(
                self.config_setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY]
            ),
            {"Incoming"},
        )
        self.assertSetEqual(
            set(
                self.config_setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY]
            ),
            {"Standard"},
        )
        self.assertSetEqual(
            set(self.config_setting[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY]),
            {"Incoming", "Standard"},
        )
        self.assertTrue(self.config_setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY])
        self.assertEqual(self.config_setting[ShelfConstants.CONFIG_ACTIVE_TAB], 0)

    @patch("shelves.utils.ShelfUtils.validate_shelf_names")
    def test_load_populates_ui_from_config(self, mock_get_configured_shelves):
        """Test if the load method correctly populates UI from config."""
        # Arrange
        self.config.setting = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_ACTIVE_TAB: 0,
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: True,
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: self.known_shelves,
        }
        mock_get_configured_shelves.return_value = self.config.setting[
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY
        ]

        # Act
        self.options_page.load()

        self.assertSetEqual(self.options_page.shelf_names, self.known_shelves)

        self.options_page.workflow_enabled.setChecked.assert_called_with(True)
        self.options_page.stage_1_includes_non_shelves.setChecked.assert_called_with(
            True
        )
        self.options_page.plugin_configuration.setCurrentIndex.assert_called_with(0)
        self.assertSetEqual(
            set(self.config.setting[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY]),
            self.options_page.shelf_names,
        )

    @patch("shelves.utils.ShelfUtils.validate_shelf_names")
    def test_load_no_configured_shelves(self, mock_validate_shelf_names):
        """Test if the load method correctly handles no configured shelves."""
        # Arrange
        self.config.setting = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: [],
            ShelfConstants.CONFIG_ACTIVE_TAB: 0,
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: True,
        }

        mock_validate_shelf_names.return_value = []
        self.options_page.shelf_management_shelves.count.return_value = 0
        self.options_page._scan_for_shelves = MagicMock()

        # Act
        self.options_page.load()

        print(self.options_page.shelf_names)
        # Assert
        self.options_page.shelf_management_shelves.addItems.assert_called_once()
        self.options_page._scan_for_shelves.assert_called_once()
        self.assertSetEqual(self.options_page.shelf_names, set())

    @patch(
        "shelves.ui.options.QtWidgets.QInputDialog.getText",
        return_value=("NewShelf", True),
    )
    def test_add_shelf(self, _mock_get_text):
        """Test adding a new, valid shelf."""
        # Arrange
        self.options_page._get_configured_shelves = MagicMock(return_value={"Incoming"})
        self.options_page.shelf_management_shelves.sortItems = MagicMock()
        self.options_page._rebuild_shelves_for_stages = MagicMock()
        self.options_page.shelf_management_shelves.addItem = MagicMock()

        # Act
        self.options_page._add_shelf()

        # Assert
        self.options_page.shelf_management_shelves.addItem.assert_called_with(
            "NewShelf"
        )
        shelf_names = {shelf_name for shelf_name in self.options_page.shelf_names}
        self.assertIn("NewShelf", shelf_names)
        self.options_page.shelf_management_shelves.sortItems.assert_called_once()

    @patch("shelves.ui.options.OptionsPage.shelf_names", new_callable=PropertyMock)
    def test_remove_shelf(self, mock_shelf_names):
        """Test removing a selected shelf."""
        # Arrange
        mock_shelf_names.return_value: set[str] = copy.deepcopy(self.known_shelves)

        mock_item = MagicMock()
        mock_item.text.return_value = (
            enumerate(mock_shelf_names.return_value)
        ).__next__()[1]
        self.options_page.shelf_management_shelves.selectedItems.return_value = [
            mock_item
        ]

        # Act
        self.options_page._remove_shelf()

        # Assert
        self.assertIn(mock_item.text.return_value, self.known_shelves)
        self.assertNotIn(mock_item.text.return_value, mock_shelf_names.return_value)

    @patch("shelves.ui.options.OptionsPage.shelf_names", new_callable=PropertyMock)
    @patch("shelves.utils.ShelfUtils.get_shelf_dirs")
    def test_remove_unknown_shelves(self, mock_get_existing_dirs, mock_shelf_names):
        """Test removing unknown shelves."""
        # Arrange
        mock_shelf_names.return_value = copy.deepcopy(self.known_shelves)
        mock_items = {}
        for name in mock_shelf_names.return_value:
            mock_item = MagicMock()
            mock_item.text.return_value = name
            mock_items[name] = [mock_item]

        mock_get_existing_dirs.return_value = copy.deepcopy(self.known_shelves)
        popped = mock_get_existing_dirs.return_value.pop()

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
        self.assertNotIn(popped, self.options_page.shelf_names)
        self.assertSetEqual(
            mock_get_existing_dirs.return_value, self.options_page.shelf_names
        )
        self.assertEqual(
            mock_get_existing_dirs.return_value, mock_shelf_names.return_value
        )


if __name__ == "__main__":
    unittest.main()
