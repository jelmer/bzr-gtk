# -*- coding: utf-8 -*-
# Copyright (C) 2007 Adeodato Simó <dato@net.com.org.es>
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

from cStringIO import StringIO

from bzrlib import tests

from bzrlib.plugins.gtk.diff import DiffView


class TestDiffView(tests.TestCase):

    def test_parse_colordiffrc(self):
        colordiffrc = '''\
newtext=blue
oldtext = Red
# now a comment and a blank line

diffstuff = #ffff00  
  # another comment preceded by whitespace
'''
        colors = {
                'newtext': 'blue',
                'oldtext': 'Red',
                'diffstuff': '#ffff00',
        }
        parsed_colors = DiffView.parse_colordiffrc(StringIO(colordiffrc))
        self.assertEqual(colors, parsed_colors)
