"""
Tests for the actions.py module.
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

from shelves.actions import DetermineShelfAction, ResetShelfAction, SetShelfAction
from shelves.constants import ShelfConstants
from shelves.dialogs import SetShelfDialog


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


class ResetShelfActionTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.actions = ResetShelfAction.__new__(ResetShelfAction)
        # test_configuration gelöscht - wurde nie genutzt

    @patch("shelves.actions.ShelfManager")
    def test_callback(self, mock_shelf_manager):
        """Test the callback method"""
        # Arrange
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance

        file_mock = MagicMock()
        file_mock.filename = "test.mp3"
        file_mock.metadata = {
            ShelfConstants.MUSICBRAINZ_ALBUMID: "album123",
            ShelfConstants.TAG_KEY: "Standard" + ShelfConstants.MANUAL_SHELF_SUFFIX,
        }

        obj = MagicMock()
        obj.iterfiles.return_value = [file_mock]

        # Act
        self.actions.callback([obj])

        # Assert
        self.assertEqual(file_mock.metadata[ShelfConstants.TAG_KEY], "Standard")
        mock_manager_instance.clear_manual_override.assert_called_once_with("album123")


class SetShelfActionTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.actions = SetShelfAction.__new__(SetShelfAction)
        self.dialog = SetShelfDialog.__new__(SetShelfDialog)

        self.test_configuration = {
            ShelfConstants.CONFIG_MOVE_FILES_TO_KEY: "/home/foobar/music",
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: sorted(
                ["Incoming", "Standard", "Stash", "Live"]
            ),
        }

        self.known_shelves = ["Incoming", "Standard", "Soundtracks", "Favorites"]

    @patch("shelves.actions.ShelfManager")
    @patch("shelves.utils.validate_shelf_name")
    @patch("shelves.utils.validate_shelf_names")
    @patch(
        "shelves.actions.SetShelfDialog",
    )
    def test_callback(
        self,
        mock_dialog_cls,
        mock_get_configured_shelves,
        mock_validate,
        mock_shelf_manager,
    ):
        # Arrange
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance
        mock_manager_instance.shelf_names = self.known_shelves
        mock_manager_instance.base_path = Path(
            str(self.test_configuration[ShelfConstants.CONFIG_MOVE_FILES_TO_KEY])
        )
        self.actions._set_shelf_recursive = MagicMock()
        mock_get_configured_shelves.return_value = self.test_configuration[
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY
        ]
        mock_validate.return_value = (True, None)
        # # Minimal initialization so that constructor-side dependencies do not occur
        self.actions.tagger = MagicMock()

        # Mocked dialog class -> Provide _instance
        self.actions.dialog = mock_dialog_cls.return_value
        self.actions.dialog.ask_for_shelf_name.return_value = "Standard"

        # Act
        self.actions.callback([AttrDict()])

        # Assert

        self.actions._set_shelf_recursive.assert_called_once()


class SetShelfDialogTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.dialog = SetShelfDialog.__new__(SetShelfDialog)
        self.test_configuration = {
            ShelfConstants.CONFIG_MOVE_FILES_TO_KEY: "/home/foobar/music",
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: sorted(
                ["Incoming", "Standard", "Stash", "Live"]
            ),
        }

    @patch("shelves.dialogs.ShelfManager")
    def test_ask_for_shelf_name(
        self,
        mock_shelf_manager,
    ):
        # Arrange
        mock_dialog_shelf_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_dialog_shelf_manager_instance
        mock_dialog_shelf_manager_instance.shelf_names = self.test_configuration[
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY
        ]

        # Mock the dialog attributes and methods to simulate user input
        self.dialog.exec_ = MagicMock(return_value=True)  # Simulate dialog acceptance
        self.dialog.shelf_name_input = MagicMock()
        self.dialog.shelf_name_input.text.return_value = "NewShelf"
        self.dialog.shelf_combo = MagicMock()  # Mock the combo box
        self.dialog.shelf_combo.currentText.return_value = (
            "NewShelf"  # Mock currentText to return the expected value
        )
        self.dialog.validation_label = MagicMock()  # Mock the validation label

        # Act
        result = self.dialog.ask_for_shelf_name()

        # Assert
        self.assertEqual(result, "NewShelf")
        self.dialog.exec_.assert_called_once()


class DetermineShelfActionTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.actions = DetermineShelfAction.__new__(DetermineShelfAction)
        self.actions.tagger = MagicMock()
        self.test_configuration = {
            ShelfConstants.CONFIG_MOVE_FILES_TO_KEY: "/home/foobar/music",
        }

    @patch("shelves.actions.ShelfManager")
    def test_callback(self, mock_shelf_manager):
        """Test the callback method"""
        # Arrange
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance
        mock_manager_instance.base_path = Path(
            str(self.test_configuration[ShelfConstants.CONFIG_MOVE_FILES_TO_KEY])
        )

        file_path = (
            Path(str(self.test_configuration[ShelfConstants.CONFIG_MOVE_FILES_TO_KEY]))
            / "Standard"
            / "file_name.foobar"
        )
        obj = MagicMock()
        file_mock = MagicMock()
        file_mock.filename = file_path
        file_mock.metadata = {}  # Initialize as dict to allow item assignment
        obj.iterfiles.return_value = [file_mock]

        # Act
        self.actions.callback([obj])

        # Assert
        mock_manager_instance.add_shelf_names.assert_called_with("Standard")
