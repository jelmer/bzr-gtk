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

from bzrlib.plugins.gtk import ui
from bzrlib.plugins.gtk.tests import (
    MockMethod,
    MockProperty,
    )
from bzrlib.progress import ProgressTask


class GtkUIFactoryTestCase(tests.TestCase):

    def test__init(self):
        ui_factory = ui.GtkUIFactory()
        self.assertIs(None, ui_factory._progress_bar_widget)

    def test_set_progress_bar_widget(self):
        ui_factory = ui.GtkUIFactory()
        progress_widget = ui.ProgressPanel()
        ui_factory.set_progress_bar_widget(progress_widget)
        self.assertIs(progress_widget, ui_factory._progress_bar_widget)

    def test_get_boolean_true(self):
        ui_factory = ui.GtkUIFactory()
        MockMethod.bind(self, ui.PromptDialog, 'run', Gtk.ResponseType.YES)
        boolean_value = ui_factory.get_boolean('test')
        self.assertIs(True, ui.PromptDialog.run.called)
        self.assertIs(True, boolean_value)

    def test_get_boolean_false(self):
        ui_factory = ui.GtkUIFactory()
        MockMethod.bind(self, ui.PromptDialog, 'run', Gtk.ResponseType.NO)
        boolean_value = ui_factory.get_boolean('test')
        self.assertIs(True, ui.PromptDialog.run.called)
        self.assertIs(False, boolean_value)

    def test_get_password(self):
        ui_factory = ui.GtkUIFactory()
        MockMethod.bind(self, ui.PasswordDialog, 'run', Gtk.ResponseType.OK)
        mock_property = MockProperty.bind(
            self, ui.PasswordDialog, 'passwd', 'secret')
        password = ui_factory.get_password('test')
        self.assertIs(True, ui.PasswordDialog.run.called)
        self.assertIs(True, mock_property.called)
        self.assertEqual('secret', password)

    def test_progress_all_finished_with_widget(self):
        ui_factory = ui.GtkUIFactory()
        progress_widget = ui.ProgressPanel()
        MockMethod.bind(self, progress_widget, 'finished')
        ui_factory.set_progress_bar_widget(progress_widget)
        self.assertIs(None, ui_factory._progress_all_finished())
        self.assertIs(True, progress_widget.finished.called)

    def test_progress_all_finished_without_widget(self):
        ui_factory = ui.GtkUIFactory()
        self.assertIs(None, ui_factory._progress_all_finished())

    def test_progress_updated_with_widget(self):
        ui_factory = ui.GtkUIFactory()
        progress_widget = ui.ProgressPanel()
        MockMethod.bind(self, progress_widget, 'update')
        ui_factory.set_progress_bar_widget(progress_widget)
        task = ProgressTask()
        task.msg = 'test'
        task.current_cnt = 1
        task.total_cnt = 2
        self.assertIs(None, ui_factory._progress_updated(task))
        self.assertIs(True, progress_widget.update.called)
        self.assertEqual(
            ('test', 1, 2), progress_widget.update.args)

    def test_progress_updated_without_widget(self):
        ui_factory = ui.GtkUIFactory()
        MockMethod.bind(self, ui.ProgressBarWindow, 'update')
        task = ProgressTask()
        task.msg = 'test'
        task.current_cnt = 1
        task.total_cnt = 2
        self.assertIs(None, ui_factory._progress_updated(task))
        self.assertIsInstance(
            ui_factory._progress_bar_widget, ui.ProgressBarWindow)
        self.assertIs(True, ui_factory._progress_bar_widget.update.called)
        self.assertEqual(
            ('test', 1, 2), ui_factory._progress_bar_widget.update.args)

    def test_report_transport_activity_with_widget(self):
        ui_factory = ui.GtkUIFactory()
        progress_widget = ui.ProgressPanel()
        MockMethod.bind(self, progress_widget, 'tick')
        ui_factory.set_progress_bar_widget(progress_widget)
        self.assertIs(
            None, ui_factory.report_transport_activity(None, None, None))
        self.assertIs(True, progress_widget.tick.called)

    def test_report_transport_activity_without_widget(self):
        ui_factory = ui.GtkUIFactory()
        MockMethod.bind(self, ui.ProgressBarWindow, 'tick')
        self.assertIs(
            None, ui_factory.report_transport_activity(None, None, None))
        self.assertIsInstance(
            ui_factory._progress_bar_widget, ui.ProgressBarWindow)
        self.assertIs(True, ui.ProgressBarWindow.tick.called)


class PromptDialogTestCase(tests.TestCase):

    def test__init(self):
        dialog = ui.PromptDialog('test 123')
        label = dialog.get_content_area().get_children()[0]
        self.assertEqual('test 123', label.props.label)
        buttons = dialog.get_action_area().get_children()
        self.assertEqual('gtk-no', buttons[0].props.label)
        self.assertEqual(
            Gtk.ResponseType.NO, dialog.get_response_for_widget(buttons[0]))
        self.assertEqual('gtk-yes', buttons[1].props.label)
        self.assertEqual(
            Gtk.ResponseType.YES, dialog.get_response_for_widget(buttons[1]))
