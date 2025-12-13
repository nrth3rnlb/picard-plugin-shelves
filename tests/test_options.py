"""
Tests for the options page logic.
"""

import unittest
from typing import Any, Iterable, Dict
from unittest.mock import MagicMock, patch, call

from PyQt5 import QtWidgets
from picard.config import ListOption, TextOption, BoolOption, IntOption

from shelves.constants import ShelfConstants
from shelves.options import ShelvesOptionsPage


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

        # Provide a config mock because __init__ is not called
        self.page.config = MagicMock()

        # Build default settings for tests and attach to the config mock
        self.page.config.settings = self.build_test_settings(self.page.options)

    @staticmethod
    def _option_key(opt: Any) -> str:
        for attr in ("key", "_key", "name"):
            if hasattr(opt, attr):
                return getattr(opt, attr)
        raise AttributeError("Option has no recognizable key attribute name")

    @staticmethod
    def _generate_value_for_option(opt: Any) -> Any:
        # Try to use the declared default first
        default = getattr(opt, "default", None)
        if isinstance(opt, ListOption):
            if default is not None:
                return list(default)
            return ["example1", "example2"]
        if isinstance(opt, TextOption):
            return default if default is not None else "example"
        if isinstance(opt, BoolOption):
            return default if default is not None else True
        if isinstance(opt, IntOption):
            return default if default is not None else 1
        # Fallback: if an unknown option type, use the default or None
        return default

    @staticmethod
    def build_test_settings(options: Iterable[Any]) -> Dict[str, Any]:
        """
        Builds a `config.settings` dict for the passed option instances.
        Pass `ShelvesOptionsPage.options` to generate generic test data
        """
        settings: Dict[str, Any] = {}
        for option in options:
            key = OptionsPageTest._option_key(option)
            settings[key] = OptionsPageTest._generate_value_for_option(option)
        return settings

    def test_build_test_settings(self):
        # simple assertions: all keys exist and values are typical
        for option in self.page.options:
            key = self._option_key(option)
            assert key in self.page.config.settings

    def test_save_writes_to_config(self):
        """Test if the save method correctly writes UI state to config."""
        # Arrange
        mock_item_1 = MagicMock()
        mock_item_1.text.return_value = "Incoming"
        mock_item_2 = MagicMock()
        mock_item_2.text.return_value = "Standard"
        mock_item_3 = MagicMock()
        mock_item_3.text.return_value = "Stash"
        # self.settings = {
        #     ShelfConstants.CONFIG_ACTIVE_TAB: 1,
        #     ShelfConstants.CONFIG_ALBUM_SHELF_KEY: "Stash",
        #     ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: ["Incoming", "Standard", "Stash"],
        #     ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: False,
        #     ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
        #     ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Stash"],
        #     ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: [""],
        # }

        self.page.plugin_configuration.currentIndex.return_value = 0  # CONFIG_ACTIVE_TAB
        self.page.shelf_management_shelves.item.side_effect = [mock_item_1, mock_item_2]
        self.page.shelf_management_shelves.count.return_value = 2
        self.page.workflow_enabled.isChecked.return_value = True  # CONFIG_WORKFLOW_ENABLED_KEY
        self.page.workflow_stage_1.item.side_effect = [mock_item_1]  # CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY
        self.page.workflow_stage_2.item.side_effect = [mock_item_2]  # CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY

        # Act
        self.page.save()

        # Assert
        settings = self.page.config.settings
        self.assertEqual(settings[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY], ["Incoming", "Standard"])
        self.assertEqual(settings[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY], ["Incoming"])
        self.assertEqual(settings[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY], ["Standard"])
        self.assertTrue(settings[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY])
        self.assertEqual(settings[ShelfConstants.CONFIG_ACTIVE_TAB], 0)


    @patch('shelves.manager.ShelfManager.get_configured_shelves', return_value=sorted(["Incoming", "Standard", "Stash", "Live"]))
    def test_load_populates_ui_from_config(self, mock_get_configured_shelves):
        """Test if the load method correctly populates UI from config."""
        # Arrange
        self.page.config.settings = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: sorted(["Incoming", "Standard", "Stash", "Live"]),
            ShelfConstants.CONFIG_ACTIVE_TAB: 0,
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: True,
        }

        self.page.shelf_management_shelves.clear = MagicMock()
        self.page.shelf_management_shelves.addItems = MagicMock()
        self.page.plugin_configuration.setCurrentIndex = MagicMock()
        self.page.workflow_enabled.setChecked = MagicMock()
        self.page.stage_1_includes_non_shelves.setChecked = MagicMock()


        # Act
        self.page.load()

        self.page.workflow_enabled.setChecked.assert_called_with(True)
        self.page.stage_1_includes_non_shelves.setChecked.assert_called_with(True)
        self.page.shelf_management_shelves.clear.assert_called_once()
        self.page.shelf_management_shelves.addItems.assert_has_calls(
            [
                call(sorted(["Incoming", "Standard", "Stash", "Live"]))
            ],
            any_order=False
        )
        self.page.plugin_configuration.setCurrentIndex.assert_called_with(0)

    @patch('shelves.manager.ShelfManager.get_configured_shelves', return_value=[])
    @patch('shelves.utils.ShelfUtils.get_existing_dirs', return_value=["Standard"])
    def test_load_no_configured_shelves(self, mock_get_configured_shelves, mock_get_existing_dirs):
        """Test if the load method correctly handles no configured shelves."""
        # Arrange
        self.page.config.settings = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: [],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: [],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: [],
            ShelfConstants.CONFIG_ACTIVE_TAB: 0,
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: True,
            "move_files_to": "/path/to/music"
        }

        self.page.shelf_management_shelves.count.return_value = 0
        self.page._populate_shelf_list = MagicMock()
        self.page.shelf_management_shelves.addItems = MagicMock()
        self.page.shelf_management_shelves.clear = MagicMock()

        # Act
        self.page.load()

        # Assert
        self.page.shelf_management_shelves.clear.assert_called_once()
        self.page.shelf_management_shelves.addItems.assert_not_called()
        self.page._populate_shelf_list.assert_called_once()

    @patch('shelves.options.QtWidgets.QInputDialog.getText', return_value=("NewShelf", True))
    @patch('shelves.options.ShelfUtils.validate_shelf_name', return_value=(True, None))
    def test_add_shelf(self, mock_validate, mock_getText):
        """Test adding a new, valid shelf."""
        # Arrange
        self.page.get_configured_shelves = MagicMock(return_value={"Incoming"})
        self.page.shelf_management_shelves.sortItems = MagicMock()
        self.page._rebuild_shelves_for_stages = MagicMock()
        self.page.shelf_management_shelves.addItem = MagicMock()

        # Act
        self.page.add_shelf()

        # Assert
        self.page.shelf_management_shelves.addItem.assert_called_with("NewShelf")
        self.page.shelf_management_shelves.sortItems.assert_called_once()
        self.page._rebuild_shelves_for_stages.assert_called_once()

    @patch('shelves.options.QtWidgets.QMessageBox.question', return_value=QtWidgets.QMessageBox.Yes)
    def test_remove_shelf(self, mock_question):
        """Test removing a selected shelf."""
        # Arrange
        mock_item = MagicMock()
        mock_item.text.return_value = "ShelfToRemove"
        self.page.shelf_management_shelves.selectedItems.return_value = [mock_item]
        self.page.get_selected_shelves_stage_1 = MagicMock(return_value=[])
        self.page.get_selected_shelves_stage_2 = MagicMock(return_value=[])
        self.page._rebuild_shelves_for_stages = MagicMock()

        self.page.shelf_management_shelves.takeItem = MagicMock()

        # Act
        self.page.remove_shelf()

        # Assert
        self.page.shelf_management_shelves.takeItem.assert_called_with(self.page.shelf_management_shelves.row(mock_item))
        self.page._rebuild_shelves_for_stages.assert_called_once()


if __name__ == "__main__":
    unittest.main()
