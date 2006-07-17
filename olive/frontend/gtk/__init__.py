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

from handler import OliveHandler

# Olive GTK UI version
__version__ = '0.1'

class OliveGtk:
    """ The main Olive GTK frontend class. This is called when launching the
    program."""
    
    def __init__(self):
        import os.path
        
        # Load the glade file
        self.gladefile = "/usr/share/olive/olive.glade"
        if not os.path.exists(self.gladefile):
            # Load from current directory if not installed
            self.gladefile = "olive.glade"

        self.toplevel = gtk.glade.XML(self.gladefile, "window_main")
        
        handler = OliveHandler(self.gladefile)
        
        # Dictionary for signal_autoconnect
        dic = { "on_window_main_destroy": gtk.main_quit,
                "on_quit_activate": gtk.main_quit,
                "on_about_activate": handler.on_about_activate,
                "on_menuitem_file_make_directory_activate": handler.not_implemented,
                "on_menuitem_branch_commit_activate": handler.not_implemented }
        
        # Connect the signals to the handlers
        self.toplevel.signal_autoconnect(dic)
        
        # Load default data into the panels
        self.treeview_left = self.toplevel.get_widget('treeview_left')
        self.treeview_right = self.toplevel.get_widget('treeview_right')
        self._load_left()
        self._load_right()
    
    def _load_left(self):
        """ Load data into the left panel. (Bookmarks) """
        pass
        
    def _load_right(self):
        """ Load data into the right panel. (Filelist) """
        import os
        import os.path
        
        import olive.backend.fileops as fileops
        
        # Create ListStore
        liststore = gtk.ListStore(str, str, str)
        
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
            liststore.append(['D', item, ''])
        for item in files:
            liststore.append(['', item, fileops.status(item)])
        
        # Create the columns and add them to the TreeView
        self.treeview_right.set_model(liststore)
        tvcolumn_filetype = gtk.TreeViewColumn('Type')
        tvcolumn_filename = gtk.TreeViewColumn('Filename')
        tvcolumn_status = gtk.TreeViewColumn('Status')
        self.treeview_right.append_column(tvcolumn_filetype)
        self.treeview_right.append_column(tvcolumn_filename)
        self.treeview_right.append_column(tvcolumn_status)
        
        # Set up the cells
        cell = gtk.CellRendererText()
        tvcolumn_filetype.pack_start(cell, True)
        tvcolumn_filetype.add_attribute(cell, 'text', 0)
        tvcolumn_filename.pack_start(cell, True)
        tvcolumn_filename.add_attribute(cell, 'text', 1)
        tvcolumn_status.pack_start(cell, True)
        tvcolumn_status.add_attribute(cell, 'text', 2)
