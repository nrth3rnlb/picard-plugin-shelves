"""
Unit tests for the `ShelfActionSet` and `ShelfActionUnset` classes, which handle the setting
and unsetting of shelves in the context of a file organization system.

These tests use mocked dependencies to isolate and validate the behavior of methods
within the `ShelfActionSet` and `ShelfActionUnset` classes. Testing includes verifying
callback scenarios for both setting and unsetting actions, mock integrations, and edge
cases such as user cancellations or unsettable conditions.
"""

import unittest
from unittest.mock import MagicMock, patch

from picard.album import Album
from picard.file import File
from picard.track import Track
from PyQt5 import QtWidgets
from typings import TagKey

from shelves.actions import ShelfActionSet
from shelves.manager import ShelfManager

# Rule of thumb (for patch)
# Patch where it is looked up, not where it "logically belongs."
# For local imports in functions, you usually patch the original module (here shelves.processors.instance)
# because there is no stable name in shelves.actions.

# Note for spec_set
# If the spec class has side effects when instantiated (like picard.file.File):
# Spec is always transferred as a class/type, not as a real object.

# Rule of thumb (so that it sticks)
# spec_set=<class>: only if the class has its relevant attributes as properties/class attributes (or I really only
# need the methods).
# spec=<class>: if I need to set instance attributes that are only created at runtime (such as filename, metadata,
# tracks, files).


class ShelfActionSetTest(unittest.TestCase):
    def setUp(self):
        self.actions = ShelfActionSet.__new__(ShelfActionSet)

    @patch("shelves.actions.SetShelfDialog", autospec=True)
    def test_set_callback(
        self,
        mock_dialog_cls,
    ):
        album_id = "c9357ca4-c5ab-460f-b57c-a4c5ab760f0d"
        shelf_name = "Standard"

        file_mock = MagicMock(spec=File)
        file_mock.filename = "/home/foobar/music/album/test.mp3"
        file_mock.metadata = {
            TagKey.MUSICBRAINZ_ALBUMID: album_id,
            TagKey.SHELF: "",
            TagKey.SHELF_LOCKED: False,
        }
        track_mock = MagicMock(spec=Track)
        track_mock.files = [file_mock]

        album_mock = MagicMock(spec=Album)
        album_mock.metadata = {TagKey.MUSICBRAINZ_ALBUMID: album_id}
        album_mock.tracks = [track_mock]

        mock_dialog_cls.return_value.ask_for_shelf_name.return_value = shelf_name

        mock_shelf_manager_cls.return_value.get_shelf_name.return_value = shelf_name

        # Act
        self.actions.callback([album_mock])

        # Assert
        mock_processors_cls.action_set_processor.assert_called_once_with(
            file=file_mock,
            shelf_name=shelf_name,
        )
        mock_shelf_manager_cls.return_value.get_shelf_name.assert_called_once_with(
            album_id
        )

    def test_set_callback_returns_early_when_user_cancels_or_enters_empty(
        self,
        mock_dialog_cls,
    ):
        # Arrange
        album_id = "c9357ca4-c5ab-460f-b57c-a4c5ab760f0d"

        file_mock = MagicMock(spec=File)
        file_mock.filename = "/home/foobar/music/album/test.mp3"
        file_mock.metadata = {
            TagKey.MUSICBRAINZ_ALBUMID: album_id,
            TagKey.SHELF: "",
            TagKey.SHELF_LOCKED: False,
        }
        track_mock = MagicMock(spec=Track)
        track_mock.files = [file_mock]

        album_mock = MagicMock(spec=Album)
        album_mock.metadata = {TagKey.MUSICBRAINZ_ALBUMID: album_id}
        album_mock.tracks = [track_mock]

        for user_value in (None, ""):
            with self.subTest(user_value=user_value):
                mock_processors_cls.action_set_processor.reset_mock()
                mock_processors_instance.reset_mock()
                mock_shelf_manager_cls.reset_mock()

                mock_dialog_cls.return_value.ask_for_shelf_name.return_value = (
                    user_value
                )

                # Act
                self.actions.callback([album_mock])

                # Assert
                mock_processors_cls.action_set_processor.assert_not_called()
                mock_processors_instance.assert_not_called()
                mock_shelf_manager_cls.assert_not_called()


class ShelfActionDialogTest(unittest.TestCase):
    def setUp(self):
        self.dialog = SetShelfDialog.__new__(SetShelfDialog)

    def test_ask_for_shelf_name(self, mock_shelf_manager_cls):
        # Arrange
        shelf_name = "Standard"
        self.dialog.exec_ = MagicMock(return_value=QtWidgets.QDialog.Accepted)
        self.dialog.shelf_combo = MagicMock(spec_ref=QtWidgets.QComboBox)
        self.dialog.shelf_combo.currentText.return_value = shelf_name

        # Act
        result = self.dialog.ask_for_shelf_name()

        # Assert
        self.assertEqual(result, shelf_name)
