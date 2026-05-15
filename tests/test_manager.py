"""
Unit tests for the vote-based shelf management in the ShelfManager class.

This module contains test cases for the `ShelfManager` class, specifically
focusing on its voting and shelf state resolution logic. The tests validate
the behavior of different methods in determining the winner shelf based on
votes and ensuring correctness of the returned results. Mocking is employed
to simulate external dependencies when necessary.
"""

import unittest
from pathlib import Path

from typings import VotingType

from shelves.manager import ShelfManager, ShelfManagerSettings


class ManagerTest(unittest.TestCase):
    """
    Tests for the core _shelf_state management logic in ShelfManager.
    """

    def setUp(self):
        pass

    @staticmethod
    def make_test_manager() -> ShelfManager:
        return ShelfManager(
            settings=ShelfManagerSettings(
                base_path=Path("/music"),
                shelf_names={"ShelfA", "ShelfB"},
            )
        )

    def test_manager_uses_explicit_settings(self):
        manager = self.make_test_manager()

        assert manager.base_path == Path("/music")
        assert manager.registered_shelf_names == {"ShelfA", "ShelfB"}

    def test_upvote(self):
        """Test that the shelf_name with the most _shelf_votes_weighted is set as the winner."""
        manager = self.make_test_manager()

        album_id = "album-1"
        manager.vote(album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.UP)
        manager.vote(album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.UP)
        manager.vote(album_id=album_id, shelf_name="ShelfB", voting_type=VotingType.UP)

        assert manager.get_shelf_name(album_id) == "ShelfA"

    def test_downvote(self):
        """Test that the shelf_name with the most _shelf_votes_weighted is set as the winner."""
        # Arrange
        manager = self.make_test_manager()

        album_id = "album-1"
        manager.vote(album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.UP)
        manager.vote(album_id=album_id, shelf_name="ShelfB", voting_type=VotingType.UP)
        manager.vote(
            album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.DOWN
        )

        assert manager.get_shelf_name(album_id) == "ShelfB"
