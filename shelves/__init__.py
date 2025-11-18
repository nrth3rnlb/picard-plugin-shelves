# -*- coding: utf-8 -*-

"""
Shelves Plugin for MusicBrainz Picard.

This plugin adds virtual shelf management to MusicBrainz Picard,
allowing music files to be organised by top-level folders.
"""
from __future__ import annotations

from typing import Any, Dict

from picard import log
from picard.file import register_file_post_load_processor, \
    register_file_post_addition_to_track_processor, register_file_post_removal_from_track_processor
from picard.metadata import register_track_metadata_processor
from picard.script import register_script_function
from picard.ui.itemviews import register_album_action
from picard.ui.options import register_options_page

from .actions import SetShelfAction as _SetShelfActionBase, DetermineShelfAction as _DetermineShelfActionBase
from .context import ShelfContext
from .manager import ShelfManager
from .options import ShelvesOptionsPage as _ShelvesOptionsPageBase
from .processors import (
    file_post_load_processor,
    file_post_save_processor,
    file_post_addition_to_track_processor,
    file_post_removal_from_track_processor,
    set_shelf_in_metadata
)
from .script_functions import func_shelf as _func_shelf_base
from .utils import ShelfValidators, ShelfUtils

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
PLUGIN_VERSION = "1.4.1"
PLUGIN_API_VERSIONS = ["2.7", "2.8"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"
PLUGIN_USER_GUIDE_URL = "https://github.com/nrth3rnlb/picard-plugin-shelves"

def _build_shelf_manager(plugin_name: str) -> ShelfManager:
    shelf_validators = ShelfValidators()
    shelf_utils = ShelfUtils()
    shelf_manager = ShelfManager(plugin_name=plugin_name, validators=shelf_validators, utils=shelf_utils)
    shelf_utils.set_shelf_manager(manager=shelf_manager)
    return shelf_manager

# Global shelf manager instance
shelf_manager_global = _build_shelf_manager(plugin_name=PLUGIN_NAME)

class ShelvesOptionsPage(_ShelvesOptionsPageBase):
    """Wrapper class for the ShelvesOptionsPage to ensure proper plugin registration."""

    def __init__(self, parent=None) -> None:
        """Initialize with the global shelf_manager instance."""
        super().__init__(parent)
        self.set_shelf_manager(shelf_manager_global)

class SetShelfAction(_SetShelfActionBase):
    """Wrapper class for SetShelfAction to ensure proper plugin registration."""

    def __init__(self) -> None:
        """Initialize with the global shelf_manager instance."""
        super().__init__(shelf_manager=shelf_manager_global)

class DetermineShelfAction(_DetermineShelfActionBase):
    """Wrapper class for DetermineShelfAction to ensure proper plugin registration."""

    def __init__(self) -> None:
        """Initialize with the global shelf_manager instance."""
        super().__init__(shelf_manager=shelf_manager_global)

# Wrapper for script function
def func_shelf(parser: Any) -> str:
    """Wrapper for func_shelf to ensure proper plugin registration."""
    return _func_shelf_base(parser)


# Wrapper functions that pass shelf_manager to processors
def _file_post_load_processor_wrapper(file: Any) -> None:
    """Wrapper for file_post_load_processor."""
    file_post_load_processor(file, shelf_manager_global)

def _file_post_addition_to_track_processor(track, file: Any) -> None:
    """Wrapper for file_post_addition_to_track_processor."""
    file_post_addition_to_track_processor(track, file, shelf_manager_global)


def _file_post_save_processor_wrapper(file: Any) -> None:
    """Wrapper for file_post_save_processor."""
    file_post_save_processor(file, shelf_manager_global)


def _set_shelf_in_metadata_wrapper(
        album: Any, metadata: Dict[str, Any], track: Any, release: Any
) -> None:
    """Wrapper for set_shelf_in_metadata."""
    set_shelf_in_metadata(album, metadata, track, release, shelf_manager_global)

def _file_post_removal_from_track_processor(track, file: Any) -> None:
    """Wrapper for file_post_removal_from_track_processor."""
    file_post_removal_from_track_processor(track, file, shelf_manager_global)


log.debug("%s: Registering plugin components", PLUGIN_NAME)

# Register metadata processors
register_track_metadata_processor(_set_shelf_in_metadata_wrapper)

# Register file processors
register_file_post_load_processor(_file_post_load_processor_wrapper)
register_file_post_addition_to_track_processor(_file_post_addition_to_track_processor)
register_file_post_removal_from_track_processor(_file_post_removal_from_track_processor)

# Register context menu actions
register_album_action(SetShelfAction())
register_album_action(DetermineShelfAction())

# Register options page
register_options_page(ShelvesOptionsPage)

# Register a script function for use in file naming
register_script_function(func_shelf, "shelf")