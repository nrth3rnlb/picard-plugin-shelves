"""
Utility functions
"""

from __future__ import annotations

from gettext import gettext as _
from pathlib import Path
from typing import Set, Tuple
from warnings import deprecated

from picard import log

from . import constants
from .exceptions import ShelfNotDeterminableException


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
        is_valid, message = validate_shelf_name(shelf_name)
        if is_valid or not message:  # Allow warnings
            valid_shelves.add(shelf_name)
        else:
            log.warning("Ignoring invalid shelf_name '%s': %s", shelf_name, message)

    return valid_shelves


@deprecated(
        "Is only mandatory until version 1.7.0. As of version 2, the use of the tag has changed. The "
        " function is used from version 2 to continue processing existing tags and will be removed in a later "
        "version will be removed."
)
def get_shelf_name_from_tag(tag_value: str) -> str:
    """
    Extract the shelf name from a tag value.

    In addition to the name of the shelf, the tag can also contain the suffix "; manual",
    This function removes this suffix.
    """
    MANUAL_SHELF_SUFFIX = "; manual"
    tag = tag_value.strip()
    if tag.endswith(MANUAL_SHELF_SUFFIX):
        return tag[: -len(MANUAL_SHELF_SUFFIX)].strip()
    return tag


def get_shelf_name_from_path(file_path: Path, base_path: Path) -> str:
    """
    Extract the shelf name from a file_path.
    :param file_path:
    :param base_path:
    :return:
    """

    try:
        if not file_path.is_relative_to(base_path):
            log.warning(_("Path '%s' is not under base directory."), file_path)
            raise ShelfNotDeterminableException(filepath=file_path)

        relative_parts = file_path.relative_to(base_path).parts
        if not relative_parts or len(relative_parts) <= 1:
            log.warning(_("File is directly in base directory."))
            raise ShelfNotDeterminableException(filepath=file_path)

        potential_shelf = relative_parts[0]
        log.debug("Potential shelf name extracted: '%s'.", potential_shelf)
        return potential_shelf

    except (KeyError, ValueError, OSError) as e:
        log.error(
                _("Error extracting shelf_name from file_path_str '%s': %s."),
                file_path,
                e,
        )
        raise ShelfNotDeterminableException(filepath=file_path, cause=e)


def validate_shelf_name(name: str) -> Tuple[bool, str]:
    """
    Validate a shelf name.

    :param name:
    :return:
    """
    if not isinstance(name, str) or not name.strip():
        return False, _("Shelf name cannot be empty")

    shelf_name = name.strip()

    invalid_names_used = [
        name_used
        for name_used in shelf_name.split()
        if name_used in constants.INVALID_SHELF_NAMES
    ]
    if invalid_names_used:
        hr_invalid_names_used = f"{', '.join(repr(c) for c in set(invalid_names_used))}"
        hr_invalid_names = (
            f"{', '.join(repr(c) for c in constants.INVALID_SHELF_NAMES)}"
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
        if char_used in constants.INVALID_SHELF_NAME_CHARS
    ]
    if invalid_chars_used:
        hr_invalid_chars_used = f"{', '.join(repr(c) for c in set(invalid_chars_used))}"
        hr_invalid_name_chars = (
            f"{', '.join(repr(c) for c in constants.INVALID_SHELF_NAME_CHARS)}"
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
        if token_used.lower() in [token.lower() for token in constants.ALBUM_INDICATORS]
    ]

    if invalid_tokens_used:
        hr_invalid_tokens_used = (
            f"{', '.join(repr(c) for c in set(invalid_tokens_used))}"
        )
        hr_invalid_name_tokens = (
            f"{', '.join(repr(c) for c in constants.ALBUM_INDICATORS)}"
        )
        return (
            False,
            f"Cannot use '{shelf_name}' as shelf name."
            f" The name contains album indicator(s): {hr_invalid_tokens_used}."
            f" Not allowed are: {hr_invalid_name_tokens}.",
        )

    # TODO(#15): Decide if max length validation should be enforced
    # if len(shelf_name) > constants.MAX_SHELF_NAME_LENGTH:
    #     return (
    #         False,
    #         f"Cannot use '{shelf_name}' as shelf name."
    #         f" The name is too long with {len(shelf_name)} characters."
    #         f" Maximum allowed is {constants.MAX_SHELF_NAME_LENGTH}.",
    #     )

    # TODO(#16): Decide if max word count validation should be enforced
    # if len(shelf_name.split()) > constants.MAX_WORD_COUNT:
    #     return (
    #         False,
    #         f"Cannot use '{shelf_name}' as shelf name."
    #         f" Shelf name is too long with {len(shelf_name.split())} words."
    #         f" Maximum allowed is {constants.MAX_WORD_COUNT}.",
    #     )

    return True, "Valid shelf name"


def get_shelf_dirs(base_path: Path) -> Set[str]:
    """

    :return:
    """
    shelf_sub_dirs: Set[str] = set()
    try:
        shelf_sub_dirs = set(entry.name for entry in base_path.iterdir() if entry.is_dir())

    except (OSError, PermissionError) as e:
        log.error("Error scanning directory: %s", e)
    return shelf_sub_dirs
