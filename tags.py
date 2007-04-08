# Copyright (C) 2007 by Szilveszter Farkas (Phanatic) <szilveszter.farkas@gmail.com>
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

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gtk

from bzrlib.plugins.gtk.logview import LogView

class TagsWindow(gtk.Window):
    """ Tags window. Allows the user to view/add/remove tags. """
    def __init__(self, branch, parent=None):
        """ Initialize the Tags window. """
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        
        # Get arguments
        self.branch = branch
        self._parent = parent
        
        # Create the widgets
        self._button_add = gtk.Button(stock=gtk.STOCK_ADD)
        self._button_remove = gtk.Button(stock=gtk.STOCK_REMOVE)
        self._button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
        self._model = gtk.ListStore(str, str)
        self._treeview_tags = gtk.TreeView(self._model)
        self._scrolledwindow_tags = gtk.ScrolledWindow()
        self._logview = LogView()
        self._hbox = gtk.HBox()
        self._vbox_buttons = gtk.VBox()
        self._vpaned = gtk.VPaned()
        
        # Set callbacks
        self._button_close.connect('clicked', self._on_close_clicked)
        
        # Set properties
        self.set_title(_("Tags - Olive"))
        
        self._scrolledwindow_tags.set_policy(gtk.POLICY_AUTOMATIC,
                                             gtk.POLICY_AUTOMATIC)
        
        # Construct the dialog
        self._scrolledwindow_tags.add(self._treeview_tags)
        
        self._vbox_buttons.pack_start(self._button_add)
        self._vbox_buttons.pack_start(self._button_remove)
        self._vbox_buttons.pack_start(self._button_close)
        
        self._vpaned.add1(self._scrolledwindow_tags)
        self._vpaned.add2(self._logview)
        
        self._hbox.pack_start(self._vpaned)
        self._hbox.pack_start(self._vbox_buttons)
        
        self.add(self._hbox)
        
        # Display everything
        self._hbox.show_all()
    
    def _on_close_clicked(self, widget):
        """ Close button event handler. """
        self.destroy()
        if self._parent is None:
            gtk.main_quit()
