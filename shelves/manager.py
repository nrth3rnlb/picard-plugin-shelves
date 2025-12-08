# -*- coding: utf-8 -*-

"""
Shelf manager for tracking album shelf assignments.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple, Optional

from picard import log, config

from .constants import ShelfConstants


class ShelfManager:
    """Manages shelf assignments and state with conflict detection."""

    def __init__(self, plugin_name: str, validators, utils) -> None:
        """
        Initialize the shelf manager.

        Args:
            plugin_name: Name of the plugin
            validators: ShelfValidators instance
            utils: ShelfUtils instance
        """

        self.validators = validators
        self.utils = utils

        self.plugin_name = plugin_name
        self._shelves_by_album: Dict[str, str] = {}
        self._shelf_votes: Dict[str, Counter] = {}

    def vote_for_shelf(self, album_id: str, shelf_name: str) -> None:
        """
        Register a shelf vote for an album (used when multiple files suggest different shelves).

        Args:
            album_id: MusicBrainz album ID
            shelf_name: Name of the shelf to vote for
        """
        if not shelf_name or not shelf_name.strip():
            return

        if album_id not in self._shelf_votes:
            self._shelf_votes[album_id] = Counter()

        self._shelf_votes[album_id][shelf_name] += 1

        # Get the shelf with most votes
        winner = self._shelf_votes[album_id].most_common(1)[0][0]

        # Check for conflicts
        if len(self._shelf_votes[album_id]) > 1:
            all_votes = self._shelf_votes[album_id].most_common()
            log.warning(
                "%s: Album %s has files from different shelves. Votes: %s. Using: '%s'",
                self.plugin_name,
                album_id,
                dict(all_votes),
                winner,
            )

        self._shelves_by_album[album_id] = winner

    def get_album_shelf(self, album_id: str) -> str | None:
        """
        Retrieve the shelf name for an album.
        Args:
            album_id: MusicBrainz album ID
        Returns:
            The shelf name for the album. If the album is not found, it returns the default shelf value.
        """
        if self._shelves_by_album.get(album_id) is not None:
            return self._shelves_by_album.get(album_id)
        log.warning("%s: The shelf of the album %s could not be identified with certainty.", self.plugin_name, album_id)

        return None

    def clear_album(self, album_id: str) -> None:
        """
        Clear all data for an album.

        Args:
            album_id: MusicBrainz album ID
        """
        self._shelves_by_album.pop(album_id, None)
        self._shelf_votes.pop(album_id, None)

    @staticmethod
    def get_configured_shelves() -> List[str]:
        """
        Retrieve the list of known shelves from config with validation.
        Returns:
            List of unique, validated shelf names
        """
        from .constants import ShelfConstants
        from .utils import ShelfUtils

        shelves = config.setting[ShelfConstants.CONFIG_SHELVES_KEY]  # type: ignore[index]

        # Validate each shelf name
        valid_shelves = []
        for shelf in shelves:
            if not isinstance(shelf, str):
                log.warning(
                    "Ignoring non-string shelf: %s", repr(shelf)
                )
                continue

            is_valid, message = ShelfUtils.validate_shelf_name(shelf)
            if is_valid or not message:  # Allow warnings
                valid_shelves.append(shelf)
            else:
                log.warning(
                    "Ignoring invalid shelf '%s': %s", shelf, message
                )
        log.debug("Known shelves: %s", valid_shelves)
        return sorted(list(set(valid_shelves)))

    @staticmethod
    def is_likely_shelf_name(name: str, known_shelves: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Check if a name is likely a shelf name or an artist/album name.

        Args:
            name: The name to validate
            known_shelves: List of known shelf names

        Returns:
            Tuple of (is_likely_shelf, reason_if_not)
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
