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

    def tick(self):
        self.show()
        self.pulse()

    def update(self, msg=None, current_cnt=None, total_cnt=None):
        self.show()
        if current_cnt is not None:
            self.current = current_cnt
        if total_cnt is not None:
            self.total = total_cnt
        if msg is not None:
            self.set_text(msg)
        if None not in (self.current, self.total):
            self.fraction = float(self.current) / self.total
            if self.fraction < 0.0 or self.fraction > 1.0:
                raise AssertionError
            self.set_fraction(self.fraction)
        while Gtk.events_pending():
            Gtk.main_iteration()

    def finished(self):
        self.hide()

    def clear(self):
        self.hide()


class ProgressBarWindow(Gtk.Window):

    def __init__(self):
        super(ProgressBarWindow, self).__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_border_width(0)
        self.set_title("Progress")
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.pb = GtkProgressBar()
        self.add(self.pb)
        self.resize(250, 15)
        self.set_resizable(False)

    def tick(self, *args, **kwargs):
        self.show_all()
        self.pb.tick(*args, **kwargs)

    def update(self, *args, **kwargs):
        self.show_all()
        self.pb.update(*args, **kwargs)

    def finished(self):
        self.pb.finished()
        self.hide()
        self.destroy()

    def clear(self):
        self.pb.clear()
        self.hide()


class ProgressPanel(Gtk.HBox):

    def __init__(self):
        super(ProgressPanel, self).__init__()
        image_loading = Gtk.Image.new_from_stock(Gtk.STOCK_REFRESH,
                                                 Gtk.IconSize.BUTTON)
        image_loading.show()

        self.pb = GtkProgressBar()
        self.set_spacing(5)
        self.set_border_width(5)
        self.pack_start(image_loading, False, False, 0)
        self.pack_start(self.pb, True, True, 0)

    def tick(self, *args, **kwargs):
        self.show_all()
        self.pb.tick(*args, **kwargs)

    def update(self, *args, **kwargs):
        self.show_all()
        self.pb.update(*args, **kwargs)

    def finished(self):
        self.pb.finished()
        self.hide()

    def clear(self):
        self.pb.clear()
        self.hide()


class PasswordDialog(Gtk.Dialog):
    """ Prompt the user for a password. """

    def __init__(self, prompt):
        super(PasswordDialog, self).__init__()

        label = Gtk.Label(label=prompt)
        self.get_content_area().pack_start(label, True, True, 10)

        self.entry = Gtk.Entry()
        self.entry.set_visibility(False)
        self.get_content_area().pack_end(self.entry, padding=10)

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

    def _progress_updated(self, task):
        """See UIFactory._progress_updated"""
        if self._progress_bar_widget is None:
            # Default to a window since nobody gave us a better mean to report
            # progress.
            self.set_progress_bar_widget(ProgressBarWindow())
        self._progress_bar_widget.update(task.msg,
                                         task.current_cnt, task.total_cnt)

