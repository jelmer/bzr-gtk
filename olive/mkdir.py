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


class MkdirDialog(gtk.Dialog):
    """ Display the Make directory dialog and perform the needed actions. """
    
    def __init__(self, wt, wtpath, parent=None):
        """ Initialize the Make directory dialog. """
        gtk.Dialog.__init__(self, title="Olive - Make directory",
                                  parent=parent,
                                  flags=0,
                                  buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        
        # Get arguments
        self.wt = wt
        self.wtpath = wtpath
        
        # Create widgets
        self._hbox = gtk.HBox()
        self._label_directory_name = gtk.Label(_i18n("Directory name"))
        self._entry = gtk.Entry()
        self._versioned = gtk.CheckButton(_i18n("_Versioned directory"), use_underline=True)
        self._button_mkdir = gtk.Button(_i18n("_Make directory"), use_underline=True)
        self._button_mkdir_icon = gtk.Image()
        self._button_mkdir_icon.set_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
        self._button_mkdir.set_image(self._button_mkdir_icon)
        
        self._entry.connect('activate', self._on_mkdir_clicked)
        self._button_mkdir.connect('clicked', self._on_mkdir_clicked)
        
        # Add widgets to dialog
        self.vbox.add(self._hbox)
        self._hbox.add(self._label_directory_name)
        self._hbox.add(self._entry)
        self._hbox.set_spacing(5)
        self.vbox.add(self._versioned)
        self.action_area.pack_end(self._button_mkdir)
        
        self.vbox.show_all()

    @show_bzr_error
    def _on_mkdir_clicked(self, widget):
        dirname = self._entry.get_text()
        
        if dirname == "":
            error_dialog(_i18n('No directory name given'),
                         _i18n('Please specify a desired name for the new directory.'))
            return
        
        try:
            os.mkdir(os.path.join(self.wt.basedir, self.wtpath, dirname))
            
            if self._versioned.get_active():
                self.wt.add([os.path.join(self.wtpath, dirname)])
        except OSError, e:
            if e.errno == 17:
                error_dialog(_i18n('Directory already exists'),
                             _i18n('Please specify another name to continue.'))
            else:
                raise
        
        self.response(gtk.RESPONSE_OK)
