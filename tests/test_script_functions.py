import unittest
from copy import copy
from typing import Set
from unittest.mock import MagicMock

from shelves.script_functions import shelf


class ScriptFunctionsTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.known_shelves: Set[str] = {
            "Incoming",
            "Standard",
            "Soundtracks",
            "Favorites",
        }

    def test_func_shelf(self):
        """Test the shelf function with known and unknown shelf values."""
        # Arrange
        known_shelf = copy(self.known_shelves).pop()

        parser = MagicMock()
        parser.file.metadata.get.return_value = known_shelf
        parser.context = MagicMock()
        parser.context.get.return_value = known_shelf

        # Act
        result = shelf(parser)

        # Assert
        expected = known_shelf
        invalid = f"Unknown{known_shelf}"
        self.assertNotEqual(invalid, result, f"Did not expect '{invalid}' but got it.")
        self.assertEqual(expected, result, f"Expected '{expected}' but got '{result}'")


if __name__ == "__main__":
    unittest.main()
