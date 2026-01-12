import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from shelves import constants
from shelves.exceptions import ShelfNotFoundException
from shelves.script_functions import shelf


class AttrDict(dict):
    """A dictionary that allows attribute-style access."""

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class ScriptFunctionsTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.test_configuration = {
            constants.CONFIG_MOVE_FILES_TO_KEY: "/home/foobar/music",
            constants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            constants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            constants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            constants.CONFIG_KNOWN_SHELVES_KEY: sorted(
                ["Incoming", "Standard", "Stash", "Live"]
            ),
        }

    @patch("shelves.script_functions.ShelfManager")
    def test_func_shelf_returns_empty_when_unknown(self, mock_manager):
        # Arrange
        mock_manager_instance = MagicMock()
        mock_manager.return_value = mock_manager_instance
        mock_manager_instance.get_album_shelf.side_effect = ShelfNotFoundException()

        album_id = "1a0c0de4-dadf-4baa-8c0d-e4dadf2baa3f"
        parser = MagicMock()
        parser.value_for_key = MagicMock(return_value=album_id)

        # Act
        result = shelf(parser)

        # Assert
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
