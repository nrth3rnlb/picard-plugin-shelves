"""
Tests for the options options_page logic.
"""

import sys
import unittest
from copy import copy, deepcopy
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

        self.known_shelves = ["Incoming", "Standard", "Soundtracks", "Favorites"]
        self.number_known_shelves = len(self.known_shelves)
        self.config_setting = {
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: self.known_shelves[
                : self.number_known_shelves - 2
            ],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: self.known_shelves[
                self.number_known_shelves - 1 :
            ],
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: False,
            ShelfConstants.CONFIG_MOVE_FILES_TO_KEY: "/music",
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: self.known_shelves,
            ShelfConstants.CONFIG_ACTIVE_TAB: 1,
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

    def test_all_options_used(self):
        for option in OptionsPage.options:
            with self.subTest(option=option.name):
                self.assertIn(option.name, self.config_setting)

    @patch("shelves.ui.options.config")
    def test_save_writes_to_config(self, mock_config):
        """Test if the save method correctly writes UI _shelf_state to config."""
        # Arrange
        mock_config.setting = copy(self.config_setting)

        self.options_page.workflow_stage_1.return_value = self.config_setting[
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY
        ]
        self.options_page.workflow_stage_2.return_value = self.config_setting[
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY
        ]
        self.options_page.shelf_management_shelves.return_value = self.config_setting[
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY
        ]

        self.options_page.plugin_configuration.currentIndex.return_value = (
            self.config_setting[ShelfConstants.CONFIG_ACTIVE_TAB]
        )
        self.options_page.workflow_enabled.isChecked.return_value = self.config_setting[
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY
        ]
        self.options_page.stage_1_includes_non_shelves.isChecked.return_value = (
            self.config_setting[ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY]
        )

        # Act
        self.options_page.save()

        # Assert
        self.assertEqual(
            self.config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY],
            self.options_page.workflow_stage_1.return_value,
        )
        self.assertEqual(
            self.config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY],
            self.options_page.workflow_stage_2.return_value,
        )
        self.assertEqual(
            self.config.setting[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY],
            self.options_page.shelf_management_shelves.return_value,
        )
        self.assertEqual(
            self.config.setting[ShelfConstants.CONFIG_ACTIVE_TAB],
            self.options_page.plugin_configuration.currentIndex(),
        )
        self.assertEqual(
            self.config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY],
            self.options_page.workflow_enabled.isChecked(),
        )
        self.assertEqual(
            self.config.setting[ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY],
            self.options_page.stage_1_includes_non_shelves.isChecked(),
        )

    @patch("shelves.ui.options.ShelfManager")
    @patch("shelves.utils.ShelfUtils.validate_shelf_names")
    def test_load_populates_ui_from_config(
        self, mock_get_configured_shelves, mock_shelf_manager
    ):
        """Test if the load method correctly populates UI from config."""
        # Arrange
        mock_get_configured_shelves.return_value = self.config.setting[
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY
        ]
        mock_instance = mock_shelf_manager.return_value

        self.config.setting = {
            ShelfConstants.CONFIG_ACTIVE_TAB: 0,
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: self.known_shelves,
            ShelfConstants.CONFIG_MOVE_FILES_TO_KEY: "/music",
            ShelfConstants.CONFIG_RENAME_SNIPPET_SKELETON_KEY: ShelfConstants.RENAME_SNIPPET,
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
        }
        self.options_page.naming_script_code.setPlainText = MagicMock()
        self.options_page.plugin_configuration.setCurrentIndex = MagicMock()
        self.options_page.shelf_management_shelves.addItems = MagicMock()
        self.options_page.stage_1_includes_non_shelves.setChecked = MagicMock()
        self.options_page.workflow_enabled.setChecked = MagicMock()

        # Act
        self.options_page.load()

        # Assert
        self.assertEqual(
            mock_instance.base_path,
            self.config.setting[ShelfConstants.CONFIG_MOVE_FILES_TO_KEY],
        )
        self.options_page.shelf_management_shelves.addItems.assert_called_once()
        self.assertSetEqual(
            mock_instance.shelf_names,
            set(self.config.setting[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY]),
        )

        self.options_page.plugin_configuration.setCurrentIndex.assert_called_with(
            self.config.setting[ShelfConstants.CONFIG_ACTIVE_TAB]
        )
        self.options_page.stage_1_includes_non_shelves.setChecked.assert_called_with(
            self.config.setting[ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY]
        )
        self.options_page.naming_script_code.setPlainText.assert_called_with(
            self.config.setting[ShelfConstants.CONFIG_RENAME_SNIPPET_SKELETON_KEY]
        )
        self.options_page.workflow_enabled.setChecked.assert_called_with(
            self.config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY]
        )

    @patch("shelves.utils.ShelfUtils.validate_shelf_names")
    def test_load_no_configured_shelves(self, mock_validate_shelf_names):
        """Test if the load method correctly handles no configured shelves."""
        # Arrange
        self.config.setting = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: [],
            ShelfConstants.CONFIG_ACTIVE_TAB: 0,
            ShelfConstants.CONFIG_MOVE_FILES_TO_KEY: "/music",
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: True,
        }

        mock_validate_shelf_names.return_value = []
        self.options_page.shelf_management_shelves.count.return_value = 0
        self.options_page._scan_for_shelves = MagicMock()

        # Act
        self.options_page.load()

        # Assert
        self.options_page.shelf_management_shelves.addItems.assert_called_once()
        self.options_page._scan_for_shelves.assert_called_once()

    @patch(
        "shelves.ui.options.QtWidgets.QInputDialog.getText",
        return_value=("NewShelf", True),
    )
    def test_add_shelf(self, _mock_get_text):
        """Test adding a new, valid shelf_name."""
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
        self.options_page.shelf_management_shelves.sortItems.assert_called_once()

    @patch("shelves.ui.options.ShelfManager.shelf_names", new_callable=PropertyMock)
    def test_remove_shelf(self, mock_shelf_names):
        """Test removing a selected shelf_name."""
        # Arrange
        mock_shelf_names.return_value = deepcopy(self.known_shelves)

        mock_item = MagicMock()
        mock_item.text.return_value = self.known_shelves[0]
        self.options_page.shelf_management_shelves.selectedItems.return_value = [
            mock_item
        ]

        # Act
        self.options_page._remove_shelf()

        # Assert
        self.assertIn(mock_item.text.return_value, self.known_shelves)

    @patch("shelves.ui.options.ShelfManager.shelf_names", new_callable=PropertyMock)
    @patch("shelves.utils.ShelfUtils.get_shelf_dirs")
    def test_remove_unknown_shelves(self, mock_get_existing_dirs, mock_shelf_names):
        """Test removing unknown shelves."""
        # Arrange
        mock_shelf_names.return_value = deepcopy(self.known_shelves)
        mock_items = {}
        for name in mock_shelf_names.return_value:
            mock_item = MagicMock()
            mock_item.text.return_value = name
            mock_items[name] = [mock_item]

        mock_get_existing_dirs.return_value = deepcopy(self.known_shelves)
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
        self.options_page.shelf_management_shelves.takeItem.assert_called_once()


if __name__ == "__main__":
    unittest.main()
