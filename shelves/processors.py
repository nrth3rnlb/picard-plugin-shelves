# -*- coding: utf-8 -*-

"""
File processors for loading and saving shelf information.
"""

from __future__ import annotations

import traceback
from typing import Any, Dict, Optional

from picard import config, log

from .constants import ShelfConstants
from .manager import ShelfManager
from .utils import ShelfUtils


class ShelfProcessors:

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
        Applies the workflow transition to a shelf name if the workflow is enabled.
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

            # Check for known shelves wildcard or direct match
            apply_transition = shelf in workflow_stage_1 or stage_1_includes_non_shelves

            if apply_transition and workflow_stage_2:
                destination_shelf = workflow_stage_2[0]
                # Avoid transitioning to the same shelf
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
        except Exception as e:
            log.debug("Failed to evaluate workflow transition: %s", e)
            log.debug("Traceback: %s", traceback.format_exc())

        return shelf

    @staticmethod
    def file_post_removal_from_track_processor(track: Any, file: Any) -> None:
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

    def file_post_addition_to_track_processor(
        self, track: Optional[Any], file: Any
    ) -> None:
        """
        Process a file after it has been added to a track, with a destroy priority model.
        """
        try:
            file_meta = getattr(file, "metadata", None)
            if file_meta is None:
                return

            shelf_name: Optional[str]
            shelf_tag: Optional[str]
            shelf_from_path: Optional[str]

            known_shelves = ShelfUtils.get_configured_shelves()
            shelf_from_path, was_explicitly_found = ShelfUtils.get_shelf_from_path(
                path=file.filename, known_shelves=known_shelves
            )
            existing_tag = file_meta.get(ShelfConstants.TAG_KEY, "")
            is_manual_in_tag = (
                isinstance(existing_tag, str)
                and ShelfConstants.MANUAL_SHELF_SUFFIX in existing_tag
            )

            # PRIORITY 1: Physical location
            if shelf_from_path and was_explicitly_found:
                shelf_name = shelf_from_path
                shelf_tag = shelf_name
                log.debug(
                    "Priority 1: Physical location in specific shelf '%s' wins.",
                    shelf_name,
                )

            # PRIORITY 2: Persistent manual tag
            elif is_manual_in_tag:
                shelf_name = ShelfUtils.get_shelf_name_from_tag(existing_tag)
                shelf_tag = existing_tag
                log.debug(
                    "Priority 2: Persisted manual tag '%s' wins.",
                    shelf_tag,
                )

            # PRIORITY 3: Standard logic
            else:
                shelf_name = self._apply_workflow_transition(shelf_from_path)
                shelf_tag = shelf_name
                log.debug(
                    "Priority 3: Default logic. Path shelf '%s', final shelf '%s'.",
                    shelf_from_path,
                    shelf_name,
                )

            # Set metadata and update manager _state
            if shelf_name:
                self._set_metadata(file, ShelfConstants.TAG_KEY, shelf_tag, "file")
                if track:
                    self._set_metadata(
                        track, ShelfConstants.TAG_KEY, shelf_tag, "track"
                    )

                ShelfUtils.add_known_shelf(shelf_name)

                album_id = file_meta.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
                if album_id:
                    # If the decision was based on a physical or persisted manual tag, _lock it in.
                    if was_explicitly_found or is_manual_in_tag:
                        ShelfManager.set_album_shelf(
                            album_id=album_id,
                            shelf=shelf_name,
                            source=ShelfConstants.SHELF_SOURCE_MANUAL,
                            lock=True,
                        )
                    else:
                        ShelfManager.vote_for_shelf(album_id=album_id, shelf=shelf_name)

                log.debug("Final shelf for %s is '%s'", file.filename, shelf_name)

        except Exception as e:
            log.error("Error in file processor: %s", e)
            log.error("Traceback: %s", traceback.format_exc())

    @staticmethod
    def file_post_save_processor(file: Any) -> None:
        """
        Process a file after Picard has saved it.
        """
        try:
            log.debug("Processing file: %s", file.filename)
            album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
            if album_id:
                ShelfManager.clear_album(album_id)
        except (KeyError, AttributeError, ValueError) as e:
            log.error("Error in file processor: %s", e)
            log.error("Traceback: %s", traceback.format_exc())

    def file_post_load_processor(self, file: Any) -> None:
        """
        Process a file after Picard has scanned it.
        """
        self.file_post_addition_to_track_processor(file=file, track=None)

    @staticmethod
    def set_shelf_in_metadata(
        _album: Any, metadata: Dict[str, Any], _track: Any, _release: Any
    ) -> None:
        """
        Set a shelf in track metadata from album assignment.
        """
        album_id = metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
        if not album_id:
            return

        shelf_name, source = ShelfManager.get_album_shelf(album_id=album_id)
        if shelf_name is not None:
            log.debug(
                "Setting shelf '%s' on track from source '%s'",
                shelf_name,
                source,
            )
            if source == ShelfConstants.SHELF_SOURCE_MANUAL:
                metadata[ShelfConstants.TAG_KEY] = (
                    f"{shelf_name}{ShelfConstants.MANUAL_SHELF_SUFFIX}"
                )
            else:
                metadata[ShelfConstants.TAG_KEY] = shelf_name
