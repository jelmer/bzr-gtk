# Copyright (C) 2006 by Szilveszter Farkas (Phanatic)
#                       <szilveszter.farkas@gmail.com>
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

from gi.repository import Gtk

from errors import show_bzr_error

from bzrlib import (
    errors,
    ui,
    )
from bzrlib.bzrdir import BzrDir
from bzrlib.transport import get_transport

from bzrlib.plugins.gtk.dialog import (
    question_dialog,
    )
from bzrlib.plugins.gtk.history import UrlHistory
from bzrlib.plugins.gtk.i18n import _i18n
from bzrlib.plugins.gtk.ui import ProgressPanel


class PushDialog(Gtk.Dialog):
    """New implementation of the Push dialog."""

    def __init__(self, repository, revid, branch=None, parent=None):
        """Initialize the Push dialog. """
        super(PushDialog, self).__init__(
            title="Push", parent=parent, flags=0,
            buttons=(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))
        self.branch = branch

        # Unused arguments
        self.repository = repository
        self.revid = revid

        # Create the widgets
        self._label_location = Gtk.Label(label=_i18n("Location:"))
        self._combo = Gtk.ComboBox.new_with_entry()
        self._button_push = Gtk.Button(_i18n("_Push"), use_underline=True)
        self._hbox_location = Gtk.Box(Gtk.Orientation.HORIZONTAL, 3)

        # Set callbacks
        self.connect('close', self._on_close_clicked)
        self._button_push.connect('clicked', self._on_push_clicked)

        # Set properties
        self._label_location.set_alignment(0, 0.5)
        self.get_content_area().set_spacing(3)

        # Pack widgets
        self._hbox_location.pack_start(
            self._label_location, False, False, 0)
        self._hbox_location.pack_start(self._combo, False, False, 0)
        self.get_content_area().pack_start(
            self._hbox_location, False, False, 0)
        self.get_action_area().pack_end(self._button_push, True, True, 0)

        # Set progress pane.
        self._progress_widget = ProgressPanel()
        ui.ui_factory.set_progress_bar_widget(self._progress_widget)
        self.get_content_area().pack_start(
            self._progress_widget, False, False, 0)
        self._push_message = Gtk.Label()
        alignment = Gtk.Alignment.new(0.0, 0.5, 0.0, 0.0)
        alignment.add(self._push_message)
        self.get_content_area().pack_start(alignment, False, False, 0)

        # Show the dialog
        self.get_content_area().show_all()
        self._progress_widget.hide()
        self._push_message.hide()

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

    @show_bzr_error
    def _on_push_clicked(self, widget):
        """Push button clicked handler. """
        self._push_message.hide()
        self._progress_widget.tick()
        location = self._combo.get_child().get_text()

        try:
            message = do_push(self.branch, location, overwrite=False)
        except errors.DivergedBranches:
            response = question_dialog(
                _i18n('Branches have been diverged'),
                _i18n('You cannot push if branches have diverged.\n'
                      'Overwrite?'))
            if response == Gtk.ResponseType.YES:
                message = do_push(self.branch, location, overwrite=True)
            else:
                return
        self._history.add_entry(location)
        if (self.branch is not None
            and self.branch.get_push_location() is None):
            self.branch.set_push_location(location)
        if message:
            self._progress_widget.finished()
            self._push_message.props.label = message
            self._push_message.show()


def do_push(br_from, location, overwrite=False):
    """Update a mirror of a branch.

    :param br_from: the source branch
    :param location: the location of the branch that you'd like to update
    :param overwrite: overwrite target location if it diverged
    :return: number of revisions pushed
    """
    transport = get_transport(location)
    location_url = transport.base

    try:
        dir_to = BzrDir.open(location_url)
        br_to = dir_to.open_branch()
    except errors.NotBranchError:
        # create a branch.
        transport = transport.clone('..')
        try:
            relurl = transport.relpath(location_url)
            transport.mkdir(relurl)
        except errors.NoSuchFile:
            response = question_dialog(
                _i18n('Non existing parent directory'),
                _i18n("The parent directory (%s)\ndoesn't exist. Create?") %
                location)
            if response == Gtk.ResponseType.OK:
                transport.create_prefix()
            else:
                return
        dir_to = br_from.bzrdir.clone(location_url,
            revision_id=br_from.last_revision())
        br_to = dir_to.open_branch()
        count = len(br_to.revision_history())
    else:
        br_to.revision_history()
        try:
            tree_to = dir_to.open_workingtree()
        except errors.NotLocalUrl:
            # FIXME - what to do here? how should we warn the user?
            count = br_to.pull(br_from, overwrite)
        except errors.NoWorkingTree:
            count = br_to.pull(br_from, overwrite)
        else:
            count = tree_to.pull(br_from, overwrite)

    return "Pushed %d revisions." % int(count)
