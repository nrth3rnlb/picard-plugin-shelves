"""
Tests for the processors.py module.
"""

import unittest
from copy import deepcopy
from unittest.mock import patch

from shelves.workflow import WorkflowEngine
from typings import ConfigKey


class WorkflowTest(unittest.TestCase):
    """Tests for the workflow transition logic."""

    def setUp(self):
        """Set up the test environment for workflow."""
        self.test_configuration = {
            ConfigKey.WORKFLOW_STAGE_1_SHELVES    : ["Incoming"],
            ConfigKey.WORKFLOW_STAGE_2_SHELVES    : ["Standard"],
            ConfigKey.WORKFLOW_ENABLED            : True,
            ConfigKey.STAGE_1_INCLUDES_NON_SHELVES: False,
            ConfigKey.MOVE_FILES_TO               : "/home/foobar/music",
            ConfigKey.KNOWN_SHELVES               : ["Incoming", "Standard", "Stash", "Live"],
        }

    @patch("shelves.workflow.config")
    def test_empty_shelf_is_not_transitioned(self, mock_config):
        """Test that an empty shelf_name value is never transitioned."""
        mock_config.setting = self.test_configuration
        self.assertEqual(WorkflowEngine.apply_transition(""), "")

    @patch("shelves.workflow.config")
    def test_disabled_workflow_returns_same_shelf(self, mock_config):
        """Test that a disabled workflow never transitions the shelf_name."""
        mock_config.setting = self.test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = False

        self.assertEqual(WorkflowEngine.apply_transition("Incoming"), "Incoming")

    @patch("shelves.workflow.config")
    def test_no_workflow_keys_leaves_shelf(self, mock_config):
        """Test that missing config keys prevent transition."""
        mock_config.setting = deepcopy(self.test_configuration)
        mock_config.setting[ConfigKey.WORKFLOW_STAGE_1_SHELVES] = []
        mock_config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES] = []
        self.assertEqual(WorkflowEngine.apply_transition("Incoming"), "Incoming")

    @patch("shelves.workflow.config")
    def test_stage1_match_transitions(self, mock_config):
        """Test that a matching shelf_name in stage 1 is correctly transitioned."""
        mock_config.setting = self.test_configuration
        self.assertEqual(WorkflowEngine.apply_transition("Standard"), "Standard")

    @patch("shelves.workflow.config")
    def test_no_match_in_stage1_leaves_shelf(self, mock_config):
        """Test that a shelf_name not in stage 1 is not transitioned."""
        mock_config.setting = self.test_configuration
        self.assertEqual(WorkflowEngine.apply_transition("other_shelf"), "other_shelf")

    @patch("shelves.workflow.config")
    def test_wildcard_in_stage1_transitions_any_shelf(self, mock_config):
        """Test that the wildcard in stage 1 transitions any shelf_name."""
        # Arrange
        mock_config.setting = deepcopy(self.test_configuration)
        mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = True

        any_shelf = "invidunt amet suscipit"

        # Act
        actual = WorkflowEngine.apply_transition(any_shelf)
        expected = mock_config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES][0]
        self.assertEqual(
                actual, expected, f"Expected {expected} but got {actual} for {any_shelf}",
        )

    @patch("shelves.workflow.config")
    def test_transition_to_same_shelf_does_nothing(self, mock_config):
        """Test that transitioning to the same shelf_name does not change the value."""
        mock_config.setting = deepcopy(self.test_configuration)
        self.assertEqual(WorkflowEngine.apply_transition("Standard"), "Standard")

    @patch("shelves.workflow.config")
    def test_missing_stage_keys_with_enabled_true_leaves_shelf(self, mock_config):
        """Test that missing stage keys with workflow enabled leaves the shelf_name unchanged."""
        mock_config.setting = deepcopy(self.test_configuration)
        mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = True
        mock_config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES] = []
        self.assertEqual(WorkflowEngine.apply_transition("Incoming"), "Incoming")


if __name__ == "__main__":
    unittest.main()
