# -*- coding: utf-8 -*-

"""
Tests for the utility functions.
"""

import math
import random
import unittest
from pathlib import Path
from unittest import skip
from unittest.mock import MagicMock, patch

from shelves import constants, utils
from shelves.manager import ShelfManager


class AttrDict(dict):
    """A dictionary that allows attribute-style access."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


class UtilsTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.test_known_shelves = ["Incoming", "Standard", "Soundtracks", "Favorites"]
        self.test_configuration = {
            constants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            constants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            constants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            constants.CONFIG_KNOWN_SHELVES_KEY: self.test_known_shelves,
        }

    @patch("shelves.utils.validate_shelf_name", new_callable=MagicMock)
    def test_get_configured_shelves_filters_and_sorts(self, mock_validate):
        # Arrange: config contains duplicates, a non-string and one invalid entry
        shelf_names = {
            "beta",
            "alpha",
            "alpha",
            42,
            "gamma",
        }

        # validate_shelf_name: accept "alpha" and "beta", reject "gamma"
        def validate_side_effect(name):
            """Mock validate_shelf_name"""
            if name in ("alpha", "beta"):
                return True, None
            return False, "invalid"

        mock_validate.side_effect = validate_side_effect

        # Act
        result = utils.validate_shelf_names(shelf_names)

        # Assert: duplicates removed, sorted, non-strings ignored, invalid excluded
        self.assertSetEqual(result, {"alpha", "beta"})

    def test_get_shelf_name_from_path(self):
        # Arrange
        shelf_sub_dir = self.test_known_shelves[0]

        # Act
        shelf_name = utils.get_shelf_name_from_path(
            Path(f"/music/{shelf_sub_dir}/artist/album/track.mp3"), Path("/music")
        )

        # Assert
        self.assertEqual(shelf_name, shelf_sub_dir)


class UtilsValidationTest(unittest.TestCase):
    """Tests for the validation functions in ShelfUtils."""

    def setUp(self):
        self.test_known_shelf_names = [
            "Incoming",
            "Standard",
            "Soundtracks",
            "Favorites",
        ]

    def test_validate_shelf_name_empty(self):
        """Test that an empty name is invalid."""
        is_valid, message = utils.validate_shelf_name("  ")
        self.assertFalse(is_valid)
        self.assertEqual(message, "Shelf name cannot be empty")

    def test_validate_shelf_name_invalid_chars(self):
        invalidations = constants.INVALID_SHELF_NAME_CHARS
        hr_invalidations = f"{', '.join(repr(c) for c in invalidations)}"
        for invalidation in invalidations:
            invalid_shelf_name = (
                f"{invalidation}{random.choice(list(self.test_known_shelf_names))}"
            )
            with self.subTest(invalid=invalid_shelf_name):
                # Arrange
                found_invalidations = [
                    found_invalidation
                    for found_invalidation in invalid_shelf_name
                    if found_invalidation in invalidations
                ]
                hr_found_invalidations = (
                    f"{', '.join(repr(c) for c in set(found_invalidations))}"
                )

                # Act
                is_valid, message = utils.validate_shelf_name(invalid_shelf_name)

                # Assert
                self.assertFalse(is_valid)
                self.assertIn(
                    f"Cannot use '{invalid_shelf_name}' as shelf name.", message
                )
                self.assertIn(f"Not allowed are: {hr_invalidations}", message)  # type: ignore[arg-type]

                self.assertIn(
                    f"The name contains invalid character(s): {hr_found_invalidations}.",
                    message,
                )

    def test_validate_shelf_name_invalid_names(self):
        invalidations = constants.INVALID_SHELF_NAMES
        hr_invalidations = f"{', '.join(repr(c) for c in invalidations)}"
        for invalidation in invalidations:
            invalid_shelf_name = f"{invalidation}"
            with self.subTest(invalid=invalid_shelf_name):
                # Arrange
                found_invalidations = [invalid_shelf_name]
                hr_found_invalidations = (
                    f"{', '.join(repr(c) for c in set(found_invalidations))}"
                )

                # Act
                is_valid, message = utils.validate_shelf_name(invalid_shelf_name)

                # Assert
                self.assertFalse(is_valid)
                self.assertIn(
                    f"Cannot use '{invalid_shelf_name}' as shelf name.", message
                )
                self.assertIn(f"Not allowed are: {hr_invalidations}", message)  # type: ignore[arg-type]

                self.assertIn(
                    f"The name is an invalid name: {hr_found_invalidations}.", message
                )

    def test_validate_shelf_name_tokens(self):
        invalidations = constants.ALBUM_INDICATORS
        hr_invalidations = f"{', '.join(repr(c) for c in invalidations)}"
        for invalidation in invalidations:
            invalid_shelf_name = f"{invalidation}{chr(0x20)}{random.choice(list(self.test_known_shelf_names))}"
            with self.subTest(invalid=invalid_shelf_name):
                # Arrange
                found_invalidations = [
                    found_invalidation
                    for found_invalidation in invalid_shelf_name.split()
                    if found_invalidation in invalidations
                ]
                hr_found_invalidations = (
                    f"{', '.join(repr(c) for c in set(found_invalidations))}"
                )

                # Act
                is_valid, message = utils.validate_shelf_name(invalid_shelf_name)

                # Assert
                self.assertFalse(is_valid)
                self.assertIn(
                    f"Cannot use '{invalid_shelf_name}' as shelf name.", message
                )
                self.assertIn(f"Not allowed are: {hr_invalidations}", message)  # type: ignore[arg-type]

                self.assertIn(
                    f"The name contains album indicator(s): {hr_found_invalidations}.",
                    message,
                )

    @skip("TODO(#15): See utils.py:168 - decide if max length should be enforced")
    def test_validate_shelf_name_too_long(self):
        """Test that a name exceeding the max length is invalid."""
        invalidations = constants.MAX_SHELF_NAME_LENGTH
        hr_invalidations = f"{invalidations}"
        #
        factor = 1 + math.ceil(
            constants.MAX_SHELF_NAME_LENGTH
            / len(random.choice(list(self.test_known_shelf_names)))
        )
        invalid_shelf_name = (
            factor * f"{chr(0x20)}{random.choice(list(self.test_known_shelf_names))}"
        ).strip()
        with self.subTest(invalid=invalid_shelf_name):
            # Arrange
            found_invalidations = [invalid_shelf_name]
            hr_found_invalidations = (
                f"{', '.join(repr(c) for c in set(found_invalidations))}"
            )

            # Act
            is_valid, message = utils.validate_shelf_name(invalid_shelf_name)
            self.assertFalse(is_valid)
            self.assertIn(f"Cannot use '{invalid_shelf_name}' as shelf name.", message)  # type: ignore[arg-type]
            self.assertIn(f"Maximum allowed is {hr_found_invalidations}.", message)  # type: ignore[arg-type]

            self.assertIn(
                f"The name is too long with {len(invalid_shelf_name)} characters.",
                message,
            )

    @skip("TODO(#16): See utils.py:177 - decide if max word count should be enforced")
    def test_validate_shelf_name_too_many_words(self):
        """Test that a name with too many words is invalid."""
        is_valid, message = utils.validate_shelf_name("One Two Three Four")
        self.assertFalse(is_valid)
        self.assertIn("Shelf name has too many words", message)  # type: ignore[arg-type]

    def test_validate_shelf_name_valid(self):
        """Test valid shelf_name names."""
        is_valid, message = utils.validate_shelf_name("Soundtracks")
        self.assertTrue(is_valid)
        self.assertEqual(message, "Valid shelf name")


class UtilsLikelyShelfTest(unittest.TestCase):
    """
    Tests for the is_likely_shelf_name function in ShelfUtils.
    """

    def setUp(self):
        self.known_shelves = ["Soundtracks", "Favorites"]

    def test_is_likely_good_new_name(self):
        """A new, valid name is likely."""
        is_likely, reason = ShelfManager.is_likely_shelf_name(
            "New Shelf", self.known_shelves
        )
        self.assertTrue(is_likely)
        self.assertIsNone(reason)

    def test_is_likely_known_shelf(self):
        """A known shelf_name is always likely."""
        is_likely, reason = ShelfManager.is_likely_shelf_name(
            "Soundtracks", self.known_shelves
        )
        self.assertTrue(is_likely)
        self.assertIsNone(reason)

    def test_is_not_likely_album_indicator(self):
        """A name with 'Vol.' or 'Disc' is not likely."""
        is_likely, reason = ShelfManager.is_likely_shelf_name(
            "Greatest Hits Vol. 2", self.known_shelves
        )
        self.assertFalse(is_likely)
        self.assertIn("contains album indicator", reason)  # type: ignore[arg-type]

        is_likely, reason = ShelfManager.is_likely_shelf_name(
            "The Album (Disc 1)", self.known_shelves
        )
        self.assertFalse(is_likely)
        self.assertIn("contains album indicator", reason)  # type: ignore[arg-type]

    def test_is_not_likely_artist_album_format(self):
        """A name with ' - ' is not likely."""
        is_likely, reason = ShelfManager.is_likely_shelf_name(
            "Artist - Album", self.known_shelves
        )
        self.assertFalse(is_likely)
        self.assertIn("contains ' - '", reason)  # type: ignore[arg-type]

    def test_is_not_likely_too_long(self):
        """A very long name is not likely."""
        long_name = "This is a very long name that is probably an album title"
        is_likely, reason = ShelfManager.is_likely_shelf_name(
            long_name, self.known_shelves
        )
        self.assertFalse(is_likely)
        self.assertIn("too long", reason)  # type: ignore[arg-type]

    def test_is_not_likely_too_many_words(self):
        """A name with many words is not likely."""
        is_likely, reason = ShelfManager.is_likely_shelf_name(
            "A Shelf With Too Many Words", self.known_shelves
        )
        self.assertFalse(is_likely)
        self.assertIn("too many words", reason)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
