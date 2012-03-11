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
from bzrlib.controldir import ControlDir
from bzrlib.push import PushResult
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
            title="Push", parent=parent, flags=0, border_width=6,
            buttons=(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))
        self.branch = branch

        # Unused arguments
        self.repository = repository
        self.revid = revid

        # Create the widgets
        self._label_location = Gtk.Label(label=_i18n("Location:"))
        self._combo = Gtk.ComboBox.new_with_entry()
        self._button_push = Gtk.Button(_i18n("_Push"), use_underline=True)
        self._hbox_location = Gtk.Box(Gtk.Orientation.HORIZONTAL, 6)
        self._push_message = Gtk.Label(xalign=0)
        self._progress_widget = ProgressPanel()

        # Set callbacks
        ui.ui_factory.set_progress_bar_widget(self._progress_widget)
        self.connect('close', self._on_close_clicked)
        self._button_push.connect('clicked', self._on_push_clicked)

        # Set properties
        content_area = self.get_content_area()
        content_area.set_spacing(6)

        # Pack widgets
        self._hbox_location.pack_start(self._label_location, False, False, 0)
        self._hbox_location.pack_start(self._combo, False, False, 0)
        content_area.pack_start(self._hbox_location, True, True, 0)
        content_area.pack_start(self._progress_widget, True, True, 0)
        content_area.pack_start(self._push_message, True, True, 0)
        self.get_action_area().pack_end(self._button_push, True, True, 0)

        # Show the dialog
        content_area.show_all()
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


def do_push(br_from, location, overwrite):
    """Update a mirror of a branch.

    :param br_from: the source branch
    :param location: the location of the branch that you'd like to update
    :param overwrite: overwrite target location if it diverged
    :return: number of revisions pushed
    """
    revision_id = None
    to_transport = get_transport(location)
    try:
        dir_to = ControlDir.open_from_transport(to_transport)
    except errors.NotBranchError:
        dir_to = None

    if dir_to is None:
        try:
            br_to = br_from.create_clone_on_transport(
                to_transport, revision_id=revision_id)
        except errors.NoSuchFile:
            response = question_dialog(
                _i18n('Non existing parent directory'),
                _i18n("The parent directory (%s)\ndoesn't exist. Create?") %
                    location)
            if response == Gtk.ResponseType.OK:
                br_to = br_from.create_clone_on_transport(
                    to_transport, revision_id=revision_id, create_prefix=True)
            else:
                return _i18n("Push aborted.")
        push_result = create_push_result(br_from, br_to)
    else:
        push_result = dir_to.push_branch(br_from, revision_id, overwrite)
    message = create_push_message(br_from, push_result)
    return message


def create_push_message(br_from, push_result):
    """Return a mesage explaining what happened during the push."""
    messages = []
    rev_count = br_from.revno() - push_result.old_revno
    messages.append(_i18n("%d revision(s) pushed.") % rev_count)
    if push_result.stacked_on is not None:
        messages.append(_i18n("Stacked on %s.") % push_result.stacked_on)
    if push_result.workingtree_updated is False:
        messages.append(_i18n(
            "\nThe working tree was not updated:"
            "\nSee 'bzr help working-trees' for more information."))
    return '\n'.join(messages)


def create_push_result(br_from, br_to):
    """Return a PushResult like one created by ControlDir.push_branch()."""
    push_result = PushResult()
    push_result.source_branch = br_from
    push_result.target_branch = br_to
    push_result.branch_push_result = None
    push_result.master_branch = None
    push_result.old_revno = 0
    push_result.old_revid = br_to.last_revision()
    push_result.workingtree_updated = None  # Not applicable to this case.
    try:
        push_result.stacked_on = br_to.get_stacked_on_url()
    except (errors.UnstackableBranchFormat,
            errors.UnstackableRepositoryFormat,
            errors.NotStacked):
        push_result.stacked_on = None
    return push_result
