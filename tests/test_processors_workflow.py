"""
Tests for the processors.py module.
"""

import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import MagicMock, patch

from typings import ConfigKey

from shelves.workflow import (
    TransitionEmptyNameToStage2,
    Transitions,
    TransitionsKnownNameToStage2,
    TransitionType,
    TransitionUnknownNameToStage2,
)


def get_strategy(workflow, cls):
    return next(s for s in workflow.transitions if isinstance(s, cls))


class WorkflowTest(unittest.TestCase):
    """Tests for the workflow transition logic."""

    def setUp(self):
        """Set up the test environment for workflow."""
        self.test_configuration = {
            ConfigKey.WORKFLOW_STAGE_1_SHELVES: ["Incoming"],
            ConfigKey.WORKFLOW_STAGE_2_SHELVES: ["Standard"],
            ConfigKey.WORKFLOW_ENABLED: True,
            ConfigKey.STAGE_1_INCLUDES_NON_SHELVES: False,
            ConfigKey.MOVE_FILES_TO: "/home/foobar/music",
            ConfigKey.KNOWN_SHELVES: ["Incoming", "Standard", "Stash", "Live"],
        }

        self.mock_shelf_manager = MagicMock()
        self.mock_manager_instance = MagicMock()
        self.mock_shelf_manager.return_value = self.mock_manager_instance
        self.mock_manager_instance.set_shelf_name = MagicMock()
        self.mock_manager_instance.base_path = Path(
            str(self.test_configuration[ConfigKey.MOVE_FILES_TO]),
        )
        self.mock_manager_instance.shelf_names = self.test_configuration[
            ConfigKey.KNOWN_SHELVES
        ]

    @patch("shelves.workflow.ContextBuilder")
    @patch("shelves.workflow.TransitionContext")
    @patch("shelves.workflow.config")
    def test_workflow_enabled(self, mock_config, mock_context, mock_context_builder):
        mock_config.setting = self.test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = True

        mock_context.transition_type = TransitionType.TO_STAGE_2
        mock_context.album_id = "019c1a82-3b9a-7538-babc-b156e1a7e8f5"
        mock_context.shelf_name = self.test_configuration[
            ConfigKey.WORKFLOW_STAGE_1_SHELVES
        ][0]
        mock_context_builder.build_context.return_value = mock_context

        # Create processor with mocked manager
        transition = Transitions(manager=self.mock_manager_instance)

        # Act
        transition.transition_to(
            mock_context.album_id, transition_type=TransitionType.TO_STAGE_2
        )

        # Assert
        self.mock_manager_instance.set_shelf_name.assert_called_with(
            album_id=mock_context.album_id,
            shelf_name=self.test_configuration[ConfigKey.WORKFLOW_STAGE_2_SHELVES][0],
        )

    @patch("shelves.workflow.ContextBuilder")
    @patch("shelves.workflow.TransitionContext")
    @patch("shelves.workflow.config")
    def test_workflow_disabled(self, mock_config, mock_context, mock_context_builder):
        mock_config.setting = self.test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = False

        mock_context.transition_type = TransitionType.TO_STAGE_2
        mock_context.album_id = "019c1a4f-4e6c-75ed-975d-fcd290068782"
        mock_context.shelf_name = self.test_configuration[
            ConfigKey.WORKFLOW_STAGE_1_SHELVES
        ][0]
        mock_context_builder.build_context.return_value = mock_context

        # Create processor with mocked manager
        transition = Transitions(manager=self.mock_manager_instance)

        # Act
        transition.transition_to(
            mock_context.album_id, transition_type=TransitionType.TO_STAGE_2
        )

        # Assert
        self.mock_manager_instance.set_shelf_name.assert_not_called()

    @patch("shelves.workflow.ContextBuilder")
    @patch("shelves.workflow.TransitionContext")
    @patch("shelves.workflow.config")
    def test_empty_shelf_is_not_transitioned(
        self, mock_config, mock_context, mock_context_builder
    ):
        mock_config.setting = self.test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = False

        mock_context.transition_type = TransitionType.TO_STAGE_2
        mock_context.album_id = "019c1a82-0a7d-7584-924c-e10e9d204402"
        mock_context.shelf_name = ""
        mock_context_builder.build_context.return_value = mock_context

        # Create processor with mocked manager
        transition = Transitions(manager=self.mock_manager_instance)

        # Act
        transition.transition_to(
            mock_context.album_id, transition_type=TransitionType.TO_STAGE_2
        )

        # Assert
        self.assertTrue(
            get_strategy(transition, TransitionEmptyNameToStage2).is_applicable(
                mock_context
            )
        )
        self.mock_manager_instance.set_shelf_name.assert_not_called()


if __name__ == "__main__":
    unittest.main()
