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

import os
from tempfile import gettempdir

from bzrlib.tests import TestCase
from bzrlib.plugins.gtk.olive import Preferences

# FIXME: need to make sure that this also tests writing/reading.
class TestPreferences(TestCase):
    def test_create(self):
        Preferences(gettempdir() + os.sep + 'bzrgtktest.conf')

    def test_add_bookmark(self):
        """make sure a bookmark can be added. This function is only supposed 
        to store the location, not try to access it. """
        x = Preferences(gettempdir() + os.sep + 'bzrgtktest_add_bookmark.conf')
        self.assertTrue(x.add_bookmark("file://foobar"))
        self.assertTrue("file://foobar" in x.get_bookmarks())

    def test_add_bookmark_twice(self):
        """Adding an already present bookmark will result in False being 
        returned."""
        x = Preferences(gettempdir() + os.sep + 'bzrgtktest_add_bookmark_twice.conf')
        self.assertTrue(x.add_bookmark("file://foobar"))
        self.assertFalse(x.add_bookmark("file://foobar"))

    def test_set_bookmark_title(self):
        """Test setting a title for an existing bookmark."""
        x = Preferences(gettempdir() + os.sep + 'bzrgtktest_set_bookmark_title.conf')
        x.add_bookmark("file://foobar")
        x.set_bookmark_title("file://foobar", "My Bookmark")

    def test_remove_bookmark(self):
        """Test removing a bookmark."""
        x = Preferences(gettempdir() + os.sep + 'bzrgtktest_remove_bookmark.conf')
        x.add_bookmark("http://example.com/branch")
        x.remove_bookmark("http://example.com/branch")
        self.assertFalse("http://example.com/branch" in x.get_bookmarks())

    def test_get_bookmarks_empty(self):
        """Test whether a new Preferences() object has an empty bookmarks 
        list."""
        x = Preferences(gettempdir() + os.sep + 'bzrgtktest_get_bookmarks_empty.conf')
        self.assertEqual([], x.get_bookmarks())

    def test_get_bookmark_title_set(self):
        """Test getting a title for an existing bookmark."""
        x = Preferences(gettempdir() + os.sep + 'bzrgtktest_get_bookmark_title_set.conf')
        x.add_bookmark("file://foobar")
        x.set_bookmark_title("file://foobar", "My Bookmark")
        self.assertEqual("My Bookmark", x.get_bookmark_title("file://foobar"))

    def test_get_bookmark_title_implicit(self):
        """Test getting a bookmark title for a bookmark that doesn't
        have a title set."""
        x = Preferences(gettempdir() + os.sep + 'bzrgtktest_get_bookmark_title_implicit.conf')
        x.add_bookmark("file://bla")
        self.assertEqual("file://bla", x.get_bookmark_title("file://bla"))

    def test_set_preference(self):
        """Check whether setting preferences works."""
        x = Preferences(gettempdir() + os.sep + 'bzrgtktest_set_preference.conf')
        x.set_preference("foo", True)
        x.set_preference("foo", False)
        x.set_preference("foo", "bloe")

    def test_get_preference_bool(self):
        """Check whether a preference can be retrieved."""
        x = Preferences(gettempdir() + os.sep + 'bzrgtktest_get_preference_bool.conf')
        x.set_preference("foo", True)
        self.assertEqual(True, x.get_preference("foo", "bool"))

    def test_get_preference_str(self):
        """Check whether a string preference can be retrieved."""
        x = Preferences(gettempdir() + os.sep + 'bzrgtktest_get_preference_str.conf')
        x.set_preference("bla", "bloe")
        self.assertEqual("bloe", x.get_preference("bla"))

    def test_get_preference_nonexistant(self):
        """Check whether get_preference returns None for nonexisting 
        options."""
        x = Preferences(gettempdir() + os.sep + 'bzrgtktest_get_preference_nonexistant.conf')
        self.assertEqual(None, x.get_preference("foo"))

