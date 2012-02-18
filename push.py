# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
# Copyright (C) 2007 by Jelmer Vernooij <jelmer@samba.org>
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

import logging
from StringIO import StringIO

from gi.repository import (
    GObject,
    Gtk,
    )

from errors import show_bzr_error

from bzrlib import ui
import bzrlib.errors as errors
from bzrlib.push import _show_push_branch
from bzrlib.plugins.gtk.history import UrlHistory
from bzrlib.plugins.gtk.i18n import _i18n
from bzrlib.plugins.gtk.ui import ProgressPanel


GObject.threads_init()


class PushDialog(Gtk.Dialog):
    """New implementation of the Push dialog."""

    def __init__(self, repository, revid, branch=None, parent=None):
        """Initialize the Push dialog. """
        super(PushDialog, self).__init__(
            title="Push", parent=parent, flags=0,
            buttons=(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))

        # Get arguments
        self.repository = repository
        self.revid = revid
        self.branch = branch

        # Create the widgets
        self._label_location = Gtk.Label(label=_i18n("Location:"))
        self._combo = Gtk.ComboBox.new_with_entry()
        self._button_push = Gtk.Button(_i18n("_Push"), use_underline=True)
        self._hbox_location = Gtk.HBox()

        # Set callbacks
        self.connect('close', self._on_close_clicked)
        self._button_push.connect('clicked', self._on_push_clicked)

        # Set properties
        self._label_location.set_alignment(0, 0.5)
        self._hbox_location.set_spacing(3)
        self.get_content_area().set_spacing(3)

        # Pack widgets
        self._hbox_location.pack_start(
            self._label_location, False, False, 0)
        self._hbox_location.pack_start(self._combo, False, False, 0)
        self.get_content_area().pack_start(
            self._hbox_location, False, False, 0)
        self.get_action_area().pack_end(self._button_push, True, True, 0)

        # Set progress pane.
        self.progress_widget = ProgressPanel()
        ui.ui_factory.set_progress_bar_widget(self.progress_widget)
        self.get_content_area().pack_start(
            self.progress_widget, False, False, 0)
        self.push_message = Gtk.Label()
        alignment = Gtk.Alignment.new(0.0, 0.5, 0.0, 0.0)
        alignment.add(self.push_message)
        self.get_content_area().pack_start(alignment, False, False, 0)

        # Show the dialog
        self.get_content_area().show_all()
        self.progress_widget.hide()

        # Build location history
        self._history = UrlHistory(self.branch.get_config(), 'push_history')
        self._build_history()

    def _build_history(self):
        """Build up the location history. """
        self._combo_model = Gtk.ListStore(str)
        for item in self._history.get_entries():
            self._combo_model.append([item])
        self._combo.set_model(self._combo_model)
        self._combo.set_entry_text_column(0)

        if self.branch is not None:
            location = self.branch.get_push_location()
            if location is not None:
                self._combo.get_child().set_text(location)

    def _on_close_clicked(self, widget):
        """Close dialog handler."""
        ui.ui_factory.set_progress_bar_widget(None)

    def _on_push_clicked(self, widget):
        """Push button clicked handler. """
        self.push_message.hide()
        self.progress_widget.show()
        while Gtk.events_pending():
            Gtk.main_iteration()
        location = self._combo.get_child().get_text()
        do_push(self.branch, location, False, self.on_push_complete)

    def on_push_complete(self, location, message):
        self._history.add_entry(location)
        if (self.branch is not None
            and self.branch.get_push_location() is None):
            self.branch.set_push_location(location)
        if message:
            self.progress_widget.finished()
            self.push_message.props.label = message
            self.push_message.show()
        message


class PushHandler(logging.Handler):
    """A logging handler to collect messages."""

    def __init__(self):
        logging.Handler.__init__(self, logging.INFO)
        self.messages = []

    def handleError(self, record):
        pass

    def emit(self, record):
        self.messages.append(record.getMessage())


@show_bzr_error
def do_push(br_from, location, overwrite, callback):
    """Update a mirror of a branch.

    ::
    :param br_from: the source branch
    :param location: the location of the branch that you'd like to update
    :param overwrite: overwrite target location if it diverged
    :return: number of revisions pushed
    """
    log = logging.getLogger('bzr')
    old_propagate = log.propagate
    message = 'Branch pushed'
    handler = PushHandler()
    try:
        try:
            log.addHandler(handler)
            log.propagate = False
            # Revid is None to imply tip.
            # The call assumes text ui (file) to write to.
            _show_push_branch(
                br_from, None, location, StringIO(), overwrite=overwrite)
            message = '\n'.join(handler.messages)
        except errors.BzrCommandError, error:
            message = _i18n('Error: ') + str(error)
    finally:
        log.removeHandler(handler)
        log.propagate = old_propagate
    callback(location, message)
