# -*- coding: utf-8 -*-

"""
Utility functions for managing shelf_names.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from picard import log

from .constants import ShelfConstants


class ShelfUtils:
    """
    Utility functions for shelf_name management.
    """

    @property
    def rename_snippet(self) -> str:
        """Get the renaming script snippet."""
        return ShelfConstants.RENAME_SNIPPET

    @staticmethod
    def validate_shelf_names(shelf_names: set[str]) -> set[str]:
        """
        Checks a list of shelf_name names and returns a list of valid names.
        :param shelf_names:
        :return:
        """
        log.debug("Known shelf_names from config: %s", shelf_names)
        # Validate each shelf_name name
        valid_shelves: set[str] = set()
        for shelf_name in shelf_names:
            is_valid, message = ShelfUtils.validate_shelf_name(shelf_name)
            if is_valid or not message:  # Allow warnings
                valid_shelves.add(shelf_name)
            else:
                log.warning("Ignoring invalid shelf_name '%s': %s", shelf_name, message)

        return valid_shelves

    @staticmethod
    def get_shelf_name_from_tag(tag_value: Optional[str]) -> Optional[str]:
        """
        Extract the shelf_name name from a tag value.

        :param tag_value:
        :return:
        """

        if not isinstance(tag_value, str):
            return None
        tag = tag_value.strip()
        if not tag:
            return None

        if tag.endswith(ShelfConstants.MANUAL_SHELF_SUFFIX):
            return tag[: -len(ShelfConstants.MANUAL_SHELF_SUFFIX)].strip() or None

        return tag

    @staticmethod
    def get_shelf_name_from_path(file_path: Path, base_path: Path) -> Optional[str]:
        """
        Extract the shelf_name name from a file_path_str.
        :param file_path:
        :param base_path:
        :return:
        """

        try:
            if not file_path.is_relative_to(base_path):
                log.debug("Path '%s' is not under base directory.", file_path)
                return None

            relative_parts = file_path.relative_to(base_path).parts
            if not relative_parts or len(relative_parts) <= 1:
                log.debug("File is directly in base directory.")
                return None

            potential_shelf = relative_parts[0]
            return potential_shelf

        except (KeyError, ValueError, OSError) as e:
            log.error(
                "Error extracting shelf_name from file_path_str '%s': %s.",
                file_path,
                e,
            )
            return None

    @staticmethod
    def validate_shelf_name(name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a shelf_name name.

        :param name:
        :return:
        """
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
    def get_shelf_dirs(base_dir: Path) -> set[str]:
        """

        :return:
        """
        shelves_found = {entry.name for entry in base_dir.iterdir() if entry.is_dir()}
        return shelves_found
