""" """

from picard.album import Album, File, Track
from picard.metadata import Metadata

from shelves.actions import ShelfActionToggleLock, _set_album_metadata, ShelfActionSet, ShelfActionUnset
from shelves.commands import ShelfCommands
from shelves.manager import ShelfManager
from shelves.typings import ShelfName, TagKey


def test_set_album_metadata_applies_same_shelf_to_all_files(mocker):
    # Arrange
    album_id = "019c60c2-2ee0-742e-bb7a-692060c8b192"
    shelf_name = ShelfName("ShelfA")
    shelf_locked = True

    manager = mocker.MagicMock(spec_set=ShelfManager)
    manager.get_shelf_name.return_value = shelf_name
    manager.is_locked.return_value = shelf_locked
    mocker.patch(
        "shelves.actions.runtime.manager_instance", return_value=manager, autospec=True
    )

    file_1 = mocker.MagicMock(spec=File)
    file_1.metadata = Metadata()
    file_1.metadata[TagKey.SHELF] = "OldShelfA"
    file_1.metadata[TagKey.SHELF_LOCKED] = False

    file_2 = mocker.MagicMock(spec=File)
    file_2.metadata = Metadata()
    file_2.metadata[TagKey.SHELF] = "OldShelfB"
    file_2.metadata[TagKey.SHELF_LOCKED] = False

    track_1 = mocker.MagicMock(spec=Track)
    track_1.files = [file_1]

    track_2 = mocker.MagicMock(spec=Track)
    track_2.files = [file_2]

    album = mocker.MagicMock(spec=Album)
    album.metadata = {
        TagKey.MUSICBRAINZ_ALBUM_ID: album_id,
    }
    album.tracks = [track_1, track_2]

    # Act
    _set_album_metadata([album])

    # Assert
    assert file_1.metadata[TagKey.SHELF] == shelf_name
    assert file_1.metadata[TagKey.SHELF_LOCKED]

    assert file_2.metadata[TagKey.SHELF] == shelf_name
    assert file_2.metadata[TagKey.SHELF_LOCKED]

    manager.get_shelf_name.assert_called_once_with(album_id)
    manager.is_locked.assert_called_once_with(album_id)

    file_1.update.assert_called_once_with()
    file_2.update.assert_called_once_with()
    track_1.update.assert_called_once_with()
    track_2.update.assert_called_once_with()
    album.update.assert_called_once_with()

def test_shelf_action_unset(mocker):
    album_id = "019c60c2-2ee0-742e-bb7a-692060c8b192"
    shelf_name = ShelfName("ShelfA")
    shelf_locked = True
    manager = mocker.MagicMock(spec_set=ShelfManager)
    manager.get_shelf_name.return_value = shelf_name
    manager.is_locked.return_value = shelf_locked
    mocker.patch(
        "shelves.actions.runtime.manager_instance", return_value=manager, autospec=True
    )
    commands = mocker.MagicMock(spec=ShelfCommands)
    mocker.patch(
        "shelves.actions.runtime.command_instance",
        return_value=commands,
    )
    set_album_metadata = mocker.patch("shelves.actions._set_album_metadata")

    file_1 = mocker.MagicMock(spec=File)
    file_1.metadata = {
        TagKey.SHELF_LOCKED: False,
    }

    track_1 = mocker.MagicMock(spec=Track)
    track_1.files = [file_1]

    album = mocker.MagicMock(spec=Album)
    album.metadata = {
        TagKey.MUSICBRAINZ_ALBUM_ID: album_id,
    }
    album.tracks = [track_1]

    # Act
    ShelfActionUnset().callback([album])

    # Assert
    commands.unset_album_shelf.assert_called_once_with(album_id=album_id)
    set_album_metadata.assert_called_once_with([album])

