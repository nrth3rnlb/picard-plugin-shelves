from picard import config, log

from . import constants


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
    def apply_transition(shelf_name: str) -> str:
        """
        Applies the workflow transition to a shelf name if the workflow is enabled.

        :param shelf_name: The current shelf name.
        :type shelf_name: str
        :return: The updated shelf name after workflow transition, or None if workflow is disabled.
        :rtype: str
        """
        if not shelf_name:
            return shelf_name

        # noinspection PyTypeHints
        if not config.setting[constants.CONFIG_WORKFLOW_ENABLED_KEY]:
            return shelf_name

        # noinspection PyTypeHints
        stage_1_includes_unknown = config.setting[
            constants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY
        ]
        # noinspection PyTypeHints
        workflow_known_shelves = config.setting[constants.CONFIG_KNOWN_SHELVES_KEY]
        # noinspection PyTypeHints
        workflow_stage_1 = config.setting[constants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY]
        # noinspection PyTypeHints
        workflow_stage_2 = config.setting[constants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY]

        if not workflow_stage_2:
            return shelf_name

        # Determine if the shelf name should be transitioned
        is_unknown_shelf = shelf_name not in workflow_known_shelves
        is_stage_1_shelf = shelf_name in workflow_stage_1

        # Either the shelf name is a stage 1 name
        # or it is unknown and stage 1 should also include unknown shelf names
        to_apply = is_stage_1_shelf or is_unknown_shelf and stage_1_includes_unknown
        if not to_apply:
            return shelf_name

        # Avoid transitioning to the same shelf name
        destination_shelf = workflow_stage_2[0]
        if shelf_name == destination_shelf:
            return shelf_name

        log.debug("%s -> %s", shelf_name, destination_shelf)
        return destination_shelf
