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

import olive.backend.errors as errors
import olive.backend.fileops as fileops

class OliveRemove:
    """ Display the Remove file(s) dialog and perform the needed actions. """
    def __init__(self, gladefile, comm, dialog):
        """ Initialize the Remove file(s) dialog. """
        self.gladefile = gladefile
        self.glade = gtk.glade.XML(self.gladefile, 'window_remove')
        
        # Communication object
        self.comm = comm
        # Dialog object
        self.dialog = dialog
        
        self.window = self.glade.get_widget('window_remove')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_remove_remove_clicked": self.remove,
                "on_button_remove_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)

    def display(self):
        """ Display the Remove file(s) dialog. """
        self.window.show_all()
        
    def remove(self, widget):
        radio_selected = self.glade.get_widget('radiobutton_remove_selected')
        radio_new = self.glade.get_widget('radiobutton_remove_new')
        
        directory = self.comm.get_path()
        
        self.comm.set_busy(self.window)
        if radio_selected.get_active():
            # Remove only the selected file
            filename = self.comm.get_selected_right()
            
            if filename is None:
                self.dialog.error_dialog('No file was selected',
                                         'Please select a file from the list,\nor choose the other option.')
                return
            
            try:
                fileops.remove([directory + '/' + filename])
            except errors.NotBranchError:
                self.dialog.error_dialog('Directory is not a branch',
                                         'You can perform this action only in a branch.')
                self.comm.set_busy(self.window, False)
                return
            except errors.NotVersionedError:
                self.dialog.error_dialog('File not versioned',
                                         'The selected file is not versioned.')
                self.comm.set_busy(self.window, False)
                return
            except:
                raise
        elif radio_new.get_active():
            # Remove added files recursively
            try:
                fileops.remove([directory], True)
            except errors.NotBranchError:
                self.dialog.error_dialog('Directory is not a branch',
                                         'You can perform this action only in a branch.')
                self.comm.set_busy(self.window, False)
                return
            except errors.NoMatchingFiles:
                dialog.warning_dialog('No matching files',
                                      'No added files were found in the working tree.')
                self.comm.set_busy(self.window, False)
            except:
                raise
        else:
            # This should really never happen.
            pass
        
        self.close()
        self.comm.refresh_right()
    
    def close(self, widget=None):
        self.window.destroy()
