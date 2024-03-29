# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
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

import os

from gi.repository import GObject
from gi.repository import Gtk

from bzrlib.branch import Branch
from bzrlib.config import GlobalConfig

from bzrlib.plugins.gtk.dialog import error_dialog
from bzrlib.plugins.gtk.errors import show_bzr_error
from bzrlib.plugins.gtk.history import UrlHistory
from bzrlib.plugins.gtk.i18n import _i18n


class CheckoutDialog(Gtk.Dialog):
    """ New implementation of the Checkout dialog. """

    def __init__(self, path=None, parent=None, remote_path=None):
        """ Initialize the Checkout dialog. """
        super(CheckoutDialog, self).__init__(
            title="Checkout - Olive", parent=parent, flags=0,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

        # Get arguments
        self.path = path

        # Create the widgets
        self._button_checkout = Gtk.Button(_i18n("Check_out"), use_underline=True)
        self._button_revision = Gtk.Button('')
        self._image_browse = Gtk.Image()
        self._filechooser = Gtk.FileChooserButton(_i18n("Please select a folder"))
        self._combo = Gtk.ComboBox.new_with_entry()
        self._label_location = Gtk.Label(label=_i18n("Branch location:"))
        self._label_destination = Gtk.Label(label=_i18n("Destination:"))
        self._label_nick = Gtk.Label(label=_i18n("Branch nick:"))
        self._label_revision = Gtk.Label(label=_i18n("Revision:"))
        self._hbox_revision = Gtk.HBox()
        self._entry_revision = Gtk.Entry()
        self._entry_nick = Gtk.Entry()
        self._check_lightweight = Gtk.CheckButton(_i18n("_Lightweight checkout"),
                                                  use_underline=True)

        # Set callbacks
        self._button_checkout.connect('clicked', self._on_checkout_clicked)
        self._button_revision.connect('clicked', self._on_revision_clicked)
        self._combo.get_child().connect('focus-out-event', self._on_combo_changed)

        # Create the table and pack the widgets into it
        self._table = Gtk.Table(rows=3, columns=2)
        self._table.attach(self._label_location, 0, 1, 0, 1)
        self._table.attach(self._label_destination, 0, 1, 1, 2)
        self._table.attach(self._label_nick, 0, 1, 2, 3)
        self._table.attach(self._label_revision, 0, 1, 3, 4)
        self._table.attach(self._combo, 1, 2, 0, 1)
        self._table.attach(self._filechooser, 1, 2, 1, 2)
        self._table.attach(self._entry_nick, 1, 2, 2, 3)
        self._table.attach(self._hbox_revision, 1, 2, 3, 4)
        self._table.attach(self._check_lightweight, 1, 2, 4, 5)

        # Set properties
        self._image_browse.set_from_stock(Gtk.STOCK_OPEN, Gtk.IconSize.BUTTON)
        self._button_revision.set_image(self._image_browse)
        self._button_revision.set_sensitive(False)
        self._filechooser.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self._label_location.set_alignment(0, 0.5)
        self._label_destination.set_alignment(0, 0.5)
        self._label_nick.set_alignment(0, 0.5)
        self._label_revision.set_alignment(0, 0.5)
        self._table.set_row_spacings(3)
        self._table.set_col_spacings(3)
        self.get_content_area().set_spacing(3)
        if self.path is not None:
            self._filechooser.set_filename(self.path)
        if remote_path is not None:
            self._combo.get_child().set_text(remote_path)

        # Pack some widgets
        self._hbox_revision.pack_start(self._entry_revision, True, True, 0)
        self._hbox_revision.pack_start(self._button_revision, False, False, 0)
        self.get_content_area().add(self._table)
        self.action_area.pack_end(self._button_checkout, False, False, 0)

        # Show the dialog
        self.get_content_area().show_all()

        # Build checkout history
        self._history = UrlHistory(GlobalConfig(), 'branch_history')
        self._build_history()

    def _build_history(self):
        """ Build up the checkout history. """
        self._combo_model = Gtk.ListStore(str)

        for item in self._history.get_entries():
            self._combo_model.append([ item ])

        self._combo.set_model(self._combo_model)
        self._combo.set_entry_text_column(0)

    def _get_last_revno(self):
        """ Get the revno of the last revision (if any). """
        location = self._combo.get_child().get_text()
        try:
            br = Branch.open(location)
        except:
            return None
        else:
            return br.revno()

    def _on_revision_clicked(self, button):
        """ Browse for revision button clicked handler. """
        from revbrowser import RevisionBrowser

        location = self._combo.get_child().get_text()

        try:
            br = Branch.open(location)
        except:
            return
        else:
            revb = RevisionBrowser(br, self)
            response = revb.run()
            if response != Gtk.ResponseType.NONE:
                revb.hide()

                if response == Gtk.ResponseType.OK:
                    if revb.selected_revno is not None:
                        self._entry_revision.set_text(revb.selected_revno)

                revb.destroy()

    @show_bzr_error
    def _on_checkout_clicked(self, button):
        """ Checkout button clicked handler. """
        location = self._combo.get_child().get_text()
        if location is '':
            error_dialog(_i18n('Missing branch location'),
                         _i18n('You must specify a branch location.'))
            return

        destination = self._filechooser.get_filename()
        try:
            revno = int(self._entry_revision.get_text())
        except:
            revno = None

        nick = self._entry_nick.get_text()
        if nick is '':
            nick = os.path.basename(location.rstrip("/\\"))

        br_from = Branch.open(location)

        revision_id = br_from.get_rev_id(revno)
        lightweight = self._check_lightweight.get_active()
        to_location = destination + os.sep + nick

        os.mkdir(to_location)

        br_from.create_checkout(to_location, revision_id, lightweight)

        self._history.add_entry(location)

        self.response(Gtk.ResponseType.OK)

    def _on_combo_changed(self, widget, event):
        """ We try to get the last revision if focus lost. """
        rev = self._get_last_revno()
        if rev is None:
            self._entry_revision.set_text(_i18n('N/A'))
            self._button_revision.set_sensitive(False)
        else:
            self._entry_revision.set_text(str(rev))
            self._button_revision.set_sensitive(True)
            if self._entry_nick.get_text() == '':
                self._entry_nick.set_text(os.path.basename(self._combo.get_child().get_text().rstrip("/\\")))
