"""
Script functions for the Shelves plugin.
"""

from __future__ import annotations

from picard.script import ScriptParser

from . import utils


def shelf(parser: ScriptParser) -> str:
    """Picard script function: `$shelf()`"""
    context_shelf, metadata_shelf = utils.squeeze_the_parser(parser)
    if not metadata_shelf and not context_shelf:
        return ""

    return metadata_shelf or context_shelf
