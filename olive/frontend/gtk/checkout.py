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

class OliveCheckout:
    """ Display checkout dialog and perform the needed operations. """
    def __init__(self, gladefile, comm):
        """ Initialize the Branch dialog. """
        self.gladefile = gladefile
        self.glade = gtk.glade.XML(self.gladefile, 'window_checkout')
        
        self.comm = comm
        
        self.window = self.glade.get_widget('window_checkout')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_checkout_checkout_clicked": self.checkout,
                "on_button_checkout_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        # Save FileChooser state
        self.filechooser = self.glade.get_widget('filechooserbutton_checkout')
        self.filechooser.set_filename(self.comm.get_path())

    def display(self):
        """ Display the Checkout dialog. """
        self.window.show_all()
    
    def checkout(self, widget):
        from dialog import OliveDialog
        dialog = OliveDialog(self.gladefile)
        print "DEBUG: dialog imported"
        
        entry_location = self.glade.get_widget('entry_checkout_location')
        location = entry_location.get_text()
        if location is '':
            dialog.error_dialog('You must specify a branch location.')
            return
        print "DEBUG: got branch location:", location
        
        destination = self.filechooser.get_filename()
        print "DEBUG: got destination:", destination
        
        spinbutton_revno = self.glade.get_widget('spinbutton_checkout_revno')
        revno = spinbutton_revno.get_value_as_int()
        if revno == 0:
            revno = None
        print "DEBUG: got revision number:", revno
        
        checkbutton_lightweight = self.glade.get_widget('checkbutton_checkout_lightweight')
        lightweight = checkbutton_lightweight.get_active()
        print "DEBUG: got lightweight:", lightweight
        
        try:
            self.comm.set_statusbar('Checkout in progress, please wait...')
            print "DEBUG: statusbar set"
            init.checkout(location, destination, revno, lightweight)
            print "DEBUG: checkout ended"
            self.comm.clear_statusbar()
            print "DEBUG: statusbar cleared"
        except errors.NotBranchError, errmsg:
            dialog.error_dialog('Not a branch: %s' % errmsg)
            self.comm.clear_statusbar()
            return
        except errors.TargetAlreadyExists, errmsg:
            dialog.error_dialog('Target already exists: %s' % errmsg)
            self.comm.clear_statusbar()
            return
        except errors.NonExistingParent, errmsg:
            dialog.error_dialog('Parent directory doesn\'t exist: %s' % errmsg)
            self.comm.clear_statusbar()
            return
        except:
            raise
        
        self.close()
        self.comm.refresh_right()

    def close(self, widget=None):
        self.window.destroy()
