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


class MainIterationTestCase(tests.TestCase):

    def test_main_iteration(self):
        # The main_iteration decorator iterates over the pending Gtk events
        # after calling its function so that the UI is updated too.
        button = Gtk.ToggleButton(label='before')

        def event_listener(button):
            button.props.label = 'after'

        button.connect('clicked', event_listener)

        def test_func(self):
            button.emit('clicked')
            return True

        decorated_func = ui.main_iteration(test_func)
        result = decorated_func(object())
        self.assertIs(True, result)
        self.assertIs(False, Gtk.events_pending())
        self.assertEqual('after', button.props.label)


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

    def test_init(self):
        # tthe label and buttons are created, then shown.
        MockMethod.bind(self, Gtk.Box, 'show_all')
        dialog = ui.PromptDialog('test 123')
        content_area = dialog.get_content_area()
        self.assertIs(True, dialog.get_content_area().show_all.called)
        self.assertIs(1, dialog.get_content_area().show_all.call_count)
        label = content_area.get_children()[0]
        self.assertEqual('test 123', label.props.label)
        buttons = dialog.get_action_area().get_children()
        self.assertEqual('gtk-no', buttons[0].props.label)
        self.assertEqual(
            Gtk.ResponseType.NO, dialog.get_response_for_widget(buttons[0]))
        self.assertEqual('gtk-yes', buttons[1].props.label)
        self.assertEqual(
            Gtk.ResponseType.YES, dialog.get_response_for_widget(buttons[1]))


class PasswordDialogTestCase(tests.TestCase):

    def test_init(self):
        # The label, password entry, and buttons are created, then shown.
        MockMethod.bind(self, Gtk.Box, 'show_all')
        dialog = ui.PasswordDialog('test password')
        content_area = dialog.get_content_area()
        self.assertIs(True, dialog.get_content_area().show_all.called)
        widgets = content_area.get_children()
        self.assertEqual('test password', widgets[0].props.label)
        self.assertEqual(False, widgets[1].props.visibility)
        buttons = dialog.get_action_area().get_children()
        self.assertEqual('gtk-cancel', buttons[0].props.label)
        self.assertEqual(
            Gtk.ResponseType.CANCEL,
            dialog.get_response_for_widget(buttons[0]))
        self.assertEqual('gtk-ok', buttons[1].props.label)
        self.assertEqual(
            Gtk.ResponseType.OK,
            dialog.get_response_for_widget(buttons[1]))


class GtkProgressBarTestCase(tests.TestCase):

    def test_init(self):
        progress_bar = ui.GtkProgressBar()
        self.assertEqual(0.0, progress_bar.props.fraction)
        self.assertIs(None, progress_bar.total)
        self.assertIs(None, progress_bar.current)

    def test_tick(self):
        # tick() shows the widget, does one pulse, then handles the pending
        # events in the main loop.
        MockMethod.bind(self, ui.GtkProgressBar, 'show')
        MockMethod.bind(self, ui.GtkProgressBar, 'pulse')
        progress_bar = ui.GtkProgressBar()
        progress_bar.tick()
        self.assertIs(True, progress_bar.show.called)
        self.assertEqual('with_main_iteration', progress_bar.tick.__name__)

    def test_update_with_data(self):
        # update() shows the widget, sets the fraction, then handles the
        # pending events in the main loop.
        MockMethod.bind(self, ui.GtkProgressBar, 'show')
        progress_bar = ui.GtkProgressBar()
        progress_bar.update(msg='test', current_cnt=5, total_cnt=10)
        self.assertIs(True, progress_bar.show.called)
        self.assertEqual(0.5, progress_bar.props.fraction)
        self.assertEqual(10, progress_bar.total)
        self.assertEqual(5, progress_bar.current)
        self.assertEqual('with_main_iteration', progress_bar.update.__name__)

    def test_update_without_data(self):
        progress_bar = ui.GtkProgressBar()
        progress_bar.update(current_cnt=5, total_cnt=None)
        self.assertEqual(0.0, progress_bar.props.fraction)
        self.assertIs(None, progress_bar.total)
        self.assertEqual(5, progress_bar.current)

    def test_update_with_insane_data(self):
        # The fraction must be between 0.0 and 1.0.
        progress_bar = ui.GtkProgressBar()
        self.assertRaises(
            ValueError, progress_bar.update, None, 20, 2)

    def test_finished(self):
        # finished() hides the widget, resets the state, then handles the
        # pending events in the main loop.
        MockMethod.bind(self, ui.GtkProgressBar, 'hide')
        progress_bar = ui.GtkProgressBar()
        progress_bar.finished()
        self.assertIs(True, progress_bar.hide.called)
        self.assertEqual(0.0, progress_bar.props.fraction)
        self.assertIs(None, progress_bar.total)
        self.assertIs(None, progress_bar.current)
        self.assertEqual('with_main_iteration', progress_bar.finished.__name__)

    def test_clear(self):
        # clear() is synonymous with finished.
        MockMethod.bind(self, ui.GtkProgressBar, 'finished')
        progress_bar = ui.GtkProgressBar()
        progress_bar.finished()
        self.assertIs(True, progress_bar.finished.called)


class ProgressContainerMixin:

    def test_tick(self):
        progress_widget = self.progress_container()
        MockMethod.bind(self, progress_widget, 'show_all')
        MockMethod.bind(self, progress_widget.pb, 'tick')
        progress_widget.tick()
        self.assertIs(True, progress_widget.show_all.called)
        self.assertIs(True, progress_widget.pb.tick.called)

    def test_update(self):
        progress_widget = self.progress_container()
        MockMethod.bind(self, progress_widget, 'show_all')
        MockMethod.bind(self, progress_widget.pb, 'update')
        progress_widget.update('test', 5, 10)
        self.assertIs(True, progress_widget.show_all.called)
        self.assertIs(True, progress_widget.pb.update.called)
        self.assertEqual(
            ('test', 5, 10), progress_widget.pb.update.args)

    def test_finished(self):
        progress_widget = self.progress_container()
        MockMethod.bind(self, progress_widget, 'hide')
        MockMethod.bind(self, progress_widget.pb, 'finished')
        progress_widget.finished()
        self.assertIs(True, progress_widget.hide.called)
        self.assertIs(True, progress_widget.pb.finished.called)

    def test_clear(self):
        progress_widget = self.progress_container()
        MockMethod.bind(self, progress_widget, 'hide')
        MockMethod.bind(self, progress_widget.pb, 'clear')
        progress_widget.clear()
        self.assertIs(True, progress_widget.hide.called)
        self.assertIs(True, progress_widget.pb.clear.called)


class ProgressBarWindowTestCase(ProgressContainerMixin, tests.TestCase):

    progress_container = ui.ProgressBarWindow

    def test_init(self):
        pb_window = ui.ProgressBarWindow()
        self.assertEqual('Progress', pb_window.props.title)
        self.assertEqual(
            Gtk.WindowPosition.CENTER_ALWAYS, pb_window.props.window_position)
        self.assertIsInstance(pb_window.pb, ui.GtkProgressBar)


class ProgressPanelTestCase(ProgressContainerMixin, tests.TestCase):

    progress_container = ui.ProgressPanel

    def test_init(self):
        pb_window = ui.ProgressPanel()
        self.assertEqual(
            Gtk.Orientation.HORIZONTAL, pb_window.props.orientation)
        self.assertEqual(5, pb_window.props.spacing)
        self.assertIsInstance(pb_window.pb, ui.GtkProgressBar)
        widgets = pb_window.get_children()
        # The image's stock and icon_name properties are always None?
        self.assertIsInstance(widgets[0], Gtk.Image)
