""" """

from shelves.typings import ConfigKey, TagKey

known_names = [
    "Incoming",
    "Standard",
    "Soundtracks",
    "Favorites",
    "Soundtracks: Games",
    "Soundtracks - Movies",
]

known_shelves_len = len(known_names)
configuration = {
    ConfigKey.ACTIVE_TAB: 1,
    ConfigKey.KNOWN_SHELVES: known_names,
    ConfigKey.STAGE_1_INCLUDES_NON_SHELVES: True,
    ConfigKey.WORKFLOW_ENABLED: True,
    ConfigKey.WORKFLOW_STAGE_1_SHELVES: known_names[: known_shelves_len - 2],
    ConfigKey.WORKFLOW_STAGE_2_SHELVES: known_names[known_shelves_len - 1 :],
    ConfigKey.ALBUM_SHELF: TagKey.SHELF,
    ConfigKey.MOVE_FILES_TO: "/music",
}
