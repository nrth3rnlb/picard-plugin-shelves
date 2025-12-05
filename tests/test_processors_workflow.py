from picard import config

from shelves.constants import ShelfConstants
from shelves.processors import _apply_workflow_transition


def test_enabled_workflow_with_none_and_empty(monkeypatch):
    monkeypatch.setattr(
        config,
        "setting",
        {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY: "inbox",
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY: "done",
        },
        raising=False,
    )
    assert _apply_workflow_transition("") == ""


def test_disabled_workflow_returns_empty(monkeypatch):
    monkeypatch.setattr(config, "setting", {}, raising=False)
    assert _apply_workflow_transition("") == ""


def test_no_workflow_keys_leaves_shelf(monkeypatch):
    monkeypatch.setattr(config, "setting", {}, raising=False)
    assert _apply_workflow_transition("inbox") == "inbox"


def test_stage1_match_transitions(monkeypatch):
    monkeypatch.setattr(
        config,
        "setting",
        {
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY: "inbox",
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY: "shelf",
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
        },
        raising=False,
    )
    assert _apply_workflow_transition("inbox") == "shelf"
    assert _apply_workflow_transition("other") == "other"


def test_wildcard_stage1_transitions(monkeypatch):
    monkeypatch.setattr(
        config,
        "setting",
        {
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY: ShelfConstants.WORKFLOW_STAGE_1_WILDCARD,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY: "done",
        },
        raising=False,
    )
    # stages present => workflow is considered enabled by fallback; wildcard should match anything
    assert _apply_workflow_transition("anything") == "done"


def test_missing_stage_keys_with_enabled_true_leaves_shelf(monkeypatch):
    monkeypatch.setattr(
        config,
        "setting",
        {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            ShelfConstants.CONFIG_WORKFLOW_STAGE_1_KEY: "inbox",
            # stage 2 missing
        },
        raising=False,
    )
    # stage2 missing while enabled -> should leave the shelf unchanged
    assert _apply_workflow_transition("inbox") == "inbox"


def test_missing_stage1_with_enabled_true_leaves_shelf(monkeypatch):
    monkeypatch.setattr(
        config,
        "setting",
        {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            # stage1 missing
            ShelfConstants.CONFIG_WORKFLOW_STAGE_2_KEY: "done",
        },
        raising=False,
    )
    # stage1 missing while enabled -> should leave the shelf unchanged
    assert _apply_workflow_transition("inbox") == "inbox"


def test_both_stages_missing_with_enabled_true_leaves_shelf(monkeypatch):
    monkeypatch.setattr(
        config,
        "setting",
        {
            ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
            # both stage1 and stage2 missing
        },
        raising=False,
    )
    # no stages present while enabled -> should leave the shelf unchanged
    assert _apply_workflow_transition("inbox") == "inbox"
