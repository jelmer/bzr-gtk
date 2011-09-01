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

from bzrlib import (
    tests,
    )

from bzrlib.plugins.gtk.annotate import (
    config,
    gannotate,
    )


class TestConfig(tests.TestCaseInTempDir):

    def setUp(self):
        # Create an instance before the env is changed so that
        # icon lookups work.
        self.window = gannotate.GAnnotateWindow()
        super(TestConfig, self).setUp()

    def test_create_initial_config(self):
        """We can create a config even without a prior conf file"""
        conf = config.GAnnotateConfig(self.window)
        # We can access the default values (we just pick a random one)
        width = conf['window']['width']
        # configobj presents attributes as strings only
        self.assertIsInstance(width, str)
