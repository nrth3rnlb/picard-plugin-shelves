# -*- coding: utf-8 -*-

"""
Utility functions for managing shelf_names.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Set, Tuple

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
    def validate_shelf_name(name: str) -> Tuple[bool, str]:
        """
        Validate a shelf name.

        :param name:
        :return:
        """
        if not isinstance(name, str) or not name.strip():
            return False, "Shelf name cannot be empty"

        shelf_name = name.strip()

        invalid_names_used = [
            name_used
            for name_used in shelf_name.split()
            if name_used in ShelfConstants.INVALID_SHELF_NAMES
        ]
        if invalid_names_used:
            hr_invalid_names_used = (
                f"{', '.join(repr(c) for c in set(invalid_names_used))}"
            )
            hr_invalid_names = (
                f"{', '.join(repr(c) for c in ShelfConstants.INVALID_SHELF_NAMES)}"
            )
            return (
                False,
                f"Cannot use '{shelf_name}' as shelf name."
                f" The name is an invalid name: {hr_invalid_names_used}."
                f" Not allowed are: {hr_invalid_names}.",
            )

        invalid_chars_used = [
            char_used
            for char_used in shelf_name
            if char_used in ShelfConstants.INVALID_SHELF_NAME_CHARS
        ]
        if invalid_chars_used:
            hr_invalid_chars_used = (
                f"{', '.join(repr(c) for c in set(invalid_chars_used))}"
            )
            hr_invalid_name_chars = (
                f"{', '.join(repr(c) for c in ShelfConstants.INVALID_SHELF_NAME_CHARS)}"
            )
            return (
                False,
                f"Cannot use '{shelf_name}' as shelf name."
                f" The name contains invalid character(s): {hr_invalid_chars_used}."
                f" Not allowed are: {hr_invalid_name_chars}.",
            )

        invalid_tokens_used = [
            token_used
            for token_used in shelf_name.split()
            if token_used.lower()
            in [token.lower() for token in ShelfConstants.ALBUM_INDICATORS]
        ]

        if invalid_tokens_used:
            hr_invalid_tokens_used = (
                f"{', '.join(repr(c) for c in set(invalid_tokens_used))}"
            )
            hr_invalid_name_tokens = (
                f"{', '.join(repr(c) for c in ShelfConstants.ALBUM_INDICATORS)}"
            )
            return (
                False,
                f"Cannot use '{shelf_name}' as shelf name."
                f" The name contains album indicator(s): {hr_invalid_tokens_used}."
                f" Not allowed are: {hr_invalid_name_tokens}.",
            )

        # TODO(#15): Decide if max length validation should be enforced
        # if len(shelf_name) > ShelfConstants.MAX_SHELF_NAME_LENGTH:
        #     return (
        #         False,
        #         f"Cannot use '{shelf_name}' as shelf name."
        #         f" The name is too long with {len(shelf_name)} characters."
        #         f" Maximum allowed is {ShelfConstants.MAX_SHELF_NAME_LENGTH}.",
        #     )

        # TODO(#16): Decide if max word count validation should be enforced
        # if len(shelf_name.split()) > ShelfConstants.MAX_WORD_COUNT:
        #     return (
        #         False,
        #         f"Cannot use '{shelf_name}' as shelf name."
        #         f" Shelf name is too long with {len(shelf_name.split())} words."
        #         f" Maximum allowed is {ShelfConstants.MAX_WORD_COUNT}.",
        #     )

        return True, "Valid shelf name"

    @staticmethod
    def get_shelf_dirs(base_path: Path) -> Set[str]:
        """

        :return:
        """
        shelf_sub_dirs: Set[str] = set()
        try:
            shelf_sub_dirs = set(
                entry.name for entry in base_path.iterdir() if entry.is_dir()
            )

        except (OSError, PermissionError) as e:
            log.error("Error scanning directory: %s", e)
        return shelf_sub_dirs
