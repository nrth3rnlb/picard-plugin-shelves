"""
Tests for the options options_page logic.
"""

import unittest
from unittest.mock import MagicMock, patch, call

from PyQt5 import QtWidgets

from shelves.constants import ShelfConstants
from shelves.ui.options import OptionsPage


class AttrDict(dict):
    """A dictionary that allows attribute-style access."""

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class OptionsPageTest(unittest.TestCase):
    """
    Tests for the OptionsPage logic.
    """

    UI_ATTRS = list(OptionsPage.__annotations__.keys())

    def setUp(self):
        """Set up a mock OptionsPage instance."""
        self.options_page: OptionsPage = OptionsPage.__new__(OptionsPage)
        # Manually mock all UI elements that might be touched.
        for attr in self.UI_ATTRS:
            setattr(self.options_page, attr, MagicMock())

        self.config_setting = {
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: False,
            "move_files_to": "/music",
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

    @patch("shelves.ui.options.config", new_callable=MagicMock)
    def test_save_writes_to_config(self, mock_config):
        """Test if the save method correctly writes UI state to config."""
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
        self.assertEqual(
            self.config_setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY],
            ["Incoming"],
        )
        self.assertEqual(
            self.config_setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY],
            ["Standard"],
        )
        self.assertEqual(
            self.config_setting[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY],
            ["Incoming", "Standard"],
        )
        self.assertTrue(self.config_setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY])
        self.assertEqual(self.config_setting[ShelfConstants.CONFIG_ACTIVE_TAB], 0)

    @patch("shelves.utils.ShelfUtils.get_configured_shelves", new_callable=MagicMock)
    def test_load_populates_ui_from_config(self, mock_get_configured_shelves):
        """Test if the load method correctly populates UI from config."""
        # Arrange
        self.config.setting = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: sorted(
                ["Incoming", "Standard", "Stash", "Live"]
            ),
            ShelfConstants.CONFIG_ACTIVE_TAB: 0,
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: True,
        }
        mock_get_configured_shelves.return_value = self.config.setting[
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY
        ]
        self.options_page.shelf_management_shelves.clear = MagicMock()
        self.options_page.shelf_management_shelves.addItems = MagicMock()
        self.options_page.plugin_configuration.setCurrentIndex = MagicMock()
        self.options_page.workflow_enabled.setChecked = MagicMock()
        self.options_page.stage_1_includes_non_shelves.setChecked = MagicMock()

        # Act
        self.options_page.load()

        self.options_page.workflow_enabled.setChecked.assert_called_with(True)
        self.options_page.stage_1_includes_non_shelves.setChecked.assert_called_with(
            True
        )
        self.options_page.shelf_management_shelves.clear.assert_called_once()
        self.options_page.shelf_management_shelves.addItems.assert_has_calls(
            [call(sorted(["Incoming", "Standard", "Stash", "Live"]))], any_order=False
        )
        self.options_page.plugin_configuration.setCurrentIndex.assert_called_with(0)

    @patch("shelves.utils.ShelfUtils.get_configured_shelves", new_callable=MagicMock)
    def test_load_no_configured_shelves(self, mock_get_configured_shelves):
        """Test if the load method correctly handles no configured shelves."""
        # Arrange
        self.config.setting = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: [],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: [],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: [],
            ShelfConstants.CONFIG_ACTIVE_TAB: 0,
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: True,
            "move_files_to": "/path/to/music",
        }

        mock_get_configured_shelves.return_value = []
        self.options_page._get_configured_shelves = MagicMock(return_value=[])
        self.options_page.shelf_management_shelves.count.return_value = 0
        self.options_page._populate_shelf_list = MagicMock()
        self.options_page.shelf_management_shelves.addItems = MagicMock()
        self.options_page.shelf_management_shelves.clear = MagicMock()

        # Act
        self.options_page.load()

        # Assert
        self.options_page.shelf_management_shelves.clear.assert_called_once()
        self.options_page.shelf_management_shelves.addItems.assert_not_called()
        self.options_page._populate_shelf_list.assert_called_once()

    @patch(
        "shelves.ui.options.QtWidgets.QInputDialog.getText",
        return_value=("NewShelf", True),
    )
    @patch("shelves.utils.ShelfUtils.validate_shelf_name", return_value=(True, None))
    def test_add_shelf(self, mock_validate, mock_getText):
        """Test adding a new, valid shelf."""
        # Arrange
        self.options_page._get_configured_shelves = MagicMock(return_value={"Incoming"})
        self.options_page.shelf_management_shelves.sortItems = MagicMock()
        self.options_page._rebuild_shelves_for_stages = MagicMock()
        self.options_page.shelf_management_shelves.addItem = MagicMock()

        # Act
        self.options_page.add_shelf()

        # Assert
        self.options_page.shelf_management_shelves.addItem.assert_called_with(
            "NewShelf"
        )
        self.options_page.shelf_management_shelves.sortItems.assert_called_once()
        self.options_page._rebuild_shelves_for_stages.assert_called_once()

    @patch(
        "shelves.ui.options.QtWidgets.QMessageBox.question",
        return_value=QtWidgets.QMessageBox.Yes,
    )
    def test_remove_shelf(self, mock_question):
        """Test removing a selected shelf."""
        # Arrange
        mock_item = MagicMock()
        mock_item.text.return_value = "ShelfToRemove"
        self.options_page.shelf_management_shelves.selectedItems.return_value = [
            mock_item
        ]
        self.options_page.get_selected_shelves_stage_1 = MagicMock(return_value=[])
        self.options_page.get_selected_shelves_stage_2 = MagicMock(return_value=[])
        self.options_page._rebuild_shelves_for_stages = MagicMock()

        self.options_page.shelf_management_shelves.takeItem = MagicMock()

        # Act
        self.options_page.remove_shelf()

        # Assert
        self.options_page.shelf_management_shelves.takeItem.assert_called_with(
            self.options_page.shelf_management_shelves.row(mock_item)
        )
        self.options_page._rebuild_shelves_for_stages.assert_called_once()


if __name__ == "__main__":
    unittest.main()
