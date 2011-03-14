# Copyright (C) 2008 Jelmer Vernooij <jelmer@samba.org>
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

"""Test the linegraph functionality."""

from bzrlib import (
    graph,
    tests,
    )

from bzrlib.plugins.gtk.branchview.linegraph import linegraph


class TestLinegraph(tests.TestCase):

    def get_graph(self, dict):
        return graph.Graph(graph.DictParentsProvider(dict))

    def test_simple(self):
        lg = linegraph(self.get_graph({"A": ("B", "C"), "B": ()}), ["A"])
        self.assertEquals(lg,
            ([
               ['A', (0, 0), [(0, 0, 0)], ['B'], [], (2,)],
               ['B', (0, 0), [], (), ['A'], (1,)]
             ],
             {'A': 0, 'B': 1},
             1))

