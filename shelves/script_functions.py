"""
Script functions for the Shelves plugin.
"""

from __future__ import annotations

from typing import Any, Optional

from picard import log
from picard.script import ScriptParser

from . import constants
from .exceptions import ShelfNotFoundException
from .manager import ShelfManager
from .workflow import WorkflowEngine


def shelf(parser: ScriptParser) -> str:
    """
    Picard script function: `$shelf()`
    """
    _shelf_debug(parser)
    metadata_shelf: str = ""
    context_shelf: str = ""
    if hasattr(parser.file, "metadata"):
        metadata_shelf = parser.file.metadata.get(constants.TAG_KEY)
        log.debug("metadata_shelf = %s", metadata_shelf)
    if hasattr(parser, "context"):
        context_shelf = parser.context.get(constants.TAG_KEY)
        log.debug("context_shelf = %s", context_shelf)

    if not metadata_shelf and not context_shelf:
        log.error("No shelf found in file metadata or context %s.", parser.file)
        return WorkflowEngine.apply_transition("")
    else:
        return WorkflowEngine.apply_transition(metadata_shelf or context_shelf)


def _shelf_debug(parser: ScriptParser) -> str:
    """
    Debugs the internal state of a `ScriptParser` object and retrieves relevant
    information about its attributes and context. Outputs debug logs about the
    state and structure of the passed `parser` object.

    :param parser: The `ScriptParser` object to debug.
    :type parser: ScriptParser
    :return: A debug status message.
    :rtype: str
    """
    log.debug("=" * 60)
    log.debug("PARSER DEBUG START")

    # What is parser.file?
    log.debug("parser.file = %s", parser.file)
    log.debug("parser.file type = %s", type(parser.file))

    # Does it have .metadata?
    if hasattr(parser.file, "metadata"):
        log.debug("✓ parser.file HAS metadata")
        log.debug("  Album ID: %s", list(parser.file.metadata.keys()))

    # What is parser.context?
    if hasattr(parser, "context"):
        log.debug("✓ parser HAS context")
        log.debug("  Keys: %s", list(parser.context.keys()))

    log.debug("PARSER DEBUG END")
    log.debug("=" * 60)
    return "DEBUG"
