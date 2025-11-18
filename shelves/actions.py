# -*- coding: utf-8 -*-

"""
Context menu actions for the Shelves plugin.
"""

from __future__ import annotations

from typing import Any, List

from PyQt5 import QtWidgets
from picard import log
from picard.ui.itemviews import BaseAction

from . import PLUGIN_NAME
from . import clear_album, vote_for_shelf
from .constants import ShelfConstants
from .utils import ShelfUtils

class SetShelfAction(BaseAction):
    """
    Context menu action: Set shelf name.
    """

    NAME = "Set shelf name..."

    # Type hint for the tagger attribute from BaseAction
    tagger: Any

    def __init__(self) -> None:
        """
        Initialize the action.
        """
        super().__init__()

    def callback(self, objs: List[Any]) -> None:
        """
        Handle the action callback.

        Args:
            objs: Selected objects in Picard
        """
        log.debug("%s: SetShelfAction called with %d objects", PLUGIN_NAME, len(objs))

        known_shelves = ShelfUtils.get_known_shelves()

        dialog = QtWidgets.QInputDialog(self.tagger.window)
        dialog.setWindowTitle("Set Shelf Name")
        dialog.setLabelText("Select or enter shelf name:")
        dialog.setComboBoxItems(known_shelves)
        dialog.setComboBoxEditable(True)
        dialog.setOption(QtWidgets.QInputDialog.UseListViewForComboBoxItems, True)

        layout = dialog.layout()
        validation_label = QtWidgets.QLabel("")
        validation_label.setStyleSheet("QLabel { color: orange; }")
        if layout:
            layout.addWidget(validation_label)

        def on_text_changed(text: str) -> None:
            """Update validation label when text changes."""
            valid, msg = ShelfUtils.validate_shelf_name(text)
            if msg:
                validation_label.setText(msg)
                style = (
                    "QLabel { color: red; }"
                    if not valid
                    else "QLabel { color: orange; }"
                )
                validation_label.setStyleSheet(style)
            else:
                validation_label.setText("")

        combo = dialog.findChild(QtWidgets.QComboBox)
        if combo:
            combo.currentTextChanged.connect(on_text_changed)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            shelf_name = dialog.textValue().strip()

            if not shelf_name:
                return

            is_valid, message = ShelfUtils.validate_shelf_name(shelf_name)
            if not is_valid:
                QtWidgets.QMessageBox.warning(
                    self.tagger.window,
                    "Invalid Shelf Name",
                    f"Cannot use this shelf name: {message}",
                )
                return

            for obj in objs:
                self._set_shelf_recursive(obj, shelf_name)

            ShelfUtils.add_known_shelf(shelf_name)
            log.info(
                "%s: Set shelf to '%s' for %d object(s)",
                PLUGIN_NAME,
                shelf_name,
                len(objs),
            )

    @staticmethod
    def _set_shelf_recursive(obj: Any, shelf_name: str) -> None:
        """
        Set the shelf name recursively on all files in an object.

        Args:
            obj: Picard object (album, track, etc.)
            shelf_name: Shelf name to set
        """
        if hasattr(obj, "metadata"):
            obj.metadata[ShelfConstants.TAG_KEY] = shelf_name
            log.debug(
                "%s: Set shelf '%s' on %s",
                PLUGIN_NAME,
                shelf_name,
                type(obj).__name__,
            )

        if hasattr(obj, "iterfiles"):
            for file in obj.iterfiles():
                file.metadata[ShelfConstants.TAG_KEY] = shelf_name


class DetermineShelfAction(BaseAction):
    """
    Context menu action: Determine shelf from storage location.
    """

    NAME = "Determine shelf"

    # Type hint for the tagger attribute from BaseAction
    tagger: Any

    def __init__(self) -> None:
        """Initialize the action."""
        super().__init__()

    def callback(self, objs: List[Any]) -> None:
        """
        Handle the action callback.

        Args:
            objs: Selected objects in Picard
        """
        log.debug(
            "%s: DetermineShelfAction called with %d objects", PLUGIN_NAME, len(objs)
        )

        # Track albums that need reinitialization
        albums_to_reinitialize = set()

        # Process each object
        for obj in objs:
            self._determine_shelf_recursive(obj, albums_to_reinitialize)

        # Reinitialize album data in shelf manager
        for album_id in albums_to_reinitialize:
            clear_album(album_id)

        # Re-vote for shelves based on file paths
        for obj in objs:
            self._revote_shelf_recursive(obj)

        log.info(
            "%s: Determined shelf for %d object(s), reinitialized %d album(s)",
            PLUGIN_NAME,
            len(objs),
            len(albums_to_reinitialize),
        )

    @staticmethod
    def _determine_shelf_recursive(obj: Any, albums_to_reinitialize: set) -> None:
        """
        Determine the shelf name from file paths recursively.

        Args:
            obj: Picard object (album, track, etc.)
            albums_to_reinitialize: Set to track albums that need reinitialization
        """
        unique_shelves = set()
        first_shelf = None

        known_shelves = ShelfUtils.get_known_shelves()
        if hasattr(obj, "iterfiles"):
            for file in obj.iterfiles():
                # Determine shelf from file path
                shelf_name = ShelfUtils.get_shelf_from_path(path=file.filename, known_shelves=known_shelves)

                # Update metadata
                file.metadata[ShelfConstants.TAG_KEY] = shelf_name
                unique_shelves.add(shelf_name)

                # Store first shelf for object metadata
                if first_shelf is None:
                    first_shelf = shelf_name

                # Track album for reinitialization
                album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)
                if album_id:
                    albums_to_reinitialize.add(album_id)

                log.debug(
                    "%s: Determined shelf '%s' for file: %s",
                    PLUGIN_NAME,
                    shelf_name,
                    file.filename,
                )

        # Add all unique shelves to known shelves
        for shelf_name in unique_shelves:
            ShelfUtils.add_known_shelf(shelf_name)

        # Update object metadata if present
        # Note: Using first file's shelf; ShelfManager voting will resolve conflicts
        if hasattr(obj, "metadata") and first_shelf:
            log.debug("%s: Update object metadata with %s", PLUGIN_NAME, first_shelf)
            obj.metadata[ShelfConstants.TAG_KEY] = first_shelf

    @staticmethod
    def _revote_shelf_recursive(obj: Any) -> None:
        """
        Re-vote for shelf assignments in the shelf manager.

        Args:
            obj: Picard object (album, track, etc.)
        """
        if hasattr(obj, "iterfiles"):
            for file in obj.iterfiles():
                shelf_name = file.metadata.get(ShelfConstants.TAG_KEY)
                album_id = file.metadata.get(ShelfConstants.MUSICBRAINZ_ALBUMID)

                if shelf_name and album_id:
                    vote_for_shelf(album_id, shelf_name)
                    log.debug(
                        "%s: Re-voted shelf '%s' for album %s",
                        PLUGIN_NAME,
                        shelf_name,
                        album_id,
                    )
