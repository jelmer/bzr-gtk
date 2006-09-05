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
    import gtk.gdk
    import gtk.glade
except:
    sys.exit(1)

import olive.backend.commit as commit
import olive.backend.errors as errors
import olive.backend.info as info

class OlivePush:
    """ Display Push dialog and perform the needed actions. """
    def __init__(self, gladefile, comm, dialog):
        """ Initialize the Push dialog. """
        self.gladefile = gladefile
        self.glade = gtk.glade.XML(self.gladefile, 'window_push')
        
        # Communication object
        self.comm = comm
        # Dialog object
        self.dialog = dialog
        
        self.window = self.glade.get_widget('window_push')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_push_push_clicked": self.push,
                "on_button_push_cancel_clicked": self.close,
                "on_button_push_test_clicked": self.test,
                "on_radiobutton_push_stored_toggled": self.stored_toggled,
                "on_radiobutton_push_specific_toggled": self.specific_toggled, }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        # Get some useful widgets
        self.radio_stored = self.glade.get_widget('radiobutton_push_stored')
        self.radio_specific = self.glade.get_widget('radiobutton_push_specific')
        self.entry_stored = self.glade.get_widget('entry_push_stored')
        self.entry_location = self.glade.get_widget('entry_push_location')
        self.check_remember = self.glade.get_widget('checkbutton_push_remember')
        self.check_overwrite = self.glade.get_widget('checkbutton_push_overwrite')
        self.check_create = self.glade.get_widget('checkbutton_push_create')
        self.label_test = self.glade.get_widget('label_push_test')
        self.image_test = self.glade.get_widget('image_push_test')
        
        # Set initial state
        self.entry_location.set_sensitive(0)
        self.check_remember.set_sensitive(0)
        self.check_create.set_sensitive(0)
		
        # Get stored location
        self.notbranch = False
        try:
            loc = info.get_push_location(self.comm.get_path())
        except errors.NotBranchError:
            self.notbranch = True
            return

        if loc is not None:
            self.entry_stored.set_text(loc)
    
    def display(self):
        """ Display the Push dialog. """
        if self.notbranch:
            self.dialog.error_dialog(_('Directory is not a branch'),
                                     _('You can perform this action only in a branch.'))
            self.close()
        else:
            self.window.show()
            self.width, self.height = self.window.get_size()
    
    def stored_toggled(self, widget):
        if widget.get_active():
            self.entry_stored.set_sensitive(1)
            self.entry_location.set_sensitive(0)
            self.check_remember.set_sensitive(0)
            self.check_create.set_sensitive(0)
        else:
            self.entry_stored.set_sensitive(0)
            self.entry_location.set_sensitive(1)
            self.check_remember.set_sensitive(1)
            self.check_create.set_sensitive(1)
    
    def specific_toggled(self, widget):
        if widget.get_active():
            self.entry_stored.set_sensitive(0)
            self.entry_location.set_sensitive(1)
            self.check_remember.set_sensitive(1)
            self.check_create.set_sensitive(1)
        else:
            self.entry_stored.set_sensitive(1)
            self.entry_location.set_sensitive(0)
            self.check_remember.set_sensitive(0)
            self.check_create.set_sensitive(0)
    
    def push(self, widget):
        revs = 0
        self.comm.set_busy(self.window)
        if self.radio_stored.get_active():
            try:
                revs = commit.push(self.comm.get_path(),
                                   overwrite=self.check_overwrite.get_active())
            except errors.NotBranchError:
                self.dialog.error_dialog(_('Directory is not a branch'),
                                         _('You can perform this action only in a branch.'))
                return
            except errors.NoLocationKnown:
                self.dialog.error_dialog(_('Push location is unknown'),
                                         _('Please specify a location manually.'))
                return
            except errors.NonExistingParent, errmsg:
                self.dialog.error_dialog(_('Non existing parent directory'),
                                         _("The parent directory (%s)\ndoesn't exist.") % errmsg)
                return
            except errors.DivergedBranchesError:
                self.dialog.error_dialog(_('Branches have been diverged'),
                                         _('You cannot push if branches have diverged. Use the\noverwrite option if you want to push anyway.'))
                return
            except:
                raise
        elif self.radio_specific.get_active():
            location = self.entry_location.get_text()
            if location == '':
                self.dialog.error_dialog(_('No location specified'),
                                         _('Please specify a location or use the default.'))
                return
            
            try:
                revs = commit.push(self.comm.get_path(), location,
                                   self.check_remember.get_active(),
                                   self.check_overwrite.get_active(),
                                   self.check_create.get_active())
            except errors.NotBranchError:
                self.dialog.error_dialog(_('Directory is not a branch'),
                                         _('You can perform this action only in a branch.'))
                self.comm.set_busy(self.window, False)
                return
            except errors.NonExistingParent, errmsg:
                self.dialog.error_dialog(_('Non existing parent directory'),
                                         _("The parent directory (%s)\ndoesn't exist.") % errmsg)
                self.comm.set_busy(self.window, False)
                return
            except errors.DivergedBranchesError:
                self.dialog.error_dialog(_('Branches have been diverged'),
                                         _('You cannot push if branches have diverged. Use the\noverwrite option if you want to push anyway.'))
                self.comm.set_busy(self.window, False)
                return
            except errors.PathPrefixNotCreated:
                self.dialog.error_dialog(_('Path prefix not created'),
                                         _("The path leading up to the specified location couldn't\nbe created."))
                self.comm.set_busy(self.window, False)
                return
            except:
                raise
        else:
            # This should really never happen
            pass
        
        self.close()
        self.dialog.info_dialog(_('Push successful'),
                                _('%d revision(s) pushed.') % revs)
    
    def test(self, widget):
        """ Test if write access possible. """
        import re
        _urlRE = re.compile(r'^(?P<proto>[^:/\\]+)://(?P<path>.*)$')
        
        if self.radio_stored.get_active():
            url = self.entry_stored.get_text()
        elif self.radio_specific.get_active():
            url = self.entry_location.get_text()
        
        m = _urlRE.match(url)
        if m:
            proto = m.groupdict()['proto']
            if (proto == 'sftp') or (proto == 'file') or (proto == 'ftp'):
                # have write acces (most probably)
                self.image_test.set_from_stock(gtk.STOCK_YES, 4)
                self.label_test.set_markup(_('<b>Write access is probably available</b>'))
            else:
                # no write access
                self.image_test.set_from_stock(gtk.STOCK_NO, 4)
                self.label_test.set_markup(_('<b>No write access</b>'))
        else:
            # couldn't determine
            self.image_test.set_from_stock(gtk.STOCK_DIALOG_QUESTION, 4)
            self.label_test.set_markup(_('<b>Could not determine</b>'))
    
    def close(self, widget=None):
        self.window.destroy()
