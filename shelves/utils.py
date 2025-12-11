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
    def get_shelf_name_from_tag(tag_value: Optional[str]) -> Optional[str]:
        """
        Extract the shelf name from a tag value.

        :param tag_value:
        :return:
        """

        if not isinstance(tag_value, str):
            return None
        tag = tag_value.strip()
        if not tag:
            return None
        suffix = ShelfConstants.MANUAL_SHELF_SUFFIX
        if suffix and suffix in tag:
            # Only strip the trailing occurrence to avoid accidental mid-string matches
            if tag.endswith(suffix):
                return tag[: -len(suffix)].strip() or None

        return tag

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
            is_likely, reason = ShelfManager.is_likely_shelf_name(potential_shelf, known_shelves)
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
    def validate_shelf_name(name: str) -> Tuple[bool, Optional[str]]:
        if not isinstance(name, str) or not name.strip():
            return False, "Shelf name cannot be empty"

        trimmed = name.strip()

        if trimmed in {".", ".."}:
            return False, "Cannot use '.' or '..'"

        bad = [ch for ch in trimmed if ch in ShelfConstants.INVALID_PATH_CHARS]
        if bad:
            return False, f"Contains invalid characters: {', '.join(sorted(set(bad)))}"

        if len(trimmed) > ShelfConstants.MAX_SHELF_NAME_LENGTH:
            return False, "Shelf name too long"

        if len(trimmed.split()) > ShelfConstants.MAX_WORD_COUNT:
            return False, "Shelf name has too many words"

        lower = trimmed.lower()
        if any(token.lower() in lower for token in ShelfConstants.ALBUM_INDICATORS):
            return False, "Name contains album indicator(s)"

        if trimmed.startswith(".") or trimmed.endswith("."):
            return True, "Shelf name may cause issues due to leading/trailing dot"

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
            config.setting[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY] = sorted(shelves)  # type: ignore[index]
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
            config.setting[ShelfConstants.CONFIG_KNOWN_SHELVES_KEY] = shelves  # type: ignore[index]
            log.debug(
                "Removed shelf '%s' from known shelves", shelf_name
            )
