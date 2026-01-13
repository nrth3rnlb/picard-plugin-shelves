import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import MagicMock, patch

from shelves import constants
from shelves.exceptions import ShelfNotFoundException
from shelves.script_functions import shelf


class AttrDict(dict):
    """A dictionary that allows attribute-style access."""

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class ScriptFunctionsTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        self.test_configuration = {
            # constants.CONFIG_MOVE_FILES_TO_KEY: "/home/foobar/music",
            constants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            constants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: False,
            constants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
            constants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
            # constants.CONFIG_KNOWN_SHELVES_KEY: sorted(
            #     ["Incoming", "Standard", "Stash", "Live"]
            # ),
        }

    @patch("shelves.workflow.config")
    def test_func_shelf_returns_same_if_not_in_stage_1_and_not_includes(
        self, mock_config
    ):
        """
        Tests the behavior of the `shelf` function to ensure it returns the same value
        when the shelf is not located in stage 1 and the parameter
        `CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY` is set to `False`.

        :param mock_config: Mocked configuration used to simulate external system settings.
        :type mock_config: unittest.mock.MagicMock
        :return: None
        :rtype: None
        """

        # Arrange
        # mock_manager_instance = MagicMock()
        # mock_manager.return_value = mock_manager_instance
        # mock_manager_instance.get_album_shelf.side_effect = ShelfNotFoundException()
        unknown_shelf = "a0358a1e25eb978a5a5a8d4fd43864a1"
        mock_config.setting = deepcopy(self.test_configuration)
        mock_config.setting[constants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY] = False
        parser = MagicMock()
        parser.file.metadata.get.return_value = unknown_shelf
        parser.context = MagicMock()
        parser.context.get.return_value = unknown_shelf

        # Act
        result = shelf(parser)

        # Assert
        expected = unknown_shelf
        self.assertEqual(result, expected)

    @patch("shelves.workflow.config")
    def test_func_shelf_returns_stage_2_if_not_in_stage_1_and_and_includes(
        self, mock_config
    ):
        """
        Tests the behavior of the `shelf` function to ensure it returns the stage 2 shelf
        when the shelf is not located in stage 1 and the parameter
        `CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY` is set to `True`.

        :param mock_config: Mocked configuration used to simulate external system settings.
        :type mock_config: unittest.mock.MagicMock
        :return: None
        :rtype: None
        """

        # Arrange
        # mock_manager_instance = MagicMock()
        # mock_manager.return_value = mock_manager_instance
        # mock_manager_instance.get_album_shelf.side_effect = ShelfNotFoundException()
        unknown_shelf = "Possim laboris accusam"
        mock_config.setting = deepcopy(self.test_configuration)
        parser = MagicMock()
        parser.file.metadata.get.return_value = unknown_shelf
        parser.context = MagicMock()
        parser.context.get.return_value = unknown_shelf

        # Act
        for includes in [True, False]:
            mock_config.setting[constants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY] = (
                includes
            )
            with self.subTest(
                msg="stage 1",
                includes_unknown=mock_config.setting[
                    constants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY
                ],
            ):
                result = shelf(parser)

                # Assert
                if not includes:
                    expected = unknown_shelf
                else:
                    expected = mock_config.setting[
                        constants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY
                    ].pop()
                self.assertEqual(result, expected)

    @patch("shelves.workflow.config")
    def test_func_shelf_returns_stage_2_if_in_stage_1_and_not_includes(
        self, mock_config
    ):
        """
        Test case for the `shelf` function to verify behavior when shelves are in
        stage 1 and checks their inclusion in stage 2 shelves.

        This test ensures that if a shelf is part of the current configuration for
        stage 1 but not included in stage 2 shelves, the function correctly returns
        the expected stage 2 shelves.

        :param mock_config: Mocked configuration object for testing.
        :type mock_config: unittest.mock.Mock
        :return: None
        :rtype: None
        """
        mock_config.setting = deepcopy(self.test_configuration)
        known_shelf = mock_config.setting[
            constants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY
        ][0]
        parser = MagicMock()
        parser.file.metadata.get.return_value = known_shelf
        parser.context = MagicMock()
        parser.context.get.return_value = known_shelf

        # Act
        for includes in [True, False]:
            mock_config.setting[constants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY] = (
                includes
            )
            with self.subTest(
                msg="stage 1",
                includes_unknown=mock_config.setting[
                    constants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY
                ],
                known_shelf=known_shelf,
            ):
                result = shelf(parser)

                # Assert
                expected = mock_config.setting[
                    constants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY
                ]
                self.assertEqual([result], expected)


if __name__ == "__main__":
    unittest.main()
