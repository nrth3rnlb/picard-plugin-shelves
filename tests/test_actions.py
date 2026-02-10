"""
Tests for the actions.py module.
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from picard.album import Album
from picard.file import File
from picard.track import Track
from typings import ConfigKey, TagKey

from shelves.actions import ShelfActionSet, ShelfActionToggleLock
from shelves.dialogs import SetShelfDialog


class ResetShelfActionTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.actions = ShelfActionToggleLock.__new__(ShelfActionToggleLock)
        self.actions.tagger = MagicMock()

        self.test_configuration = {
            ConfigKey.MOVE_FILES_TO: "/home/foobar/music",
            ConfigKey.WORKFLOW_ENABLED: True,
            ConfigKey.WORKFLOW_STAGE_1_SHELVES: ["Incoming"],
            ConfigKey.WORKFLOW_STAGE_2_SHELVES: ["Standard"],
            ConfigKey.KNOWN_SHELVES: sorted(["Incoming", "Standard", "Stash", "Live"]),
        }

        self.known_shelves = ["Incoming", "Standard", "Soundtracks", "Favorites"]

    @patch("shelves.actions.ShelfManager")
    def test_callback(self, mock_shelf_manager):
        """Test the callback method"""
        # Arrange
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance
        mock_manager_instance.base_path = Path(
            str(self.test_configuration[ConfigKey.MOVE_FILES_TO])
        )
        album_id = "e653893a-ac0e-4246-9389-3aac0e7246f9"
        shelf_name = "Standard"
        file_mock = MagicMock()
        file_mock.filename = f"/home/foobar/music/{shelf_name}/test.mp3"
        file_mock.metadata = {
            TagKey.MUSICBRAINZ_ALBUMID: album_id,
            TagKey.SHELF: shelf_name,
            TagKey.SHELF_LOCKED: True,
        }

        obj = MagicMock()
        obj.iterfiles.return_value = [file_mock]

        # Act
        self.actions.callback([obj])

        # Assert
        mock_manager_instance.unlock.assert_called_once_with(album_id)


class SetShelfActionTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.actions = ShelfActionSet.__new__(ShelfActionSet)
        self.dialog = SetShelfDialog.__new__(SetShelfDialog)
        self.actions.tagger = MagicMock()

        self.test_configuration = {
            ConfigKey.MOVE_FILES_TO: "/home/foobar/music",
            ConfigKey.WORKFLOW_ENABLED: True,
            ConfigKey.WORKFLOW_STAGE_1_SHELVES: ["Incoming"],
            ConfigKey.WORKFLOW_STAGE_2_SHELVES: ["Standard"],
            ConfigKey.KNOWN_SHELVES: sorted(["Incoming", "Standard", "Stash", "Live"]),
        }

        self.known_shelves = ["Incoming", "Standard", "Soundtracks", "Favorites"]

    @patch("shelves.actions.ShelfManager")
    @patch("shelves.actions.SetShelfDialog")
    def test_callback(
        self,
        mock_dialog_cls,
        mock_shelf_manager,
    ):
        # Arrange
        album_id = "c9357ca4-c5ab-460f-b57c-a4c5ab760f0d"
        shelf_name = "Standard"
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance
        mock_manager_instance.registered_shelf_names = self.known_shelves
        mock_manager_instance.base_path = Path(
            str(self.test_configuration[ConfigKey.MOVE_FILES_TO])
        )
        mock_manager_instance.setting = self.test_configuration
        mock_manager_instance.is_locked.return_value = False

        # Mocked dialog class -> Provide _instance
        self.actions.dialog = mock_dialog_cls.return_value
        self.actions.dialog.ask_for_shelf_name.return_value = shelf_name

        file_mock = MagicMock(File)
        file_mock.filename = f"/home/foobar/music/{shelf_name}/test.mp3"
        file_mock.metadata = {
            TagKey.MUSICBRAINZ_ALBUMID: album_id,
            TagKey.SHELF: shelf_name,
        }
        track_mock = MagicMock(Track)
        track_mock.files = [file_mock]

        album_mock = MagicMock(Album)
        album_mock.tracks = [track_mock]

        # Act
        self.actions.callback([album_mock])

        # Assert
        self.assertEqual(context.strategy, StrategyKnownNameToStage2.__name__)


class SetShelfDialogTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.dialog = SetShelfDialog.__new__(SetShelfDialog)
        self.test_configuration = {
            ConfigKey.MOVE_FILES_TO: "/home/foobar/music",
            ConfigKey.WORKFLOW_ENABLED: True,
            ConfigKey.WORKFLOW_STAGE_1_SHELVES: ["Incoming"],
            ConfigKey.WORKFLOW_STAGE_2_SHELVES: ["Standard"],
            ConfigKey.KNOWN_SHELVES: sorted(["Incoming", "Standard", "Stash", "Live"]),
        }

    @patch("shelves.dialogs.ShelfManager")
    def test_ask_for_shelf_name(
        self,
        mock_shelf_manager,
    ):
        # Arrange
        mock_dialog_shelf_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_dialog_shelf_manager_instance
        mock_dialog_shelf_manager_instance.registered_shelf_names = (
            self.test_configuration[ConfigKey.KNOWN_SHELVES]
        )

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

    # @patch("shelves.actions.ShelfManager")
    # def test_callback(self, mock_shelf_manager):
    #     """Test the callback method"""
    #     # Arrange
    #     mock_manager_instance = MagicMock()
    #     mock_shelf_manager.return_value = mock_manager_instance
    #     mock_manager_instance.base_path = Path(
    #         str(self.test_configuration[ConfigKey.MOVE_FILES_TO])
    #     )
    #
    #     file_path = (
    #         Path(str(self.test_configuration[ConfigKey.MOVE_FILES_TO]))
    #         / "Standard"
    #         / "file_name.foobar"
    #     )
    #     obj = MagicMock()
    #     file_mock = MagicMock()
    #     file_mock.filename = file_path
    #     file_mock.metadata = {}  # Initialize as dict to allow item assignment
    #     obj.iterfiles.return_value = [file_mock]
    #
    #     # Act
    #     self.actions.callback([obj])
    #
    #     # Assert
    #     mock_manager_instance.add_shelf_names.assert_called_with("Standard")
