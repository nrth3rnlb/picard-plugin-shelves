"""
Utility functions
"""

from __future__ import annotations

import logging
from gettext import gettext as _
from pathlib import Path
from typing import Any, Set, Tuple
from warnings import deprecated

from picard import log
from picard.script import ScriptParser

from .constants import ALBUM_INDICATORS, INVALID_SHELF_NAME_CHARS, INVALID_SHELF_NAMES
from .exceptions import ShelfNotDeterminableException
from .typings import TagKey


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
    "Is only mandatory until version 1.7.0. As of version 2, the use of the tag has changed. The function is  "
    "used from version 2 to continue processing existing tags and will be removed in a later version will be "
    "removed."
)
def get_shelf_name_from_tag(tag_value: str) -> str:
    """
    Extract the shelf name from a tag value.

    In addition to the name of the shelf, the tag can also contain the suffix "; manual",
    This function removes this suffix.
    """
    if not tag_value:
        return ""
    MANUAL_SHELF_SUFFIX = "; manual"
    tag = tag_value.strip()
    if tag.endswith(MANUAL_SHELF_SUFFIX):
        return tag[: -len(MANUAL_SHELF_SUFFIX)].strip()
    return tag


def get_shelf_name_from_path(file_path: Path, base_path: Path) -> str:
    """Extract the shelf name from a file_path."""
    try:
        if not file_path.is_relative_to(base_path):
            log.warning(_("Path '%s' is not under base directory."), file_path)
            raise ShelfNotDeterminableException(filepath=file_path)

        relative_parts = file_path.relative_to(base_path).parts
        if not relative_parts or len(relative_parts) <= 1:
            log.warning(_("File is directly in base directory."))
            raise ShelfNotDeterminableException(filepath=file_path)
        return relative_parts[0]

    except (KeyError, ValueError, OSError) as e:
        log.error(
            _("Error extracting shelf_name from file_path_str '%s': %s."),
            file_path,
            e,
        )
        raise ShelfNotDeterminableException(filepath=file_path, cause=e)


def validate_shelf_name(name: str) -> Tuple[bool, str]:
    """Validate a shelf name."""
    if not isinstance(name, str) or not name.strip():
        return False, _("Shelf name cannot be empty")

    shelf_name = name.strip()

    invalid_names_used = [
        name_used
        for name_used in shelf_name.split()
        if name_used in INVALID_SHELF_NAMES
    ]
    if invalid_names_used:
        hr_invalid_names_used = f"{', '.join(repr(c) for c in set(invalid_names_used))}"
        hr_invalid_names = f"{', '.join(repr(c) for c in INVALID_SHELF_NAMES)}"
        return (
            False,
            f"Cannot use '{shelf_name}' as shelf name."
            f" The name is an invalid name: {hr_invalid_names_used}."
            f" Not allowed are: {hr_invalid_names}.",
        )

    invalid_chars_used = [
        char_used for char_used in shelf_name if char_used in INVALID_SHELF_NAME_CHARS
    ]
    if invalid_chars_used:
        hr_invalid_chars_used = f"{', '.join(repr(c) for c in set(invalid_chars_used))}"
        hr_invalid_name_chars = (
            f"{', '.join(repr(c) for c in INVALID_SHELF_NAME_CHARS)}"
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
        if token_used.lower() in [token.lower() for token in ALBUM_INDICATORS]
    ]

    if invalid_tokens_used:
        hr_invalid_tokens_used = (
            f"{', '.join(repr(c) for c in set(invalid_tokens_used))}"
        )
        hr_invalid_name_tokens = f"{', '.join(repr(c) for c in ALBUM_INDICATORS)}"
        return (
            False,
            f"Cannot use '{shelf_name}' as shelf name."
            f" The name contains album indicator(s): {hr_invalid_tokens_used}."
            f" Not allowed are: {hr_invalid_name_tokens}.",
        )

    # TODO(#15): Decide if max length validation should be enforced
    # if len(shelf_name) > MAX_SHELF_NAME_LENGTH:
    #     return (
    #         False,
    #         f"Cannot use '{shelf_name}' as shelf name."
    #         f" The name is too long with {len(shelf_name)} characters."
    #         f" Maximum allowed is {MAX_SHELF_NAME_LENGTH}.",
    #     )

    # TODO(#16): Decide if max word count validation should be enforced
    # if len(shelf_name.split()) > MAX_WORD_COUNT:
    #     return (
    #         False,
    #         f"Cannot use '{shelf_name}' as shelf name."
    #         f" Shelf name is too long with {len(shelf_name.split())} words."
    #         f" Maximum allowed is {MAX_WORD_COUNT}.",
    #     )

    return True, "Valid shelf name"


