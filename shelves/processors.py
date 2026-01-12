"""
File processors for loading and saving shelf_name information.
"""

from __future__ import annotations

import inspect
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

from picard import log

from . import constants, utils
from .manager import ShelfManager


class ShelfProcessors:
    """
    File processors for loading and saving shelf_name information.
    """

    @staticmethod
    def _set_metadata(obj: Any, key: str, value: Any, label: str) -> None:
        """Safely sets metadata on a Picard object."""
        meta = getattr(obj, "metadata", None)
        filename = getattr(obj, "filename", "<unknown>")
        if meta is None:
            log.debug("%s metadata missing for: %s", label, filename)
            return
        try:
            meta[key] = value
        except TypeError as e:
            log.debug("Failed to set %s metadata for: %s; %s", label, filename, e)

    @staticmethod
    def file_post_removal_from_track_processor(_track: Any, file: Any) -> None:
        """
        Process a file after it has been removed from a track.
        """
        log.debug(
            "(file_post_removal_from_track_processor) Processing file: %s",
            file.filename,
        )
        album_id = file.metadata.get(constants.MUSICBRAINZ_ALBUMID)
        if album_id:
            ShelfManager().clear_album(album_id)

    @staticmethod
    def file_post_addition_to_track_processor(track: Optional[Any], file: Any) -> None:
        """
        Process a file after it has been added to a track, with a destroy priority model.
        """
        file_meta = getattr(file, "metadata", None)
        if not file_meta:
            return
        album_id = file_meta.get(constants.MUSICBRAINZ_ALBUMID)
        if not album_id:
            return

        if name_from_path := utils.get_shelf_name_from_path(
            file_path=Path(file.filename), base_path=ShelfManager().base_path
        ):
            name_from_path = name_from_path.strip()

        name_from_tag: str = file_meta.get(constants.TAG_KEY, "").strip()
        name_from_tag_without_suffix: str = name_from_tag.replace(
            constants.MANUAL_SHELF_SUFFIX, ""
        ).strip()
        is_known_name_from_path = (
            name_from_path and name_from_path in ShelfManager().shelf_names
        )
        is_known_name_from_tag_and_manual = (
            name_from_tag
            and name_from_tag_without_suffix in ShelfManager().shelf_names
            and constants.MANUAL_SHELF_SUFFIX in name_from_tag
        )
        is_known_name_from_tag = (
            name_from_tag and name_from_tag_without_suffix in ShelfManager().shelf_names
        )
        is_unknown_name_from_tag = (
            name_from_tag
            and name_from_tag_without_suffix not in ShelfManager().shelf_names
        )
        is_unknown_name_from_path = (
            name_from_path is not None
            and name_from_path not in ShelfManager().shelf_names
        )

        context = {
            ShelfProcessors.known_name_from_path.__name__: is_known_name_from_path,
            ShelfProcessors.known_name_from_tag_and_manual.__name__: is_known_name_from_tag_and_manual,
            ShelfProcessors.known_name_from_tag.__name__: is_known_name_from_tag,
            ShelfProcessors.unknown_name_from_tag.__name__: is_unknown_name_from_tag,
            ShelfProcessors.unknown_name_from_path.__name__: is_unknown_name_from_path,
        }

        for strategy in ShelfProcessors.strategies:
            if strategy(
                album_id=album_id,
                file=file,
                track=track,
                name_from_path=name_from_path,
                name_from_tag=name_from_tag,
                context=context,
            ):
                break

    @staticmethod
    def file_post_save_processor(file: Any) -> None:
        """
        Process a file after it has been saved.
        :param file:
        :return:
        """
        try:
            log.debug("Processing file: %s", file.filename)
            album_id = file.metadata.get(constants.MUSICBRAINZ_ALBUMID)
            if album_id:
                ShelfManager().clear_album(album_id)
        except (KeyError, AttributeError, ValueError) as e:
            log.error("Error in file processor: %s", e)
            log.error("Traceback: %s", traceback.format_exc())

    @staticmethod
    def file_post_load_processor(file: Any) -> None:
        """
        Process a file after Picard has scanned it.
        """
        ShelfProcessors.file_post_addition_to_track_processor(file=file, track=None)

    @staticmethod
    def set_shelf_in_metadata(
        _album: Any,
        metadata: Dict[str, Any],
        _track: Any,
        _release: Any,
    ) -> None:
        """
        Set a shelf_name in track metadata from album assignment.
        """
        album_id = metadata.get(constants.MUSICBRAINZ_ALBUMID)
        if not album_id:
            return

        shelf_name, source = ShelfManager().get_album_shelf(album_id=album_id)
        if shelf_name is not None:
            log.debug(
                "Setting shelf_name '%s' on track from source '%s'",
                shelf_name,
                source,
            )
            if source == constants.SHELF_SOURCE_MANUAL:
                metadata[constants.TAG_KEY] = (
                    f"{shelf_name}{constants.MANUAL_SHELF_SUFFIX}"
                )
            else:
                metadata[constants.TAG_KEY] = shelf_name

    @staticmethod
    def known_name_from_path(
        album_id, file, track, name_from_path, name_from_tag, context
    ) -> bool:
        if not context[inspect.currentframe().f_code.co_name]:
            return False
        shelf_name = name_from_path
        ShelfProcessors._set_metadata(
            file if file else track,
            constants.TAG_KEY,
            shelf_name,
            "file" if file else "track",
        )
        ShelfManager().set_album_shelf(
            album_id=album_id, shelf_name=shelf_name, lock=True
        )
        return True

    @staticmethod
    def known_name_from_tag_and_manual(
        album_id, file, track, name_from_path, name_from_tag, context
    ) -> bool:
        if not context[inspect.currentframe().f_code.co_name]:
            return False
        shelf_name = name_from_tag
        ShelfProcessors._set_metadata(
            file if file else track,
            constants.TAG_KEY,
            shelf_name,
            "file" if file else "track",
        )
        ShelfManager().set_album_shelf(
            album_id=album_id, shelf_name=shelf_name, lock=True
        )
        return True

    @staticmethod
    def known_name_from_tag(
        album_id, file, track, name_from_path, name_from_tag, context
    ) -> bool:
        if not context[inspect.currentframe().f_code.co_name]:
            return False
        shelf_name = name_from_tag
        ShelfProcessors._set_metadata(
            file if file else track,
            constants.TAG_KEY,
            shelf_name,
            "file" if file else "track",
        )
        ShelfManager().set_album_shelf(
            album_id=album_id, shelf_name=shelf_name, lock=True
        )
        return True

    @staticmethod
    def unknown_name_from_tag(
        album_id, file, track, name_from_path, name_from_tag, context
    ) -> bool:
        if not context[inspect.currentframe().f_code.co_name]:
            return False
        shelf_name = name_from_path
        ShelfProcessors._set_metadata(
            file if file else track,
            constants.TAG_KEY,
            shelf_name,
            "file" if file else "track",
        )
        ShelfManager().vote_for_shelf(
            album_id=album_id,
            shelf_name=shelf_name,
        )
        return True

    @staticmethod
    def unknown_name_from_path(
        album_id, file, track, name_from_path, name_from_tag, context
    ) -> bool:
        if not context[inspect.currentframe().f_code.co_name]:
            return False
        shelf_name = name_from_path
        ShelfProcessors._set_metadata(
            file if file else track,
            constants.TAG_KEY,
            shelf_name,
            "file" if file else "track",
        )
        ShelfManager().vote_for_shelf(
            album_id=album_id,
            shelf_name=shelf_name,
        )
        return True


ShelfProcessors.strategies = [
    ShelfProcessors.known_name_from_path,
    ShelfProcessors.known_name_from_tag_and_manual,
    ShelfProcessors.known_name_from_tag,
    ShelfProcessors.unknown_name_from_tag,
    ShelfProcessors.unknown_name_from_path,
]
