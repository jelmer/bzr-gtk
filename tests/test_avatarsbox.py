# Copyright (C) 2011 Curtis Hovey <sinzui.is@verizon.net>
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

"""Test the AvatarsBox functionality."""

from bzrlib import (
    tests,
    )

from bzrlib.plugins.gtk.avatarsbox import Avatar


class TestAvatar(tests.TestCase):

    def test__init(self):
        apparent_username = 'Random J User <randomjuser@eg.dom>'
        avatar = Avatar(apparent_username)
        self.assertEqual(apparent_username, avatar.apparent_username)
        self.assertEqual('Random J User', avatar.username)
        self.assertEqual('randomjuser@eg.dom', avatar.email)
        self.assertEqual(None, avatar.image)

    def test_eq_true(self):
        apparent_username = 'Random J User <randomjuser@eg.dom>'
        avatar_1 = Avatar(apparent_username)
        avatar_2 = Avatar(apparent_username)
        self.assertTrue(avatar_1 == avatar_2)

    def test_eq_false(self):
        apparent_username = 'Random J User <randomjuser@eg.dom>'
        avatar_1 = Avatar(apparent_username)
        avatar_2 = Avatar(apparent_username)
        avatar_2.username = 'changed'
        self.assertFalse(avatar_1 == avatar_2)
