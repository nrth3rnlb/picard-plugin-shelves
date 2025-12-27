# -*- coding: utf-8 -*-

"""
Tests for the processor priority logic.
"""

import unittest
from copy import copy
from typing import Set
from unittest.mock import MagicMock, patch, PropertyMock

from shelves.constants import ShelfConstants
from shelves.processors import ShelfProcessors


class ProcessorPriorityTest(unittest.TestCase):
    """
    Tests the priority logic in the file_post_addition_to_track_processor.
    """

    def setUp(self):
        """Set up the test environment for workflow."""
        self.processors = ShelfProcessors.__new__(ShelfProcessors)
        self.known_shelves: Set[str] = {
            "Incoming",
            "Standard",
            "Soundtracks",
            "Favorites",
        }
        self.config_setting = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            ShelfConstants.CONFIG_MOVE_FILES_TO_KEY: "/music",
        }

    @patch("shelves.utils.ShelfUtils.get_shelf_name_from_path")
    @patch("shelves.utils.ShelfUtils.validate_shelf_names")
    @patch("shelves.processors.config")
    def test_manual_location_known_shelf_overrides_manual_tag(
        self,
        mock_config,
        mock_get_configured_shelves,
        mock_get_shelf_from_path,
    ):
        """
        PRIORITY 1: A file that is manually moved to a known or possible shelf_name folder
        must take over this shelf_name and ignores all previous manual markings.
        """
        # Arrange
        mock_config.setting = self.config_setting
        mock_config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY] = False

        mock_get_configured_shelves.return_value = self.known_shelves

        shelf_sub_dir = self.known_shelves[0]
        mock_get_shelf_from_path.return_value = shelf_sub_dir

        file_mock = MagicMock()
        file_mock.filename = f"/music/{shelf_sub_dir}/artist/album/track.mp3"
        file_mock.metadata = {
            ShelfConstants.MUSICBRAINZ_ALBUMID: "album123",
            ShelfConstants.TAG_KEY: f"{shelf_sub_dir} {ShelfConstants.MANUAL_SHELF_SUFFIX}",
        }

        # Act
        self.processors.file_post_addition_to_track_processor(
            track=None, file=file_mock
        )

        # Assert
        self.assertEqual(file_mock.metadata[ShelfConstants.TAG_KEY], shelf_sub_dir)

    @patch("shelves.ui.options.ShelfManager.shelf_names", new_callable=PropertyMock)
    @patch("shelves.manager.ShelfManager.set_album_shelf")
    @patch("shelves.processors.config")
    def test_file_post_addition_to_track_processor_priority_1(  # is_known_name_from_path
        self,
        mock_config,
        mock_set_album_shelf,
        mock_shelf_manager_shelf_names,
    ):
        """
        priority_1 = is_known_name_from_path
        """
        # Arrange
        mock_config.settings = self.config_setting
        mock_shelf_manager_shelf_names.return_value = self.known_shelves
        shelf_sub_dir = copy(self.known_shelves).pop()

        file_mock = MagicMock()
        file_mock.filename = f"/music/{shelf_sub_dir}/artist/album/track.mp3"
        file_mock.metadata = {
            ShelfConstants.MUSICBRAINZ_ALBUMID: "",
            ShelfConstants.TAG_KEY: f"{shelf_sub_dir}",
        }

        # Act
        self.processors.file_post_addition_to_track_processor(
            track=None, file=file_mock
        )

        # Assert

        mock_set_album_shelf.assert_called_with(
            album_id="album123", shelf="Favorites", lock=True
        )

    @patch("shelves.manager.ShelfManager.set_album_shelf")
    @patch("shelves.utils.ShelfUtils.get_shelf_name_from_path")
    @patch("shelves.utils.ShelfUtils.validate_shelf_names")
    @patch("shelves.processors.config")
    def test_file_post_addition_to_track_processor_priority_2(
        self,
        mock_config,
        mock_get_configured_shelves,
        mock_get_shelf_from_path,
        mock_set_album_shelf,
    ):
        """
        PRIORITY 2: A file with a manual tag in a neutral location should keep its manual tag.
        """
        # Arrange
        mock_config.settings = self.config_setting
        mock_get_configured_shelves.return_value = self.known_shelves
        mock_get_shelf_from_path.return_value = "Incoming"

        file_mock = MagicMock()
        file_mock.metadata = {
            ShelfConstants.MUSICBRAINZ_ALBUMID: "album123",
            ShelfConstants.TAG_KEY: f"Favorites{ShelfConstants.MANUAL_SHELF_SUFFIX}",
        }

        # Act
        ShelfProcessors.file_post_addition_to_track_processor(
            track=None, file=file_mock
        )

        # Assert
        mock_set_album_shelf.assert_called_with(
            album_id="album123", shelf="Favorites", lock=True
        )

    @patch("shelves.manager.ShelfManager.set_album_shelf")
    @patch("shelves.ui.options.ShelfManager.shelf_names", new_callable=PropertyMock)
    @patch("shelves.processors.ShelfProcessors._apply_workflow_transition")
    @patch("shelves.utils.ShelfUtils.get_shelf_name_from_path")
    @patch("shelves.processors.config")
    def test_file_post_addition_to_track_processor_priority_4(
        self,
        mock_config,
        mock_get_shelf_from_path,
        mock_apply_workflow_transition,
        mock_shelf_manager_shelf_names,
        mock_set_album_shelf,
    ):
        """
        PRIORITY 3: The standard logic should be applied to a file without special properties
        """
        # Arrange
        mock_config.settings = self.config_setting
        mock_shelf_manager_shelf_names.return_value = self.known_shelves

        shelf_sub_dir = copy(self.known_shelves).pop()
        mock_get_shelf_from_path.return_value = shelf_sub_dir

        file_mock = MagicMock()
        file_mock.filename = f"/music/{shelf_sub_dir}/artist/album/track.mp3"
        file_mock.metadata = {
            ShelfConstants.MUSICBRAINZ_ALBUMID: "album123",
            ShelfConstants.TAG_KEY: "",
        }

        # Act
        ShelfProcessors.file_post_addition_to_track_processor(
            track=None, file=file_mock
        )

        # Assert
        mock_set_album_shelf.assert_called_with(
            album_id="album123", shelf=shelf_sub_dir, lock=True
        )


if __name__ == "__main__":
    unittest.main()
