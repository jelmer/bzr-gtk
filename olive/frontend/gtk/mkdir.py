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

class OliveMkdir:
    """ Display the Make directory dialog and perform the needed actions. """
    def __init__(self, gladefile, comm, dialog):
        """ Initialize the Make directory dialog. """
        self.gladefile = gladefile
        self.glade = gtk.glade.XML(self.gladefile, 'window_mkdir')
        
        # Communication object
        self.comm = comm
        # Dialog object
        self.dialog = dialog
        
        self.window = self.glade.get_widget('window_mkdir')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_mkdir_mkdir_clicked": self.mkdir,
                "on_button_mkdir_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)

    def display(self):
        """ Display the Make directory dialog. """
        self.window.show_all()

    def mkdir(self, widget):
        # Get the widgets
        entry = self.glade.get_widget('entry_mkdir')
        checkbox = self.glade.get_widget('checkbutton_mkdir_versioned')
        
        dirname = entry.get_text()
        
        if dirname == "":
            self.dialog.error_dialog('No directory name given',
                                     'Please specify a desired name for the new directory.')
            return
        
        newdir = self.comm.get_path() + '/' + dirname
        
        if checkbox.get_active():
            # Want to create a versioned directory
            try:
                fileops.mkdir(newdir)
            except errors.DirectoryAlreadyExists:
                self.dialog.error_dialog('Directory already exists',
                                         'Please specify another name to continue.')
                return
            except errors.NotBranchError:
                self.dialog.warning_dialog('Directory is not in a branch',
                                           'You can only create a non-versioned directory.')
        else:
            # Just a simple directory
            try:
                os.mkdir(newdir)
            except OSError, e:
                if e.errno == 17:
                    self.dialog.error_dialog('Directory already exists',
                                             'Please specify another name to continue.')
                    return

        self.close()
        self.comm.refresh_right()
    
    def close(self, widget=None):
        self.window.destroy()
