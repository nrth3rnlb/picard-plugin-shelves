"""
Unit tests for script_functions.py.

This module contains unit tests for testing the functionalities
provided by the `shelf` function in the script_functions module.
The tests validate expected behaviors for both known and unknown
shelf values in various scenarios.
"""

import unittest
from copy import copy
from typing import Set
from unittest.mock import MagicMock

from shelves.script_functions import shelf


class ScriptFunctionsTest(unittest.TestCase):
    def setUp(self):
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
