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
  	import gtk.glade
except:
	sys.exit(1)

from olive.frontend.gtk.handler import OliveHandler

# Olive GTK UI version
__version__ = '0.1'

class OliveGtk:
    """ The main Olive GTK frontend class. This is called when launching the
    program."""
    
    def __init__(self):
        # Load the glade file
        self.gladefile = "/usr/share/olive/olive.glade"
        self.toplevel = gtk.glade.XML(self.gladefile, "window_main")
        
        handler = OliveHandler(self.gladefile)
        
        # Dictionary for signal_autoconnect
        dic = { "on_window_main_destroy": gtk.main_quit,
                "on_about_activate": handler.about }
        
        # Connect the signals to the handlers
        self.toplevel.signal_autoconnect(dic)
        
        # Load default data into the panels
        self.treeview_left = self.toplevel.get_widget('treeview_left')
        self.treeview_right = self.toplevel.get_widget('treeview_right')
        self.load_left()
        self.load_right()
    
    def load_left(self):
        """ Load data into the left panel. (Bookmarks) """
        pass
        
    def load_right(self):
        """ Load data into the right panel. (Filelist) """
        import os
        import os.path
        
        # Create ListStore
        liststore = gtk.ListStore(str, str)
        
        dirs = []
        files = []
        
        # Fill the appropriate lists
        for item in os.listdir('.'):
            if os.path.isdir(item):
                dirs.append(item)
            else:
                files.append(item)
            
        # Sort'em
        dirs.sort()
        files.sort()
        
        # Add'em to the ListStore
        for item in dirs:    
            liststore.append(['D', item])
        for item in files:
            liststore.append(['', item])
        
        # Create the columns and add them to the TreeView
        self.treeview_right.set_model(liststore)
        tvcolumn_filename = gtk.TreeViewColumn('Filename')
        tvcolumn_filetype = gtk.TreeViewColumn('Type')
        self.treeview_right.append_column(tvcolumn_filetype)
        self.treeview_right.append_column(tvcolumn_filename)
        
        # Set up the cells
        cell = gtk.CellRendererText()
        tvcolumn_filetype.pack_start(cell, True)
        tvcolumn_filetype.add_attribute(cell, 'text', 0)
        tvcolumn_filename.pack_start(cell, True)
        tvcolumn_filename.add_attribute(cell, 'text', 1)
