from pathlib import Path

from picard import config

from .manager import ShelfManagerSettings
from .typings import ConfigKey

__all__ = ("shelf_manager_settings_from_picard_config",)


def shelf_manager_settings_from_picard_config() -> ShelfManagerSettings:
    """Create ShelfManagerSettings from Picard's global plugin configuration."""

    # noinspection PyTypeHints
    return ShelfManagerSettings(
        base_path=Path(
            config.setting[ConfigKey.MOVE_FILES_TO]  # ty:ignore[not-subscriptable]
        ),
        shelf_names=set(
            config.setting[ConfigKey.KNOWN_SHELVES]  # ty:ignore[not-subscriptable]
        ),
    )
