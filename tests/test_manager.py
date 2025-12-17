# -*- coding: utf-8 -*-

"""
Tests for the _ShelfManager class.
"""

import unittest
from unittest.mock import MagicMock

from shelves.manager import _ShelfManager


class ManagerTest(unittest.TestCase):
    """
    Tests for the core state management logic in _ShelfManager.
    """

    def setUp(self):
        """Set up a new _ShelfManager instance for each test."""
        # Mock the dependencies required by the _ShelfManager constructor
        self.mock_validators = MagicMock()
        self.mock_utils = MagicMock()
        self.manager = _ShelfManager()
        self.album_id = "album123"

    def test_vote_for_shelf_increments_counter(self):
        """Test that voting for a shelf increments its vote count."""
        self.manager.vote_for_shelf(self.album_id, "ShelfA")
        self.manager.vote_for_shelf(self.album_id, "ShelfA")
        self.assertEqual(self.manager._shelf_votes[self.album_id]["ShelfA"], 2)

    def test_voting_determines_winner(self):
        """Test that the shelf with the most votes is set as the winner."""
        self.manager.vote_for_shelf(self.album_id, "ShelfA")
        self.manager.vote_for_shelf(self.album_id, "ShelfB")
        self.manager.vote_for_shelf(self.album_id, "ShelfA")

        # The internal winner should be 'ShelfA'
        self.assertEqual(self.manager._shelves_by_album[self.album_id], "ShelfA")

    def test_get_album_shelf_returns_winner(self):
        """Test that get_album_shelf returns the correct winner."""
        self.manager.vote_for_shelf(self.album_id, "ShelfB")
        self.manager.vote_for_shelf(self.album_id, "ShelfB")
        self.manager.vote_for_shelf(self.album_id, "ShelfA")

        shelf = self.manager.get_album_shelf(self.album_id)
        self.assertEqual(shelf, "ShelfB")

    def test_get_album_shelf_returns_none_for_unknown_album(self):
        """Test that get_album_shelf returns None for an album with no votes."""
        shelf = self.manager.get_album_shelf("unknown_album_id")
        self.assertIsNone(shelf)

    def test_clear_album_resets_state(self):
        """Test that clear_album removes all voting data for an album."""
        self.manager.vote_for_shelf(self.album_id, "ShelfA")

        # Verify state exists
        self.assertIn(self.album_id, self.manager._shelf_votes)
        self.assertIn(self.album_id, self.manager._shelves_by_album)

        # Clear and verify state is gone
        self.manager.clear_album(self.album_id)
        self.assertNotIn(self.album_id, self.manager._shelf_votes)
        self.assertNotIn(self.album_id, self.manager._shelves_by_album)


if __name__ == "__main__":
    unittest.main()
