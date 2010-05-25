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


class MoveDialog(gtk.Dialog):
    """ Display the Move dialog and perform the needed actions. """
    
    def __init__(self, wt, wtpath, selected, parent=None):
        """ Initialize the Move dialog. """
        gtk.Dialog.__init__(self, title="Olive - Move",
                                  parent=parent,
                                  flags=0,
                                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        
        # Get arguments
        self.wt = wt
        self.wtpath = wtpath
        self.selected = selected
        
        if self.selected is None:
            self.selected = ""
        
        if self.wtpath == "":
            directory = os.path.dirname(self.wt.abspath(self.selected))
        else:
            directory = os.path.dirname(self.wt.abspath(self.wtpath + os.sep + self.selected))
        
        # Create widgets
        self._hbox = gtk.HBox()
        self._label_move_to = gtk.Label(_i18n("Move to"))
        self._filechooser_dialog = gtk.FileChooserDialog(title="Please select a folder",
                                    parent=self.window,
                                    action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                    buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                             gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        self._filechooser_dialog.set_default_response(gtk.RESPONSE_OK)
        self.filechooser = gtk.FileChooserButton(self._filechooser_dialog)
        self._button_move = gtk.Button(_i18n("_Move"))
        self._button_move_icon = gtk.Image()
        self._button_move_icon.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_BUTTON)
        self._button_move.set_image(self._button_move_icon)
        
        self._button_move.connect('clicked', self._on_move_clicked)
        
        # Set location
        self._filechooser_dialog.set_current_folder(directory)
        
        # Add widgets to dialog
        self.vbox.add(self._hbox)
        self._hbox.add(self._label_move_to)
        self._hbox.add(self.filechooser)
        self._hbox.set_spacing(5)
        self.action_area.pack_end(self._button_move)
        
        self.vbox.show_all()

    @show_bzr_error
    def _on_move_clicked(self, widget):
        destination = self.filechooser.get_filename()
        
        if destination == None:
            error_dialog(_i18n('No folder was selected'),
                         _i18n('Please select a folder to move the selected file to'))
            return
        
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
        
        self.response(gtk.RESPONSE_OK)
