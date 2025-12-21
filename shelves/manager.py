# -*- coding: utf-8 -*-

"""
Shelf manager for tracking album shelf assignments.
"""

from __future__ import annotations

import threading
from collections import Counter, namedtuple
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any

from picard import log

from .constants import ShelfConstants

LogData = namedtuple("LogData", ["album_id", "votes", "winner"])

# Minimaler In‑Memory‑State
_STATE: Dict[str, Dict[str, Any]] = defaultdict(dict)
_VOTES: Dict[str, List[Tuple[str, float, str]]] = defaultdict(list)
_LOCK = threading.Lock()

class SingletonMeta(type):
    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class ShelfManager(metaclass=SingletonMeta):
    """Manages shelf assignments and state with conflict detection."""
    _shelves_by_album: Dict[str, str] = {}
    _shelf_votes: Dict[str, Counter] = {}

    def __init__(self) -> None:
        self._store = {}
        
    def _get(self, key, default=None):
        return self._store.get(key, default)

    def _set(self, key, value):
        self._store[key] = value

    @staticmethod
    def vote_for_shelf(album_id: str, shelf: str, weight: float, reason: str) -> None:
        if not shelf or not shelf.strip():
            return

        log_data = None
        with _LOCK:
            # Weighted counting (counter can only use ints,
            # therefore, additionally _VOTES for weights)
            if album_id not in ShelfManager._shelf_votes:
                ShelfManager._shelf_votes[album_id] = Counter()
            # For a quick "majority" view, we increase the count by 1
            ShelfManager._shelf_votes[album_id][shelf] += 1
            winner = ShelfManager._shelf_votes[album_id].most_common(1)[0][0]
            if len(ShelfManager._shelf_votes[album_id]) > 1:
                all_votes = ShelfManager._shelf_votes[album_id].most_common()
                log_data = (album_id, dict(all_votes), winner)
            ShelfManager._shelves_by_album[album_id] = winner

        # Weighted for the real decision
        _VOTES.setdefault(album_id, []).append(
            (shelf, float(weight), str(reason or ""))
        )

        if log_data:
            log.warning(
                "Album %s has files from different shelves. Votes: %s. Use: '%s'",
                log_data[0],
                log_data[1],
                log_data[2],
            )

    # def vote_for_shelf(self, album_id: str, shelf_name: str) -> None:
    #     if not shelf_name or not shelf_name.strip():
    #         return
    #
    #     if album_id not in self._shelf_votes:
    #         self._shelf_votes[album_id] = Counter()
    #
    #     self._shelf_votes[album_id][shelf_name] += 1
    #
    #     # Get the shelf with most votes
    #     winner = self._shelf_votes[album_id].most_common(1)[0][0]
    #
    #     # Check for conflicts
    #     if len(self._shelf_votes[album_id]) > 1:
    #         all_votes = self._shelf_votes[album_id].most_common()
    #         log.warning(
    #             "%s: Album %s has files from different shelves. Votes: %s. Using: '%s'",
    #             self.plugin_name,
    #             album_id,
    #             dict(all_votes),
    #             winner,
    #         )
    #
    #     self._shelves_by_album[album_id] = winner

    @staticmethod
    def _winner(votes: List[Tuple[str, float, str]]) -> Optional[str]:
        if not votes:
            return None
        agg: Dict[str, float] = {}
        for shelf, weight, _ in votes:
            agg[shelf] = agg.get(shelf, 0.0) + float(weight)
        return max(agg.items(), key=lambda kv: kv[1])[0]

    @staticmethod
    def _get_manual_override(album_id: str) -> Optional[str]:
        st = _STATE.get(album_id, {})
        if (
            st.get("shelf_locked")
            or st.get("shelf_source") == ShelfConstants.SHELF_SOURCE_MANUAL
        ):
            return st.get("shelf")
        return None

    # def get_album_shelf(self, album_id: str) -> str | None:
    #     if self._shelves_by_album.get(album_id) is not None:
    #         return self._shelves_by_album.get(album_id)
    #     log.warning(
    #         "The shelf of the album %s could not be identified with certainty.",
    #         album_id,
    #     )
    #
    #     return None

    @staticmethod
    def get_album_shelf(album_id: str) -> tuple[Optional[str], str]:
        """
        Read with priority:
        1. Manual lock or `shelf_source=='manual'` => return the current value.
        2. Otherwise, weighted winner from `_VOTES`.
        3. Fallback to the last observed winner (`_shelves_by_album`).
        """
        # 1. Manual lock
        manual_shelf = ShelfManager._get_manual_override(album_id=album_id)
        if manual_shelf:
            return manual_shelf, ShelfConstants.SHELF_SOURCE_MANUAL

        # 2. Weighted decision
        chosen = ShelfManager._winner(_VOTES.get(album_id, []))
        if chosen:
            return chosen, ShelfConstants.SHELF_SOURCE_VOTES

        # 3. Fallback: simple majority winner from counter
        with _LOCK:
            shelf_name = ShelfManager._shelves_by_album.get(album_id)
            if shelf_name is None:
                log.warning(
                    "Shelf for album %s could not be determined with certainty.",
                    album_id,
                )
            return shelf_name, ShelfConstants.SHELF_SOURCE_FALLBACK

    @staticmethod
    def clear_album(album_id: str) -> None:
        ShelfManager._shelves_by_album.pop(album_id, None)
        ShelfManager._shelf_votes.pop(album_id, None)

    @staticmethod
    def is_likely_shelf_name(
        name: str, known_shelves: List[str]
    ) -> Tuple[bool, Optional[str]]:
        if not name:
            return False, "Empty name"

        if name in known_shelves:
            return True, None

        # Heuristics for suspicious names
        suspicious_reasons = []

        # Contains ` - ` (typical for "Artist - Album")
        if " - " in name:
            suspicious_reasons.append(
                "contains ' - ' (typical for 'Artist - Album' format)"
            )

        # Too long
        if len(name) > ShelfConstants.MAX_SHELF_NAME_LENGTH:
            suspicious_reasons.append(f"too long ({len(name)} chars)")

        # Too many words
        word_count = len(name.split())
        if word_count > ShelfConstants.MAX_WORD_COUNT:
            suspicious_reasons.append(f"too many words ({word_count})")

        # Contains album indicators
        if any(indicator in name for indicator in ShelfConstants.ALBUM_INDICATORS):
            suspicious_reasons.append("contains album indicator (Vol., Disc, etc.)")

        if suspicious_reasons:
            return False, "; ".join(suspicious_reasons)

        return True, None

    @staticmethod
    def set_album_shelf(
        album_id: str,
        shelf: str,
        source: str = ShelfConstants.SHELF_SOURCE_MANUAL,
        lock: Optional[bool] = None,
    ) -> Optional[str]:
        state = _STATE.setdefault(album_id, {})
        if lock is None:
            lock = source == ShelfConstants.SHELF_SOURCE_MANUAL

        # Manually locked => can only be overwritten manually
        if state.get("shelf_locked") and source != ShelfConstants.SHELF_SOURCE_MANUAL:
            return state.get("shelf")

        state["shelf"] = shelf
        state["shelf_source"] = source
        state["shelf_locked"] = bool(lock)

        if source == ShelfConstants.SHELF_SOURCE_MANUAL:
            # Register dominant decision (∞ weight)
            ShelfManager.vote_for_shelf(
                album_id=album_id,
                shelf=shelf,
                weight=float("inf"),
                reason="manual override",
            )

        return shelf

    @staticmethod
    def clear_manual_override(album_id: str) -> None:
        state = _STATE.setdefault(album_id, {})
        state["shelf_locked"] = False
        if state.get("shelf_source") == ShelfConstants.SHELF_SOURCE_MANUAL:
            state["shelf_source"] = ShelfConstants.SHELF_SOURCE_VOTES
