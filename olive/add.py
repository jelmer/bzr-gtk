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

import bzrlib.add
import bzrlib.errors as errors

from dialog import error_dialog
from gladefile import GLADEFILENAME


class OliveAdd:
    """ Display the Add file(s) dialog and perform the needed actions. """
    def __init__(self, wt, wtpath, selected=[]):
        """ Initialize the Add file(s) dialog. """
        self.glade = gtk.glade.XML(GLADEFILENAME, 'window_add', 'olive-gtk')
        
        self.window = self.glade.get_widget('window_add')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_add_add_clicked": self.add,
                "on_button_add_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)

        self.wt = wt
        self.wtpath = wtpath
        self.selected = selected

    def display(self):
        """ Display the Add file(s) dialog. """
        self.window.show_all()
        
    def add(self, widget):
        radio_selected = self.glade.get_widget('radiobutton_add_selected')
        radio_unknown = self.glade.get_widget('radiobutton_add_unknown')
        
        if radio_selected.get_active():
            # Add only the selected file
            filename = self.selected
            
            if filename is None:
                error_dialog(_('No file was selected'),
                             _('Please select a file from the list,\nor choose the other option.'))
                return
            
            fullpath = self.wt.abspath(os.path.join(self.wtpath, filename))
            
            try:
                bzrlib.add.smart_add([fullpath])
            except errors.NotBranchError:
                error_dialog(_('Directory is not a branch'),
                             _('You can perform this action only in a branch.'))
                return
        elif radio_unknown.get_active():
            # Add unknown files recursively
            fullpath = self.wt.abspath(self.wtpath)
            
            try:
                bzrlib.add.smart_add([fullpath], True)
            except errors.NotBranchError:
                error_dialog(_('Directory is not a branch'),
                             _('You can perform this action only in a branch.'))
                return
        
        self.close()
    
    def close(self, widget=None):
        self.window.destroy()