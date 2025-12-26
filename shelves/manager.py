# -*- coding: utf-8 -*-

"""
Shelf manager for tracking album shelf_name assignments.
"""

from __future__ import annotations

import threading
from collections import Counter, defaultdict, namedtuple
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from picard import log

from .constants import ShelfConstants


class ShelfManager:
    """Manages shelf_name assignments and _shelf_state with conflict detection."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._test_value = None
            self.log_data = namedtuple("log_data", ["album_id", "votes", "winner"])

            # Minimum in-memory state
            self._shelf_state: Dict[str, Dict[str, Any]] = defaultdict(dict)
            self._shelf_votes: Dict[str, List[Tuple[str, float, str]]] = defaultdict(
                list
            )
            # self._shelf_votes: Dict[str, Counter] = {}

            self._shelves_by_album: Dict[str, str] = {}

            # Cache shelf_name names
            self._shelf_names: Set[str] = set()

            self._base_path: str = ""

    @property
    def shelf_names(self) -> Set[str]:
        """
        Get the list of shelf_name names.

        :return:
        """
        return self._shelf_names

    @shelf_names.setter
    def shelf_names(self, value: Set[str]):
        self._shelf_names = value

    @property
    def shelf_votes(self):
        """

        :return:
        """
        return self._shelf_votes

    @property
    def test_value(self):
        """

        :return:
        """
        return self._test_value

    @test_value.setter
    def test_value(self, value):
        """

        :param value:
        :return:
        """
        self._test_value = value

    @property
    def base_path(self) -> Path:
        """
        Get the base file_path_str.
        :return:
        """
        return self.base_path

    @base_path.setter
    def base_path(self, value: str):
        """
        Sets the base file_path_str for the shelf_name paths.
        :param value:
        :return:
        """
        base_path_str = value
        self._base_path = Path(base_path_str).resolve()

    @classmethod
    def destroy(cls):
        """
        Destroy the singleton instance.
        :return:
        """
        cls._instance = None

    @classmethod
    def vote_for_shelf(
        cls,
        album_id: str,
        shelf_name: str,
        weight: float = 0.0,
        reason: str = None,
    ) -> None:
        """

        :param album_id:
        :param shelf_name:
        :param weight:
        :param reason:
        :return:
        """
        if not shelf_name or not shelf_name.strip():
            return

        # pylint: disable=protected-access
        with cls._lock:
            # Weighted counting (counter can only use ints,
            # therefore, additionally _shelf_votes for weights)

            if album_id not in cls._instance._shelf_votes:
                cls._instance._shelf_votes[album_id] = Counter()

            # For a quick "majority" view, we increase the count by 1
            cls._instance._shelf_votes[album_id][shelf_name] += 1

            winner = cls._instance._shelf_votes[album_id].most_common(1)[0][0]

            if len(cls._instance._shelf_votes[album_id]) > 1:
                all_votes = cls._instance._shelf_votes[album_id].most_common()
                cls._instance.log_data = (album_id, dict(all_votes), winner)

            cls._instance._shelves_by_album[album_id] = winner

        # Weighted for the real decision
        vote = cls._instance._shelf_votes.setdefault(album_id, [])
        vote["shelf_name"] = shelf_name
        vote["weight"] = weight
        vote["reason"] = reason

        if cls._instance.log_data:
            log.warning(
                "Album %s has files from different shelf_names. Votes: %s. Use: '%s'",
                cls._instance.log_data[0],
                cls._instance.log_data[1],
                cls._instance.log_data[2],
            )

    # def vote_for_shelf(cls, album_id: str, shelf_name: str) -> None:
    #     if not shelf_name or not shelf_name.strip():
    #         return
    #
    #     if album_id not in cls._shelf_votes:
    #         cls._shelf_votes[album_id] = Counter()
    #
    #     cls._shelf_votes[album_id][shelf_name] += 1
    #
    #     # Get the shelf_name with most _shelf_votes
    #     winner = cls._shelf_votes[album_id].most_common(1)[0][0]
    #
    #     # Check for conflicts
    #     if len(cls._shelf_votes[album_id]) > 1:
    #         all_votes = cls._shelf_votes[album_id].most_common()
    #         log.warning(
    #             "%s: Album %s has files from different shelf_names. Votes: %s. Using: '%s'",
    #             cls.plugin_name,
    #             album_id,
    #             dict(all_votes),
    #             winner,
    #         )
    #
    #     cls._shelves_by_album[album_id] = winner

    @classmethod
    def _winner(cls, votes: List[Tuple[str, float, str]]) -> Optional[str]:
        if not votes:
            return None
        agg: Dict[str, float] = {}
        for shelf, weight, _ in votes:
            agg[shelf] = agg.get(shelf, 0.0) + float(weight)
        return max(agg.items(), key=lambda kv: kv[1])[0]

    @classmethod
    def _get_manual_override(cls, album_id: str) -> Optional[str]:
        # pylint: disable=protected-access
        state = cls._instance._shelf_state.get(album_id, {})
        if (
            state.get("shelf_locked")
            or state.get("shelf_source") == ShelfConstants.SHELF_SOURCE_MANUAL
        ):
            return state.get("shelf_name")
        return None

    # def get_album_shelf(cls, album_id: str) -> str | None:
    #     if cls._shelves_by_album.get(album_id) is not None:
    #         return cls._shelves_by_album.get(album_id)
    #     log.warning(
    #         "The shelf_name of the album %s could not be identified with certainty.",
    #         album_id,
    #     )
    #
    #     return None

    @classmethod
    def get_album_shelf(cls, album_id: str) -> tuple[Optional[str], str]:
        """
        Read with priority:
        1. Manual _lock or `shelf_source=='manual'` => return the current value.
        2. Otherwise, weighted winner from `_shelf_votes`.
        3. Fallback to the last observed winner (`_shelves_by_album`).

        :param album_id:
        :return:
        """
        # 1. Manual _lock
        manual_shelf = cls._get_manual_override(album_id=album_id)
        if manual_shelf:
            return manual_shelf, ShelfConstants.SHELF_SOURCE_MANUAL

        # 2. Weighted decision
        # pylint: disable=protected-access
        chosen = cls._winner(cls._instance._shelf_votes.get(album_id, []))
        if chosen:
            return chosen, ShelfConstants.SHELF_SOURCE_VOTES

        # 3. Fallback: simple majority winner from counter
        # pylint: disable=protected-access
        with cls._instance._lock:
            # pylint: disable=protected-access
            shelf_name = cls._instance._shelves_by_album.get(album_id)
            if shelf_name is None:
                log.warning(
                    "Shelf for album %s could not be determined with certainty.",
                    album_id,
                )
            return shelf_name, ShelfConstants.SHELF_SOURCE_FALLBACK

    @classmethod
    def clear_album(cls, album_id: str) -> None:
        """

        :param album_id:
        :return:
        """
        # pylint: disable=protected-access
        cls._instance._shelves_by_album.pop(album_id, None)
        cls._instance._shelf_votes.pop(album_id, None)

    @classmethod
    def is_likely_shelf_name(
        cls,
        name: str,
        known_shelves: Set[str],
    ) -> Tuple[bool, Optional[str]]:
        """

        :param name:
        :param known_shelves:
        :return:
        """
        if not name:
            return False, "Empty name"

        if name in known_shelves:
            return True, None

        # Heuristics for suspicious names
        suspicious_reasons = []

        # Contains ` - ` (typical for "Artist - Album")
        if " - " in name:
            suspicious_reasons.append(
                "contains ' - ' (typical for 'Artist - Album' format)",
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

    @classmethod
    def set_album_shelf(
        cls,
        album_id: str,
        shelf: str,
        source: str = ShelfConstants.SHELF_SOURCE_MANUAL,
        lock: Optional[bool] = None,
    ) -> Optional[str]:
        """

        :param album_id:
        :param shelf:
        :param source:
        :param lock:
        :return:
        """
        # pylint: disable=protected-access
        state = cls._instance._shelf_state.setdefault(album_id, {})
        if lock is None:
            lock = source == ShelfConstants.SHELF_SOURCE_MANUAL

        # Manually locked => can only be overwritten manually
        if state.get("shelf_locked") and source != ShelfConstants.SHELF_SOURCE_MANUAL:
            return state.get("shelf_name")

        state["shelf_name"] = shelf
        state["shelf_source"] = source
        state["shelf_locked"] = bool(lock)

        if source == ShelfConstants.SHELF_SOURCE_MANUAL:
            # Register dominant decision (∞ weight)
            cls.vote_for_shelf(
                album_id=album_id,
                shelf_name=shelf,
                weight=float("inf"),
                reason="manual override",
            )

        return shelf

    @classmethod
    def clear_manual_override(cls, album_id: str) -> None:
        """

        :param album_id:
        :return:
        """
        # pylint: disable=protected-access
        state = cls._instance._shelf_state.setdefault(album_id, {})
        state["shelf_locked"] = False
        if state.get("shelf_source") == ShelfConstants.SHELF_SOURCE_MANUAL:
            state["shelf_source"] = ShelfConstants.SHELF_SOURCE_VOTES
