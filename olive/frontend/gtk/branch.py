# Copyright (C) 2006 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

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

import olive.backend.init as init
import olive.backend.errors as errors

class OliveBranch:
    """ Display branch dialog and perform the needed operations. """
    def __init__(self, gladefile, comm):
        """ Initialize the Branch dialog. """
        self.gladefile = gladefile
        self.glade = gtk.glade.XML(self.gladefile, 'window_branch')
        
        self.comm = comm
        
        self.window = self.glade.get_widget('window_branch')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_branch_branch_clicked": self.branch,
                "on_button_branch_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        # Save FileChooser state
        self.filechooser = self.glade.get_widget('filechooserbutton_branch')
        self.filechooser.set_filename(self.comm.get_path())

    def display(self):
        """ Display the Branch dialog. """
        self.window.show_all()
    
    def branch(self, widget):
        from dialog import OliveDialog
        dialog = OliveDialog(self.gladefile)
        
        entry_location = self.glade.get_widget('entry_branch_location')
        location = entry_location.get_text()
        if location is '':
            dialog.error_dialog('You must specify a branch location.')
            return
        
        destination = self.filechooser.get_filename()
        
        spinbutton_revno = self.glade.get_widget('spinbutton_branch_revno')
        revno = spinbutton_revno.get_value_as_int()
        if revno == 0:
            revno = None
        
        self.comm.set_busy(self.window)
        try:
            init.branch(location, destination, revno)
        except errors.NonExistingSource, errmsg:
            dialog.error_dialog('Non existing source: %s' % errmsg)
            self.comm.set_busy(self.window, False)
            return
        except errors.TargetAlreadyExists, errmsg:
            dialog.error_dialog('Target already exists: %s' % errmsg)
            self.comm.set_busy(self.window, False)
            return
        except errors.NonExistingParent, errmsg:
            dialog.error_dialog('Parent directory doesn\'t exist: %s' % errmsg)
            self.comm.set_busy(self.window, False)
            return
        except errors.NonExistingRevision:
            dialog.error_dialog('The given revision doesn\'t exist.')
            self.comm.set_busy(self.window, False)
            return
        except errors.NotBranchError, errmsg:
            dialog.error_dialog('Not a branch: %s' % errmsg)
            self.comm.set_busy(self.window, False)
            return
        except:
            raise
        
        self.close()
        self.comm.refresh_right()

    def close(self, widget=None):
        self.window.destroy()
