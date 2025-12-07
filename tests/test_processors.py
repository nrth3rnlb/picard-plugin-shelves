# -*- coding: utf-8 -*-

"""
Tests for the processors module.
"""

import unittest

from shelves.constants import ShelfConstants


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
            "setting": {
                ShelfConstants.CONFIG_WORKFLOW_ENABLED_KEY: True,
                ShelfConstants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
                ShelfConstants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
                "move_files_to": "/music"
            }
        }


if __name__ == "__main__":
    unittest.main()
