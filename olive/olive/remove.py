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

from bzrlib.plugins.gtk import _i18n
from bzrlib.plugins.gtk.dialog import error_dialog, warning_dialog
from bzrlib.plugins.gtk.errors import show_bzr_error


class RemoveDialog(gtk.Dialog):
    """ This class wraps the old Remove window into a gtk.Dialog. """
    
    def __init__(self, wt, wtpath, selected='', parent=None):
        """ Initialize the Remove file(s) dialog. """
        gtk.Dialog.__init__(self, title="Olive - Remove files",
                                  parent=parent,
                                  flags=0,
                                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        
        # Get arguments
        self.wt = wt
        self.wtpath = wtpath
        self.selected = selected
        
        # Create widgets
        self._label = gtk.Label(_i18n("Which file(s) do you want to remove?"))
        self._radio_selected = gtk.RadioButton(None, _i18n("Selected: %s"%self.selected), False)
        self._radio_added = gtk.RadioButton(self._radio_selected, _i18n("All files with status 'added'"), False)
        self._button_remove = gtk.Button(stock=gtk.STOCK_REMOVE)
        
        self._button_remove.connect('clicked', self._on_remove_clicked)
        
        self.vbox.add(self._label)
        self.vbox.add(self._radio_selected)
        self.vbox.add(self._radio_added)
        self.vbox.set_spacing(3)
        self.action_area.pack_end(self._button_remove)
        
        self.vbox.show_all()
        
    @show_bzr_error
    def _on_remove_clicked(self, button):
        """ Remove button clicked handler. """
        if self._radio_selected.get_active():
            # Remove only the selected file
            filename = self.selected
            
            if filename is None:
                error_dialog(_i18n('No file was selected'),
                             _i18n('Please select a file from the list,\nor choose the other option.'))
                return
            
            self.wt.remove(os.path.join(self.wtpath, filename))
        elif self._radio_added.get_active():
            # Remove added files recursively
            added = self.wt.changes_from(self.wt.basis_tree()).added
            file_list = sorted([f[0] for f in added], reverse=True)
            if len(file_list) == 0:
                warning_dialog(_i18n('No matching files'),
                               _i18n('No added files were found in the working tree.'))
                return
            self.wt.remove(file_list)
        
        self.response(gtk.RESPONSE_OK)
