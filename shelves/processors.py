# -*- coding: utf-8 -*-

"""
File processors for loading and saving shelf_name information.
"""

from __future__ import annotations

import traceback
from os import name
from typing import Any, Dict, Optional

from picard import config, log

from .constants import ShelfConstants
from .manager import ShelfManager
from .utils import ShelfUtils


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
    def _apply_workflow_transition(shelf: Optional[str]) -> Optional[str]:
        """
        Applies the workflow transition to a shelf_name name if the workflow is enabled.
        """
        if not shelf:
            return shelf

        try:
            if not config.setting[ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY]:  # type: ignore
                return shelf

            workflow_stage_1 = config.setting[
                ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY  # type: ignore
            ]
            workflow_stage_2 = config.setting[
                ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY  # type: ignore
            ]
            stage_1_includes_non_shelves = config.setting[
                ShelfConstants.CONFIG_STAGE_1_INCLUDES_NON_SHELVES_KEY  # type: ignore
            ]

            # Check for known shelf_names wildcard or direct match
            apply_transition = shelf in workflow_stage_1 or stage_1_includes_non_shelves

            if apply_transition and workflow_stage_2:
                destination_shelf = workflow_stage_2[0]
                # Avoid transitioning to the same shelf_name
                if shelf != destination_shelf:
                    log.debug(
                        "Applying workflow transition: '%s' -> '%s'",
                        shelf,
                        destination_shelf,
                    )
                    return destination_shelf
        except KeyError as e:
            log.debug(
                "Workflow configuration key not found (%s), skipping transition.",
                e,
            )
        except (AttributeError, ValueError) as e:
            log.debug("Failed to evaluate workflow transition: %s", e)
            log.debug("Traceback: %s", traceback.format_exc())

        return shelf

    @staticmethod
    def file_post_removal_from_track_processor(_track: Any, file: Any) -> None:
        """
        Process a file after it has been removed from a track.
        """
        log.debug(
            "(file_post_removal_from_track_processor) Processing file: %s",
            file.filename,
        )
        album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
        if album_id:
            ShelfManager.clear_album(album_id)

    @staticmethod
    def file_post_addition_to_track_processor(track: Optional[Any], file: Any) -> None:
        """
        Process a file after it has been added to a track, with a destroy priority model.
        """
        shelf_name: Optional[str] = None

        try:
            file_meta = getattr(file, "metadata", None)
            if not file_meta:
                return
            album_id = file_meta.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
            if not album_id:
                return

            name_from_path = ShelfUtils.get_shelf_name_from_path(
                file_path=file, base_path=ShelfManager().base_path
            )
            name_from_tag = file_meta.get(ShelfConstants.TAG_KEY, "")

            is_known_name_from_path = (
                name_from_path and name_from_path in ShelfManager().shelf_names
            )
            is_known_name_from_tag_and_manual = (
                name_from_tag
                and name_from_tag in ShelfManager().shelf_names
                and ShelfConstants.MANUAL_SHELF_SUFFIX in name_from_tag
            )
            is_known_name_from_tag = (
                name_from_tag and name_from_tag in ShelfManager().shelf_names
            )
            is_unknown_name_from_tag = (
                name_from_tag and name_from_tag not in ShelfManager().shelf_names
            )
            is_unknown_name_from_path = (
                name_from_path is not None
                and name_from_path not in ShelfManager().shelf_names
            )

            priority_1 = is_known_name_from_path
            priority_2 = is_known_name_from_tag_and_manual
            priority_3 = is_known_name_from_tag
            priority_4 = is_unknown_name_from_tag
            priority_5 = is_unknown_name_from_path

            if priority_1:
                shelf_name = name_from_path
            elif priority_2:
                shelf_name = name_from_tag
            elif priority_3:
                shelf_name = name_from_tag
            elif priority_4 or priority_5:
                shelf_name = name_from_path

            # Set metadata and update manager _shelf_state
            if shelf_name is not None:
                shelf_name = ShelfProcessors._apply_workflow_transition(shelf_name)
                ShelfProcessors._set_metadata(
                    file,
                    ShelfConstants.TAG_KEY,
                    shelf_name,
                    "file",
                )
                if track:
                    ShelfProcessors._set_metadata(
                        track,
                        ShelfConstants.TAG_KEY,
                        shelf_name,
                        "track",
                    )

                # If the decision was based on a physical or persisted manual tag, lock it in.
                if priority_1 or priority_2 or priority_3:
                    ShelfManager().set_album_shelf(
                        album_id=album_id, shelf_name=shelf_name, lock=True
                    )

                ShelfManager().vote_for_shelf(
                    album_id=album_id,
                    shelf_name=shelf_name,
                )

        except (KeyError, AttributeError, ValueError) as e:
            log.error("Error in file processor: %s", e)
            log.error("Traceback: %s", traceback.format_exc())

    @staticmethod
    def file_post_save_processor(file: Any) -> None:
        """
        Process a file after it has been saved.
        :param file:
        :return:
        """
        try:
            log.debug("Processing file: %s", file.filename)
            album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
            if album_id:
                ShelfManager.clear_album(album_id)
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
        album_id = metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
        if not album_id:
            return

        shelf_name, source = ShelfManager.get_album_shelf(album_id=album_id)
        if shelf_name is not None:
            log.debug(
                "Setting shelf_name '%s' on track from source '%s'",
                shelf_name,
                source,
            )
            if source == ShelfConstants.SHELF_SOURCE_MANUAL:
                metadata[ShelfConstants.TAG_KEY] = (
                    f"{shelf_name}{ShelfConstants.MANUAL_SHELF_SUFFIX}"
                )
            else:
                metadata[ShelfConstants.TAG_KEY] = shelf_name
