# -*- coding: utf-8 -*-

"""
Tests for the processor priority logic.
"""

import unittest
from copy import copy
from pathlib import Path
from typing import Set
from unittest.mock import MagicMock, patch

from typings import ConfigKey, ProcessingType, TagKey

from shelves.processors import (
    Processors,
    StrategyKnownIdenticalNames,
    StrategyKnownNameFromPathDiffersFromTag,
    StrategyUnknownNameFromPath,
)


def get_strategy(processors, cls):
    return next(s for s in processors.strategies if isinstance(s, cls))


class ProcessorsTest(unittest.TestCase):
    """
    Tests the priority logic in the file_post_addition_to_track_processor.
    """

    def setUp(self):
        """Set up the test environment for workflow."""
        # Create mock manager to avoid config access during init
        self.mock_manager = MagicMock()
        self.mock_manager.shelf_names = {
            "Incoming",
            "Standard",
            "Soundtracks",
            "Favorites",
        }
        self.mock_manager.base_path = Path("/music")
        self.processors = Processors(manager=self.mock_manager)

        self.known_shelves: Set[str] = {
            "Incoming",
            "Standard",
            "Soundtracks",
            "Favorites",
        }
        self.test_configuration = {
            ConfigKey.WORKFLOW_ENABLED: False,
            ConfigKey.WORKFLOW_STAGE_1_SHELVES: ["Incoming"],
            ConfigKey.WORKFLOW_STAGE_2_SHELVES: ["Standard"],
            ConfigKey.MOVE_FILES_TO: "/music",
        }

    @patch("shelves.processors.ContextBuilder")
    @patch("shelves.processors.Context")
    @patch("shelves.processors.ShelfManager")
    def test_known_identical_names_strategy(
        self, mock_shelf_manager, mock_context, mock_context_builder
    ):
        # Arrange
        shelf_sub_dir = copy(self.known_shelves).pop()
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance
        mock_manager_instance.base_path = Path(
            str(self.test_configuration[ConfigKey.MOVE_FILES_TO]),
        )
        mock_manager_instance.registered_shelf_names = self.known_shelves

        mock_context.name_from_tag = shelf_sub_dir
        mock_context.name_from_path = shelf_sub_dir
        mock_context.is_locked = False
        mock_context.processing_type = ProcessingType.ADD

        mock_context_builder.build.return_value = mock_context

        file_mock = MagicMock()
        file_mock.filename = f"/music/{shelf_sub_dir}/artist/album/track.mp3"
        file_mock.metadata = {
            TagKey.MUSICBRAINZ_ALBUMID: "f62b3023-34e7-40cd-bd08-b183118cb1fd",
            TagKey.SHELF: shelf_sub_dir,
        }
        # Create processor with mocked manager
        processors = Processors(manager=mock_manager_instance)

        # Act
        processors.file_post_addition_to_track_processor(
            track=MagicMock(),
            file=file_mock,
        )

        # Assert
        self.assertTrue(
            get_strategy(processors, StrategyKnownIdenticalNames).is_applicable(
                mock_context
            )
        )

    @patch("shelves.processors.ContextBuilder")
    @patch("shelves.processors.Context")
    @patch("shelves.processors.ShelfManager")
    def test_known_name_from_path(
        self, mock_shelf_manager, mock_context, mock_context_builder
    ):
        # Arrange
        shelf_sub_dirs = copy(self.known_shelves)
        name_from_tag = shelf_sub_dirs.pop()
        name_from_path = shelf_sub_dirs.pop()
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance
        mock_manager_instance.base_path = Path(
            str(self.test_configuration[ConfigKey.MOVE_FILES_TO]),
        )
        mock_manager_instance.registered_shelf_names = self.known_shelves

        mock_context.name_from_tag = name_from_tag
        mock_context.name_from_path = name_from_path
        mock_context.is_locked = False
        mock_context.processing_type = ProcessingType.ADD
        mock_context_builder.build.return_value = mock_context

        file_mock = MagicMock()
        file_mock.filename = f"/music/{name_from_path}/artist/album/track.mp3"
        file_mock.metadata = {
            TagKey.MUSICBRAINZ_ALBUMID: "019c008b-3934-7d68-9713-84de82082007",
            TagKey.SHELF: name_from_tag,
        }
        # Create processor with mocked manager
        processors = Processors(manager=mock_manager_instance)

        # Act
        processors.file_post_addition_to_track_processor(
            track=MagicMock(),
            file=file_mock,
        )

        # Assert
        self.assertTrue(
            get_strategy(
                processors, StrategyKnownNameFromPathDiffersFromTag
            ).is_applicable(mock_context)
        )

    @patch("shelves.processors.ContextBuilder")
    @patch("shelves.processors.Context")
    @patch("shelves.processors.ShelfManager")
    def test_unknown_name_from_path(
        self, mock_shelf_manager, mock_context, mock_context_builder
    ):
        shelf_sub_dir = copy(self.known_shelves).pop()
        unknown_shelf_subdir = f"unknown_{shelf_sub_dir}"
        mock_manager_instance = MagicMock()
        mock_shelf_manager.return_value = mock_manager_instance
        mock_manager_instance.base_path = Path(
            str(self.test_configuration[ConfigKey.MOVE_FILES_TO]),
        )
        mock_manager_instance.registered_shelf_names = self.known_shelves

        mock_context.name_from_tag = shelf_sub_dir
        mock_context.name_from_path = unknown_shelf_subdir
        mock_context.is_locked = False
        mock_context.processing_type = ProcessingType.ADD

        mock_context_builder.build.return_value = mock_context

        file_mock = MagicMock()
        file_mock.filename = f"/music/{unknown_shelf_subdir}/artist/album/track.mp3"
        file_mock.metadata = {
            TagKey.MUSICBRAINZ_ALBUMID: "019c008f-cadf-7d19-83d5-d3f0b8ea3f69",
            TagKey.SHELF: shelf_sub_dir,
        }
        # Create processor with mocked manager
        processors = Processors(manager=mock_manager_instance)

        # Act
        processors.file_post_addition_to_track_processor(
            track=MagicMock(),
            file=file_mock,
        )

        # Assert
        self.assertTrue(
            get_strategy(processors, StrategyUnknownNameFromPath).is_applicable(
                mock_context
            )
        )


if __name__ == "__main__":
    unittest.main()