def get_shelf_dirs(base_path: Path) -> Set[str]:
    """Get a set of subdirectories in the given base path."""
    shelf_sub_dirs: Set[str] = set()
    try:
        shelf_sub_dirs = set(
            entry.name for entry in base_path.iterdir() if entry.is_dir()
        )

    except (OSError, PermissionError) as e:
        log.error("Error scanning directory: %s", e)
    return shelf_sub_dirs


def debug_track(track: Any):
    """Debug track object for logging."""
    if log.get_effective_level() > logging.DEBUG:
        return

    log.debug("=" * 60)
    log.debug("TRACK DEBUG START")

    log.debug("track = %s", track)

    if hasattr(track, "metadata"):
        log.debug("✓\ttrack HAS metadata")
        log.debug("\tKeys: %s", sorted(list(track.metadata.keys())))
        log.debug(
            "\tTagKey.SHELF: %s",
            track.metadata.get(TagKey.SHELF, "(not set)"),
        )
        log.debug(
            "\tTagKey.SHELF_LOCKED: %s",
            track.metadata.get(TagKey.SHELF_LOCKED, "(not set)"),
        )

    log.debug("TRACK DEBUG END")
    log.debug("=" * 60)


def debug_file(file: Any):
    """Debug file object for logging."""
    if log.get_effective_level() > logging.DEBUG:
        return

    log.debug("=" * 60)
    log.debug("FILE DEBUG START")

    log.debug("file = %s", file)

    if hasattr(file, "metadata"):
        log.debug("✓\tfile HAS metadata")
        log.debug("\tKeys: %s", sorted(list(file.metadata.keys())))
        log.debug("\tTagKey.SHELF: %s", file.metadata.get(TagKey.SHELF, "(not set)"))
        log.debug(
            "\tTagKey.SHELF_LOCKED: %s",
            file.metadata.get(TagKey.SHELF_LOCKED, "(not set)"),
        )

    log.debug("FILE DEBUG END")
    log.debug("=" * 60)


def debug_parser(parser: ScriptParser):
    """Debugs the internal state of a `ScriptParser` object."""
    if log.get_effective_level() > logging.DEBUG:
        return

    log.debug("=" * 60)
    log.debug("PARSER DEBUG START")

    # What is parser.file?
    log.debug("parser.file = %s", parser.file)
    log.debug("parser.file type = %s", type(parser.file))

    # Does it have .metadata?
    if hasattr(parser.file, "metadata"):
        log.debug("✓\tparser.file HAS metadata")
        log.debug("\tKeys: %s", sorted(list(parser.file.metadata.keys())))
        log.debug(
            "\tTagKey.SHELF: %s",
            parser.file.metadata.get(TagKey.SHELF, "(not set)"),
        )
        log.debug(
            "\tTagKey.SHELF_LOCKED: %s",
            parser.file.metadata.get(TagKey.SHELF_LOCKED, "(not set)"),
        )

    # What is parser.context?
    if hasattr(parser, "context"):
        log.debug("✓\tparser HAS context")
        log.debug("\tKeys: %s", sorted(list(parser.context.keys())))
        log.debug(
            "\tTagKey.SHELF: %s",
            parser.context.get(TagKey.SHELF, "(not set)"),
        )
        log.debug(
            "\tTagKey.SHELF_LOCKED: %s",
            parser.context.get(TagKey.SHELF_LOCKED, "(not set)"),
        )

    log.debug("PARSER DEBUG END")
    log.debug("=" * 60)


def squeeze_the_parser(parser: ScriptParser) -> tuple[str, str]:
    """
    Extracts and processes the metadata and context tags from the given parser and
    returns their corresponding shelf names. If the required attributes are not
    present in the parser, the corresponding shelf name will be an empty string.
    """
    debug_parser(parser)
    metadata_shelf: str = ""
    context_shelf: str = ""
    if hasattr(parser.file, "metadata"):
        metadata_shelf = parser.file.metadata.get(TagKey.SHELF)
        metadata_shelf = get_shelf_name_from_tag(metadata_shelf)
        log.debug("metadata_shelf = %s", metadata_shelf)
    if hasattr(parser, "context"):
        context_shelf = parser.context.get(TagKey.SHELF)
        context_shelf = get_shelf_name_from_tag(context_shelf)
        log.debug("context_shelf = %s", context_shelf)
    return context_shelf, metadata_shelf
