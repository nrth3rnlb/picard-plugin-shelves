"""
Constants for the Shelves plugin.
"""

from __future__ import annotations

# Validation limits
# TODO Make configurable
MAX_SHELF_NAME_LENGTH: int = 30
MAX_WORD_COUNT: int = 3
INVALID_SHELF_NAME_CHARS: set[str] = set()
INVALID_SHELF_NAMES: frozenset[str] = frozenset([".", ".."])
ALBUM_INDICATORS: frozenset[str] = frozenset(["Vol.", "Volume", "Disc", "CD", "Part"])

# noinspection SpellCheckingInspection
RENAME_SNIPPET: str = """$set(_shelffolder,$shelf())
$set(_shelffolder,$if($not($eq(%_shelffolder%,)),%_shelffolder%/))

%_shelffolder%
$if2(%albumartist%,%artist%)/%album%/%title%"""
