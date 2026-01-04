# -*- coding: utf-8 -*-

"""
Shelf manager for tracking album shelf_name assignments.
"""

from __future__ import annotations

import threading
from collections import Counter, defaultdict, namedtuple
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from picard import config, log

from .constants import ShelfConstants
from .utils import ShelfUtils


class ShelfManager:
    """Manages shelf_name assignments and _shelf_state with conflict detection."""

    _instance = None
    _lock = threading.Lock()
    _log_data: Optional[Tuple[str, Dict[str, int], str]] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # noinspection PyTypeHints
    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._test_value = None

            # Minimum in-memory state
            self._shelf_state: Dict[str, Dict[str, Any]] = defaultdict(dict)
            self._shelf_votes_weighted: Dict[str, List[Tuple[str, float, str]]] = (
                defaultdict(list)
            )
            self._shelf_votes_counted: Dict[str, Counter] = {}
            self._shelves_by_album: Dict[str, str] = {}

            self.base_path: Path = config.setting[
                ShelfConstants.CONFIG_MOVE_FILES_TO_KEY
            ]

            self.shelf_names: Set[str] = set(
                config.setting[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY]
            )

    @property
    def shelf_names(self) -> Set[str]:
        """
        Get the list of shelf_name names.

        :return:
        """
        return self._shelf_names

    @shelf_names.setter
    def shelf_names(self, names: Set[str]):
        """
        Set the list of shelf_name names.
        :param names:
        :type names:
        :return:
        :rtype:
        """
        self._shelf_names = set(
            filter(lambda name: ShelfUtils.validate_shelf_name(name)[0], names)
        )

    @property
    def shelf_votes(self):
        """

        :return:
        """
        return self._shelf_votes_weighted

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
        return self._base_path

    @base_path.setter
    def base_path(self, value: str):
        """
        Sets the base file_path_str for the shelf_name paths.
        :param value:
        :return:
        """
        self._base_path = Path(value).resolve()

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
        if not shelf_name:
            return

        shelf_name = shelf_name.strip()

        with cls._lock:
            # Counter for majority decisions
            if album_id not in ShelfManager()._shelf_votes_counted:
                ShelfManager()._shelf_votes_counted[album_id] = Counter()
            ShelfManager()._shelf_votes_counted[album_id][shelf_name] += 1

            winner = ShelfManager()._shelf_votes_counted[album_id].most_common(1)[0][0]
            LogData = namedtuple("LogData", ["album_id", "votes", "winner"])

            if len(ShelfManager()._shelf_votes_counted[album_id]) > 1:
                all_votes = ShelfManager()._shelf_votes_counted[album_id].most_common()
                ShelfManager()._log_data = LogData(album_id, dict(all_votes), winner)

            ShelfManager()._shelves_by_album[album_id] = winner

            # For weighted decisions
            if not hasattr(cls._instance, "_shelf_votes_weighted"):
                ShelfManager()._shelf_votes_weighted = defaultdict(list)
            ShelfManager()._shelf_votes_weighted[album_id].append(
                (shelf_name, weight, reason)
            )

        if _log_data := ShelfManager()._log_data:
            log.warning(
                "Album %s has files from different shelf_names. Votes: %s. Use: '%s'",
                _log_data[0],
                _log_data[1],
                _log_data[2],
            )

    # def vote_for_shelf(cls, album_id: str, shelf_name: str) -> None:
    #     if not shelf_name or not shelf_name.strip():
    #         return
    #
    #     if album_id not in cls._shelf_votes_weighted:
    #         cls._shelf_votes_weighted[album_id] = Counter()
    #
    #     cls._shelf_votes_weighted[album_id][shelf_name] += 1
    #
    #     # Get the shelf_name with most _shelf_votes_weighted
    #     winner = cls._shelf_votes_weighted[album_id].most_common(1)[0][0]
    #
    #     # Check for conflicts
    #     if len(cls._shelf_votes_weighted[album_id]) > 1:
    #         all_votes = cls._shelf_votes_weighted[album_id].most_common()
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
        state = ShelfManager()._shelf_state.get(album_id, {})
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
        2. Otherwise, weighted winner from `_shelf_votes_weighted`.
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
        chosen = cls._winner(ShelfManager()._shelf_votes_weighted.get(album_id, []))
        if chosen:
            return chosen, ShelfConstants.SHELF_SOURCE_VOTES

        # 3. Fallback: simple majority winner from counter
        # pylint: disable=protected-access
        with ShelfManager()._lock:
            # pylint: disable=protected-access
            shelf_name = ShelfManager()._shelves_by_album.get(album_id)
            if shelf_name is None:
                log.warning(
                    "Shelf for album '%s' could not be determined with certainty.",
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
        ShelfManager()._shelves_by_album.pop(album_id, None)
        ShelfManager()._shelf_votes_weighted.pop(album_id, None)

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
        shelf_name: str,
        source: str = ShelfConstants.SHELF_SOURCE_MANUAL,
        lock: Optional[bool] = None,
    ) -> Optional[str]:
        """

        :param album_id:
        :param shelf_name:
        :param source:
        :param lock:
        :return:
        """
        # pylint: disable=protected-access
        state = ShelfManager()._shelf_state.setdefault(album_id, {})
        if lock is None:
            lock = source == ShelfConstants.SHELF_SOURCE_MANUAL

        # Manually locked => can only be overwritten manually
        if state.get("shelf_locked") and source != ShelfConstants.SHELF_SOURCE_MANUAL:
            return state.get("shelf_name")

        state["shelf_name"] = shelf_name
        state["shelf_source"] = source
        state["shelf_locked"] = bool(lock)

        if source == ShelfConstants.SHELF_SOURCE_MANUAL:
            # Register dominant decision (∞ weight)
            cls.vote_for_shelf(
                album_id=album_id,
                shelf_name=shelf_name,
                weight=float("inf"),
                reason="manual override",
            )

        return shelf_name

    @classmethod
    def clear_manual_override(cls, album_id: str) -> None:
        """

        :param album_id:
        :return:
        """
        state = ShelfManager()._shelf_state.setdefault(album_id, {})
        state["shelf_locked"] = False
        if state.get("shelf_source") == ShelfConstants.SHELF_SOURCE_MANUAL:
            state["shelf_source"] = ShelfConstants.SHELF_SOURCE_VOTES

    @classmethod
    def intersect_shelf_names(cls, names: Set[str] | str) -> None:
        """
        Intersect shelf names with the provided set and update the UI.

        :param names: Single shelf name or set of shelf names to intersect.
        :type names: Set[str] | str
        :return: None
        :rtype: None
        """
        if isinstance(names, str):
            names = {names}
        ShelfManager().shelf_names = ShelfManager().shelf_names.intersection(names)

    @classmethod
    def remove_shelf_names(cls, names: Set[str] | str) -> None:
        """
        Remove shelf names from the registry and update the UI if requested.

        :param names: Single shelf name or set of shelf names to remove.
        :type names: Set[str] | str
        :return: None
        :rtype: None
        """
        if isinstance(names, str):
            names = {names}
        ShelfManager().shelf_names = ShelfManager().shelf_names.difference(names)

    @classmethod
    def add_shelf_names(cls, names: Set[str] | str) -> None:
        """
        Add shelf names to the registry and update the UI.

        :param names: Single shelf name or set of shelf names to add.
        :type names: Set[str] | str
        :return: None
        """
        if isinstance(names, str):
            names = {names}
        ShelfManager().shelf_names = ShelfManager().shelf_names.union(names)
