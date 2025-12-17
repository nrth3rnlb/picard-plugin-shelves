# -*- coding: utf-8 -*-

"""
Script functions for the Shelves plugin.
"""

from __future__ import annotations

from typing import Any

from .constants import ShelfConstants
from .utils import ShelfUtils


def func_shelf(parser: Any) -> str:
    """
    Picard script function: `$shelf()`
    Returns the clean shelf name from the file's metadata, removing any internal suffixes.
    """
    shelf_tag = parser.context[ShelfConstants.TAG_KEY]
    if not isinstance(shelf_tag, str):
        return ""

    shelf_name = ShelfUtils.get_shelf_name_from_tag(shelf_tag)
    if not shelf_name:
        return ""
    return shelf_name
