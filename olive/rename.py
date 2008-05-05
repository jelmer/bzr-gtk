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
from bzrlib.workingtree import WorkingTree

from errors import show_bzr_error
from bzrlib.plugins.gtk.dialog import error_dialog
from guifiles import GLADEFILENAME
from bzrlib.plugins.gtk import _i18n


class OliveRename:
    """ Display the Rename dialog and perform the needed actions. """
    def __init__(self, wt, wtpath, selected=[]):
        """ Initialize the Rename dialog. """
        self.glade = gtk.glade.XML(GLADEFILENAME, 'window_rename')
        
        self.window = self.glade.get_widget('window_rename')
        self.entry = self.glade.get_widget('entry_rename')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_rename_rename_clicked": self.rename,
                "on_button_rename_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        self.wt = wt
        self.wtpath = wtpath
        self.selected = selected
        
    def display(self):
        """ Display the Rename dialog. """
        if self.selected is not None:
            self.entry.set_text(self.selected)
        
        self.window.show_all()

    @show_bzr_error
    def rename(self, widget):
        # Get entry
        old_filename = self.selected
        new_filename = self.entry.get_text()
            
        if old_filename is None:
            error_dialog(_i18n('No file was selected'),
                         _i18n('Please select a file from the list to proceed.'))
            return
        
        if new_filename == "":
            error_dialog(_i18n('Filename not given'),
                         _i18n('Please specify a new name for the file.'))
            return
        
        source = os.path.join(self.wtpath, old_filename)
        destination = os.path.join(self.wtpath, new_filename)
        
        # Rename the file
        wt1, path1 = WorkingTree.open_containing(self.wt.abspath(source))
        wt2, path2 = WorkingTree.open_containing(self.wt.abspath(source))

        if wt1.basedir != wt2.basedir:
            error_dialog(_i18n('Not the same branch'),
                         _i18n('The destination is not in the same branch.'))
            return
        wt1.rename_one(source, destination)
        self.close()
    
    def close(self, widget=None):
        self.window.destroy()
