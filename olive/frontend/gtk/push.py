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
    import gtk.gdk
    import gtk.glade
except:
    sys.exit(1)

import olive.backend.commit as commit
import olive.backend.errors as errors

class OlivePush:
    """ Display Push dialog and perform the needed actions. """
    def __init__(self, gladefile, comm):
        """ Initialize the Push dialog. """
        self.gladefile = gladefile
        self.glade = gtk.glade.XML(self.gladefile, 'window_push')
        
        self.comm = comm
        
        self.window = self.glade.get_widget('window_push')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_push_push_clicked": self.push,
                "on_button_push_cancel_clicked": self.close,
                "on_radiobutton_push_stored_toggled": self.stored_toggled,
                "on_radiobutton_push_specific_toggled": self.specific_toggled, }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        # Get some useful widgets
        self.entry_location = self.glade.get_widget('entry_push_location')
        self.check_remember = self.glade.get_widget('checkbutton_push_remember')
        self.check_overwrite = self.glade.get_widget('checkbutton_push_overwrite')
        self.check_create = self.glade.get_widget('checkbutton_push_create')
    
    def display(self):
        """ Display the Push dialog. """
        self.window.show()
        self.width, self.height = self.window.get_size()
    
    def stored_toggled(self, widget):
        if widget.get_active():
            self.entry_location.hide()
            self.check_remember.hide()
            self.check_overwrite.hide()
            self.check_create.hide()
            self.window.resize(self.width, self.height)
        else:
            self.entry_location.show()
            self.check_remember.show()
            self.check_overwrite.show()
            self.check_create.show()
    
    def specific_toggled(self, widget):
        if widget.get_active():
            self.entry_location.show()
            self.check_remember.show()
            self.check_overwrite.show()
            self.check_create.show()
        else:
            self.entry_location.hide()
            self.check_remember.hide()
            self.check_overwrite.hide()
            self.check_create.hide()
    
    def push(self, widget):
        from dialog import OliveDialog
        dialog = OliveDialog(self.gladefile)
        
        radio_stored = self.glade.get_widget('radiobutton_push_stored')
        radio_specific = self.glade.get_widget('radiobutton_push_specific')
        
        revs = 0
        self.comm.set_busy(self.window)
        if radio_stored.get_active():
            try:
                revs = commit.push(self.comm.get_path())
            except errors.NotBranchError:
                dialog.error_dialog('Directory is not a branch.')
                return
            except errors.NoLocationKnown:
                dialog.error_dialog('No location known.')
                return
            except errors.NonExistingParent, errmsg:
                dialog.error_dialog('Parent directory doesn\'t exist: %s', errmsg)
                return
            except errors.DivergedBranchesError:
                dialog.error_dialog('Branches have been diverged.')
                return
            except:
                raise
        elif radio_specific.get_active():
            location = self.entry_location.get_text()
            if location == '':
                dialog.error_dialog('No location specified.')
                return
            
            try:
                revs = commit.push(self.comm.get_path(), location,
                                   self.check_remember.get_active(),
                                   self.check_overwrite.get_active(),
                                   self.check_create.get_active())
            except errors.NotBranchError:
                dialog.error_dialog('Directory is not a branch.')
                self.comm.set_busy(self.window, False)
                return
            except errors.NonExistingParent, errmsg:
                dialog.error_dialog('Parent directory doesn\'t exist: %s', errmsg)
                self.comm.set_busy(self.window, False)
                return
            except errors.DivergedBranchesError:
                dialog.error_dialog('Branches have been diverged.')
                self.comm.set_busy(self.window, False)
                return
            except errors.PathPrefixNotCreated:
                dialog.error_dialog('Path prefix couldn\'t be created.')
                self.comm.set_busy(self.window, False)
                return
            except:
                raise
        else:
            # This should really never happen
            pass
        
        self.close()
        dialog.info_dialog('%d revision(s) pushed.' % revs)
    
    def close(self, widget=None):
        self.window.destroy()
