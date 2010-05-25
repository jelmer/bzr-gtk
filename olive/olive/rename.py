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

import bzrlib.errors as errors
from bzrlib.workingtree import WorkingTree

from bzrlib.plugins.gtk import _i18n
from bzrlib.plugins.gtk.dialog import error_dialog
from bzrlib.plugins.gtk.errors import show_bzr_error


class RenameDialog(gtk.Dialog):
    """ Display the Rename dialog and perform the needed actions. """
    
    def __init__(self, wt, wtpath, selected=None, parent=None):
        """ Initialize the Rename file dialog. """
        gtk.Dialog.__init__(self, title="Olive - Rename files",
                                  parent=parent,
                                  flags=0,
                                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        
        # Get arguments
        self.wt = wt
        self.wtpath = wtpath
        self.selected = selected
        
        # Create widgets
        self._hbox = gtk.HBox()
        self._label_rename_to = gtk.Label(_i18n("Rename to"))
        self._entry = gtk.Entry()
        self._button_rename = gtk.Button(_i18n("_Rename"))
        self._button_rename_icon = gtk.Image()
        self._button_rename_icon.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_BUTTON)
        self._button_rename.set_image(self._button_rename_icon)
        
        self._entry.connect('activate', self._on_rename_clicked)
        self._button_rename.connect('clicked', self._on_rename_clicked)
        
        # Set text
        if self.selected is not None:
            self._entry.set_text(self.selected)
        
        # Add widgets to dialog
        self.vbox.add(self._hbox)
        self._hbox.add(self._label_rename_to)
        self._hbox.add(self._entry)
        self._hbox.set_spacing(5)
        self.action_area.pack_end(self._button_rename)
        
        self.vbox.show_all()
        
    @show_bzr_error
    def _on_rename_clicked(self, widget):
        # Get entry
        old_filename = self.selected
        new_filename = self._entry.get_text()
            
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
        
        self.response(gtk.RESPONSE_OK)