def test_shelf_action_set(mocker):
    album_id = "019c60c2-2ee0-742e-bb7a-692060c8b192"
    shelf_name = ShelfName("ShelfA")
    shelf_locked = True
    manager = mocker.MagicMock(spec_set=ShelfManager)
    manager.get_shelf_name.return_value = shelf_name
    manager.is_locked.return_value = shelf_locked
    mocker.patch(
        "shelves.actions.runtime.manager_instance", return_value=manager, autospec=True
    )
    commands = mocker.MagicMock(spec=ShelfCommands)
    mocker.patch(
        "shelves.actions.runtime.command_instance",
        return_value=commands,
    )
    set_album_metadata = mocker.patch("shelves.actions._set_album_metadata")
    ask_for_name = mocker.patch("shelves.actions._ask_for_name", return_value=shelf_name)

    file_1 = mocker.MagicMock(spec=File)
    file_1.metadata = {
        TagKey.SHELF_LOCKED: False,
    }

    track_1 = mocker.MagicMock(spec=Track)
    track_1.files = [file_1]

    album = mocker.MagicMock(spec=Album)
    album.metadata = {
        TagKey.MUSICBRAINZ_ALBUM_ID: album_id,
    }
    album.tracks = [track_1]

    # Act
    ShelfActionSet().callback([album])

    # Assert
    commands.set_album_shelf.assert_called_once_with(album_id=album_id, shelf_name=shelf_name)
    set_album_metadata.assert_called_once_with([album])
    ask_for_name.assert_called_once()

def test_shelf_action_lock_locks_unlocked_file(mocker):
    # Arrange
    album_id = "019c60c2-2ee0-742e-bb7a-692060c8b192"
    shelf_name = ShelfName("ShelfA")
    shelf_locked = True
    manager = mocker.MagicMock(spec_set=ShelfManager)
    manager.get_shelf_name.return_value = shelf_name
    manager.is_locked.return_value = shelf_locked
    mocker.patch(
        "shelves.actions.runtime.manager_instance", return_value=manager, autospec=True
    )
    commands = mocker.MagicMock(spec=ShelfCommands)
    mocker.patch(
        "shelves.actions.runtime.command_instance",
        return_value=commands,
    )
    set_album_metadata = mocker.patch("shelves.actions._set_album_metadata")

    file_1 = mocker.MagicMock(spec=File)
    file_1.metadata = {
        TagKey.SHELF_LOCKED: False,
    }

    track_1 = mocker.MagicMock(spec=Track)
    track_1.files = [file_1]

    album = mocker.MagicMock(spec=Album)
    album.metadata = {
        TagKey.MUSICBRAINZ_ALBUM_ID: album_id,
    }
    album.tracks = [track_1]

    # Act
    ShelfActionToggleLock().callback([album])

    # Assert
    commands.toggle_album_shelf_lock.assert_called_once_with(album_id=album_id)
    set_album_metadata.assert_called_once_with([album])


def test_shelf_action_lock_unlocks_locked_file(mocker):
    # Arrange
    album_id = "019c60c2-2ee0-742e-bb7a-692060c8b192"
    shelf_name = ShelfName("ShelfA")
    shelf_locked = True
    manager = mocker.MagicMock(spec_set=ShelfManager)
    manager.get_shelf_name.return_value = shelf_name
    manager.is_locked.return_value = shelf_locked
    mocker.patch(
        "shelves.actions.runtime.manager_instance", return_value=manager, autospec=True
    )
    commands = mocker.MagicMock(spec=ShelfCommands)
    mocker.patch(
        "shelves.actions.runtime.command_instance",
        return_value=commands,
    )
    set_album_metadata = mocker.patch("shelves.actions._set_album_metadata")

    file_1 = mocker.MagicMock(spec=File)
    file_1.metadata = {
        TagKey.SHELF_LOCKED: True,
    }

    track_1 = mocker.MagicMock(spec=Track)
    track_1.files = [file_1]

    album = mocker.MagicMock(spec=Album)
    album.metadata = {
        TagKey.MUSICBRAINZ_ALBUM_ID: album_id,
    }
    album.tracks = [track_1]

    # Act
    ShelfActionToggleLock().callback([album])

    # Assert
    commands.toggle_album_shelf_lock.assert_called_once_with(album_id=album_id)
    set_album_metadata.assert_called_once_with([album])
