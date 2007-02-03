# Copyright (C) 2007 Jelmer Venrooij <jelmer@samba.org>
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

from bzrlib.tests import TestCaseInTempDir
from bzrlib.plugins.gtk.history import UrlHistory

from bzrlib import config

class TestsUrlHistory(TestCaseInTempDir):
    def setUp(self):
        super(TestsUrlHistory, self).setUp()
        self.config = config.GlobalConfig()

    def test_add_entry(self):
        """Tests whether a URL can be added to the history list.
        The history store should only store the url, not try to
        access it."""
        self.history = UrlHistory(self.config, 'test_add_entry')
        self.history.add_entry("http://foobarbla")

    def test_get_entries(self):
        self.history = UrlHistory(self.config, 'test_get_entries')
        self.history.add_entry("http://foobar")
        self.history.add_entry("file://bla")
        self.assertEqual(["http://foobar", "file://bla"], self.history.get_entries())

    def test_get_empty(self):
        self.history = UrlHistory(self.config, 'test_get_empty')
        self.assertEqual([], self.history.get_entries())
