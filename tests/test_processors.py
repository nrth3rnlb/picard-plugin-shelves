"""
Unit tests for the Processors class and its associated strategies.

This module contains unit tests for validating the behavior of various
strategies in the `Processors` class, specifically to ensure correct handling
of file post-addition processing logic under different conditions. The tests
cover scenarios such as known identical names, differing names derived from
tags and paths, and unknown names obtained from paths.
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock

from picard.file import File

from shelves.contexts import ProcessingContext
from shelves.manager import ShelfManager, ShelfManagerSettings, ShelfName
from shelves.processors import (
    Processors,
    StrategyKnownIdenticalNames,
    StrategyKnownNameFromPathDiffersFromTag,
    StrategyManualSet,
    StrategyManualUnset,
    StrategyUnknownNameFromPath,
)
from shelves.typings import ConfigKey, TagKey, VotingType

# def get_strategy(processors, cls):
#     return next(s for s in processors.strategies if isinstance(s, cls))


class ProcessorsTest(unittest.TestCase):
    """
    Tests the priority logic in the file_post_addition_to_track_processor.
    """

    def setUp(self):
        pass  # self.processors = Processors.__new__(Processors)

    @staticmethod
    def make_test_manager() -> ShelfManager:
        return ShelfManager(
            settings=ShelfManagerSettings(
                base_path=Path("/music"),
                shelf_names={ShelfName("ShelfA"), ShelfName("ShelfB")},
            )
        )

    def test_known_identical_names_strategy(
        self,
    ):
        file_mock = MagicMock(spec=File)
        file_mock.filename = "/music/ShelfA/artist/album/track.mp3"
        file_mock.metadata = {
            TagKey.MUSICBRAINZ_ALBUM_ID: "019c60c2-2ee0-742e-bb7a-692060c8b192",
            TagKey.SHELF: "ShelfA",
            TagKey.SHELF_LOCKED: False,
        }

        # Do not use a singleton instance; instead, instantiate it directly
        manager = self.make_test_manager()
        context: ProcessingContext = Processors(manager).build_processing_context(
            file=file_mock,
            processing_type=ProcessingContext.ProcessingType.LOAD,
            name_to_set=ShelfName("ShelfA"),
        )
        strategy = None
        strategies = [cls(manager) for cls in Processors.STRATEGY_ORDER]
        for strategy in strategies:
            if strategy.is_applicable(context):
                break
        expected_strategy = StrategyKnownIdenticalNames
        self.assertIsInstance(
            strategy,
            expected_strategy,
            msg=f"Expected {expected_strategy.__name__} but got {strategy.__class__.__name__}",
        )

    def test_known_name_from_path_differs_from_tag(self):
        # Arrange
        file_mock = MagicMock(spec=File)
        file_mock.filename = "/music/ShelfA/artist/album/track.mp3"
        file_mock.metadata = {TagKey.SHELF: ShelfName("ShelfB")}

        # Do not use a singleton instance; instead, instantiate it directly
        manager = self.make_test_manager()
        context: ProcessingContext = Processors(manager).build_processing_context(
            file=file_mock,
            processing_type=ProcessingContext.ProcessingType.LOAD,
        )
        strategy = None
        strategies = [cls(manager) for cls in Processors.STRATEGY_ORDER]
        for strategy in strategies:
            if strategy.is_applicable(context):
                break
        expected_strategy = StrategyKnownNameFromPathDiffersFromTag
        self.assertIsInstance(
            strategy,
            expected_strategy,
            msg=f"Expected {expected_strategy.__name__} but got {strategy.__class__.__name__}",
        )

    def test_unknown_name_from_path(self):
        file_mock = MagicMock(spec=File)
        file_mock.filename = "/music/unknown/artist/album/track.mp3"
        file_mock.metadata = {}

        # Do not use a singleton instance; instead, instantiate it directly
        manager = self.make_test_manager()
        context: ProcessingContext = Processors(manager).build_processing_context(
            file=file_mock,
            processing_type=ProcessingContext.ProcessingType.LOAD,
        )
        strategy = None
        strategies = [cls(manager) for cls in Processors.STRATEGY_ORDER]
        for strategy in strategies:
            if strategy.is_applicable(context):
                break

        expected_strategy = StrategyUnknownNameFromPath
        self.assertIsInstance(
            strategy,
            expected_strategy,
            msg=f"Expected {expected_strategy.__name__} but got {strategy.__class__.__name__}",
        )

    def test_strategy_manual_set(self):
        """
        Test that a strategy can be manually set in the processing context.
        """
        file_mock = MagicMock(spec=File)
        file_mock.filename = "/music/unknown/artist/album/track.mp3"
        file_mock.metadata = {TagKey.SHELF: ShelfName("ShelfB")}

        # Do not use a singleton instance; instead, instantiate it directly
        manager = self.make_test_manager()
        context: ProcessingContext = Processors(manager).build_processing_context(
            file=file_mock,
            processing_type=ProcessingContext.ProcessingType.SET,
            name_to_set=ShelfName("ShelfA"),
        )
        strategy = None
        strategies = [cls(manager) for cls in Processors.STRATEGY_ORDER]
        for strategy in strategies:
            if strategy.is_applicable(context):
                break

        expected_strategy = StrategyManualSet
        self.assertIsInstance(
            strategy,
            expected_strategy,
            msg=f"Expected {expected_strategy.__name__} but got {strategy.__class__.__name__}",
        )

    def test_strategy_manual_unset(self):
        """
        Test that a strategy can be manually unset in the processing context.
        """
        file_mock = MagicMock(spec=File)
        file_mock.filename = "/music/unknown/artist/album/track.mp3"
        file_mock.metadata = {TagKey.SHELF: ShelfName("ShelfB")}

        # Do not use a singleton instance; instead, instantiate it directly
        manager = self.make_test_manager()
        context: ProcessingContext = Processors(manager).build_processing_context(
            file=file_mock,
            processing_type=ProcessingContext.ProcessingType.UNSET,
        )
        strategy = None
        strategies = [cls(manager) for cls in Processors.STRATEGY_ORDER]
        for strategy in strategies:
            if strategy.is_applicable(context):
                break

        expected_strategy = StrategyManualUnset
        self.assertIsInstance(
            strategy,
            expected_strategy,
            msg=f"Expected {expected_strategy.__name__} but got {strategy.__class__.__name__}",
        )
