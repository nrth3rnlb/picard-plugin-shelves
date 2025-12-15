import unittest
from unittest.mock import patch, MagicMock

from shelves.constants import ShelfConstants
from shelves.script_functions import func_shelf


class AttrDict(dict):
    """A dictionary that allows attribute-style access."""

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

class ScriptFunctionsTest(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        pass


    def test_func_shelf_returns_empty_for_non_string_tag(self):
        parser = MagicMock()
        parser.context = {ShelfConstants.TAG_KEY: None}

        result = func_shelf(parser)
        self.assertEqual(result, "")

    def test_func_shelf_returns_empty_when_no_shelf_name(self):
        tag = "SomeTag"
        parser = MagicMock()
        parser.context = {ShelfConstants.TAG_KEY: tag}

        with patch("shelves.script_functions.ShelfUtils.get_shelf_name_from_tag", return_value=""):
            result = func_shelf(parser)
            self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
