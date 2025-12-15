"""
Tests for the actions.py module.
"""

import unittest
from unittest.mock import MagicMock, patch

from shelves import SetShelfAction


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class SetShelfActionTest(unittest.TestCase):

    def setUp(self):
        """Set up the test environment"""
        self.actions = SetShelfAction.__new__(SetShelfAction)
        self.dialog = SetShelfDialog.__new__(SetShelfDialog)

        self.config_setting = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: sorted(
                ["Incoming", "Standard", "Stash", "Live"]
            ),
        }

        self.known_shelves = ["Incoming", "Standard", "Soundtracks", "Favorites"]

    @patch("shelves.utils.ShelfUtils.validate_shelf_name", new_callable=MagicMock)
    @patch("shelves.utils.ShelfUtils.get_configured_shelves", new_callable=MagicMock)
    @patch("shelves.actions.SetShelfDialog", new_callable=MagicMock)
    @patch("shelves.processors.config", new_callable=MagicMock)
    def test_callback(
        self, mock_config, mock_dialog_cls, mock_get_configured_shelves, mock_validate
    ):
        """Callback test"""
        # Arrange
        self.actions._set_shelf_recursive = MagicMock()
        mock_config.setting = self.config_setting
        mock_get_configured_shelves.return_value = self.config_setting[
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY
        ]
        mock_validate.return_value = (True, None)
        # Minimal initialization so that constructor-side dependencies do not occur
        self.actions.tagger = MagicMock()

        # Mocked dialog class -> Provide instance
        self.actions.dialog = mock_dialog_cls.return_value
        self.actions.dialog.ask_for_shelf_name.return_value = "Standard"

        # Act
        self.actions.callback([AttrDict()])

        # Assert

        self.actions._set_shelf_recursive.assert_called_once()


import unittest
from unittest.mock import MagicMock, patch

from shelves.actions import SetShelfDialog


class SetShelfDialogTest(unittest.TestCase):

    def setUp(self):
        """Set up the test environment"""
        self.dialog = SetShelfDialog.__new__(SetShelfDialog)
        self.config_setting = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: sorted(
                ["Incoming", "Standard", "Stash", "Live"]
            ),
        }

    @patch("shelves.utils.ShelfUtils.get_configured_shelves", new_callable=MagicMock)
    @patch("shelves.processors.config", new_callable=MagicMock)
    def test_ask_for_shelf_name(self, mock_config, mock_get_configured_shelves):
        """Test the ask_for_shelf_name method"""
        # Arrange
        mock_config.setting = self.config_setting
        mock_get_configured_shelves.return_value = self.config_setting[
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
        result = self.dialog.ask_for_shelf_name(
            known_shelves=self.config_setting[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY]
        )

        # Assert
        self.assertEqual(result, "NewShelf")
        self.dialog.exec_.assert_called_once()


import unittest
from unittest.mock import MagicMock, patch

from shelves import DetermineShelfAction


class DetermineShelfActionTest(unittest.TestCase):

    def setUp(self):
        """Set up the test environment"""
        self.actions = DetermineShelfAction.__new__(DetermineShelfAction)
        self.actions.tagger = MagicMock()

    @patch("shelves.utils.ShelfUtils.get_configured_shelves", new_callable=MagicMock)
    @patch("shelves.utils.ShelfUtils.get_shelf_from_path", new_callable=MagicMock)
    @patch("shelves.utils.ShelfUtils.add_known_shelf", new_callable=MagicMock)
    def test_callback(
        self,
        mock_add_known_shelf,
        mock_get_shelf_from_path,
        mock_get_configured_shelves,
    ):
        """Test the callback method"""
        # Arrange
        mock_get_configured_shelves.return_value = ["Incoming", "Standard"]
        mock_get_shelf_from_path.return_value = ("Standard", None)

        obj = MagicMock()
        file_mock = MagicMock()
        file_mock.filename = "test.mp3"
        file_mock.metadata = {}  # Initialize as dict to allow item assignment
        obj.iterfiles.return_value = [file_mock]

        # Act
        self.actions.callback([obj])

        # Assert
        mock_get_configured_shelves.assert_called_once()
        mock_get_shelf_from_path.assert_called_once_with(
            path="test.mp3", known_shelves=["Incoming", "Standard"]
        )
        self.assertEqual(file_mock.metadata[ShelfConstants.TAG_KEY], "Standard")
        mock_add_known_shelf.assert_called_once_with("Standard")

    @patch("shelves.utils.ShelfUtils.get_configured_shelves", new_callable=MagicMock)
    @patch("shelves.utils.ShelfUtils.get_shelf_from_path", new_callable=MagicMock)
    @patch("shelves.utils.ShelfUtils.add_known_shelf", new_callable=MagicMock)
    def test_determine_shelf_recursive(
        self,
        mock_add_known_shelf,
        mock_get_shelf_from_path,
        mock_get_configured_shelves,
    ):
        """Test the _determine_shelf_recursive static method"""
        # Arrange
        mock_get_configured_shelves.return_value = ["Incoming", "Standard"]
        mock_get_shelf_from_path.return_value = ("Incoming", None)

        obj = MagicMock()
        file_mock = MagicMock()
        file_mock.filename = "another_test.mp3"
        file_mock.metadata = {}  # Initialize as dict to allow item assignment
        obj.iterfiles.return_value = [file_mock]

        # Act
        DetermineShelfAction._determine_shelf_recursive(obj)

        # Assert
        mock_get_configured_shelves.assert_called_once()
        mock_get_shelf_from_path.assert_called_once_with(
            path="another_test.mp3", known_shelves=["Incoming", "Standard"]
        )
        self.assertEqual(file_mock.metadata[ShelfConstants.TAG_KEY], "Incoming")
        mock_add_known_shelf.assert_called_once_with("Incoming")


import unittest
from unittest.mock import MagicMock, patch

from shelves.actions import ResetShelfAction
from shelves.constants import ShelfConstants


class ResetShelfActionTest(unittest.TestCase):

    def setUp(self):
        """Set up the test environment"""
        self.action = ResetShelfAction.__new__(ResetShelfAction)
        self.action.tagger = MagicMock()

    @patch("shelves.actions.DetermineShelfAction", new_callable=MagicMock)
    @patch("shelves.manager.ShelfManager", new_callable=MagicMock)
    def test_callback(self, mock_shelf_manager, mock_determine_action_class):
        """Test the callback method"""
        # Arrange
        mock_determine_action_class.return_value = MagicMock()

        obj = MagicMock()
        file_mock = MagicMock()
        file_mock.filename = "test.mp3"
        file_mock.metadata = {
            ShelfConstants.MUSICBRAINZ_ALBUMID: "album123",
            ShelfConstants.TAG_KEY: "Standard" + ShelfConstants.MANUAL_SHELF_SUFFIX,
        }
        obj.iterfiles.return_value = [file_mock]

        # Act
        self.action.callback([obj])

        # Assert
        mock_shelf_manager.clear_manual_override.assert_called_once_with("album123")
        self.assertEqual(file_mock.metadata[ShelfConstants.TAG_KEY], "")
