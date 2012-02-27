# Copyright (C) 2006 Szilveszter Farkas <szilveszter.farkas@gmail.com>
# Copyright (C) 2007 Jelmer Vernooij <jelmer@samba.org>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


"""GTK UI
"""

from gi.repository import Gtk

from bzrlib.ui import UIFactory


def main_iteration(function):
    def with_main_iteration(self, *args, **kwargs):
        result = function(self, *args, **kwargs)
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        return result
    return with_main_iteration


class PromptDialog(Gtk.Dialog):
    """Prompt the user for a yes/no answer."""

    def __init__(self, prompt):
        super(PromptDialog, self).__init__()

        label = Gtk.Label(label=prompt)
        self.get_content_area().pack_start(label, True, True, 10)
        self.get_content_area().show_all()

        self.add_buttons(Gtk.STOCK_YES, Gtk.ResponseType.YES, Gtk.STOCK_NO,
                         Gtk.ResponseType.NO)


class GtkProgressBar(Gtk.ProgressBar):

    def __init__(self):
        super(GtkProgressBar, self).__init__()
        self.set_fraction(0.0)
        self.current = None
        self.total = None

    @main_iteration
    def tick(self):
        self.show()
        self.pulse()

    @main_iteration
    def update(self, msg=None, current_cnt=None, total_cnt=None):
        self.show()
        if current_cnt is not None:
            self.current = current_cnt
        if total_cnt is not None:
            self.total = total_cnt
        if msg is not None:
            self.set_text(msg)
        if None not in (self.current, self.total):
            fraction = float(self.current) / self.total
            if fraction < 0.0 or fraction > 1.0:
                raise ValueError
            self.set_fraction(fraction)

    @main_iteration
    def finished(self):
        self.set_fraction(0.0)
        self.current = None
        self.total = None
        self.hide()

    def clear(self):
        self.finished()


class ProgressContainerMixin:
    """Expose GtkProgressBar methods to a container class."""

    def tick(self, *args, **kwargs):
        self.show_all()
        self.pb.tick(*args, **kwargs)

    def update(self, *args, **kwargs):
        self.show_all()
        self.pb.update(*args, **kwargs)

    def finished(self):
        self.hide()
        self.pb.finished()

    def clear(self):
        self.hide()
        self.pb.clear()


class ProgressBarWindow(ProgressContainerMixin, Gtk.Window):

    def __init__(self):
        super(ProgressBarWindow, self).__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_border_width(0)
        self.set_title("Progress")
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.pb = GtkProgressBar()
        self.add(self.pb)
        self.resize(250, 15)
        self.set_resizable(False)


class ProgressPanel(ProgressContainerMixin, Gtk.Box):

    def __init__(self):
        super(ProgressPanel, self).__init__(Gtk.Orientation.HORIZONTAL, 5)
        image_loading = Gtk.Image.new_from_stock(Gtk.STOCK_REFRESH,
                                                 Gtk.IconSize.BUTTON)
        image_loading.show()

        self.pb = GtkProgressBar()
        self.set_border_width(5)
        self.pack_start(image_loading, False, False, 0)
        self.pack_start(self.pb, True, True, 0)


class PasswordDialog(Gtk.Dialog):
    """ Prompt the user for a password. """

    def __init__(self, prompt):
        super(PasswordDialog, self).__init__()

        label = Gtk.Label(label=prompt)
        self.get_content_area().pack_start(label, True, True, 10)

        self.entry = Gtk.Entry()
        self.entry.set_visibility(False)
        self.get_content_area().pack_end(self.entry, False, False, 10)

        self.get_content_area().show_all()

        self.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK,
                         Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

    def _get_passwd(self):
        return self.entry.get_text()

    passwd = property(_get_passwd)


class GtkUIFactory(UIFactory):
    """A UI factory for GTK user interfaces."""

    def __init__(self):
        """Create a GtkUIFactory"""
        super(GtkUIFactory, self).__init__()
        self.set_progress_bar_widget(None)

    def set_progress_bar_widget(self, widget):
        self._progress_bar_widget = widget

    def get_boolean(self, prompt):
        """GtkDialog with yes/no answers"""
        dialog = PromptDialog(prompt)
        response = dialog.run()
        dialog.destroy()
        return (response == Gtk.ResponseType.YES)

    def get_password(self, prompt='', **kwargs):
        """Prompt the user for a password.

        :param prompt: The prompt to present the user
        :param kwargs: Arguments which will be expanded into the prompt.
                       This lets front ends display different things if
                       they so choose.
        :return: The password string, return None if the user
                 canceled the request.
        """
        dialog = PasswordDialog(prompt % kwargs)
        response = dialog.run()
        passwd = dialog.passwd
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            return passwd
        else:
            return None

    def _progress_all_finished(self):
        """See UIFactory._progress_all_finished"""
        pbw = self._progress_bar_widget
        if pbw:
            pbw.finished()

    def _ensure_progress_widget(self):
        if self._progress_bar_widget is None:
            # Default to a window since nobody gave us a better means to report
            # progress.
            self.set_progress_bar_widget(ProgressBarWindow())

    def _progress_updated(self, task):
        """See UIFactory._progress_updated"""
        self._ensure_progress_widget()
        self._progress_bar_widget.update(task.msg,
                                         task.current_cnt, task.total_cnt)

    def report_transport_activity(self, transport, byte_count, direction):
        """See UIFactory.report_transport_activity"""
        self._ensure_progress_widget()
        self._progress_bar_widget.tick()
