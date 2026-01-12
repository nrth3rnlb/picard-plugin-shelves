# -*- coding: utf-8 -*-

"""
Tests for the processor priority logic.
"""

import unittest
from copy import copy, deepcopy
from pathlib import Path
from typing import Set
from unittest.mock import MagicMock, PropertyMock, patch

from shelves import constants
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
        self.test_configuration = {
            constants.CONFIG_WORKFLOW_ENABLED_KEY: False,
            constants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            constants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            constants.CONFIG_MOVE_FILES_TO_KEY: "/music",
        }

    # @patch("shelves.utils.get_shelf_name_from_path")
    # @patch("shelves.utils.validate_shelf_names")
    # @patch("shelves.processors.config")
    # def test_manual_location_known_shelf_overrides_manual_tag(
    #     self,
    #     mock_config,
    #     mock_get_configured_shelves,
    #     mock_get_shelf_from_path,
    # ):
    #     """
    #     PRIORITY 1: A file that is manually moved to a known or possible shelf_name folder
    #     must take over this shelf_name and ignores all previous manual markings.
    #     """
    #     # Arrange
    #     mock_config.setting = self.test_configuration
    #     mock_config.setting[constants.CONFIG_WORKFLOW_ENABLED_KEY] = False
    #
    #     mock_get_configured_shelves.return_value = self.test_known_shelves
    #
    #     shelf_sub_dir = self.test_known_shelves[0]
    #     mock_get_shelf_from_path.return_value = shelf_sub_dir
    #
    #     file_mock = MagicMock()
    #     file_mock.filename = f"/music/{shelf_sub_dir}/artist/album/track.mp3"
    #     file_mock.metadata = {
    #         constants.MUSICBRAINZ_ALBUMID: "album123",
    #         constants.TAG_KEY: f"{shelf_sub_dir} {constants.MANUAL_SHELF_SUFFIX}",
    #     }
    #
    #     # Act
    #     self.processors.file_post_addition_to_track_processor(
    #         track=None, file=file_mock
    #     )
    #
    #     # Assert
    #     self.assertEqual(file_mock.metadata[constants.TAG_KEY], shelf_sub_dir)

    @patch("shelves.processors.ShelfManager")
    @patch(
        "shelves.workflow.WorkflowEngine.apply_transition",
        new_callable=MagicMock,
    )
    def test_file_post_addition_to_track_processor_known_name_from_path(  # is_known_name_from_path
        self,
        mock_apply_workflow_transition,
        mock_shelf_manager,
    ):
        # Arrange
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance
        mock_manager_instance.base_path = Path(
            str(self.test_configuration[constants.CONFIG_MOVE_FILES_TO_KEY])
        )
        mock_manager_instance.shelf_names = self.known_shelves

        shelf_sub_dir = copy(self.known_shelves).pop()
        mock_apply_workflow_transition.return_value = shelf_sub_dir

        file_mock = MagicMock()
        file_mock.filename = f"/music/{shelf_sub_dir}/artist/album/track.mp3"
        file_mock.metadata = {
            constants.MUSICBRAINZ_ALBUMID: "f62b3023-34e7-40cd-bd08-b183118cb1fd",
            constants.TAG_KEY: "no_tag_set",
        }

        # Act
        self.processors.file_post_addition_to_track_processor(
            track=None, file=file_mock
        )

        # Assert
        mock_manager_instance.set_album_shelf.assert_called_with(
            album_id="f62b3023-34e7-40cd-bd08-b183118cb1fd",
            shelf_name=shelf_sub_dir,
            lock=True,
        )

    @patch("shelves.processors.ShelfManager")
    @patch(
        "shelves.workflow.WorkflowEngine.apply_transition",
        new_callable=MagicMock,
    )
    def test_file_post_addition_to_track_processor_known_name_from_tag_and_manual(
        self,
        mock_apply_workflow_transition,
        mock_shelf_manager,
    ):
        """
        Manually moved to another known shelf folder.

        A file that has been manually moved to a known shelf folder
        must adopt this shelf folder and ignore all previous manual markings.
        """
        # Arrange
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance
        mock_manager_instance.shelf_names = self.known_shelves
        mock_manager_instance.base_path = Path(
            self.test_configuration[constants.CONFIG_MOVE_FILES_TO_KEY]
        )

        known_shelves_clone = copy(self.known_shelves)
        shelf_name = known_shelves_clone.pop()
        shelf_sub_dir = known_shelves_clone.pop()
        mock_apply_workflow_transition.return_value = shelf_sub_dir

        file_mock = MagicMock()
        file_mock.filename = f"/music/{shelf_sub_dir}/artist/album/track.mp3"
        file_mock.metadata = {
            constants.MUSICBRAINZ_ALBUMID: "f62b3023-34e7-40cd-bd08-b183118cb1fd",
            constants.TAG_KEY: f"{shelf_name}{constants.MANUAL_SHELF_SUFFIX}",
        }

        # Act
        ShelfProcessors.file_post_addition_to_track_processor(
            track=None, file=file_mock
        )

        # Assert
        # The name of the shelf determined from the path wins
        # The name of the shelf from the tag loses
        mock_manager_instance.set_album_shelf.assert_called_with(
            album_id="f62b3023-34e7-40cd-bd08-b183118cb1fd",
            shelf_name=shelf_sub_dir,
            lock=True,
        )

    @patch("shelves.processors.ShelfManager")
    @patch(
        "shelves.workflow.WorkflowEngine.apply_transition",
        new_callable=MagicMock,
    )
    def test_file_post_addition_to_track_processor_priority_4(
        self,
        mock_apply_workflow_transition,
        mock_shelf_manager,
    ):
        """
        PRIORITY 3: The standard logic should be applied to a file without special properties
        """
        # Arrange
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance
        mock_manager_instance.shelf_names = self.known_shelves
        mock_manager_instance.base_path = Path(
            self.test_configuration[constants.CONFIG_MOVE_FILES_TO_KEY]
        )

        shelf_sub_dir = copy(self.known_shelves).pop()
        mock_apply_workflow_transition.return_value = shelf_sub_dir

        file_mock = MagicMock()
        file_mock.filename = f"/music/{shelf_sub_dir}/artist/album/track.mp3"
        file_mock.metadata = {
            constants.MUSICBRAINZ_ALBUMID: "album123",
            constants.TAG_KEY: "",
        }

        # Act
        ShelfProcessors.file_post_addition_to_track_processor(
            track=None, file=file_mock
        )

        # Assert
        mock_manager_instance.set_album_shelf.assert_called_with(
            album_id="album123", shelf_name=shelf_sub_dir, lock=True
        )


if __name__ == "__main__":
    unittest.main()
