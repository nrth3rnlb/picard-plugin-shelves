# -*- coding: utf-8 -*-

"""
Tests for the processor priority logic.
"""

import unittest
from unittest.mock import MagicMock, patch

from shelves.constants import ShelfConstants
from shelves.processors import ShelfProcessors


class ProcessorPriorityTest(unittest.TestCase):
    """
    Tests the priority logic in the file_post_addition_to_track_processor.
    """

    def setUp(self):
        """Set up the test environment for workflow."""
        self.processors = ShelfProcessors.__new__(ShelfProcessors)
        self.config_setting = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            ShelfConstants.CONFIG_MOVE_FILES_TO_KEY: "/music",
        }
        self.known_shelves = ["Incoming", "Standard", "Soundtracks", "Favorites"]

    @patch("shelves.utils.ShelfUtils.get_shelf_from_path")
    @patch("shelves.utils.ShelfUtils.get_configured_shelves")
    @patch("shelves.processors.config")
    def test_manual_location_known_shelf_overrides_manual_tag(
        self,
        mock_config,
        mock_get_configured_shelves,
        mock_get_shelf_from_path,
    ):
        """
        PRIORITY 1: A file that is manually moved to a known or possible shelf folder
        must take over this shelf and ignores all previous manual markings.
        """
        # Arrange
        mock_config.setting = self.config_setting
        mock_config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY] = False

        mock_get_configured_shelves.return_value = self.known_shelves

        known_shelf = self.known_shelves[0]
        subdir_shelf = known_shelf
        mock_get_shelf_from_path.return_value = (subdir_shelf, True)

        file_mock = MagicMock()
        file_mock.filename = f"/music/{subdir_shelf}/artist/album/track.mp3"
        file_mock.metadata = {
            ShelfConstants.MUSICBRAINZ_ALBUMID: "album123",
            ShelfConstants.TAG_KEY: f"{known_shelf} {ShelfConstants.MANUAL_SHELF_SUFFIX}",
        }

        # Act
        self.processors.file_post_addition_to_track_processor(
            track=None, file=file_mock
        )

        # Assert
        self.assertEqual(file_mock.metadata[ShelfConstants.TAG_KEY], subdir_shelf)

    @patch("shelves.utils.ShelfUtils.add_known_shelf")
    @patch("shelves.utils.ShelfUtils.get_shelf_from_path")
    @patch("shelves.utils.ShelfUtils.get_configured_shelves")
    @patch("shelves.processors.config")
    def test_manual_location_unknown_shelf_overrides_manual_tag(
        self,
        mock_config,
        mock_get_configured_shelves,
        mock_get_shelf_from_path,
        _mock_add_known_shelf,
    ):
        """
        PRIORITY 1: A file that is manually moved to a known or possible shelf folder
        must take over this shelf and ignores all previous manual markings.
        """
        # Arrange
        mock_config.setting = self.config_setting
        mock_config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY] = False

        mock_get_configured_shelves.return_value = self.known_shelves

        known_shelf = self.known_shelves[0]
        unknown_shelf = f"Unknown_{known_shelf}"

        mock_get_shelf_from_path.return_value = (unknown_shelf, True)

        file_mock = MagicMock()
        file_mock.filename = f"/music/{unknown_shelf}/artist/album/track.mp3"
        file_mock.metadata = {
            ShelfConstants.MUSICBRAINZ_ALBUMID: "album123",
            ShelfConstants.TAG_KEY: f"{known_shelf} {ShelfConstants.MANUAL_SHELF_SUFFIX}",
        }

        # Act
        self.processors.file_post_addition_to_track_processor(
            track=None, file=file_mock
        )

        # Assert
        self.assertEqual(file_mock.metadata[ShelfConstants.TAG_KEY], unknown_shelf)

    @patch("shelves.utils.ShelfUtils.get_shelf_from_path")
    @patch("shelves.utils.ShelfUtils.get_configured_shelves")
    @patch("shelves.processors.config")
    def test_manual_tag_overrides_workflow(
        self,
        mock_config,
        mock_get_configured_shelves,
        mock_get_shelf_from_path,
    ):
        """
        PRIORITY 2: A file with a manual tag in a neutral location should keep its manual tag.
        """
        # Arrange
        mock_config.settings = self.config_setting
        mock_get_configured_shelves.return_value = self.known_shelves

        mock_get_shelf_from_path.return_value = ("Incoming", False)

        file_mock = MagicMock()
        file_mock.filename = "/music/Soundtracks/artist/album/track.mp3"
        file_mock.metadata = {
            ShelfConstants.MUSICBRAINZ_ALBUMID: "album123",
            ShelfConstants.TAG_KEY: f"Favorites{ShelfConstants.MANUAL_SHELF_SUFFIX}",
        }

        # Act
        ShelfProcessors.file_post_addition_to_track_processor(
            track=None, file=file_mock
        )

        # Assert
        self.assertEqual(
            file_mock.metadata[ShelfConstants.TAG_KEY],
            f"Favorites{ShelfConstants.MANUAL_SHELF_SUFFIX}",
        )

    @patch("shelves.processors.ShelfProcessors._apply_workflow_transition")
    @patch("shelves.utils.ShelfUtils.add_known_shelf")
    @patch("shelves.utils.ShelfUtils.get_shelf_from_path")
    @patch("shelves.utils.ShelfUtils.get_configured_shelves")
    @patch("shelves.processors.config")
    def test_workflow_applies_by_default(
        self,
        mock_config,
        mock_get_configured_shelves,
        mock_get_shelf_from_path,
        _mock_add_known_shelf,
        mock_apply_workflow_transition,
    ):
        """
        PRIORITY 3: Auf eine Datei ohne manuelle Kennzeichnung
        oder spezifischen Speicherort sollte der Arbeitsablauf angewendet werden.
        """
        # Arrange
        mock_config.settings = self.config_setting
        mock_get_configured_shelves.return_value = self.known_shelves

        known_shelf = self.known_shelves[0]

        mock_get_shelf_from_path.return_value = (known_shelf, False)

        file_mock = MagicMock()
        file_mock.filename = f"/music/{known_shelf}/artist/album/track.mp3"
        file_mock.metadata = {
            ShelfConstants.MUSICBRAINZ_ALBUMID: "album123",
            ShelfConstants.TAG_KEY: "",
        }

        ShelfProcessors.file_post_addition_to_track_processor(
            track=None, file=file_mock
        )

        # Assert
        mock_apply_workflow_transition.assert_called_once_with(known_shelf)
        self.assertEqual(known_shelf, known_shelf)


if __name__ == "__main__":
    unittest.main()
