"""
Tests for the processors.py module.
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from typings import ConfigKey

from shelves.transitions import (
    StrategyEmptyNameToStage2,
    StrategyKnownNameToStage2,
    StrategyUnknownNameToStage2,
    Transitions,
    TransitionType,
)


def get_strategy(transitions, cls):
    return next(s for s in transitions.transitions if isinstance(s, cls))


class TransitionsTest(unittest.TestCase):
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

    @patch("shelves.transitions.ContextBuilder")
    @patch("shelves.transitions.config")
    def test_workflow_enabled(self, mock_config, mock_context_builder):
        mock_config.setting = self.test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = True

        mock_context = MagicMock()
        mock_context.transition_type = TransitionType.TO_STAGE_2
        mock_context.album_id = "019c1a82-3b9a-7538-babc-b156e1a7e8f5"
        mock_context.shelf_name = mock_config.setting[
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
            shelf_name=mock_config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES][0],
        )

    @patch("shelves.transitions.ContextBuilder")
    @patch("shelves.transitions.config")
    def test_workflow_disabled(self, mock_config, mock_context_builder):
        mock_config.setting = self.test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = False

        mock_context = MagicMock()
        mock_context.transition_type = TransitionType.TO_STAGE_2
        mock_context.album_id = "019c1a4f-4e6c-75ed-975d-fcd290068782"
        mock_context.shelf_name = mock_config.setting[
            ConfigKey.WORKFLOW_STAGE_1_SHELVES
        ][0]
        mock_context_builder.build_context.return_value = mock_context

        cases = [
            # (STAGE_1_INCLUDES_NON_SHELVES, expected_is_applicable, expect_set_called)
            (False, True, True),
            (True, True, True),
        ]

        transition = Transitions(manager=self.mock_manager_instance)

        for includes, expected_is_applicable, expect_is_called in cases:
            with self.subTest(
                includes_non_shelves=includes,
                strategy_applies=expected_is_applicable,
                set_shelf_name=expect_is_called,
            ):
                mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = includes

                # Create fresh processor for each case
                transitions = Transitions(manager=self.mock_manager_instance)

                for strategy in transitions.transitions:
                    # Ensure previous call history doesn't interfere
                    self.mock_manager_instance.set_shelf_name.reset_mock()

                    # Act
                    transition.transition_to(
                        mock_context.album_id, transition_type=TransitionType.TO_STAGE_2
                    )

                    # Assert applicability
                    self.assertEqual(
                        get_strategy(transitions, strategy).is_applicable(mock_context),
                        expected_is_applicable,
                    )

                    # Assert set_shelf_name call state
                    if expect_is_called:
                        self.mock_manager_instance.set_shelf_name.assert_called_with(
                            album_id=mock_context.album_id,
                            shelf_name=mock_config.setting[
                                ConfigKey.WORKFLOW_STAGE_2_SHELVES
                            ][0],
                        )
                    else:
                        self.mock_manager_instance.set_shelf_name.assert_not_called()

    @patch("shelves.transitions.ContextBuilder")
    @patch("shelves.transitions.config")
    def test_known_name_to_stage_2_strategy(self, mock_config, mock_context_builder):
        mock_config.setting = self.test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = True

        mock_context = MagicMock()
        mock_context.transition_type = TransitionType.TO_STAGE_2
        mock_context.album_id = "019c1a82-0a7d-7584-924c-e10e9d204402"
        mock_context.shelf_name = mock_config.setting[ConfigKey.KNOWN_SHELVES][0]
        mock_context_builder.build_context.return_value = mock_context

        cases = [
            # (STAGE_1_INCLUDES_NON_SHELVES, expected_is_applicable, expect_set_called)
            (False, True, True),
            (True, True, True),
        ]

        for includes, expected_is_applicable, expect_is_called in cases:
            with self.subTest(
                includes_non_shelves=includes,
                strategy_applies=expected_is_applicable,
                set_shelf_name=expect_is_called,
            ):
                mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = includes

                # Create fresh processor for each case
                transitions = Transitions(manager=self.mock_manager_instance)

                # Ensure previous call history doesn't interfere
                self.mock_manager_instance.set_shelf_name.reset_mock()

                # Act
                transitions.transition_to(
                    mock_context.album_id, transition_type=TransitionType.TO_STAGE_2
                )

                # Assert applicability
                self.assertEqual(
                    get_strategy(transitions, StrategyKnownNameToStage2).is_applicable(
                        mock_context
                    ),
                    expected_is_applicable,
                )

                # Assert set_shelf_name call state
                if expect_is_called:
                    self.mock_manager_instance.set_shelf_name.assert_called_with(
                        album_id=mock_context.album_id,
                        shelf_name=mock_config.setting[
                            ConfigKey.WORKFLOW_STAGE_2_SHELVES
                        ][0],
                    )
                else:
                    self.mock_manager_instance.set_shelf_name.assert_not_called()

    @patch("shelves.transitions.ContextBuilder")
    @patch("shelves.transitions.config")
    def test_unknown_name_to_stage_2_strategy(self, mock_config, mock_context_builder):
        mock_config.setting = self.test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = True

        mock_context = MagicMock()
        mock_context.transition_type = TransitionType.TO_STAGE_2
        mock_context.album_id = "019c1a82-0a7d-7584-924c-e10e9d204402"
        mock_context.shelf_name = "UnknownShelf"
        mock_context_builder.build_context.return_value = mock_context

        cases = [
            # (STAGE_1_INCLUDES_NON_SHELVES, expected_is_applicable, expect_set_called)
            (False, False, False),
            (True, True, True),
        ]

        for includes, expected_is_applicable, expect_is_called in cases:
            with self.subTest(
                includes_non_shelves=includes,
                strategy_applies=expected_is_applicable,
                set_shelf_name=expect_is_called,
            ):
                mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = includes

                # Create fresh processor for each case
                transition = Transitions(manager=self.mock_manager_instance)

                # Ensure previous call history doesn't interfere
                self.mock_manager_instance.set_shelf_name.reset_mock()

                # Act
                transition.transition_to(
                    mock_context.album_id, transition_type=TransitionType.TO_STAGE_2
                )

                # Assert applicability
                self.assertEqual(
                    get_strategy(transition, StrategyUnknownNameToStage2).is_applicable(
                        mock_context
                    ),
                    expected_is_applicable,
                )

                # Assert set_shelf_name call state
                if expect_is_called:
                    self.mock_manager_instance.set_shelf_name.assert_called_with(
                        album_id=mock_context.album_id,
                        shelf_name=mock_config.setting[
                            ConfigKey.WORKFLOW_STAGE_2_SHELVES
                        ][0],
                    )
                else:
                    self.mock_manager_instance.set_shelf_name.assert_not_called()

    @patch("shelves.transitions.ContextBuilder")
    @patch("shelves.transitions.config")
    def test_empty_name_to_stage_2_strategy(self, mock_config, mock_context_builder):
        # Prepare
        mock_config.setting = self.test_configuration
        mock_config.setting[ConfigKey.WORKFLOW_ENABLED] = True

        mock_context = MagicMock()
        mock_context.transition_type = TransitionType.TO_STAGE_2
        mock_context.album_id = "019c1a82-0a7d-7584-924c-e10e9d204402"
        mock_context.shelf_name = ""
        mock_context_builder.build_context.return_value = mock_context

        cases = [
            # (STAGE_1_INCLUDES_NON_SHELVES, expected_is_applicable, expect_set_called)
            (False, True, False),
            (True, True, False),
        ]

        for includes, expected_is_applicable, expect_is_called in cases:
            with self.subTest(
                includes_non_shelves=includes,
                strategy_applies=expected_is_applicable,
                set_shelf_name=expect_is_called,
            ):
                mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = includes

                # Create fresh processor for each case
                transition = Transitions(manager=self.mock_manager_instance)

                # Ensure previous call history doesn't interfere
                self.mock_manager_instance.set_shelf_name.reset_mock()

                # Act
                transition.transition_to(
                    mock_context.album_id, transition_type=TransitionType.TO_STAGE_2
                )

                # Assert applicability
                self.assertEqual(
                    get_strategy(transition, StrategyEmptyNameToStage2).is_applicable(
                        mock_context
                    ),
                    expected_is_applicable,
                )

                # Assert set_shelf_name call state
                if expect_is_called:
                    self.mock_manager_instance.set_shelf_name.assert_called_with(
                        album_id=mock_context.album_id,
                        shelf_name=mock_config.setting[
                            ConfigKey.WORKFLOW_STAGE_2_SHELVES
                        ][0],
                    )
                else:
                    self.mock_manager_instance.set_shelf_name.assert_not_called()


if __name__ == "__main__":
    unittest.main()
