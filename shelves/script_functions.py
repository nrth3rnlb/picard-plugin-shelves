"""
Script functions for the Shelves plugin.
"""

from gettext import gettext as _

from picard.script import script_function

from .typings import TagKey


@script_function(
    documentation=_(
        """`$shelf()`

Returns the album-level shelf name."""
    ),
)
def func_shelf(parser) -> str:
    # utils._debug_parser(parser)
    return parser.context.get(TagKey.SHELF, "")
