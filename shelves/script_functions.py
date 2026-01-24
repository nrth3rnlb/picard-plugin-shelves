"""
Script functions for the Shelves plugin.
"""

from __future__ import annotations

from picard import log
from picard.script import ScriptParser

from . import utils
from .workflow import WorkflowEngine


def shelf(parser: ScriptParser) -> str:
    """
    Picard script function: `$shelf()`
    """
    context_shelf, metadata_shelf = utils.squeeze_the_parser(parser)

    if not metadata_shelf and not context_shelf:
        log.error("No shelf found in file metadata or context %s.", parser.file)
        return WorkflowEngine.apply_transition("")
    else:
        return WorkflowEngine.apply_transition(metadata_shelf or context_shelf)
