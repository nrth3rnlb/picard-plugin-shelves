# -*- coding: utf-8 -*-

"""
Tests for the utility functions.
"""

import unittest
from unittest.mock import patch, MagicMock

from shelves.constants import ShelfConstants
from shelves.manager import _ShelfManager
from shelves.utils import ShelfUtils


class AttrDict(dict):
    """A dictionary that allows attribute-style access."""

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class UtilsTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.config_setting = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: sorted(
                ["Incoming", "Standard", "Stash", "Live"]
            ),
        }

    @patch("shelves.utils.ShelfUtils.validate_shelf_name", new_callable=MagicMock)
    @patch("shelves.utils.config", new_callable=MagicMock)
    def test_get_configured_shelves_filters_and_sorts(self, mock_config, mock_validate):
        # Arrange: config contains duplicates, a non-string and one invalid entry
        mock_config.setting = {
            ShelfConstants.CONFIG_KNOWN_SHELVES_KEY: [
                "beta",
                "alpha",
                "alpha",
                42,
                "gamma",
            ]
        }

        # validate_shelf_name: accept "alpha" and "beta", reject "gamma"
        def validate_side_effect(name):
            if name in ("alpha", "beta"):
                return True, None
            return False, "invalid"

        mock_validate.side_effect = validate_side_effect

        # Act
        result = ShelfUtils.get_configured_shelves()

        # Assert: duplicates removed, sorted, non-strings ignored, invalid excluded
        self.assertEqual(result, ["alpha", "beta"])


class UtilsValidationTest(unittest.TestCase):
    """
    Tests for the validation functions in ShelfUtils.
    """

    def test_validate_shelf_name_valid(self):
        """Test valid shelf names."""
        is_valid, message = ShelfUtils.validate_shelf_name("Soundtracks")
        self.assertTrue(is_valid)
        self.assertIsNone(message)

    def test_validate_shelf_name_empty(self):
        """Test that an empty name is invalid."""
        is_valid, message = ShelfUtils.validate_shelf_name("  ")
        self.assertFalse(is_valid)
        self.assertEqual(message, "Shelf name cannot be empty")

    def test_validate_shelf_name_reserved(self):
        """Test that reserved names like '.' and '..' are invalid."""
        is_valid, message = ShelfUtils.validate_shelf_name(".")
        self.assertFalse(is_valid)
        self.assertIn("Cannot use '.' or '..'", message)  # type: ignore[arg-type]

        is_valid, message = ShelfUtils.validate_shelf_name("..")
        self.assertFalse(is_valid)
        self.assertIn("Cannot use '.' or '..'", message)  # type: ignore[arg-type]

    def test_validate_shelf_name_invalid_chars(self):
        """Test that names with invalid characters are rejected."""
        is_valid, message = ShelfUtils.validate_shelf_name("My<Shelf")
        self.assertFalse(is_valid)
        self.assertIn("Contains invalid characters: <", message)  # type: ignore[arg-type]

        is_valid, message = ShelfUtils.validate_shelf_name("A|B")
        self.assertFalse(is_valid)
        self.assertIn("Contains invalid characters: |", message)  # type: ignore[arg-type]

    def test_validate_shelf_name_too_long(self):
        """Test that a name exceeding the max length is invalid."""
        long_name = "a" * (ShelfConstants.MAX_SHELF_NAME_LENGTH + 1)
        is_valid, message = ShelfUtils.validate_shelf_name(long_name)
        self.assertFalse(is_valid)
        self.assertIn("Shelf name too long", message)  # type: ignore[arg-type]

    def test_validate_shelf_name_too_many_words(self):
        """Test that a name with too many words is invalid."""
        is_valid, message = ShelfUtils.validate_shelf_name("One Two Three Four")
        self.assertFalse(is_valid)
        self.assertIn("Shelf name has too many words", message)  # type: ignore[arg-type]

    def test_validate_shelf_name_album_indicators(self):
        """Test that a name containing album indicators is invalid."""
        is_valid, message = ShelfUtils.validate_shelf_name("Album Vol. 1")
        self.assertFalse(is_valid)
        self.assertIn("contains album indicator(s)", message)  # type: ignore[arg-type]

    def test_validate_shelf_name_dots_warning(self):
        """Test that names with leading/trailing dots are valid but return a warning."""
        is_valid, message = ShelfUtils.validate_shelf_name(".hidden")
        self.assertTrue(is_valid)
        self.assertIn("may cause issues", message)  # type: ignore[arg-type]

        is_valid, message = ShelfUtils.validate_shelf_name("visible.")
        self.assertTrue(is_valid)
        self.assertIn("may cause issues", message)  # type: ignore[arg-type]


class UtilsLikelyShelfTest(unittest.TestCase):
    """
    Tests for the is_likely_shelf_name function in ShelfUtils.
    """

    def setUp(self):
        self.known_shelves = ["Soundtracks", "Favorites"]

    def test_is_likely_known_shelf(self):
        """A known shelf is always likely."""
        is_likely, reason = _ShelfManager.is_likely_shelf_name(
            "Soundtracks", self.known_shelves
        )
        self.assertTrue(is_likely)
        self.assertIsNone(reason)

    def test_is_likely_good_new_name(self):
        """A new, valid name is likely."""
        is_likely, reason = _ShelfManager.is_likely_shelf_name(
            "New Shelf", self.known_shelves
        )
        self.assertTrue(is_likely)
        self.assertIsNone(reason)

    def test_is_not_likely_artist_album_format(self):
        """A name with ' - ' is not likely."""
        is_likely, reason = _ShelfManager.is_likely_shelf_name(
            "Artist - Album", self.known_shelves
        )
        self.assertFalse(is_likely)
        self.assertIn("contains ' - '", reason)  # type: ignore[arg-type]

    def test_is_not_likely_too_long(self):
        """A very long name is not likely."""
        long_name = "This is a very long name that is probably an album title"
        is_likely, reason = _ShelfManager.is_likely_shelf_name(
            long_name, self.known_shelves
        )
        self.assertFalse(is_likely)
        self.assertIn("too long", reason)  # type: ignore[arg-type]

    def test_is_not_likely_too_many_words(self):
        """A name with many words is not likely."""
        is_likely, reason = _ShelfManager.is_likely_shelf_name(
            "A Shelf With Too Many Words", self.known_shelves
        )
        self.assertFalse(is_likely)
        self.assertIn("too many words", reason)  # type: ignore[arg-type]

    def test_is_not_likely_album_indicator(self):
        """A name with 'Vol.' or 'Disc' is not likely."""
        is_likely, reason = _ShelfManager.is_likely_shelf_name(
            "Greatest Hits Vol. 2", self.known_shelves
        )
        self.assertFalse(is_likely)
        self.assertIn("contains album indicator", reason)  # type: ignore[arg-type]

        is_likely, reason = _ShelfManager.is_likely_shelf_name(
            "The Album (Disc 1)", self.known_shelves
        )
        self.assertFalse(is_likely)
        self.assertIn("contains album indicator", reason)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
