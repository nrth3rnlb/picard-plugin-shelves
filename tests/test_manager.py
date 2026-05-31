"""
Tests for shelf assignment management.

This module contains tests for the `ShelfManager` class and related value
objects such as `ShelfName` and `AlbumId`. The tests cover explicit manager
settings, registered shelf names, and string-like behavior of shelf-related
identifier types.
"""

from pathlib import Path

import pytest

from shelves.manager import (
    ShelfManager,
    ShelfManagerSettings,
)
from shelves.typings import ShelfName, AlbumId


def make_test_manager() -> ShelfManager:
    return ShelfManager(
        settings=ShelfManagerSettings(
            base_path=Path("/music"),
            shelf_names={ShelfName("ShelfA"), ShelfName("ShelfB")},
        )
    )

def test_manager_set_name():
    manager = make_test_manager()
    album_id = AlbumId("019c60c2-2ee0-742e-bb7a-692060c8b192")
    manager.set_name(album_id, ShelfName("ShelfA"))

    assert manager.get_shelf_name(album_id) == ShelfName("ShelfA")

def test_manager_get_name():
    manager = make_test_manager()
    album_id = AlbumId("019c60c2-2ee0-742e-bb7a-692060c8b192")
    manager.set_name(album_id, ShelfName("ShelfA"))

    assert manager.get_shelf_name(album_id) == ShelfName("ShelfA")

def test_manager_set_name_and_lock():
    manager = make_test_manager()
    album_id = AlbumId("019c60c2-2ee0-742e-bb7a-692060c8b192")
    manager.set_name(album_id, ShelfName("ShelfA"), locked=True)

    assert manager.get_shelf_name(album_id) == ShelfName("ShelfA")
    assert manager.is_locked(album_id)

def test_set_name_fails_on_locked():
    manager = make_test_manager()
    album_id = AlbumId("019c60c2-2ee0-742e-bb7a-692060c8b192")
    manager.set_name(album_id, ShelfName("ShelfA"), locked=True)
    manager.set_name(album_id, ShelfName("ShelfB"))

    assert manager.get_shelf_name(album_id) == ShelfName("ShelfA")
    assert manager.is_locked(album_id)

def test_set_name_success_on_unlocked():
    manager = make_test_manager()
    album_id = AlbumId("019c60c2-2ee0-742e-bb7a-692060c8b192")
    manager.set_name(album_id, ShelfName("ShelfA"), locked=False)
    manager.set_name(album_id, ShelfName("ShelfB"), locked=False)

    assert manager.get_shelf_name(album_id) == ShelfName("ShelfB")
    assert not manager.is_locked(album_id)

def test_manager_unset_name():
    manager = make_test_manager()
    album_id = AlbumId("019c60c2-2ee0-742e-bb7a-692060c8b192")
    manager.set_name(album_id, ShelfName("ShelfA"))
    manager.unset_name(album_id)

    assert manager.get_shelf_name(album_id) == ShelfName()

def test_manager_unset_name_fails_on_locked():
    manager = make_test_manager()
    album_id = AlbumId("019c60c2-2ee0-742e-bb7a-692060c8b192")
    manager.set_name(album_id, ShelfName("ShelfA"), locked=True)
    manager.unset_name(album_id)

    assert manager.get_shelf_name(album_id) == ShelfName("ShelfA")
    assert manager.is_locked(album_id)

def test_manager_lock():
    manager = make_test_manager()
    album_id = AlbumId("019c60c2-2ee0-742e-bb7a-692060c8b192")
    manager.lock(album_id)

    assert manager.is_locked(album_id)

def test_manager_unlock():
    manager = make_test_manager()
    album_id = AlbumId("019c60c2-2ee0-742e-bb7a-692060c8b192")
    manager.lock(album_id)
    manager.unlock(album_id)

    assert not manager.is_locked(album_id)

def test_manager_uses_explicit_settings():
    manager = make_test_manager()

    assert manager.base_path == Path("/music")
    assert manager.registered_shelf_names == {
        ShelfName("ShelfA"),
        ShelfName("ShelfB"),
    }

def test_add_shelf_names():
    manager = make_test_manager()
    manager.add_shelf_names({ShelfName("ShelfC"), ShelfName("ShelfD")})
    assert manager.registered_shelf_names == {
        ShelfName("ShelfA"),
        ShelfName("ShelfB"),
        ShelfName("ShelfC"),
        ShelfName("ShelfD"),
    }

def test_remove_shelf_names():
    manager = make_test_manager()
    manager.remove_shelf_names({ShelfName("ShelfA"), ShelfName("ShelfB")})
    assert manager.registered_shelf_names == set()

def test_intersect_shelf_names():
    manager = make_test_manager()
    manager.intersect_shelf_names({ShelfName("ShelfB"), ShelfName("ShelfC")})
    assert manager.registered_shelf_names == {ShelfName("ShelfB")}

def test_album_id_behaves_like_string():
    album_id = AlbumId("019c60c2-2ee0-742e-bb7a-692060c8b192")

    assert album_id == "019c60c2-2ee0-742e-bb7a-692060c8b192"
    assert str(album_id) == "019c60c2-2ee0-742e-bb7a-692060c8b192"
    assert album_id in {"019c60c2-2ee0-742e-bb7a-692060c8b192"}


def test_shelf_name_behaves_like_string():
    shelf_name = ShelfName("ShelfA")

    assert shelf_name == "ShelfA"
    assert str(shelf_name) == "ShelfA"
    assert shelf_name in {"ShelfA", "ShelfB"}
    assert "ShelfA" in {shelf_name, ShelfName("ShelfB")}


def test_shelf_name_defaults_to_empty_string():
    assert ShelfName() == ""
    assert str(ShelfName()) == ""


def test_shelf_name_converts_none_to_empty_string():
    assert ShelfName(None) == ""

def test_album_id_converts_none_to_empty_string():
    assert AlbumId(None) == ""


def test_is_likely_shelf_name():
    manager = make_test_manager()
    assert manager.is_likely_shelf_name(ShelfName("ShelfA"))
    assert not manager.is_likely_shelf_name(ShelfName("Vol. 1"))
