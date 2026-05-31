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

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from shelves.contexts import TransitionContext
from shelves.transitions import (
    StrategyEmptyNameToStage2,
    StrategyKnownNameToStage2,
    StrategyUnknownNameToStage2,
    Transitions,
)
from shelves.typings import ConfigKey


def get_strategy(workflow, cls):
    return next(s for s in workflow.strategies if isinstance(s, cls))


@pytest.fixture
def test_configuration():
    return {
        ConfigKey.WORKFLOW_STAGE_1_SHELVES: ["Incoming"],
        ConfigKey.WORKFLOW_STAGE_2_SHELVES: ["Standard"],
        ConfigKey.WORKFLOW_ENABLED: True,
        ConfigKey.STAGE_1_INCLUDES_NON_SHELVES: False,
        ConfigKey.MOVE_FILES_TO: "/home/foobar/music",
        ConfigKey.KNOWN_SHELVES: ["Incoming", "Standard", "Stash", "Live"],
    }


@pytest.fixture
def mock_manager_instance(test_configuration):
    mock_manager = MagicMock()
    mock_manager_instance = MagicMock()
    mock_manager.return_value = mock_manager_instance
    mock_manager_instance.set_shelf_name = MagicMock()
    mock_manager_instance.base_path = Path(
        str(test_configuration[ConfigKey.MOVE_FILES_TO]),
    )
    mock_manager_instance.registered_shelf_names = test_configuration[
        ConfigKey.KNOWN_SHELVES
    ]
    return mock_manager_instance


@pytest.fixture
def mock_config():
    return MagicMock()


@pytest.fixture
def mock_context_builder():
    return MagicMock()


class TestTransitions:
    """Tests for the workflow transition logic."""

    @pytest.mark.parametrize(
        "includes,expectation",
        [
            # (STAGE_1_INCLUDES_NON_SHELVES, expectation)
            (False, True),
            (True, True),
        ],
    )
    def test_known_name_to_stage_2_strategy(
        self,
        mock_config,
        mock_context_builder,
        test_configuration,
        mock_manager_instance,
        includes,
        expectation,
    ):
        mock_config.setting = test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = True

        mock_context = MagicMock()
        mock_context.transition_type = TransitionContext.TransitionType.TO_STAGE_2
        mock_context.album_id = "019c1a82-0a7d-7584-924c-e10e9d204402"
        mock_context.shelf_name = mock_config.setting[ConfigKey.KNOWN_SHELVES][0]
        mock_context_builder.build_context.return_value = mock_context

        mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = includes

        # Create fresh processor for each case
        transition = Transitions(_manager=mock_manager_instance)

        # Ensure previous call history doesn't interfere
        mock_manager_instance.set_shelf_name.reset_mock()

        # Act
        context = transition.transition_to(
            mock_context.album_id,
            transition_type=TransitionContext.TransitionType.TO_STAGE_2,
        )

        # Expected
        if expectation:
            assert context.strategy == StrategyKnownNameToStage2.__name__
        else:
            assert context.strategy != StrategyKnownNameToStage2.__name__

    @pytest.mark.parametrize(
        "includes,expectation",
        [
            # (STAGE_1_INCLUDES_NON_SHELVES, expectation)
            (False, False),
            (True, True),
        ],
    )
    def test_unknown_name_to_stage_2_strategy(
        self,
        mock_config,
        mock_context_builder,
        test_configuration,
        mock_manager_instance,
        includes,
        expectation,
    ):
        mock_config.setting = test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = True

        mock_context = MagicMock()
        mock_context.transition_type = TransitionContext.TransitionType.TO_STAGE_2
        mock_context.album_id = "019c1a82-0a7d-7584-924c-e10e9d204402"
        mock_context.shelf_name = "UnknownShelf"
        mock_context_builder.build_context.return_value = mock_context

        mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = includes

        # Create fresh processor for each case
        transition = Transitions(_manager=mock_manager_instance)

        # Ensure previous call history doesn't interfere
        mock_manager_instance.set_shelf_name.reset_mock()

        # Act
        context = transition.transition_to(
            mock_context.album_id,
            transition_type=TransitionContext.TransitionType.TO_STAGE_2,
        )

        # Expected
        if expectation:
            assert context.strategy == StrategyUnknownNameToStage2.__name__
        else:
            assert context.strategy != StrategyUnknownNameToStage2.__name__

    @pytest.mark.parametrize(
        "includes,expectation",
        [
            # (STAGE_1_INCLUDES_NON_SHELVES, expectation)
            (False, True),
            (True, True),
        ],
    )
    def test_empty_name_to_stage_2_strategy(
        self,
        mock_config,
        mock_context_builder,
        test_configuration,
        mock_manager_instance,
        includes,
        expectation,
    ):
        # Prepare
        mock_config.setting = test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = True

        mock_context = MagicMock()
        mock_context.transition_type = TransitionContext.TransitionType.TO_STAGE_2
        mock_context.album_id = "019c1a82-0a7d-7584-924c-e10e9d204402"
        mock_context.shelf_name = ""
        mock_context_builder.build_context.return_value = mock_context

        mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = includes

        # Create fresh processor for each case
        transition = Transitions(_manager=mock_manager_instance)

        # Ensure previous call history doesn't interfere
        mock_manager_instance.set_shelf_name.reset_mock()

        # Act
        context = transition.transition_to(
            mock_context.album_id,
            transition_type=TransitionContext.TransitionType.TO_STAGE_2,
        )

        # Expected
        if expectation:
            assert context.strategy == StrategyEmptyNameToStage2.__name__
        else:
            assert context.strategy != StrategyEmptyNameToStage2.__name__
