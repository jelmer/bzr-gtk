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

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gtk

from olive import delimiter
from errors import show_bzr_error

from bzrlib.branch import Branch
from bzrlib.config import GlobalConfig
import bzrlib.errors as errors

from dialog import error_dialog, info_dialog


class BranchDialog(gtk.Dialog):
    """ New implementation of the Branch dialog. """
    def __init__(self, path=None, parent=None):
        """ Initialize the Branch dialog. """
        gtk.Dialog.__init__(self, title="Branch - Olive",
                                  parent=parent,
                                  flags=0,
                                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        
        # Get arguments
        self.path = path
        
        # Create the widgets
        self._button_branch = gtk.Button(_("_Branch"), use_underline=True)
        self._button_revision = gtk.Button('')
        self._image_browse = gtk.Image()
        self._filechooser = gtk.FileChooserButton(_("Please select a folder"))
        self._combo = gtk.ComboBoxEntry()
        self._label_location = gtk.Label(_("Branch location:"))
        self._label_destination = gtk.Label(_("Destination:"))
        self._label_nick = gtk.Label(_("Branck nick:"))
        self._label_revision = gtk.Label(_("Revision:"))
        self._hbox_revision = gtk.HBox()
        self._entry_revision = gtk.Entry()
        self._entry_nick = gtk.Entry()
        
        # Set callbacks
        self._button_branch.connect('clicked', self._on_branch_clicked)
        self._button_revision.connect('clicked', self._on_revision_clicked)
        self._combo.connect('changed', self._on_combo_changed)
        
        # Create the table and pack the widgets into it
        self._table = gtk.Table(rows=3, columns=2)
        self._table.attach(self._label_location, 0, 1, 0, 1)
        self._table.attach(self._label_destination, 0, 1, 1, 2)
        self._table.attach(self._label_nick, 0, 1, 2, 3)
        self._table.attach(self._label_revision, 0, 1, 3, 4)
        self._table.attach(self._combo, 1, 2, 0, 1)
        self._table.attach(self._filechooser, 1, 2, 1, 2)
        self._table.attach(self._entry_nick, 1, 2, 2, 3)
        self._table.attach(self._hbox_revision, 1, 2, 3, 4)
        
        # Set properties
        self._image_browse.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON)
        self._button_revision.set_image(self._image_browse)
        self._button_revision.set_sensitive(False)
        self._filechooser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        self._label_location.set_alignment(0, 0.5)
        self._label_destination.set_alignment(0, 0.5)
        self._label_nick.set_alignment(0, 0.5)
        self._label_revision.set_alignment(0, 0.5)
        self._table.set_row_spacings(3)
        self._table.set_col_spacings(3)
        self.vbox.set_spacing(3)
        if self.path is not None:
            self._filechooser.set_filename(self.path)
        
        # Pack some widgets
        self._hbox_revision.pack_start(self._entry_revision, True, True)
        self._hbox_revision.pack_start(self._button_revision, False, False)
        self.vbox.add(self._table)
        self.action_area.pack_end(self._button_branch)
        
        # Show the dialog
        self.vbox.show_all()
        
        # Build branch history
        self._build_history()
    
    def _build_history(self):
        """ Build up the branch history. """
        config = GlobalConfig()
        history = config.get_user_option('gbranch_history')
        if history is not None:
            self._combo_model = gtk.ListStore(str)
            for item in history.split(delimiter):
                self._combo_model.append([ item ])
            self._combo.set_model(self._combo_model)
            self._combo.set_text_column(0)
    
    def _add_to_history(self, location):
        """ Add specified location to the history (if not yet added). """
        config = GlobalConfig()
        history = config.get_user_option('gbranch_history')
        if history is None:
            config.set_user_option('gbranch_history', location)
        else:
            h = history.split(delimiter)
            if location not in h:
                h.append(location)
            config.set_user_option('gbranch_history', delimiter.join(h))                
    
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
            if response != gtk.RESPONSE_NONE:
                revb.hide()
        
                if response == gtk.RESPONSE_OK:
                    if revb.selected_revno is not None:
                        self._entry_revision.set_text(revb.selected_revno)
            
                revb.destroy()
    
    @show_bzr_error
    def _on_branch_clicked(self, button):
        """ Branch button clicked handler. """
        location = self._combo.get_child().get_text()
        if location is '':
            error_dialog(_('Missing branch location'),
                         _('You must specify a branch location.'))
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
        
        br_from.lock_read()
        try:
            from bzrlib.transport import get_transport

            revision_id = br_from.get_rev_id(revno)

            basis_dir = None
            
            to_location = destination + os.sep + nick
            to_transport = get_transport(to_location)
            
            to_transport.mkdir('.')
            
            try:
                # preserve whatever source format we have.
                dir = br_from.bzrdir.sprout(to_transport.base,
                                            revision_id,
                                            basis_dir)
                branch = dir.open_branch()
                revs = branch.revno()
            except errors.NoSuchRevision:
                to_transport.delete_tree('.')
                raise
        finally:
            br_from.unlock()
                
        self._add_to_history(location)
        info_dialog(_('Branching successful'),
                    _('%d revision(s) branched.') % revs)
        
        self.response(gtk.RESPONSE_OK)
    
    def _on_combo_changed(self, widget):
        """ We try to get the last revision if focus lost. """
        rev = self._get_last_revno()
        if rev is None:
            self._entry_revision.set_text(_('N/A'))
            self._button_revision.set_sensitive(False)
        else:
            self._entry_revision.set_text(str(rev))
            self._button_revision.set_sensitive(True)
            if self._entry_nick.get_text() == '':
                self._entry_nick.set_text(os.path.basename(self._combo.get_child().get_text().rstrip("/\\")))
