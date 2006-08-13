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

import olive.backend.errors as errors
import olive.backend.fileops as fileops

class OliveRename:
    """ Display the Rename dialog and perform the needed actions. """
    def __init__(self, gladefile, comm, dialog):
        """ Initialize the Rename dialog. """
        self.gladefile = gladefile
        self.glade = gtk.glade.XML(self.gladefile, 'window_rename')
        
        # Communication object
        self.comm = comm
        # Dialog object
        self.dialog = dialog
        
        self.window = self.glade.get_widget('window_rename')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_rename_rename_clicked": self.rename,
                "on_button_rename_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
    def display(self):
        """ Display the Rename dialog. """
        self.window.show_all()

    def rename(self, widget):
        # Get entry
        entry = self.glade.get_widget('entry_rename')
        
        old_filename = self.comm.get_selected_right()
        new_filename = entry.get_text()
            
        if old_filename is None:
            self.dialog.error_dialog('No file was selected',
                                     'Please select a file from the list to proceed.')
            return
        
        if new_filename == "":
            self.dialog.error_dialog('Filename not given',
                                     'Please specify a new name for the file.')
            return
        
        source = self.comm.get_path() + '/' + old_filename
        destination = self.comm.get_path() + '/' + new_filename
        
        # Rename the file
        try:
            fileops.rename(source, destination)
        except errors.NotBranchError:
            self.dialog.error_dialog('File is not in a branch',
                                     'The selected file is not in a branch.')
            return
        except errors.NotSameBranchError:
            self.dialog.error_dialog('Not the same branch',
                                     'The destination is not in the same branch.')
            return
        except:
            raise

        self.close()
        self.comm.refresh_right()
    
    def close(self, widget=None):
        self.window.destroy()
