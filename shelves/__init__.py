# -*- coding: utf-8 -*-

"""
Shelves Plugin for MusicBrainz Picard.

This plugin adds virtual shelf management to MusicBrainz Picard,
allowing music files to be organised by top-level folders.
"""
from __future__ import annotations

import threading
from collections import Counter
from collections import namedtuple

from picard import log
from picard.file import (
    register_file_post_load_processor,
    register_file_post_addition_to_track_processor,
    register_file_post_removal_from_track_processor
)
from picard.metadata import register_track_metadata_processor
from picard.script import register_script_function
from picard.ui.itemviews import register_album_action
from picard.ui.options import register_options_page

from .constants import ShelfConstants

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

from .utils import ShelfUtils

LogData = namedtuple('LogData', ['album_id', 'votes', 'winner'])
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

# Minimaler In‑Memory‑State
_STATE: Dict[str, Dict[str, Any]] = defaultdict(dict)
_VOTES: Dict[str, List[Tuple[str, float, str]]] = defaultdict(list)


class ShelfManager:
    """
    Thread-safe manager for shelves:
    - Manual overrides (`shelf_source='manual'`, `shelf_locked=True`) have priority.
    - Automatic/workflow only writes if no manual lock is active.
    - Votes are evaluated weightedly.
    """

    def __init__(self) -> None:
        self._shelves_by_album: Dict[str, str] = {}
        self._shelf_votes: Dict[str, Counter] = {}
        self._lock = threading.Lock()

    def vote_for_shelf(self, album_id: str, shelf: str, weight: float, reason: str) -> None:
        if not shelf or not shelf.strip():
            return

        log_data = None
        with self._lock:
            # Weighted counting (counter can only use ints, therefore additionally _VOTES for weights)
            if album_id not in self._shelf_votes:
                self._shelf_votes[album_id] = Counter()
            # For a quick "majority" view, we increase the count by 1
            self._shelf_votes[album_id][shelf] += 1
            winner = self._shelf_votes[album_id].most_common(1)[0][0]
            if len(self._shelf_votes[album_id]) > 1:
                all_votes = self._shelf_votes[album_id].most_common()
                log_data = (album_id, dict(all_votes), winner)
            self._shelves_by_album[album_id] = winner

        # Weighted for the real decision
        _VOTES.setdefault(album_id, []).append((shelf, float(weight), str(reason or "")))

        if log_data:
            log.warning(
                "%s: Album %s hat Dateien aus unterschiedlichen Shelves. Votes: %s. Nutze: '%s'",
                PLUGIN_NAME, log_data[0], log_data[1], log_data[2]
            )

    @staticmethod
    def _winner(votes: List[Tuple[str, float, str]]) -> Optional[str]:
        if not votes:
            return None
        agg: Dict[str, float] = {}
        for shelf, weight, _ in votes:
            agg[shelf] = agg.get(shelf, 0.0) + float(weight)
        return max(agg.items(), key=lambda kv: kv[1])[0]

    def set_album_shelf(self, album_id: str, shelf: str, *, source: str = ShelfConstants.SHELF_SOURCE_MANUAL,
                        lock: Optional[bool] = None) -> \
            Optional[str]:
        st = _STATE.setdefault(album_id, {})
        if lock is None:
            lock = (source == ShelfConstants.SHELF_SOURCE_MANUAL)

        # Manually locked => can only be overwritten manually
        if st.get("shelf_locked") and source != ShelfConstants.SHELF_SOURCE_MANUAL:
            return st.get("shelf")

        st["shelf"] = shelf
        st["shelf_source"] = source
        st["shelf_locked"] = bool(lock)

        if source == ShelfConstants.SHELF_SOURCE_MANUAL:
            # Register dominant decision (∞ weight)
            self.vote_for_shelf(album_id, shelf, weight=float("inf"), reason="manual override")

        return shelf

    @staticmethod
    def clear_manual_override(album_id: str) -> None:
        st = _STATE.setdefault(album_id, {})
        st["shelf_locked"] = False
        if st.get("shelf_source") == ShelfConstants.SHELF_SOURCE_MANUAL:
            st["shelf_source"] = ShelfConstants.SHELF_SOURCE_VOTES

    @staticmethod
    def _get_manual_override(album_id: str) -> Optional[str]:
        st = _STATE.get(album_id, {})
        if st.get("shelf_locked") or st.get("shelf_source") == ShelfConstants.SHELF_SOURCE_MANUAL:
            return st.get("shelf")
        return None

    def get_album_shelf(self, album_id: str) -> tuple[Optional[str], str]:
        """
        Read with priority:
        1. Manual lock or `shelf_source=='manual'` => return the current value.
        2. Otherwise, weighted winner from `_VOTES`.
        3. Fallback to the last observed winner (`_shelves_by_album`).
        """
        # 1. Manual lock
        manual_shelf = self._get_manual_override(album_id)
        if manual_shelf:
            return manual_shelf, ShelfConstants.SHELF_SOURCE_MANUAL

        # 2. Weighted decision
        chosen = self._winner(_VOTES.get(album_id, []))
        if chosen:
            return chosen, ShelfConstants.SHELF_SOURCE_VOTES

        # 3. Fallback: simple majority winner from counter
        with self._lock:
            shelf_name = self._shelves_by_album.get(album_id)
            if shelf_name is None:
                log.warning("%s: Shelf for album %s could not be determined with certainty.", PLUGIN_NAME, album_id)
            return shelf_name, ShelfConstants.SHELF_SOURCE_FALLBACK

    def clear_album(self, album_id: str) -> None:
        with self._lock:
            self._shelves_by_album.pop(album_id, None)
            self._shelf_votes.pop(album_id, None)
        _STATE.pop(album_id, None)
        _VOTES.pop(album_id, None)


