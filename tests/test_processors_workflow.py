from picard import config

from shelves.constants import ShelfConstants
from shelves.processors import _apply_workflow_transition


def test_empty_shelf_is_not_transitioned(monkeypatch):
    """Test that an empty shelf value is never transitioned."""
    monkeypatch.setattr(
        config,
        "settings",
        {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["inbox"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["done"],
        },
        raising=False,
    )
    assert _apply_workflow_transition("") == ""


def test_disabled_workflow_returns_same_shelf(monkeypatch):
    """Test that a disabled workflow never transitions the shelf."""
    monkeypatch.setattr(
        config,
        "settings",
        {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: False,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["inbox"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["done"],
        },
        raising=False,
    )
    assert _apply_workflow_transition("inbox") == "inbox"


def test_no_workflow_keys_leaves_shelf(monkeypatch):
    """Test that missing config keys prevent transition."""
    monkeypatch.setattr(config, "settings", {}, raising=False)
    assert _apply_workflow_transition("inbox") == "inbox"


def test_stage1_match_transitions(monkeypatch):
    """Test that a matching shelf in stage 1 is correctly transitioned."""
    monkeypatch.setattr(
        config,
        "settings",
        {
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["inbox", "unsorted"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["shelf"],
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
        },
        raising=False,
    )
    assert _apply_workflow_transition("inbox") == "shelf"
    assert _apply_workflow_transition("unsorted") == "shelf"


def test_no_match_in_stage1_leaves_shelf(monkeypatch):
    """Test that a shelf not in stage 1 is not transitioned."""
    monkeypatch.setattr(
        config,
        "settings",
        {
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["inbox"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["done"],
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
        },
        raising=False,
    )
    assert _apply_workflow_transition("other_shelf") == "other_shelf"


def test_wildcard_in_stage1_transitions_any_shelf(monkeypatch):
    """Test that the wildcard in stage 1 transitions any shelf."""
    monkeypatch.setattr(
        config,
        "settings",
        {
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: [ShelfConstants.WORKFLOW_STAGE_1_WILDCARD],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["default"],
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
        },
        raising=False,
    )
    assert _apply_workflow_transition("any_shelf") == "default"
    assert _apply_workflow_transition("another_shelf") == "default"


def test_transition_to_same_shelf_does_nothing(monkeypatch):
    """Test that transitioning to the same shelf does not change the value."""
    monkeypatch.setattr(
        config,
        "settings",
        {
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["inbox"],
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["inbox"],
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
        },
        raising=False,
    )
    assert _apply_workflow_transition("inbox") == "inbox"


def test_missing_stage_keys_with_enabled_true_leaves_shelf(monkeypatch):
    """Test that missing stage keys with workflow enabled leaves the shelf unchanged."""
    monkeypatch.setattr(
        config,
        "settings",
        {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["inbox"],
            # stage 2 missing
        },
        raising=False,
    )
    assert _apply_workflow_transition("inbox") == "inbox"
