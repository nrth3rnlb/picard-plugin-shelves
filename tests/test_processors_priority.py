# -*- coding: utf-8 -*-

"""
Tests for the processor priority logic.
"""

import unittest
from unittest.mock import MagicMock, patch

from shelves.constants import ShelfConstants
from shelves.processors import file_post_addition_to_track_processor


class AttrDict(dict):
    """A dictionary that allows attribute-style access."""

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class ProcessorPriorityTest(unittest.TestCase):
    """
    Tests the priority logic in the file_post_addition_to_track_processor.
    """

    def setUp(self):
        """Set up the test environment for workflow."""
        self.config_setting = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            "move_files_to": "/music",
        }
        self.known_shelves = ["Incoming", "Standard", "Soundtracks", "Favorites"]

    @patch("shelves.processors.vote_for_shelf")
    @patch("shelves.manager.ShelfManager", new_callable=MagicMock)
    @patch("shelves.processors.ShelfUtils.add_known_shelf")
    @patch("shelves.utils.ShelfUtils.get_configured_shelves")
    @patch("shelves.processors.config", new_callable=MagicMock)
    def test_physical_location_overrides_manual_tag(
        self, mock_config, mock_get_shelves, mock_add_shelf, mock_manager, mock_vote
    ):
        """
        PRIORITY 1: A file physically moved to a known shelf folder should adopt that shelf,
        ignoring any previous manual tag.
        """
        # Arrange
        mock_config.settings = self.config_setting
        mock_get_shelves.return_value = self.known_shelves

        file = AttrDict(
            {
                "filename": "/music/Soundtracks/artist/album/track.mp3",
                "metadata": {
                    ShelfConstants.TAG_KEY: f"Favorites{ShelfConstants.MANUAL_SHELF_SUFFIX}",
                    ShelfConstants.MUSICBRAINZ_ALBUMID: "album123",
                },
            }
        )

        with patch(
            "shelves.processors.ShelfUtils.get_shelf_from_path",
            return_value=("Soundtracks", True),
        ):
            # Act
            file_post_addition_to_track_processor(track=None, file=file)

        # Assert
        self.assertEqual(file.metadata[ShelfConstants.TAG_KEY], "Soundtracks")
        mock_manager.set_album_shelf.assert_called_with(
            "album123", "Soundtracks", source="manual", lock=True
        )

    @patch("shelves.manager.ShelfManager.set_album_shelf", new_callable=MagicMock)
    @patch("shelves.utils.ShelfUtils.get_shelf_from_path", new_callable=MagicMock)
    @patch("shelves.utils.ShelfUtils.get_configured_shelves", new_callable=MagicMock)
    @patch("shelves.processors.config", new_callable=MagicMock)
    def test_manual_tag_overrides_workflow(
        self,
        mock_config,
        mock_get_configured_shelves,
        mock_get_shelf_from_path,
        mock_manager,
    ):
        """
        PRIORITY 2: A file with a manual tag in a neutral location should keep its manual tag.
        """
        # Arrange
        mock_config.settings = self.config_setting
        mock_get_configured_shelves.return_value = self.known_shelves

        file = AttrDict(
            {
                "filename": "/music/Incoming/artist/album/track.mp3",
                "metadata": {
                    ShelfConstants.TAG_KEY: f"Favorites{ShelfConstants.MANUAL_SHELF_SUFFIX}",
                    ShelfConstants.MUSICBRAINZ_ALBUMID: "album123",
                },
            }
        )
        mock_get_shelf_from_path.return_value = ("Incoming", False)

        # Act
        file_post_addition_to_track_processor(track=None, file=file)

        # Assert
        self.assertEqual(
            file.metadata[ShelfConstants.TAG_KEY],
            f"Favorites{ShelfConstants.MANUAL_SHELF_SUFFIX}",
        )
        mock_manager.set_album_shelf.assert_called_with(
            "album123", "Favorites", source="manual", lock=True
        )

    @unittest.skip("I no longer know why I need this. There is no default (anymore)")
    @patch("shelves.processors.vote_for_shelf")
    @patch("shelves.utils.ShelfUtils.get_configured_shelves")
    @patch("shelves.processors.config", new_callable=MagicMock)
    def test_workflow_applies_by_default(
        self,
        mock_config,
        mock_get_configured_shelves,
        mock_vote,
    ):
        """
        PRIORITY 3: A file with no manual tag or specific location should have the workflow applied.
        """
        # Arrange
        mock_config.settings = self.config_setting
        mock_get_configured_shelves.return_value = self.known_shelves

        file = AttrDict(
            {
                "filename": "/music/Incoming/artist/album/track.mp3",
                "metadata": {
                    ShelfConstants.TAG_KEY: "",
                    ShelfConstants.MUSICBRAINZ_ALBUMID: "album123",
                },
            }
        )

        with patch(
            "shelves.processors.ShelfUtils.get_shelf_from_path",
            return_value=("Incoming", False),
        ):
            # Act
            file_post_addition_to_track_processor(track=None, file=file)

        # Assert
        self.assertEqual(file.metadata[ShelfConstants.TAG_KEY], "Standard")
        mock_vote.assert_called_with("album123", "Standard")


if __name__ == "__main__":
    unittest.main()
