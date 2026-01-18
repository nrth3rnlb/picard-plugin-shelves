# -*- coding: utf-8 -*-

"""
Tests for the ShelfManager class.
"""

import unittest
from unittest.mock import patch

from shelves import constants
from shelves.manager import ShelfManager


class ManagerTest(unittest.TestCase):
    """
    Tests for the core _shelf_state management logic in ShelfManager.
    """

    def setUp(self):
        """Set up a new ShelfManager _instance for each test."""
        self.test_configuration: dict[
            str,
            str | list[str] | bool | int,
        ] = {
            constants.CONFIG_MOVE_FILES_TO_KEY: "/music",
        }

    @patch("shelves.manager.config")
    def test_singleton(self, _mock_config):
        """Test that the ShelfManager is a singleton."""
        ShelfManager.destroy()
        a = ShelfManager()
        a.test_value = "foobar"
        b = ShelfManager()
        self.assertEqual("foobar", b.test_value)

    @patch("shelves.manager.config")
    def test_singleton_destroy(self, _mock_config):
        """Test that the ShelfManager is a singleton."""

        ShelfManager.destroy()
        a = ShelfManager()
        a.test_value = "foobar"
        ShelfManager.destroy()
        b = ShelfManager()
        self.assertNotEqual(b.test_value, "foobar")

    # def test_vote_for_shelf_increments_counter(self):
    #     """Test that voting for a shelf_name increments its vote count."""
    #     ShelfManager.destroy()
    #     ShelfManager().vote_for_shelf(
    #         _album_id, "ShelfA", weight=0.1, reason="test"
    #     )
    #     ShelfManager().vote_for_shelf(
    #         _album_id, "ShelfA", weight=0.1, reason="test"
    #     )
    #     # pylint: disable=protected-access
    #     self.assertEqual(
    #         ShelfManager()._shelf_votes_weighted[_album_id]["ShelfA"], 2
    #     )

    @patch("shelves.manager.config")
    def test_voting_determines_winner(self, _mock_config):
        """Test that the shelf_name with the most _shelf_votes_weighted is set as the winner."""
        # Arrange
        ShelfManager.destroy()
        _album_id = "4cce8861-b30e-46ce-8e88-61b30e06ceb9"
        # pylint: disable=protected-access
        ShelfManager().vote_for_shelf(_album_id, "ShelfA", weight=0.1, reason="test")
        ShelfManager().vote_for_shelf(_album_id, "ShelfB", weight=0.1, reason="test")
        ShelfManager().vote_for_shelf(_album_id, "ShelfA", weight=0.1, reason="test")

        # The internal winner should be 'ShelfA'
        self.assertEqual(
                ShelfManager().get_album_shelf(_album_id),
                ("ShelfA", constants.SHELF_SOURCE_VOTES),
        )

    @patch("shelves.manager.config")
    def test_get_album_shelf_returns_winner(self, _mock_config):
        """Test that get_album_shelf returns the correct winner."""
        ShelfManager.destroy()
        _album_id = "4cce8861-b30e-46ce-8e88-61b30e06ceb9"
        # pylint: disable=protected-access
        ShelfManager().vote_for_shelf(_album_id, "ShelfB", weight=0.1, reason="test")
        ShelfManager().vote_for_shelf(_album_id, "ShelfB", weight=0.1, reason="test")
        ShelfManager().vote_for_shelf(_album_id, "ShelfA", weight=0.1, reason="test")

        # The internal winner should be 'ShelfA'
        self.assertEqual(
                ShelfManager().get_album_shelf(_album_id),
                ("ShelfB", constants.SHELF_SOURCE_VOTES),
        )

    @patch("shelves.manager.config")
    def test_clear_album_resets_state(self, _mock_config):
        """Test that clear_album removes all voting data for an album."""
        ShelfManager.destroy()
        # mock_config.setting = self.test_configuration
        _album_id = "4cce8861-b30e-46ce-8e88-61b30e06ceb9"
        ShelfManager().vote_for_shelf(_album_id, "ShelfA", weight=0.1, reason="test")

        # Verify _shelf_state exists
        # pylint: disable=protected-access
        self.assertIn(_album_id, ShelfManager()._assignment_engine._shelf_votes_weighted)
        self.assertIn(_album_id, ShelfManager()._assignment_engine._shelf_votes_counted)

        # Clear and verify _shelf_state is gone
        ShelfManager().clear_album(_album_id)
        # pylint: disable=protected-access
        self.assertNotIn(_album_id, ShelfManager()._assignment_engine._shelf_votes_weighted)
        self.assertNotIn(_album_id, ShelfManager()._assignment_engine._shelf_votes_counted)


if __name__ == "__main__":
    unittest.main()
