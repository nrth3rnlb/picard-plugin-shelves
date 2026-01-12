# -*- coding: utf-8 -*-

"""
Tests for the processors module.
"""

import unittest

from shelves import constants


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
                constants.CONFIG_WORKFLOW_ENABLED_KEY: True,
                constants.CONFIG_WORKFLOW_STAGE_1_SHELVES_KEY: ["Incoming"],
                constants.CONFIG_WORKFLOW_STAGE_2_SHELVES_KEY: ["Standard"],
                constants.CONFIG_MOVE_FILES_TO_KEY: "/music",
            }
        }


if __name__ == "__main__":
    unittest.main()
