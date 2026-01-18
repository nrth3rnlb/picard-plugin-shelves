"""
Tests for the actions.py module.
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from shelves import constants
from shelves.actions import ShelfActionDetermine, ShelfActionSet, ShelfActionUnlock
from shelves.dialogs import SetShelfDialog


class ResetShelfActionTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.actions = ShelfActionUnlock.__new__(ShelfActionUnlock)
        self.actions.tagger = MagicMock()

    @patch("shelves.actions.ShelfManager")
    def test_callback(self, mock_shelf_manager):
        """Test the callback method"""
        # Arrange
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance

        file_mock = MagicMock()
        file_mock.filename = "test.mp3"
        file_mock.metadata = {
            constants.MUSICBRAINZ_ALBUMID: "album123",
            constants.TAG_KEY            : "Standard",
            constants.TAG_LOCKED_KEY     : True
        }

        obj = MagicMock()
        obj.iterfiles.return_value = [file_mock]

        # Act
        self.actions.callback([obj])

        # Assert
        mock_manager_instance.unlock.assert_called_once_with("album123")


class SetShelfActionTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.actions = ShelfActionSet.__new__(ShelfActionSet)
        self.dialog = SetShelfDialog.__new__(SetShelfDialog)
        self.actions.tagger = MagicMock()

        self.test_configuration = {
            constants.CONFIG_MOVE_FILES_TO_KEY           : "/home/foobar/music",
            constants.CONFIG_WORKFLOW_ENABLED_KEY        : True,
            constants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            constants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            constants.CONFIG_KNOWN_SHELVES_KEY           : sorted(
                    ["Incoming", "Standard", "Stash", "Live"]
            ),
        }

        self.known_shelves = ["Incoming", "Standard", "Soundtracks", "Favorites"]

    @patch("shelves.actions.ShelfManager")
    @patch("shelves.actions.SetShelfDialog")
    def test_callback(self, mock_dialog_cls, mock_shelf_manager, ):
        # Arrange
        album_id = "c9357ca4-c5ab-460f-b57c-a4c5ab760f0d"
        shelf_name = "Standard"
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance
        mock_manager_instance.shelf_names = self.known_shelves
        mock_manager_instance.base_path = Path(
                str(self.test_configuration[constants.CONFIG_MOVE_FILES_TO_KEY])
        )
        mock_manager_instance.is_locked.return_value = False

        # Mocked dialog class -> Provide _instance
        self.actions.dialog = mock_dialog_cls.return_value
        self.actions.dialog.ask_for_shelf_name.return_value = shelf_name

        file_mock = MagicMock()
        file_mock.filename = "test.mp3"
        file_mock.metadata = {
            constants.MUSICBRAINZ_ALBUMID: album_id,
            constants.TAG_KEY            : shelf_name,
            constants.TAG_LOCKED_KEY     : True
        }

        obj = MagicMock()
        obj.iterfiles.return_value = [file_mock]

        # Act
        self.actions.callback([obj])

        # Assert
        mock_manager_instance.set_album_shelf.assert_called_with(
                album_id=album_id, shelf_name=shelf_name, lock=True,
        )


class SetShelfDialogTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.dialog = SetShelfDialog.__new__(SetShelfDialog)
        self.test_configuration = {
            constants.CONFIG_MOVE_FILES_TO_KEY           : "/home/foobar/music",
            constants.CONFIG_WORKFLOW_ENABLED_KEY        : True,
            constants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            constants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            constants.CONFIG_KNOWN_SHELVES_KEY           : sorted(
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
            constants.CONFIG_KNOWN_SHELVES_KEY
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
        self.actions = ShelfActionDetermine.__new__(ShelfActionDetermine)
        self.actions.tagger = MagicMock()
        self.test_configuration = {
            constants.CONFIG_MOVE_FILES_TO_KEY: "/home/foobar/music",
        }

    @patch("shelves.actions.ShelfManager")
    def test_callback(self, mock_shelf_manager):
        """Test the callback method"""
        # Arrange
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance
        mock_manager_instance.base_path = Path(
                str(self.test_configuration[constants.CONFIG_MOVE_FILES_TO_KEY])
        )

        file_path = (
                Path(str(self.test_configuration[constants.CONFIG_MOVE_FILES_TO_KEY]))
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
