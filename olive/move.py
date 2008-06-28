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
from os.path import dirname

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gtk
import gtk.glade

import bzrlib.errors as errors
from bzrlib.workingtree import WorkingTree

from bzrlib.plugins.gtk import _i18n
from bzrlib.plugins.gtk.dialog import error_dialog
from bzrlib.plugins.gtk.errors import show_bzr_error
from guifiles import GLADEFILENAME


class OliveMove:
    """ Display the Move dialog and perform the needed actions. """
    def __init__(self, wt, wtpath, selected=[]):
        """ Initialize the Move dialog. """
        self.glade = gtk.glade.XML(GLADEFILENAME, 'window_move', 'olive-gtk')
        
        self.window = self.glade.get_widget('window_move')
        
        # Dictionary for signal_autoconnect
        dic = { "on_button_move_move_clicked": self.move,
                "on_button_move_cancel_clicked": self.close }
        
        # Connect the signals to the handlers
        self.glade.signal_autoconnect(dic)
        
        self.wt = wt
        self.wtpath = wtpath
        self.selected = selected
        
        if self.selected is None:
            self.selected = ""
        
        if self.wtpath == "":
            directory = dirname(self.wt.abspath(self.selected))
        else:
            directory = dirname(self.wt.abspath(self.wtpath + os.sep + self.selected))
        
        # Set FileChooser directory
        self.filechooser = self.glade.get_widget('filechooserbutton_move')
        self.filechooser.set_filename(directory)

    def display(self):
        """ Display the Move dialog. """
        self.window.show_all()

    @show_bzr_error
    def move(self, widget):
        destination = self.filechooser.get_filename()

        filename = self.selected
            
        if filename is None:
            error_dialog(_i18n('No file was selected'),
                         _i18n('Please select a file from the list to proceed.'))
            return
        
        source = os.path.join(self.wtpath, filename)
        
        # Move the file to a directory
        wt1, path1 = WorkingTree.open_containing(self.wt.abspath(source))
        wt2, path2 = WorkingTree.open_containing(destination)
        if wt1.basedir != wt2.basedir:
            error_dialog(_i18n('Not the same branch'),
                         _i18n('The destination is not in the same branch.'))
            return

        wt1.move([source], wt1.relpath(destination))
        self.close()
    
    def close(self, widget=None):
        self.window.destroy()
