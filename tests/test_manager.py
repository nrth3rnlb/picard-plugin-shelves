"""
Unit tests for the vote-based shelf management in the ShelfManager class.

This module contains test cases for the `ShelfManager` class, specifically
focusing on its voting and shelf state resolution logic. The tests validate
the behavior of different methods in determining the winner shelf based on
votes and ensuring correctness of the returned results. Mocking is employed
to simulate external dependencies when necessary.
"""

import unittest
from unittest.mock import patch

from picard import config
from typings import ConfigKey, VotingType

import tests
from shelves.exceptions import ShelfNotFoundException
from shelves.manager import ShelfManager


class ManagerTest(unittest.TestCase):
    """
    Tests for the core _shelf_state management logic in ShelfManager.
    """

    def setUp(self):
        self.test_configuration: dict[
            str,
            str | list[str] | bool | int,
        ] = {
            ConfigKey.MOVE_FILES_TO: "/music",
        }

    @patch("shelves.manager.config", spec_set=config)
    def test_upvote(self, mock_config):
        """Test that the shelf_name with the most _shelf_votes_weighted is set as the winner."""
        # Arrange
        mock_config.setting = tests.configuration
        manager = ShelfManager()

        album_id = "019c003f-66fa-7a57-89ff-767bdc16ab09"
        manager.vote(album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.UP)
        manager.vote(album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.UP)
        manager.vote(album_id=album_id, shelf_name="ShelfB", voting_type=VotingType.UP)

        self.assertEqual(
            ShelfManager().get_shelf_name(album_id),
            "ShelfA",
        )

    @patch("shelves.manager.config", spec_set=config)
    def test_downvote(self, mock_config):
        """Test that the shelf_name with the most _shelf_votes_weighted is set as the winner."""
        # Arrange
        mock_config.setting = tests.configuration
        manager = ShelfManager()

        album_id = "019c003f-66fa-7a57-89ff-767bdc16ab09"
        manager.vote(
            album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.DOWN
        )
        manager.vote(
            album_id=album_id, shelf_name="ShelfB", voting_type=VotingType.DOWN
        )

        self.assertRaises(ShelfNotFoundException)

    @patch("shelves.manager.config", spec_set=config)
    def test_mixed_vote(self, mock_config):
        """Test that voting for a shelf_name increments its vote count."""
        # Arrange
        mock_config.setting = tests.configuration
        manager = ShelfManager()

        album_id = "019c6169-acbe-75d9-8ebc-dc6b79a1d67d"
        with self.subTest(album_id=album_id):
            manager.vote(
                album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.UP
            )
            manager.vote(
                album_id=album_id, shelf_name="ShelfB", voting_type=VotingType.UP
            )
            manager.vote(
                album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.DOWN
            )
            self.assertEqual(
                ShelfManager().get_shelf_name(album_id),
                "ShelfB",
            )

        # Act
        album_id = "019c616e-e067-7c84-91b3-999c54d6a219"
        with self.subTest(album_id=album_id):
            manager.vote(
                album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.DOWN
            )
            manager.vote(
                album_id=album_id, shelf_name="ShelfA", voting_type=VotingType.UP
            )
            manager.vote(
                album_id=album_id, shelf_name="ShelfB", voting_type=VotingType.UP
            )

            self.assertEqual(
                ShelfManager().get_shelf_name(album_id),
                "ShelfA",
            )
