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
from guifiles import GLADEFILENAME


class OliveMkdir:
    """ Display the Make directory dialog and perform the needed actions. """
    def __init__(self, wt, wtpath):
        """ Initialize the Make directory dialog. """
        self.glade = gtk.glade.XML(GLADEFILENAME, 'window_mkdir', 'olive-gtk')
        
        self.window = self.glade.get_widget('window_mkdir')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_mkdir_mkdir_clicked": self.mkdir,
                "on_button_mkdir_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        self.wt = wt
        self.wtpath = wtpath

    def display(self):
        """ Display the Make directory dialog. """
        self.window.show_all()

    def mkdir(self, widget):
        # Get the widgets
        entry = self.glade.get_widget('entry_mkdir')
        checkbox = self.glade.get_widget('checkbutton_mkdir_versioned')
        
        dirname = entry.get_text()
        
        if dirname == "":
            error_dialog(_('No directory name given'),
                         _('Please specify a desired name for the new directory.'))
            return
        
        if checkbox.get_active():
            # Want to create a versioned directory
            try:
                os.mkdir(os.path.join(self.wt.basedir, self.wtpath, dirname))

                self.wt.add([os.path.join(self.wtpath, dirname)])
            except OSError, e:
                if e.errno == 17:
                    error_dialog(_('Directory already exists'),
                                 _('Please specify another name to continue.'))
                else:
                    raise
            except errors.NotBranchError:
                warning_dialog(_('Directory is not in a branch'),
                               _('You can only create a non-versioned directory.'))
        else:
            # Just a simple directory
            try:
                os.mkdir(os.path.join(self.wt.basedir, self.wtpath, dirname))
            except OSError, e:
                if e.errno == 17:
                    error_dialog(_('Directory already exists'),
                                 _('Please specify another name to continue.'))
                    return

        self.close()
    
    def close(self, widget=None):
        self.window.destroy()
