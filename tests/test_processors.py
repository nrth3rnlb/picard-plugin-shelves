# -*- coding: utf-8 -*-

"""
Tests for the processors module.
"""

import unittest


class AttrDict(dict):
    """A dictionary that allows attribute-style access."""

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class ProcessorsTest(unittest.TestCase):
    """
    Tests for the file processors in the Shelves plugin.
    """

    def setUp(self):
        """Set up the test environment."""
        self.config = {
            "settings": {
                ConfigKey.WORKFLOW_ENABLED        : True,
                ConfigKey.WORKFLOW_STAGE_1_SHELVES: ["Incoming"],
                ConfigKey.WORKFLOW_STAGE_2_SHELVES: ["Standard"],
                ConfigKey.MOVE_FILES_TO           : "/music",
            }
        }


if __name__ == "__main__":
    unittest.main()
