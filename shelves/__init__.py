# -*- coding: utf-8 -*-

"""
Shelves Plugin for MusicBrainz Picard.

This plugin adds virtual shelf management to MusicBrainz Picard,
allowing music files to be organized by top-level folders.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from picard.file import (
    register_file_post_load_processor,
    register_file_post_addition_to_track_processor,
    register_file_post_removal_from_track_processor,
)
from picard.metadata import register_track_metadata_processor
from picard.script import register_script_function
from picard.ui.itemviews import register_album_action
from picard.ui.options import register_options_page

from .actions import (
    SetShelfAction as _SetShelfActionBase,
    DetermineShelfAction as _DetermineShelfActionBase,
    ResetShelfAction as _ResetShelfActionBase,
)
from .processors import ShelfProcessors
from .script_functions import func_shelf as _func_shelf_base
from .ui.options import OptionsPage as _ShelvesOptionsPageBase

# Plugin metadata
PLUGIN_NAME = "Shelves"
PLUGIN_AUTHOR = "nrth3rnlb"
PLUGIN_DESCRIPTION = """
The **Shelves** plugin adds virtual shelf management to MusicBrainz Picard, allowing you to organise your music files by top-level folders (shelves) in your music library.

Think of your music library as a physical library with different shelves — one for your standard collection, one for incoming/unprocessed music, one for Christmas music, etc.

## Features

- **Automatic shelf detection** from file paths during scanning
- **Smart detection** prevents artist/album names from being mistaken as shelves
- **Manual shelf assignment** via context menu
- **Shelf management** in plugin settings (add, remove, scan directory)
- **Workflow automation** automatically moves files between shelves (e.g. "Incoming" > "Standard")
- **Script function `$shelf()`** for file naming integration
- **Visual script preview** in settings shows your file naming snippet
"""
PLUGIN_VERSION = "1.6.1"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"


class ShelvesOptionsPage(_ShelvesOptionsPageBase):
    """Wrapper class for the OptionsPage to ensure proper plugin registration."""

    # def __init__(self, parent=None) -> None:
    #     """Initialize with the global shelf_manager instance."""
    #     # super().__init__(parent)


class SetShelfAction(_SetShelfActionBase):
    """Wrapper class for SetShelfAction to ensure proper plugin registration."""

    # def __init__(self) -> None:
    #     """Initialize with the global shelf_manager instance."""
    #     super().__init__()


class DetermineShelfAction(_DetermineShelfActionBase):
    """Wrapper class for DetermineShelfAction to ensure proper plugin registration."""

    # def __init__(self) -> None:
    #     """Initialize with the global shelf_manager instance."""
    #     super().__init__()


class ResetShelfAction(_ResetShelfActionBase):
    """Wrapper class for ResetShelfAction to ensure proper plugin registration."""

    # def __init__(self) -> None:
    #     """Initialize with the global shelf_manager instance."""
    #     super().__init__()


shelf_processors = ShelfProcessors()

# Wrapper for script function
def func_shelf(parser: Any) -> Optional[str]:
    """Wrapper for func_shelf to ensure proper plugin registration."""
    return _func_shelf_base(parser)


# Wrapper functions that pass shelf_manager to processors
def _file_post_load_processor_wrapper(file: Any) -> None:
    """Wrapper for file_post_load_processor."""
    shelf_processors.file_post_load_processor(file=file)


def _file_post_addition_to_track_processor(track: Any, file: Any) -> None:
    """Wrapper for file_post_addition_to_track_processor."""
    shelf_processors.file_post_addition_to_track_processor(track=track, file=file)


# def _file_post_save_processor_wrapper(file: Any) -> None:
#     """Wrapper for file_post_save_processor."""
#     file_post_save_processor(file)


def _set_shelf_in_metadata_wrapper(
    album: Any, metadata: Dict[str, Any], track: Any, release: Any
) -> None:
    """Wrapper for set_shelf_in_metadata."""
    shelf_processors.set_shelf_in_metadata(album, metadata, track, release)


def _file_post_removal_from_track_processor(track: Any, file: Any) -> None:
    """Wrapper for file_post_removal_from_track_processor."""
    shelf_processors.file_post_removal_from_track_processor(track=track, file=file)


# Register metadata processors
register_track_metadata_processor(_set_shelf_in_metadata_wrapper)

# Register file processors
register_file_post_load_processor(_file_post_load_processor_wrapper)
register_file_post_addition_to_track_processor(_file_post_addition_to_track_processor)
register_file_post_removal_from_track_processor(_file_post_removal_from_track_processor)

# Register context menu actions
register_album_action(SetShelfAction())
register_album_action(DetermineShelfAction())
register_album_action(ResetShelfAction())

# Register options options_page
register_options_page(ShelvesOptionsPage)

# Register a script function for use in file naming
register_script_function(function=func_shelf, name="shelf")
