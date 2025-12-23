# -*- coding: utf-8 -*-

"""
Tests for the ShelfManager class.
"""

import unittest
from unittest.mock import MagicMock

from shelves.manager import ShelfManager


class ManagerTest(unittest.TestCase):
    """
    Tests for the core _state management logic in ShelfManager.
    """

    def setUp(self):
        """Set up a new ShelfManager _instance for each test."""
        # Mock the dependencies required by the ShelfManager constructor
        self.mock_validators = MagicMock()
        self.mock_utils = MagicMock()
        self.album_id = "album123"

    def test_singleton(self):
        """Test that the ShelfManager is a singleton."""
        ShelfManager.destroy()
        a = ShelfManager()
        a.test_value = "foobar"
        b = ShelfManager()
        self.assertEqual("foobar", b.test_value)

    def test_singleton_destroy(self):
        """Test that the ShelfManager is a singleton."""
        ShelfManager.destroy()
        a = ShelfManager()
        a.test_value = "foobar"
        ShelfManager.destroy()
        b = ShelfManager()
        self.assertNotEqual(b.test_value, "foobar")

    def test_vote_for_shelf_increments_counter(self):
        """Test that voting for a shelf increments its vote count."""
        ShelfManager.destroy()
        ShelfManager().vote_for_shelf(
            self.album_id, "ShelfA", weight=0.0, reason="test"
        )
        ShelfManager().vote_for_shelf(
            self.album_id, "ShelfA", weight=0.0, reason="test"
        )
        # pylint: disable=protected-access
        self.assertEqual(ShelfManager()._shelf_votes[self.album_id]["ShelfA"], 2)

    def test_voting_determines_winner(self):
        """Test that the shelf with the most _votes is set as the winner."""
        ShelfManager.destroy()
        # pylint: disable=protected-access
        ShelfManager().vote_for_shelf(
            self.album_id, "ShelfA", weight=0.0, reason="test"
        )
        ShelfManager().vote_for_shelf(
            self.album_id, "ShelfB", weight=0.0, reason="test"
        )
        ShelfManager().vote_for_shelf(
            self.album_id, "ShelfA", weight=0.0, reason="test"
        )

        # The internal winner should be 'ShelfA'
        self.assertEqual(ShelfManager()._shelves_by_album[self.album_id], "ShelfA")

    def test_get_album_shelf_returns_winner(self):
        """Test that get_album_shelf returns the correct winner."""
        ShelfManager.destroy()
        # pylint: disable=protected-access
        ShelfManager().vote_for_shelf(
            self.album_id, "ShelfB", weight=0.0, reason="test"
        )
        ShelfManager().vote_for_shelf(
            self.album_id, "ShelfB", weight=0.0, reason="test"
        )
        ShelfManager().vote_for_shelf(
            self.album_id, "ShelfA", weight=0.0, reason="test"
        )

        shelf, decision = ShelfManager().get_album_shelf(self.album_id)
        self.assertEqual(shelf, "ShelfB")
        self.assertEqual(decision, "_votes")

    def test_get_album_shelf_returns_none_for_unknown_album(self):
        """Test that get_album_shelf returns None for an album with no _votes."""
        ShelfManager.destroy()
        # pylint: disable=protected-access
        shelf, decision = ShelfManager().get_album_shelf("unknown_album_id")
        self.assertIsNone(shelf)
        self.assertEqual(decision, "fallback")

    def test_clear_album_resets_state(self):
        """Test that clear_album removes all voting data for an album."""
        ShelfManager.destroy()
        ShelfManager().vote_for_shelf(
            self.album_id, "ShelfA", weight=0.0, reason="test"
        )

        # Verify _state exists
        # pylint: disable=protected-access
        self.assertIn(self.album_id, ShelfManager()._shelf_votes)
        self.assertIn(self.album_id, ShelfManager()._shelves_by_album)

        # Clear and verify _state is gone
        ShelfManager.clear_album(self.album_id)
        # pylint: disable=protected-access
        self.assertNotIn(self.album_id, ShelfManager()._shelf_votes)
        self.assertNotIn(self.album_id, ShelfManager()._shelves_by_album)


if __name__ == "__main__":
    unittest.main()
