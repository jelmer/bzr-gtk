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

"""Test the CellRendererGraph functionality."""

from gi.repository import Gtk

from bzrlib import (
    tests,
    )

from bzrlib.plugins.gtk.branchview.graphcell import CellRendererGraph


class CellRendererGraphTestCase(tests.TestCase):

    def test_columns_len(self):
        cell = CellRendererGraph()
        self.assertEqual(0, cell.columns_len)
        cell.columns_len = 1
        self.assertEqual(1, cell.columns_len)

    def test_props_writeonly(self):
        # Props can be set, but not read, though they can be accessed
        # as attributes
        cell = CellRendererGraph()
        cell.props.node = (1, 0)
        cell.props.tags = ['2.0']
        cell.props.in_lines = ((1, 2, 1.0))
        cell.props.out_lines = ((1, 3, 1.0))
        self.assertEqual((1, 0), cell.node)
        self.assertRaises(TypeError, cell.props, 'node')
        self.assertEqual(['2.0'], cell.tags)
        self.assertRaises(TypeError, cell.props, 'tags')
        self.assertEqual(((1, 2, 1.0)), cell.in_lines)
        self.assertRaises(TypeError, cell.props, 'in_lines')
        self.assertEqual(((1, 3, 1.0)), cell.out_lines)
        self.assertRaises(TypeError, cell.props, 'out_lines')

    def test_do_activate(self):
        # The cell cannot be activated. It returns True to indicate the
        # event is handled.
        cell = CellRendererGraph()
        self.assertEqual(
            True, cell.do_activate(None, None, None, None, None))

    def test_do_editing_started(self):
        # The cell cannot be edited. It returns None.
        cell = CellRendererGraph()
        self.assertEqual(
            None, cell.do_editing_started(None, None, None, None, None))

    def test_do_get_size(self):
        # The layout offset and size is based by cell.box_size(widget)
        # box_size is cached, and this can be set ensure a predictable result.
        cell = CellRendererGraph()
        cell.columns_len = 1
        cell._box_size = 21
        treeview = Gtk.TreeView()
        self.assertEqual(
            (0, 0, 44, 22), cell.do_get_size(treeview, None))

    def test_do_render(self):
        # A simple test to verify the method is defined. Cairo is broken
        # in gi--contexts cannot get created.
        cell = CellRendererGraph()
        self.assertEqual(
            "<type 'instancemethod'>", str(type(cell.do_render)))
