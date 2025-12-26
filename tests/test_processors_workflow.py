"""
Tests for the processors.py module.
"""

import unittest
from unittest.mock import MagicMock, patch

from shelves import ShelfProcessors
from shelves.constants import ShelfConstants


class AttrDict(dict):
    """A dictionary that allows attribute-style access."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


class WorkflowTest(unittest.TestCase):
    """Tests for the workflow transition logic."""

    def setUp(self):
        """Set up the test environment for workflow."""
        self.config_setting = {
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: False,
            ShelfConstants.CONFIG_MOVE_FILES_TO_KEY: "/music",
        }
        self.known_shelves = ["Incoming", "Standard", "Soundtracks", "Favorites"]

    def test_empty_shelf_is_not_transitioned(self):
        """Test that an empty shelf_name value is never transitioned."""
        self.assertEqual(ShelfProcessors._apply_workflow_transition(""), "")

    @patch("shelves.utils.ShelfUtils.validate_shelf_names")
    @patch("shelves.processors.config", new_callable=MagicMock)
    def test_disabled_workflow_returns_same_shelf(
        self, mock_config, mock_get_configured_shelves
    ):
        """Test that a disabled workflow never transitions the shelf_name."""
        mock_config.setting = self.config_setting
        mock_config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY] = False
        mock_get_configured_shelves.return_value = self.known_shelves

        self.assertEqual(
            ShelfProcessors._apply_workflow_transition("Incoming"), "Incoming"
        )

    @patch("shelves.processors.config", new_callable=MagicMock)
    def test_no_workflow_keys_leaves_shelf(self, mock_config):
        """Test that missing config keys prevent transition."""
        mock_config.setting = {}
        self.assertEqual(
            ShelfProcessors._apply_workflow_transition("Incoming"), "Incoming"
        )

    @patch("shelves.utils.ShelfUtils.validate_shelf_names")
    @patch("shelves.processors.config", new_callable=MagicMock)
    def test_stage1_match_transitions(
        self,
        mock_config,
        mock_get_configured_shelves,
    ):
        """Test that a matching shelf_name in stage 1 is correctly transitioned."""
        mock_config.setting = self.config_setting
        mock_get_configured_shelves.return_value = self.known_shelves
        self.assertEqual(
            ShelfProcessors._apply_workflow_transition("Incoming"), "Standard"
        )

    @patch("shelves.processors.config", new_callable=MagicMock)
    def test_no_match_in_stage1_leaves_shelf(self, mock_config):
        """Test that a shelf_name not in stage 1 is not transitioned."""
        mock_config.setting = self.config_setting
        self.assertEqual(
            ShelfProcessors._apply_workflow_transition("other_shelf"), "other_shelf"
        )

    @patch("shelves.processors.config", new_callable=MagicMock)
    def test_wildcard_in_stage1_transitions_any_shelf(self, mock_config):
        """Test that the wildcard in stage 1 transitions any shelf_name."""
        mock_config.setting = self.config_setting
        self.config_setting[ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY] = (
            True
        )
        self.assertEqual(
            ShelfProcessors._apply_workflow_transition("any_shelf"), "Standard"
        )
        self.assertEqual(
            ShelfProcessors._apply_workflow_transition("another_shelf"), "Standard"
        )

    @patch("shelves.processors.config", new_callable=MagicMock)
    def test_transition_to_same_shelf_does_nothing(self, mock_config):
        """Test that transitioning to the same shelf_name does not change the value."""
        mock_config.setting = self.config_setting
        self.assertEqual(
            ShelfProcessors._apply_workflow_transition("Standard"), "Standard"
        )

    @patch("shelves.processors.config", new_callable=MagicMock)
    def test_missing_stage_keys_with_enabled_true_leaves_shelf(self, mock_config):
        """Test that missing stage keys with workflow enabled leaves the shelf_name unchanged."""
        mock_config.setting = {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            # stage 2 missing
        }
        self.assertEqual(
            ShelfProcessors._apply_workflow_transition("Incoming"), "Incoming"
        )


if __name__ == "__main__":
    unittest.main()
