from __future__ import annotations

from gettext import gettext as _

MESSAGE_INVALID_SHELF_NAME: str = _("Shelf name is not valid.")
MESSAGE_MOVE_SELECTED_ITEMS_DISABLED: str = _(
    "The list of {name_of_target_stage} is full, no further elements possible.",
)
MESSAGE_MOVE_SELECTED_ITEMS_ENABLED: str = _(
    "Move selected shelf names to the list of the {name_of_target_stage}.",
)
MESSAGE_PROVIDE_SHELF_NAME: str = _("Provide a name for the new shelf:")
MESSAGE_USED_SHELF_NAME: str = _(
    "The shelf names '{list_of_shelf_names}' are used in your workflow. Are you sure you want to remove them?",
)

NAME_WORKFLOW_STAGE_1: str = _("origin shelves")
NAME_WORKFLOW_STAGE_2: str = _("target shelves")
NAME_WORKFLOW_STAGE_ALL: str = _("Available shelf names")

TITLE_ADD_SHELF_NAME: str = _("Add a shelf name.")
TITLE_REMOVE_SHELF_NAMES: str = _("Remove shelf names?")

PRIMARY_RELEASE_TYPES: dict[str, str] = {
    "Album": "Album",
    "Broadcast": "Broadcast",
    "EP": "EP",
    "Other": "Other",
    "Single": "Single",
}

SECONDARY_RELEASE_TYPES: dict[str, str] = {
    "Audio drama": "Audio drama",
    "Audiobook": "Audiobook",
    "Compilation": "Compilation",
    "DJ-mix": "DJ-mix",
    "Demo": "Demo",
    "Field recording": "Field recording",
    "Interview": "Interview",
    "Live": "Live",
    "Remix": "Remix",
    "Soundtrack": "Soundtrack",
    "Spoken word": "Spoken word",
    "Mixtape/Street": "Mixtape/Street",
}
