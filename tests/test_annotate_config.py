# Copyright (C) 2009 Canonical Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Test the annotate configuration functionality."""

import os

from bzrlib import (
    tests,
    )

from bzrlib.plugins.gtk.annotate import (
    config,
    gannotate,
    )
from bzrlib.plugins.gtk.annotate.config import gannotate_config_filename


class TestConfig(tests.TestCaseInTempDir):

    def setUp(self):
        # Create an instance before the env is changed so that
        # icon lookups work.
        self.window = gannotate.GAnnotateWindow()
        super(TestConfig, self).setUp()

    def tearDown(self):
        self.window.destroy()
        super(TestConfig, self).tearDown()

    def test_create_initial_config(self):
        """We can create a config even without a prior conf file"""
        conf = config.GAnnotateConfig(self.window)
        # We can access the default values (we just pick a random one)
        width = conf['window']['width']
        # configobj presents attributes as strings only
        self.assertIsInstance(width, str)

    def test_write(self):
        """The window values are save"""
        conf = config.GAnnotateConfig(self.window)
        self.window.pane.set_position(200)
        self.assertIs(False, conf._write())
        self.assertEqual(200, conf['window']['pane_position'])
        self.assertIs(True, os.path.isfile(gannotate_config_filename()))
