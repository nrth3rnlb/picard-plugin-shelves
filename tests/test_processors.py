"""
Unit tests for the Processors class and its associated strategies.

This module contains unit tests for validating the behavior of various
strategies in the `Processors` class, specifically to ensure correct handling
of file post-addition processing logic under different conditions. The tests
cover scenarios such as known identical names, differing names derived from
tags and paths, and unknown names obtained from paths.
"""

import unittest
from copy import copy
from pathlib import Path
from unittest.mock import MagicMock, patch

from picard.file import File
from picard.track import Track
from typings import ConfigKey, TagKey, VotingType

import tests
from shelves.manager import ShelfManager
from shelves.processors import Processors

# def get_strategy(processors, cls):
#     return next(s for s in processors.strategies if isinstance(s, cls))


class ProcessorsTest(unittest.TestCase):
    """
    Tests the priority logic in the file_post_addition_to_track_processor.
    """

    def setUp(self):
        pass  # self.processors = Processors.__new__(Processors)

    @patch("shelves.processors.ShelfManager", spec_set=ShelfManager)
    @patch("shelves.manager.instance", spec_set=ShelfManager)
    def test_known_identical_names_strategy(
        self,
        mock_manager_instance,
        mock_manager_cls,
    ):
        # Arrange
        album_id = "f62b3023-34e7-40cd-bd08-b183118cb1fd"
        names = copy(tests.known_names)
        shelf_sub_dir = names.pop()

        mock_manager_instance.return_value = mock_manager_cls
        mock_manager_instance.base_path = Path(
            str(tests.configuration[ConfigKey.MOVE_FILES_TO]),
        )
        mock_manager_instance.registered_shelf_names = set(tests.known_names)
        mock_manager_instance.vote = MagicMock()

        file_mock = MagicMock(spec=File)
        file_mock.filename = f"/music/{shelf_sub_dir}/artist/album/track.mp3"
        file_mock.metadata = {
            TagKey.MUSICBRAINZ_ALBUMID: album_id,
            TagKey.SHELF: shelf_sub_dir,
            TagKey.SHELF_LOCKED: False,
        }

        # Act
        Processors(manager=mock_manager_instance).file_post_addition_to_track_processor(
            track=MagicMock(spec=Track),
            file=file_mock,
        )
        # Assert
        mock_manager_instance.vote.assert_any_call(
            voting_type=VotingType.UP, album_id=album_id, shelf_name=shelf_sub_dir
        )
        for known_name in names:
            mock_manager_instance.vote.assert_any_call(
                voting_type=VotingType.DOWN, album_id=album_id, shelf_name=known_name
            )

    @patch("shelves.processors.ShelfManager", spec_set=ShelfManager)
    @patch("shelves.manager.instance", spec_set=ShelfManager)
    def test_known_name_from_path(self, mock_manager_instance, mock_manager_cls):
        # Arrange
        album_id = "019c60c2-2ee0-742e-bb7a-692060c8b192"
        names = copy(tests.known_names)
        shelf_sub_dir = names.pop()

        mock_manager_instance.return_value = mock_manager_cls
        mock_manager_instance.base_path = Path(
            str(tests.configuration[ConfigKey.MOVE_FILES_TO]),
        )
        mock_manager_instance.registered_shelf_names = set(tests.known_names)
        mock_manager_instance.vote = MagicMock()

        file_mock = MagicMock(spec=File)
        file_mock.filename = f"/music/{shelf_sub_dir}/artist/album/track.mp3"
        file_mock.metadata = {
            TagKey.MUSICBRAINZ_ALBUMID: album_id,
            TagKey.SHELF: "",
            TagKey.SHELF_LOCKED: False,
        }

        # Act
        Processors(manager=mock_manager_instance).file_post_addition_to_track_processor(
            track=MagicMock(spec=Track),
            file=file_mock,
        )
        # Assert
        mock_manager_instance.vote.assert_any_call(
            voting_type=VotingType.UP, album_id=album_id, shelf_name=shelf_sub_dir
        )
        for known_name in names:
            mock_manager_instance.vote.assert_any_call(
                voting_type=VotingType.DOWN, album_id=album_id, shelf_name=known_name
            )

    @patch("shelves.processors.ShelfManager", spec_set=ShelfManager)
    @patch("shelves.manager.instance", spec_set=ShelfManager)
    def test_unknown_name_from_path(self, mock_manager_instance, mock_manager_cls):
        album_id = "019c60c2-2ee0-742e-bb7a-692060c8b192"
        names = copy(tests.known_names)
        unknown_name = "unknown"
        mock_manager_instance.return_value = mock_manager_cls
        mock_manager_instance.base_path = Path(
            str(tests.configuration[ConfigKey.MOVE_FILES_TO]),
        )
        mock_manager_instance.registered_shelf_names = set(tests.known_names)
        mock_manager_instance.vote = MagicMock()

        file_mock = MagicMock(spec=File)
        file_mock.filename = f"/music/{unknown_name}/artist/album/track.mp3"
        file_mock.metadata = {
            TagKey.MUSICBRAINZ_ALBUMID: album_id,
            TagKey.SHELF: "",
            TagKey.SHELF_LOCKED: False,
        }

        # Act
        Processors(manager=mock_manager_instance).file_post_addition_to_track_processor(
            track=MagicMock(spec=Track),
            file=file_mock,
        )
        # Assert
        mock_manager_instance.vote.assert_any_call(
            voting_type=VotingType.UP, album_id=album_id, shelf_name=unknown_name
        )
        for known_name in names:
            mock_manager_instance.vote.assert_any_call(
                voting_type=VotingType.DOWN, album_id=album_id, shelf_name=known_name
            )
