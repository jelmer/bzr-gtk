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
import gtk.glade

from bzrlib.branch import Branch
import bzrlib.errors as errors

from dialog import error_dialog, info_dialog, warning_dialog
from errors import show_bzr_error
from olive.guifiles import GLADEFILENAME


class MergeDialog:
    """ Display the Merge dialog and perform the needed actions. """
    def __init__(self, wt, wtpath,default_branch_path=None):
        """ Initialize the Merge dialog. """
        self.glade = gtk.glade.XML(GLADEFILENAME, 'window_merge', 'olive-gtk')
        
        self.window = self.glade.get_widget('window_merge')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_merge_merge_clicked": self.merge,
                "on_button_merge_cancel_clicked": self.close,
                "on_button_merge_open_clicked": self.open }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)

        self.wt = wt
        self.wtpath = wtpath
        
        # Get some widgets
        self.entry = self.glade.get_widget('entry_merge')
        if default_branch_path:
            self.entry.set_text(default_branch_path)

    def display(self):
        """ Display the Add file(s) dialog. """
        self.window.show_all()

    @show_bzr_error
    def merge(self, widget):
        branch = self.entry.get_text()
        if branch == "":
            error_dialog(_('Branch not given'),
                         _('Please specify a branch to merge from.'))
            return

        other_branch = Branch.open_containing(branch)[0]

        try:
            conflicts = self.wt.merge_from_branch(other_branch)
        except errors.BzrCommandError, errmsg:
            error_dialog(_('Bazaar command error'), str(errmsg))
            return
        
        self.close()
        if conflicts == 0:
            # No conflicts found.
            info_dialog(_('Merge successful'),
                        _('All changes applied successfully.'))
        else:
            # There are conflicts to be resolved.
            warning_dialog(_('Conflicts encountered'),
                           _('Please resolve the conflicts manually before committing.'))
    
    def open(self, widget):
        fcd = gtk.FileChooserDialog(title="Please select a folder",
                                    parent=self.window,
                                    action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                             gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        fcd.set_default_response(gtk.RESPONSE_OK)
        
        if fcd.run() == gtk.RESPONSE_OK:
            self.entry.set_text(fcd.get_filename())
        
        fcd.destroy()
        
    def close(self, widget=None):
        self.window.destroy()
