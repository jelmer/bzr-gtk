# Copyright (C) 2007 Jelmer Vernooij <jelmer@samba.org>
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

from bzrlib.tests import TestCase, TestCaseInTempDir
from bzrlib.plugins.gtk.olive import Preferences

import os

# FIXME: need to make sure that this also tests writing/reading.
class TestPreferences(TestCaseInTempDir):
    def setUp(self):
        super(TestPreferences, self).setUp()
        self.prefs = Preferences(os.path.join(self.test_dir, 'prefs'))

    def test_create(self):
        Preferences()

    def test_add_bookmark(self):
        """make sure a bookmark can be added. This function is only supposed 
        to store the location, not try to access it. """
        self.assertTrue(self.prefs.add_bookmark("file://foobar"))
        self.assertTrue("file://foobar" in self.prefs.get_bookmarks())

    def test_add_bookmark_twice(self):
        """Adding an already present bookmark will result in False being 
        returned."""
        self.assertTrue(self.prefs.add_bookmark("file://foobar"))
        self.assertFalse(self.prefs.add_bookmark("file://foobar"))

    def test_set_bookmark_title(self):
        """Test setting a title for an existing bookmark."""
        self.prefs.add_bookmark("file://foobar")
        self.prefs.set_bookmark_title("file://foobar", "My Bookmark")

    def test_remove_bookmark(self):
        """Test removing a bookmark."""
        self.prefs.add_bookmark("http://example.com/branch")
        self.prefs.remove_bookmark("http://example.com/branch")
        self.assertFalse("http://example.com/branch" in self.prefs.get_bookmarks())

    def test_get_bookmarks_empty(self):
        """Test whether a new Preferences() object has an empty bookmarks 
        list."""
        self.assertEqual([], self.prefs.get_bookmarks())

    def test_get_bookmark_title_set(self):
        """Test getting a title for an existing bookmark."""
        self.prefs.add_bookmark("file://foobar")
        self.prefs.set_bookmark_title("file://foobar", "My Bookmark")
        self.assertEqual("My Bookmark", self.prefs.get_bookmark_title("file://foobar"))

    def test_get_bookmark_title_implicit(self):
        """Test getting a bookmark title for a bookmark that doesn't
        have a title set."""
        self.prefs.add_bookmark("file://bla")
        self.assertEqual("file://bla", self.prefs.get_bookmark_title("file://bla"))

    def test_set_preference(self):
        """Check whether setting preferences works."""
        self.prefs.set_preference("foo", True)
        self.prefs.set_preference("foo", False)
        self.prefs.set_preference("foo", "bloe")

    def test_get_preference_bool(self):
        """Check whether a preference can be retrieved."""
        self.prefs.set_preference("foo", True)
        self.assertEqual(True, self.prefs.get_preference("foo", "bool"))

    def test_get_preference_str(self):
        """Check whether a string preference can be retrieved."""
        self.prefs.set_preference("bla", "bloe")
        self.assertEqual("bloe", self.prefs.get_preference("bla"))

    def test_get_preference_nonexistant(self):
        """Check whether get_preference returns None for nonexisting 
        options."""
        self.assertEqual(None, self.prefs.get_preference("foo"))

