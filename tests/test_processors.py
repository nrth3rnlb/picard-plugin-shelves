# -*- coding: utf-8 -*-

"""
Tests for the processors module.
"""

import unittest
from unittest.mock import MagicMock, patch

from shelves.constants import ShelfConstants
from shelves.processors import file_post_load_processor


class AttrDict(dict):
    """A dictionary that allows attribute-style access."""

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class ProcessorsTest(unittest.TestCase):
    """
    Tests for the file processors in the Shelves plugin.
    """

    def setUp(self):
        """Set up the test environment."""
        self.config = {
            "setting": {
                ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
                ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
                ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
                "move_files_to": "/music"
            }
        }

    @patch('shelves.processors.config', new_callable=MagicMock)
    @patch('shelves.processors.ShelfUtils.get_configured_shelves', return_value=["Incoming", "Standard", "Modscene"])
    def test_manual_tag_is_preserved(self, mock_get_shelves, mock_config):
        """
        Test that a file with a manual shelf tag preserves its tag
        even when a workflow transition would otherwise apply.
        """
        # Arrange
        mock_config.setting = self.config['setting']

        # Mock a file object with a manual tag
        file = AttrDict({
            "filename": "/music/Incoming/artist/album/track.mp3",
            "metadata": {
                ShelfConstants.TAG_KEY: f"Modscene{ShelfConstants.MANUAL_SHELF_SUFFIX}",
                ShelfConstants.MUSICBRAINZ_ALBUMID: "album123"
            }
        })

        # Act
        with patch('shelves.processors._shelf_manager', new_callable=MagicMock()):
            file_post_load_processor(file)

        # Assert
        # The tag should remain the manual one, ignoring the path and workflow.
        self.assertEqual(file.metadata[ShelfConstants.TAG_KEY], f"Modscene{ShelfConstants.MANUAL_SHELF_SUFFIX}")


if __name__ == "__main__":
    unittest.main()
