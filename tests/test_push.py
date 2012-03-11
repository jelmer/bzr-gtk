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
    errors,
    tests,
    ui,
    )

from bzrlib.plugins.gtk import (
    push,
    set_ui_factory,
    )
from bzrlib.plugins.gtk.tests import MockMethod
from bzrlib.plugins.gtk.history import UrlHistory
from bzrlib.plugins.gtk.ui import ProgressPanel


class PushTestCase(tests.TestCaseWithMemoryTransport):

    def make_push_branch(self):
        tree = self.make_branch_and_memory_tree('test')
        return tree.branch

    def test_init(self):
        set_ui_factory()
        branch = self.make_push_branch()
        dialog = push.PushDialog(
            repository=None, revid=None, branch=branch, parent=None)
        self.assertIs(None, dialog.props.parent)
        self.assertIs(None, dialog.repository)
        self.assertIs(None, dialog.revid)
        self.assertIs(branch, dialog.branch)
        # Layout rules to match HIG.
        self.assertIsInstance(dialog._label_location, Gtk.Label)
        self.assertIsInstance(dialog._combo, Gtk.ComboBox)
        self.assertIsInstance(dialog._button_push, Gtk.Button)
        self.assertIsInstance(dialog._hbox_location, Gtk.Box)
        self.assertIsInstance(dialog._progress_widget, ProgressPanel)
        self.assertIsInstance(dialog._push_message, Gtk.Label)
        self.assertIsInstance(dialog._history, UrlHistory)
        self.assertIs(
            ui.ui_factory._progress_bar_widget, dialog._progress_widget)
        self.assertEqual(
            Gtk.Orientation.HORIZONTAL,
            dialog._hbox_location.props.orientation)
        self.assertEqual(0.0, dialog._push_message.props.xalign)
        self.assertEqual(6, dialog.props.border_width)
        self.assertEqual(6, dialog._hbox_location.props.spacing)
        self.assertEqual(6, dialog.get_content_area().props.spacing)
        # Show rules.
        self.assertIs(True, dialog._combo.props.visible)
        self.assertIs(False, dialog._progress_widget.props.visible)
        self.assertIs(False, dialog._push_message.props.visible)

    def test_build_history(self):
        set_ui_factory()
        branch = self.make_push_branch()
        branch.set_push_location('lp:~user/fnord/trunk')
        dialog = push.PushDialog(None, None, branch)
        dialog._history.add_entry('lp:~user/fnord/test1')
        dialog._history.add_entry('lp:~user/fnord/test2')
        dialog._build_history()
        self.assertEqual(
            'lp:~user/fnord/trunk', dialog._combo.get_child().props.text)
        self.assertIsInstance(dialog._combo_model, Gtk.ListStore)
        self.assertIs(dialog._combo.get_model(), dialog._combo_model)
        locations = [row[0] for row in dialog._combo_model]
        self.assertEqual(
            ['lp:~user/fnord/test1', 'lp:~user/fnord/test2'], locations)

    def test_on_close_clicked(self):
        # The ui_factory's progress bar widget is set to None.
        set_ui_factory()
        branch = self.make_push_branch()
        dialog = push.PushDialog(None, None, branch)
        dialog._on_close_clicked(None)
        self.assertIs(None, ui.ui_factory._progress_bar_widget)

    def test_on_push_clicked_without_errors(self):
        # Verify the dialog's and branch's final states after a push.
        MockMethod.bind(self, push, 'do_push', "test success")
        set_ui_factory()
        branch = self.make_push_branch()
        dialog = push.PushDialog(None, None, branch)
        MockMethod.bind(self, dialog._progress_widget, 'tick')
        dialog._combo.get_child().props.text = 'lp:~user/fnord/test'
        dialog._on_push_clicked(None)
        self.assertIs(True, dialog._progress_widget.tick.called)
        self.assertIs(False, dialog._progress_widget.props.visible)
        self.assertIs(True, push.do_push.called)
        self.assertEqual(
            (branch, 'lp:~user/fnord/test'), push.do_push.args)
        self.assertEqual(
            {'overwrite': False}, push.do_push.kwargs)
        self.assertIs(True, dialog._push_message.props.visible)
        self.assertEqual('test success', dialog._push_message.props.label)
        self.assertEqual(
            'lp:~user/fnord/test', dialog._history.get_entries()[-1])
        self.assertEqual('lp:~user/fnord/test', branch.get_push_location())

    def test_on_push_clicked_with_divered_branches(self):
        # Verify that when DivergedBranches is raise, the user can choose
        # to overwrite the branch.
        error = errors.DivergedBranches(None, None)
        MockMethod.bind(self, push, 'do_push', raise_error=error)
        MockMethod.bind(self, push, 'question_dialog', Gtk.ResponseType.YES)
        set_ui_factory()
        branch = self.make_push_branch()
        dialog = push.PushDialog(None, None, branch)
        dialog._combo.get_child().props.text = 'lp:~user/fnord/test'
        dialog._on_push_clicked(None)
        self.assertIs(True, push.do_push.called)
        self.assertEqual(2, push.do_push.call_count)
        self.assertEqual(
            (branch, 'lp:~user/fnord/test'), push.do_push.args)
        self.assertEqual(
            {'overwrite': True}, push.do_push.kwargs)


class PushTestCase(tests.TestCaseWithTransport):

    def setup_ui(self):
        set_ui_factory()
        progress_panel = ProgressPanel()
        ui.ui_factory.set_progress_bar_widget(progress_panel)
        MockMethod.bind(self, progress_panel.pb, 'tick')
        MockMethod.bind(self, progress_panel.pb, 'update')
        MockMethod.bind(self, progress_panel.pb, 'finished')
        return progress_panel

    def make_from_branch(self):
        from_tree = self.make_branch_and_tree('this')
        self.build_tree(['this/a', 'this/b'])
        from_tree.add(['a', 'b'])
        from_tree.commit("msg")
        return from_tree.branch

    def test_do_push_without_dir(self):
        progress_panel = self.setup_ui()
        from_branch = self.make_from_branch()
        message = push.do_push(from_branch, 'that', False)
        self.assertEqual('1 revision(s) pushed.', message)
        self.assertEqual(False, progress_panel.pb.tick.called)
        self.assertEqual(True, progress_panel.pb.update.called)
        self.assertEqual(True, progress_panel.pb.finished.called)

    def test_do_push_without_parent_dir(self):
        progress_panel = self.setup_ui()
        from_branch = self.make_from_branch()
        MockMethod.bind(self, push, 'question_dialog', Gtk.ResponseType.OK)
        message = push.do_push(from_branch, 'that/there', False)
        self.assertEqual('1 revision(s) pushed.', message)
        self.assertEqual(True, push.question_dialog.called)
        self.assertEqual(False, progress_panel.pb.tick.called)
        self.assertEqual(True, progress_panel.pb.update.called)
        self.assertEqual(True, progress_panel.pb.finished.called)

    def test_do_push_with_dir(self):
        progress_panel = self.setup_ui()
        self.make_branch_and_tree('that')
        from_branch = self.make_from_branch()
        message = push.do_push(from_branch, 'that', False)
        self.assertEqual('1 revision(s) pushed.', message)
        self.assertEqual(False, progress_panel.pb.tick.called)
        self.assertEqual(True, progress_panel.pb.update.called)
        self.assertEqual(True, progress_panel.pb.finished.called)
