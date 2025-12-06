# -*- coding: utf-8 -*-

"""
Utility functions for managing shelves.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from picard import config, log

from .constants import ShelfConstants
from .manager import ShelfManager


class ShelfUtils:
    """
    Utility functions for shelf management.
    """

    @staticmethod
    def get_shelf_from_path(path: str, known_shelves: List[str]) -> Tuple[Optional[str], bool]:
        """
        Extract the shelf name from a file path.

        Args:
            path: The file path to analyze.
            known_shelves: A list of known shelf names.

        Returns:
            A tuple containing:
            - The determined shelf name (e.g., "Soundtracks" or "Standard").
            - A boolean indicating if the shelf was explicitly found from the path (`True`)
              or if it's a fallback value (`False`).
        """
        try:
            base_path_str = config.setting["move_files_to"]
            base_path = Path(base_path_str).resolve()
            file_path = Path(path).resolve()

            if not file_path.is_relative_to(base_path):
                log.debug("Path '%s' is not under base directory.", path)
                return None, False

            relative_parts = file_path.relative_to(base_path).parts
            if not relative_parts or len(relative_parts) <= 1:
                log.debug("File is directly in base directory.")
                return None, False

            potential_shelf = relative_parts[0]
            is_likely, reason = ShelfUtils.is_likely_shelf_name(potential_shelf, known_shelves)

            if is_likely:
                log.debug("Confirmed shelf '%s' from path.", potential_shelf)
                return potential_shelf, True
            else:
                log.warning(
                    "Folder '%s' is not a likely shelf (%s). "
                    "If this is a shelf, add it in settings.",
                    potential_shelf, reason
                )
                return None, False

        except (KeyError, ValueError, OSError) as e:
            log.error("Error extracting shelf from path '%s': %s.", path, e)
            return None, False

    @staticmethod
    def validate_shelf_name(name: str) -> Tuple[bool, str]:
        """
        Validate a shelf name for use as a directory name by processing a list of validation rules.

        Args:
            name: The shelf name to validate

        Returns:
            Tuple of (is_valid, warning_or_error_message)
        """
        stripped_name = name.strip()
        if not stripped_name:
            return False, "Shelf name cannot be empty"

        def check_reserved_names(n):
            if n in (".", ".."):
                return False, "Cannot use '.' or '..' as shelf name", True
            return True, None, False

        def check_invalid_chars(n):
            invalid = [c for c in ShelfConstants.INVALID_PATH_CHARS if c in n]
            if invalid:
                return False, f"Contains invalid characters: {', '.join(invalid)}", True
            return True, None, False

        def check_length(n):
            if len(n) > ShelfConstants.MAX_SHELF_NAME_LENGTH:
                return False, f"Shelf name too long ({len(n)} chars, maximum is {ShelfConstants.MAX_SHELF_NAME_LENGTH})", True
            return True, None, False

        def check_word_count(n):
            words = n.split()
            if len(words) > ShelfConstants.MAX_WORD_COUNT:
                return False, f"Shelf name has too many words ({len(words)}, maximum is {ShelfConstants.MAX_WORD_COUNT})", True
            return True, None, False

        def check_album_indicators(n):
            found_indicators: List[str] = []
            for indicator in ShelfConstants.ALBUM_INDICATORS:
                if indicator in n:
                    found_indicators.append(n)

            if found_indicators:
                return False, f"Shelf name contains album indicator(s): {found_indicators}, album indicators are {ShelfConstants.ALBUM_INDICATORS}", True

            return True, None, False

        def check_dots(n):
            if n.startswith(".") or n.endswith("."):
                return True, "Warning: Names starting or ending with '.' may cause issues on some systems", False
            return True, None, False

        validation_functions = [
            check_reserved_names,
            check_invalid_chars,
            check_length,
            check_word_count,
            check_album_indicators,
            check_dots,
        ]

        warning_message = ""
        for func in validation_functions:
            is_valid, message, is_error_message = func(stripped_name)
            if not is_valid:
                return False, message
            if message:
                warning_message = message

        return True, warning_message

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

    @staticmethod
    def get_existing_dirs() -> list[str]:
        """
        Load existing directories from the music directory.
        Returns: List of directory names
        """
        music_dir_str = config.setting["move_files_to"]  # type: ignore[index]
        music_dir = Path(music_dir_str)

        shelves_found = [entry.name for entry in music_dir.iterdir() if entry.is_dir()]
        return shelves_found

    @staticmethod
    def add_known_shelf(shelf_name: str) -> None:
        """
        Add a shelf name to the list of known shelves.
        Args:
            shelf_name: Name of the shelf to add
        """
        if not shelf_name or not shelf_name.strip():
            return

        shelves = ShelfManager.get_configured_shelves()
        if shelf_name not in shelves:
            shelves.append(shelf_name)
            config.setting[ShelfConstants.CONFIG_SHELVES_KEY] = sorted(shelves)  # type: ignore[index]
            log.debug("Added shelf '%s' to known shelves", shelf_name)

    @staticmethod
    def remove_known_shelf(shelf_name: str) -> None:
        """
        Remove a shelf name from the list of known shelves.

        Args:
            shelf_name: Name of the shelf to remove
        """
        shelves = ShelfManager.get_configured_shelves()
        if shelf_name in shelves:
            shelves.remove(shelf_name)
            config.setting[ShelfConstants.CONFIG_SHELVES_KEY] = shelves  # type: ignore[index]
            log.debug(
                "Removed shelf '%s' from known shelves", shelf_name
            )

    @staticmethod
    def get_shelf_name_from_tag(shelf_tag: str) -> Optional[str]:
        if not isinstance(shelf_tag, str):
            return None
        return shelf_tag.split(ShelfConstants.MANUAL_SHELF_SUFFIX)[0].strip()
