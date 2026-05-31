"""
Tests for script_functions.py.
"""

from unittest.mock import MagicMock

from picard.script import ScriptParser

from shelves.script_functions import func_shelf


def test_func_shelf(mocker):
    """"""
    # Arrange
    known_shelf = "ShelfA"

    parser = mocker.MagicMock(spec=ScriptParser)
    parser.context = mocker.MagicMock()
    parser.context.get.return_value = known_shelf

    # Act
    result = func_shelf(parser)

    # Assert
    expected = known_shelf
    invalid = f"Unknown{known_shelf}"
    assert invalid != result, f"Did not expect '{invalid}' but got it."
    assert expected == result, f"Expected '{expected}' but got '{result}'"
