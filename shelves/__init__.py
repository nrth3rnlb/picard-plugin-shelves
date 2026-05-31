"""
Shelves Plugin for MusicBrainz Picard.

This plugin adds virtual shelf_name management to MusicBrainz Picard,
allowing music files to be organized by top-level folders.

Shelf assignment is album-scoped. Individual tracks/files do not own
independent shelf assignments; they only provide hints for detecting
or updating the album-level shelf.
"""

from typing import Any, Optional

from picard import log
from picard.file import (
    register_file_post_addition_to_track_processor,
    register_file_post_load_processor,
    register_file_post_removal_from_track_processor,
    register_file_post_save_processor,
)
from picard.metadata import register_track_metadata_processor
from picard.script import register_script_function
from picard.ui.itemviews import register_album_action
from picard.ui.options import register_options_page

from . import runtime
from .actions import (
    ShelfActionToggleLock as _ShelfActionToggleLock,
)
from .actions import (
    ShelfActionSet as _ShelfActionSet,
)
from .actions import (
    ShelfActionUnset as _ShelfActionUnset,
)
from .options.page import OptionsPage as _ShelvesOptionsPageBase
from .script_functions import func_shelf as _shelf

# Plugin metadata
# noinspection PyUnusedName
PLUGIN_NAME = "Shelves"
# noinspection PyUnusedName
PLUGIN_AUTHOR = "nrthэrnlb"
# noinspection PyUnusedName
PLUGIN_DESCRIPTION = """
The **Shelves** plugin adds virtual shelf management to MusicBrainz Picard, allowing you to
organise your music files by top-level folders (shelves) in your music library.

Think of your music library as a physical library with different shelves — one for your standard
collection, one for incoming/unprocessed music, one for Christmas music, etc.

## Features

- **Automatic shelf name detection** from file paths during scanning
- **Smart detection** prevents artist/album names from being mistaken as shelves
- **Manual shelf name assignment** via context menu
- **Workflow automation** automatically moves files between shelves (e.g. "Incoming" > "Standard")
- **Script function `$shelf()`** for file naming integration

Shelf assignment is album-scoped. Individual tracks/files do not own independent shelf assignments;
they only provide hints for detecting or updating the album-level shelf.
"""
# noinspection PyUnusedName
PLUGIN_VERSION = "2.1.1b1"
# noinspection PyUnusedName
PLUGIN_API_VERSIONS = ["2.0"]
# noinspection PyUnusedName
PLUGIN_LICENSE = "GPL-2.0-or-later"
# noinspection PyUnusedName
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"


class ShelvesOptionsPage(_ShelvesOptionsPageBase):
    """Wrapper class for the OptionsPage to ensure proper plugin registration."""


class ShelfActionSet(_ShelfActionSet):
    """Wrapper class for ShelfActionSet to ensure proper plugin registration."""


class ShelfActionUnset(_ShelfActionUnset):
    """Wrapper class for ShelfActionUnset to ensure proper plugin registration."""


class ShelfActionToggleLock(_ShelfActionToggleLock):
    """Wrapper class for ShelfActionToggleLock to ensure proper plugin registration."""


# Wrapper for script function
def script_function_shelf(parser: Any) -> Optional[str]:
    """Wrapper for shelf to ensure proper plugin registration."""
    return _shelf(parser)


def _track_metadata_processor(
    album: Any,
    metadata: dict[str, Any],
    track: Any,
    release: Any,
) -> None:
    """Wrapper for track_metadata_processor."""
    runtime.processor_instance().track_metadata_processor(
        _album=album, metadata=metadata, _track=track, _release=release
    )


# Wrapper functions that pass shelf_manager to processors
def _file_post_save_processor(file: Any) -> None:
    """Wrapper for file_post_save_processor."""
    runtime.processor_instance().file_post_save_processor(file=file)


# Wrapper functions that pass shelf_manager to processors
def _file_post_load_processor(file: Any) -> None:
    """Wrapper for file_post_load_processor."""
    log.debug("_file_post_load_processor")
    runtime.processor_instance().file_post_load_processor(file=file)


def _file_post_addition_to_track_processor(track: Any, file: Any) -> None:
    """Wrapper for file_post_addition_to_track_processor."""
    log.debug("_file_post_addition_to_track_processor")
    runtime.processor_instance().file_post_addition_to_track_processor(
        track=track, file=file
    )


def _file_post_removal_from_track_processor(track: Any, file: Any) -> None:
    """Wrapper for file_post_removal_from_track_processor."""
    runtime.processor_instance().file_post_removal_from_track_processor(
        track=track, file=file
    )


# Register metadata processors
register_track_metadata_processor(_track_metadata_processor)

# Register file processors
register_file_post_load_processor(_file_post_load_processor)
register_file_post_save_processor(_file_post_save_processor)
register_file_post_addition_to_track_processor(_file_post_addition_to_track_processor)
register_file_post_removal_from_track_processor(_file_post_removal_from_track_processor)

# Register context menu actions
register_album_action(ShelfActionSet())
register_album_action(ShelfActionUnset())
register_album_action(ShelfActionToggleLock())

# Register options page
register_options_page(ShelvesOptionsPage)

# Register script functions
register_script_function(function=script_function_shelf, name="shelf")
