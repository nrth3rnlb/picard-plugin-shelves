# -*- coding: utf-8 -*-

"""
Script functions for the Shelves plugin.
"""

from __future__ import annotations

from typing import Any

from picard import config, log

from .constants import ShelfConstants

PLUGIN_NAME = "Shelves"


def _resolve_shelf_from_context(ctx: Any) -> str:
    """
    Runtime resolver:
    - If context indicates a manual override, return it as-is.
    - Else, apply workflow transition if enabled.
    """
    # Base shelf from context (fallback)
    shelf = ctx.get("shelf", "")

    # Prefer manual override if present
    shelf_source = ctx.get("shelf_source", "")
    shelf_locked = bool(ctx.get("shelf_locked", False))
    if shelf_locked or shelf_source == "manual":
        return shelf

    # Workflow enabled?
    try:
        is_workflow = config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY]  # type: ignore[index]
    except KeyError:
        return shelf

    if not is_workflow:
        return shelf

    # Workflow stages
    try:
        workflow_stage_1 = config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY]  # type: ignore[index]
        workflow_stage_2 = config.setting[ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY]  # type: ignore[index]
    except KeyError:
        return shelf

    # Apply transition only if not manually overridden
    if shelf == workflow_stage_1 or workflow_stage_1 == ShelfConstants.WORKFLOW_STAGE_1_WILDCARD:
        log.debug(
            "%s: Applying workflow transition: '%s' -> '%s'",
            PLUGIN_NAME,
            workflow_stage_1,
            workflow_stage_2,
        )
        return workflow_stage_2

    return shelf


def func_shelf(parser: Any) -> str:
    """
    Picard script function: `$shelf()`
    Returns the shelf name, prioritizing manual overrides and otherwise applying workflow transition.
    """
    return _resolve_shelf_from_context(parser.context)