# Global instance - initialized once at module import
_shelf_manager = ShelfManager()


# Wrapper
def vote_for_shelf(album_id: str, shelf: str, weight: float = 1.0, reason: str = "") -> None:
    _shelf_manager.vote_for_shelf(album_id, shelf, weight, reason)


def get_album_shelf(album_id: str) -> tuple[Optional[str], str]:
    return _shelf_manager.get_album_shelf(album_id)


def clear_album(album_id: str) -> None:
    _shelf_manager.clear_album(album_id)


from .actions import SetShelfAction as _SetShelfActionBase, DetermineShelfAction as _DetermineShelfActionBase
from .options import ShelvesOptionsPage as _ShelvesOptionsPageBase
from .processors import (
    file_post_load_processor,
    file_post_save_processor,
    file_post_addition_to_track_processor,
    file_post_removal_from_track_processor,
    set_shelf_in_metadata
)
from .script_functions import func_shelf as _func_shelf_base


class ShelvesOptionsPage(_ShelvesOptionsPageBase):
    """Wrapper class for the ShelvesOptionsPage to ensure proper plugin registration."""

    def __init__(self, parent=None) -> None:
        """Initialize with the global shelf_manager instance."""
        super().__init__(parent)


class SetShelfAction(_SetShelfActionBase):
    """Wrapper class for SetShelfAction to ensure proper plugin registration."""

    def __init__(self) -> None:
        """Initialize with the global shelf_manager instance."""
        super().__init__()


class DetermineShelfAction(_DetermineShelfActionBase):
    """Wrapper class for DetermineShelfAction to ensure proper plugin registration."""

    def __init__(self) -> None:
        """Initialize with the global shelf_manager instance."""
        super().__init__()


# Wrapper for script function
def func_shelf(parser: Any) -> Optional[str]:
    """Wrapper for func_shelf to ensure proper plugin registration."""
    return _func_shelf_base(parser)


# Wrapper functions that pass shelf_manager to processors
def _file_post_load_processor_wrapper(file: Any) -> None:
    """Wrapper for file_post_load_processor."""
    file_post_load_processor(file)


def _file_post_addition_to_track_processor(track: Any, file: Any) -> None:
    """Wrapper for file_post_addition_to_track_processor."""
    file_post_addition_to_track_processor(track, file)


def _file_post_save_processor_wrapper(file: Any) -> None:
    """Wrapper for file_post_save_processor."""
    file_post_save_processor(file)


def _set_shelf_in_metadata_wrapper(
        album: Any, metadata: Dict[str, Any], track: Any, release: Any
) -> None:
    """Wrapper for set_shelf_in_metadata."""
    set_shelf_in_metadata(album, metadata, track, release)


def _file_post_removal_from_track_processor(track: Any, file: Any) -> None:
    """Wrapper for file_post_removal_from_track_processor."""
    file_post_removal_from_track_processor(track, file)


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
register_script_function(function=func_shelf, name="shelf")
