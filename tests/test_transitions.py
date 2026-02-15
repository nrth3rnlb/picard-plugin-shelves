"""
Unit tests for the workflow transition logic, validating the behavior of
various strategies under different configurations.

This module includes tests to verify the assignment of appropriate
transition strategies based on workflow settings and shelf configurations.
The tests use mock objects and simulate different scenarios to ensure that
the transitions work as expected.

Classes:
    TransitionsTest: Contains test cases for the behavior of workflow
    transitions based on different strategies and configurations.
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from contexts import TransitionContext
from typings import ConfigKey

from shelves.transitions import (
    StrategyEmptyNameToStage2,
    StrategyKnownNameToStage2,
    StrategyUnknownNameToStage2,
    Transitions,
)


def get_strategy(workflow, cls):
    return next(s for s in workflow.strategies if isinstance(s, cls))


class TransitionsTest(unittest.TestCase):
    """Tests for the workflow transition logic."""

    def setUp(self):

        self.test_configuration = {
            ConfigKey.WORKFLOW_STAGE_1_SHELVES: ["Incoming"],
            ConfigKey.WORKFLOW_STAGE_2_SHELVES: ["Standard"],
            ConfigKey.WORKFLOW_ENABLED: True,
            ConfigKey.STAGE_1_INCLUDES_NON_SHELVES: False,
            ConfigKey.MOVE_FILES_TO: "/home/foobar/music",
            ConfigKey.KNOWN_SHELVES: ["Incoming", "Standard", "Stash", "Live"],
        }

        self.mock_manager = MagicMock()
        self.mock_manager_instance = MagicMock()
        self.mock_manager.return_value = self.mock_manager_instance
        self.mock_manager_instance.set_shelf_name = MagicMock()
        self.mock_manager_instance.base_path = Path(
            str(self.test_configuration[ConfigKey.MOVE_FILES_TO]),
        )
        self.mock_manager_instance.registered_shelf_names = self.test_configuration[
            ConfigKey.KNOWN_SHELVES
        ]

    @patch("shelves.transitions.ContextBuilder")
    @patch("shelves.transitions.config")
    def test_known_name_to_stage_2_strategy(self, mock_config, mock_context_builder):
        mock_config.setting = self.test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = True

        mock_context = MagicMock()
        mock_context.transition_type = TransitionContext.TransitionType.TO_STAGE_2
        mock_context.album_id = "019c1a82-0a7d-7584-924c-e10e9d204402"
        mock_context.shelf_name = mock_config.setting[ConfigKey.KNOWN_SHELVES][0]
        mock_context_builder.build_context.return_value = mock_context

        cases = [
            # (STAGE_1_INCLUDES_NON_SHELVES, expectation)
            (False, True),
            (True, True),
        ]

        for includes, expectation in cases:
            with self.subTest(
                includes_non_shelves=includes,
                expectation=expectation,
            ):
                mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = includes

                # Create fresh processor for each case
                transition = Transitions(manager=self.mock_manager_instance)

                # Ensure previous call history doesn't interfere
                self.mock_manager_instance.set_shelf_name.reset_mock()

                # Act
                context = transition.transition_to(
                    mock_context.album_id,
                    transition_type=TransitionContext.TransitionType.TO_STAGE_2,
                )

                # Expected
                if expectation:
                    self.assertEqual(
                        context.strategy, StrategyKnownNameToStage2.__name__
                    )
                else:
                    self.assertNotEqual(
                        context.strategy, StrategyKnownNameToStage2.__name__
                    )

    @patch("shelves.transitions.ContextBuilder")
    @patch("shelves.transitions.config")
    def test_unknown_name_to_stage_2_strategy(self, mock_config, mock_context_builder):
        mock_config.setting = self.test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = True

        mock_context = MagicMock()
        mock_context.transition_type = TransitionContext.TransitionType.TO_STAGE_2
        mock_context.album_id = "019c1a82-0a7d-7584-924c-e10e9d204402"
        mock_context.shelf_name = "UnknownShelf"
        mock_context_builder.build_context.return_value = mock_context

        cases = [
            # (STAGE_1_INCLUDES_NON_SHELVES, expectation)
            (False, False),
            (True, True),
        ]

        for includes, expectation in cases:
            with self.subTest(
                includes_non_shelves=includes,
                expectation=expectation,
            ):
                mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = includes

                # Create fresh processor for each case
                transition = Transitions(manager=self.mock_manager_instance)

                # Ensure previous call history doesn't interfere
                self.mock_manager_instance.set_shelf_name.reset_mock()

                # Act
                context = transition.transition_to(
                    mock_context.album_id,
                    transition_type=TransitionContext.TransitionType.TO_STAGE_2,
                )

                # Expected
                if expectation:
                    self.assertEqual(
                        context.strategy, StrategyUnknownNameToStage2.__name__
                    )
                else:
                    self.assertNotEqual(
                        context.strategy, StrategyUnknownNameToStage2.__name__
                    )

    @patch("shelves.transitions.ContextBuilder")
    @patch("shelves.transitions.config")
    def test_empty_name_to_stage_2_strategy(self, mock_config, mock_context_builder):
        # Prepare
        mock_config.setting = self.test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = True

        mock_context = MagicMock()
        mock_context.transition_type = TransitionContext.TransitionType.TO_STAGE_2
        mock_context.album_id = "019c1a82-0a7d-7584-924c-e10e9d204402"
        mock_context.shelf_name = ""
        mock_context_builder.build_context.return_value = mock_context

        cases = [
            # (STAGE_1_INCLUDES_NON_SHELVES, expectation)
            (False, True),
            (True, True),
        ]

        for includes, expectation in cases:
            with self.subTest(
                includes_non_shelves=includes,
                expectation=expectation,
            ):
                mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = includes

                # Create fresh processor for each case
                transition = Transitions(manager=self.mock_manager_instance)

                # Ensure previous call history doesn't interfere
                self.mock_manager_instance.set_shelf_name.reset_mock()

                # Act
                context = transition.transition_to(
                    mock_context.album_id,
                    transition_type=TransitionContext.TransitionType.TO_STAGE_2,
                )

                # Expected
                if expectation:
                    self.assertEqual(
                        context.strategy, StrategyEmptyNameToStage2.__name__
                    )
                else:
                    self.assertNotEqual(
                        context.strategy, StrategyEmptyNameToStage2.__name__
                    )
