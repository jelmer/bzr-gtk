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

import bzrlib.errors as errors

from dialog import error_dialog, warning_dialog
from gladefile import GLADEFILENAME


class OliveRemove:
    """ Display the Remove file(s) dialog and perform the needed actions. """
    def __init__(self, wt, wtpath, selected=[]):
        """ Initialize the Remove file(s) dialog. """
        self.glade = gtk.glade.XML(GLADEFILENAME, 'window_remove')
        
        self.window = self.glade.get_widget('window_remove')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_remove_remove_clicked": self.remove,
                "on_button_remove_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        self.wt = wt
        self.wtpath = wtpath
        self.selected = selected

    def display(self):
        """ Display the Remove file(s) dialog. """
        self.window.show_all()
        
    def remove(self, widget):
        radio_selected = self.glade.get_widget('radiobutton_remove_selected')
        radio_new = self.glade.get_widget('radiobutton_remove_new')
        
        if radio_selected.get_active():
            # Remove only the selected file
            filename = self.selected
            
            if filename is None:
                error_dialog(_('No file was selected'),
                             _('Please select a file from the list,\nor choose the other option.'))
                return
            
            fullpath = self.wt.abspath(os.path.join(self.wtpath, filename))
            
            try:
                self.wt.remove(fullpath)
            except errors.NotBranchError:
                error_dialog(_('Directory is not a branch'),
                             _('You can perform this action only in a branch.'))
                return
            except errors.NotVersionedError:
                error_dialog(_('File not versioned'),
                             _('The selected file is not versioned.'))
                return
        elif radio_new.get_active():
            # Remove added files recursively
            added = self.wt.changes_from(self.wt.basis_tree()).added
            file_list = sorted([f[0] for f in added], reverse=True)
            if len(file_list) == 0:
                warning_dialog(_('No matching files'),
                               _('No added files were found in the working tree.'))
                return
            self.wt.remove(file_list)
        
        self.close()
    
    def close(self, widget=None):
        self.window.destroy()