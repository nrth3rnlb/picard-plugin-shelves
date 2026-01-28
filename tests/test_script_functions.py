import unittest
from copy import deepcopy
from unittest.mock import MagicMock, patch

from typings import ConfigKey

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
            ConfigKey.MOVE_FILES_TO: "/home/foobar/music",
            ConfigKey.WORKFLOW_ENABLED: True,
            ConfigKey.STAGE_1_INCLUDES_NON_SHELVES: False,
            ConfigKey.WORKFLOW_STAGE_1_SHELVES: ["Incoming"],
            ConfigKey.WORKFLOW_STAGE_2_SHELVES: ["Standard"],
            ConfigKey.KNOWN_SHELVES: ["Incoming", "Standard", "Stash", "Live"],
        }

    # @patch("shelves.workflow.config")
    # def test_func_shelf_returns_stage_2_if_not_in_stage_1_and_and_includes(
    #         self, mock_config,
    # ):
    #     """
    #     This function tests the behavior of the `shelf` function under different configurations
    #     relating to stage inclusions. Specifically, it examines how the function behaves when
    #     a shelf is not in stage 1 and the configuration includes or excludes unknown shelves
    #     for stage 1 processing. The test ensures the correct shelf is returned in all cases.
    #
    #     :param mock_config: Mock object providing configuration settings used within the test.
    #     :type mock_config: MagicMock
    #     """
    #
    #     # Arrange
    #     # mock_manager_instance = MagicMock()
    #     # mock_manager.return_value = mock_manager_instance
    #     # mock_manager_instance.resolve_shelf_name.side_effect = ShelfNotFoundException()
    #     unknown_shelf = "Possim laboris accusam"
    #     mock_config.setting = deepcopy(self.test_configuration)
    #     parser = MagicMock()
    #     parser.file.metadata.get.return_value = unknown_shelf
    #     parser.context = MagicMock()
    #     parser.context.get.return_value = unknown_shelf
    #
    #     # Act
    #     for includes in [True, False]:
    #         mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = (
    #             includes
    #         )
    #         with self.subTest(
    #                 msg=ConfigKey.WORKFLOW_STAGE_1_SHELVES,
    #                 includes_unknown=mock_config.setting[
    #                     ConfigKey.STAGE_1_INCLUDES_NON_SHELVES
    #                 ],
    #         ):
    #             result = shelf(parser)
    #
    #             # Assert
    #             if not includes:
    #                 expected = unknown_shelf
    #             else:
    #                 expected = mock_config.setting[
    #                     ConfigKey.WORKFLOW_STAGE_2_SHELVES
    #                 ].pop()
    #             self.assertEqual(expected, result)

    @patch("shelves.workflow.config")
    def test_func_shelf(
        self,
        mock_config,
    ):
        """ """
        # Arrange
        mock_config.setting = deepcopy(self.test_configuration)

        known_shelves: set[str] = set(
            deepcopy(self.test_configuration[ConfigKey.KNOWN_SHELVES]),
        )

        # Stage 2 entfernen
        known_shelves = known_shelves.difference(
            set(self.test_configuration[ConfigKey.WORKFLOW_STAGE_2_SHELVES]),
        )

        # Einen Shelf Namen für Stage 1 auswählen
        mock_config.setting[ConfigKey.WORKFLOW_STAGE_1_SHELVES] = [known_shelves.pop()]

        # Einen Shelf Namen entnehmen, der bekannt ist und in keinem Stage verwendet wird.
        known_shelf = known_shelves.pop()

        parser = MagicMock()
        parser.file.metadata.get.return_value = known_shelf
        parser.context = MagicMock()
        parser.context.get.return_value = known_shelf

        # Act
        # No matter how CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY is set, the shelf name must not be changed.
        for includes in [True, False]:
            mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = includes
            with self.subTest(
                msg=ConfigKey.WORKFLOW_STAGE_1_SHELVES,
                includes_unknown=mock_config.setting[
                    ConfigKey.STAGE_1_INCLUDES_NON_SHELVES
                ],
            ):
                result = shelf(parser)

                # Assert
                invalid = deepcopy(
                    mock_config.setting[ConfigKey.WORKFLOW_STAGE_2_SHELVES]
                ).pop()
                expected = known_shelf
                self.assertNotEqual(
                    invalid, result, f"Did not expect '{invalid}' but got it."
                )
                self.assertEqual(
                    expected, result, f"Expected '{expected}' but got '{result}'"
                )

    # @patch("shelves.workflow.config")
    # def test_func_shelf_returns_stage_2_if_in_stage_1_and_not_includes(
    #         self, mock_config,
    # ):
    #     """
    #     Test case to validate the behavior of the `shelf` function when the input is in
    #     stage 1 of the workflow and conditionally includes non-shelves components.
    #
    #     This test ensures that the function returns a result from stage 2 shelves
    #     if the input is in stage 1, properly handling the scenario where the stage 1
    #     configuration includes or excludes non-shelf components.
    #
    #     :param mock_config: A mock object that intercepts and simulates the
    #         configuration used during the workflow process.
    #     :type mock_config: MagicMock
    #     :return: Validates if expected results from stage 2 shelves are returned for
    #         specific scenarios. No direct return value.
    #     :rtype: None
    #     """
    #     mock_config.setting = deepcopy(self.test_configuration)
    #     stage_1_shelf_name = mock_config.setting[
    #         ConfigKey.WORKFLOW_STAGE_1_SHELVES
    #     ][0]
    #     parser = MagicMock()
    #     parser.file.metadata.get.return_value = stage_1_shelf_name
    #     parser.context = MagicMock()
    #     parser.context.get.return_value = stage_1_shelf_name
    #
    #     # Act
    #     # No matter how CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY is set, the shelf name must be changed.
    #     for includes in [True, False]:
    #         mock_config.setting[ConfigKey.STAGE_1_INCLUDES_NON_SHELVES] = (
    #             includes
    #         )
    #         with self.subTest(
    #                 msg=ConfigKey.WORKFLOW_STAGE_1_SHELVES,
    #                 stage_1_shelf_name=stage_1_shelf_name,
    #                 includes_unknown=mock_config.setting[
    #                     ConfigKey.STAGE_1_INCLUDES_NON_SHELVES
    #                 ],
    #         ):
    #             result = shelf(parser)
    #
    #             # Assert
    #             expected = mock_config.setting[
    #                 ConfigKey.WORKFLOW_STAGE_2_SHELVES
    #             ]
    #             self.assertEqual(
    #                     expected, [result], f"Expected {expected} but got {result}",
    #             )


if __name__ == "__main__":
    unittest.main()
