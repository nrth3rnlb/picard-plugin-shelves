# -*- coding: utf-8 -*-

"""
Tests for the ShelfManager class.
"""

import unittest
from unittest.mock import patch

from typings import ConfigKey, VotingType

from shelves.manager import ShelfManager
from shelves.typings import ProcessingType


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
            ConfigKey.MOVE_FILES_TO: "/music",
        }

    # def test_vote_for_shelf_increments_counter(self):
    #     """Test that voting for a shelf_name increments its vote count."""
    #     ShelfManager.destroy()
    #     ShelfManager().upvote(
    #         _album_id, "ShelfA"
    #     )
    #     ShelfManager().upvote(
    #         _album_id, "ShelfA"
    #     )
    #     # pylint: disable=protected-access
    #     self.assertEqual(
    #         ShelfManager()._shelf_votes_weighted[_album_id]["ShelfA"], 2
    #     )

    @patch("shelves.manager.config")
    def test_voting_determines_winner(self, _mock_config):
        """Test that the shelf_name with the most _shelf_votes_weighted is set as the winner."""
        # Arrange
        album_id = "019c003f-66fa-7a57-89ff-767bdc16ab09"
        ShelfManager().vote(album_id=album_id, shelf_name="ShelfA")
        ShelfManager().vote(
            album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.UP
        )
        ShelfManager().vote(
            album_id=album_id, shelf_name="ShelfB", voting_type=VotingType.UP
        )
        ShelfManager().vote(
            album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.UP
        )

        # The internal winner should be 'ShelfA'
        self.assertEqual(
            ShelfManager().get_shelf_name(album_id),
            "ShelfA",
        )

    @patch("shelves.manager.config")
    def test_get_album_shelf_returns_winner(self, _mock_config):
        """Test that resolve_shelf_name returns the correct winner."""
        album_id = "4cce8861-b30e-46ce-8e88-61b30e06ceb9"
        ShelfManager().vote(album_id=album_id, shelf_name="ShelfA")
        ShelfManager().vote(
            album_id=album_id, shelf_name="ShelfB", voting_type=VotingType.UP
        )
        ShelfManager().vote(
            album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.UP
        )
        ShelfManager().vote(
            album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.UP
        )
        ShelfManager().vote(
            album_id=album_id, shelf_name="ShelfB", voting_type=VotingType.UP
        )
        ShelfManager().vote(
            album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.UP
        )

        # The internal winner should be 'ShelfA'
        self.assertEqual(
            ShelfManager().get_shelf_name(album_id),
            "ShelfA",
        )


if __name__ == "__main__":
    unittest.main()
