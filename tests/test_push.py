# Copyright (C) 2012 Curtis Hovey <sinzui.is@verizon.net>
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

"""Test the ui functionality."""

from gi.repository import Gtk

from bzrlib import (
    tests,
    )

from bzrlib.plugins.gtk import set_ui_factory
from bzrlib.plugins.gtk.push import PushDialog
from bzrlib.plugins.gtk.tests import (
    MockMethod,
    MockProperty,
    )


class PushTestCase(tests.TestCaseWithMemoryTransport):

    def test_init(self):
        tree = self.make_branch_and_memory_tree('test')
        branch = tree.branch
        set_ui_factory()
        dialog = PushDialog(
            repository=None, revid=None, branch=branch, parent=None)
        self.assertIs(None, dialog.props.parent)
        self.assertIs(None, dialog.repository)
        self.assertIs(None, dialog.revid)
        self.assertIs(branch, dialog.branch)
        self.assertIsInstance(dialog._label_location, Gtk.Label)
        self.assertIsInstance(dialog._combo, Gtk.ComboBox)
        self.assertIsInstance(dialog._button_push, Gtk.Button)
        self.assertIsInstance(dialog._hbox_location, Gtk.Box)
        self.assertEqual(
            Gtk.Orientation.HORIZONTAL,
            dialog._hbox_location.props.orientation)
        self.assertEqual(3, dialog._hbox_location.props.spacing)
