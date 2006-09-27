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
import sys

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk
    import gtk.glade
except:
    sys.exit(1)

import bzrlib.errors as errors

class OliveMove:
    """ Display the Move dialog and perform the needed actions. """
    def __init__(self, gladefile, comm):
        """ Initialize the Move dialog. """
        self.gladefile = gladefile
        self.glade = gtk.glade.XML(self.gladefile, 'window_move', 'olive-gtk')
        
        # Communication object
        self.comm = comm
        
        self.window = self.glade.get_widget('window_move')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_move_move_clicked": self.move,
                "on_button_move_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        # Set FileChooser directory
        self.filechooser = self.glade.get_widget('filechooserbutton_move')
        self.filechooser.set_filename(self.comm.get_path())

    def display(self):
        """ Display the Move dialog. """
        self.window.show_all()

    def move(self, widget):
        destination = self.filechooser.get_filename()

        filename = self.comm.get_selected_right()
            
        if filename is None:
            error_dialog(_('No file was selected'),
                                     _('Please select a file from the list to proceed.'))
            return
        
        source = self.comm.get_path() + '/' + filename
        
        # Move the file to a directory
        try:
            wt1, path1 = WorkingTree.open_containing(source)
            wt2, path2 = WorkingTree.open_containing(destination)
            if wt1.base != wt2.base:
                error_dialog(_('Not the same branch'),
                                         _('The destination is not in the same branch.'))
                return

            wt1.move([source], destination)
        except errors.NotBranchError:
            error_dialog(_('File is not in a branch'),
                                     _('The selected file is not in a branch.'))
            return

        self.close()
        self.comm.refresh_right()
    
    def close(self, widget=None):
        self.window.destroy()
