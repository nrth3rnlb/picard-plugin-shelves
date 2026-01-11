import traceback

from constants import ShelfConstants
from picard import config, log


class WorkflowEngine:
    """
    Manages workflow transitions for shelf names.

    This class provides functionality to apply workflow transitions to shelf names
    based on configuration settings. The workflow determines the transition rules
    and destination shelves based on predefined stages and conditions.

    The class ensures that transitions only occur when the workflow is enabled,
    and specific configuration keys are present and valid.

    :ivar CONFIG_WORKFLOW_ENABLED_KEY: Key to check if workflow is enabled.
    :type CONFIG_WORKFLOW_ENABLED_KEY: str
    :ivar CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: Key for the first stage shelves in the workflow.
    :type CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: str
    :ivar CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: Key for the second stage shelves in the workflow.
    :type CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: str
    :ivar CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: Key indicating whether non-shelf items are part of stage 1.
    :type CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY: str
    """

    @staticmethod
    def apply_workflow_transition(shelf_name: str) -> str:
        """
        Applies the workflow transition to a shelf name if the workflow is enabled.

        :param shelf_name: The current shelf name.
        :type shelf_name: str
        :return: The updated shelf name after workflow transition, or None if workflow is disabled.
        :rtype: str
        """
        if not shelf_name:
            return shelf_name

        try:
            # noinspection PyTypeHints
            if not config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY]:
                return shelf_name
            # noinspection PyTypeHints
            workflow_stage_1 = config.setting[
                ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY
            ]
            # noinspection PyTypeHints
            workflow_stage_2 = config.setting[
                ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY
            ]
            # noinspection PyTypeHints
            stage_1_includes_non_shelves = config.setting[
                ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY
            ]

            # Check for known shelf name wildcard or direct match
            apply_transition = (
                shelf_name in workflow_stage_1 or stage_1_includes_non_shelves
            )

            if apply_transition and workflow_stage_2:
                destination_shelf = workflow_stage_2[0]
                # Avoid transitioning to the same shelf name
                if shelf_name != destination_shelf:
                    log.debug(
                        "Applying workflow transition: '%s' -> '%s'",
                        shelf_name,
                        destination_shelf,
                    )
                    return destination_shelf
        except KeyError as e:
            log.debug(
                "Workflow configuration key not found (%s), skipping transition.",
                e,
            )
        except (AttributeError, ValueError) as e:
            log.debug("Failed to evaluate workflow transition: %s", e)
            log.debug("Traceback: %s", traceback.format_exc())

        return shelf_name
