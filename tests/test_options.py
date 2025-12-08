"""
Tests for the options page logic.
"""

import unittest
from unittest.mock import MagicMock, patch

from PyQt5 import QtWidgets

from shelves.constants import ShelfConstants
from shelves.options import ShelvesOptionsPage


# Mock PyQt5 before it's imported by the plugin code


class OptionsPageTest(unittest.TestCase):
    """
    Tests for the ShelvesOptionsPage logic.
    """

    UI_ATTRS = list(ShelvesOptionsPage.__annotations__.keys())

    @patch('shelves.options.uic')
    @patch('picard.ui.options.OptionsPage.__init__', return_value=None)
    @patch('picard.ui.options.OptionsPage.style', return_value=MagicMock())
    def setUp(self, mock_style, mock_options_init, mock_uic):
        """Set up a mock ShelvesOptionsPage instance."""

        self.page = ShelvesOptionsPage.__new__(ShelvesOptionsPage)

        # Manually mock all UI elements that might be touched.
        for attr in self.UI_ATTRS:
            setattr(self.page, attr, MagicMock())

        ShelvesOptionsPage.__init__(self.page)

        self.page.config = MagicMock()
        self.page.config.setting = {}


    def test_save_writes_to_config(self):
        """Test if the save method correctly writes UI state to config."""
        # Arrange
        mock_item1 = MagicMock()
        mock_item1.text.return_value = "Shelf1"
        mock_item2 = MagicMock()
        mock_item2.text.return_value = "Shelf2"
        self.page.shelf_list.count.return_value = 2
        self.page.shelf_list.item.side_effect = [mock_item1, mock_item2]

        self.page.get_selected_shelves_stage_1 = MagicMock(return_value=["Shelf1"])
        self.page.get_selected_shelves_stage_2 = MagicMock(return_value=["Shelf2"])

        self.page.workflow_enabled.isChecked.return_value = True
        self.page.tabWidget.currentIndex.return_value = 1

        # Act
        self.page.save()

        # Assert
        settings = self.page.config.setting
        self.assertEqual(settings[ShelfConstants.CONFIG_SHELVES_KEY], ["Shelf1", "Shelf2"])
        self.assertEqual(settings[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY], ["Shelf1"])
        self.assertEqual(settings[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY], ["Shelf2"])
        self.assertTrue(settings[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY])
        self.assertEqual(settings[ShelfConstants.CONFIG_ACTIVE_TAB], 1)

    @patch('shelves.manager.ShelfManager.get_configured_shelves', return_value=["ShelfA", "ShelfB"])
    def test_load_populates_ui_from_config(self, mock_get_configured_shelves):
        """Test if the load method correctly populates UI from config."""
        # Arrange
        self.page.config.setting = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["ShelfA"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["ShelfB"],
            ShelfConstants.CONFIG_ACTIVE_TAB: 0
        }

        # Simulate the state of shelf_list *after* addItems has been called
        mock_item_a = MagicMock()
        mock_item_a.text.return_value = "ShelfA"
        mock_item_b = MagicMock()
        mock_item_b.text.return_value = "ShelfB"
        self.page.shelf_list.count.return_value = 2
        self.page.shelf_list.item.side_effect = [mock_item_a, mock_item_b]

        self.page.build_workflow_stage_1 = MagicMock()
        self.page.build_workflow_stage_2 = MagicMock()
        self.page.populate_shelf_list = MagicMock()

        # Act
        self.page.load()

        # Assert
        self.page.shelf_list.clear.assert_called_once()
        self.page.shelf_list.addItems.assert_called_with(["ShelfA", "ShelfB"])
        self.page.workflow_enabled.setChecked.assert_called_with(True)

        # The core of the fix: _rebuild_workflow_dropdowns uses the items from shelf_list
        # We need to check that it was called correctly.
        self.page.build_workflow_stage_1.assert_called_with(["ShelfA", "ShelfB"])
        self.page.build_workflow_stage_2.assert_called_with(["ShelfA", "ShelfB"])

    @patch('shelves.options.QtWidgets.QInputDialog.getText', return_value=("NewShelf", True))
    @patch('shelves.options.ShelfUtils.validate_shelf_name', return_value=(True, None))
    def test_add_shelf(self, mock_validate, mock_getText):
        """Test adding a new, valid shelf."""
        # Arrange
        self.page._get_configured_shelves = MagicMock(return_value={"ShelfA"})
        self.page._rebuild_shelves_for_stages = MagicMock()

        # Act
        self.page.add_shelf()

        # Assert
        self.page.shelf_list.addItem.assert_called_with("NewShelf")
        self.page.shelf_list.sortItems.assert_called_once()
        self.page._rebuild_shelves_for_stages.assert_called_once()

    @patch('shelves.options.QtWidgets.QMessageBox.question', return_value=QtWidgets.QMessageBox.Yes)
    def test_remove_shelf(self, mock_question):
        """Test removing a selected shelf."""
        # Arrange
        mock_item = MagicMock()
        mock_item.text.return_value = "ShelfToRemove"
        self.page.shelf_list.selectedItems.return_value = [mock_item]
        self.page.get_selected_shelves_stage_1 = MagicMock(return_value=[])
        self.page.get_selected_shelves_stage_2 = MagicMock(return_value=[])
        self.page._rebuild_shelves_for_stages = MagicMock()

        # Act
        self.page.remove_shelf()

        # Assert
        self.page.shelf_list.takeItem.assert_called_with(self.page.shelf_list.row(mock_item))
        self.page._rebuild_shelves_for_stages.assert_called_once()


if __name__ == "__main__":
    unittest.main()
