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

from branch import OliveBranch
from dialog import OliveDialog

class OliveHandler:
    """ Signal handler class for Olive. """
    def __init__(self, gladefile, comm):
        self.gladefile = gladefile
        self.comm = comm
        
        self.dialog = OliveDialog(self.gladefile)
    
    def on_about_activate(self, widget):
        self.dialog.about()
        
    def on_menuitem_branch_branch_activate(self, widget):
        """ Branch/Branch... menu handler. """
        branch = OliveBranch(self.gladefile, self.comm)
        branch.display()
        
    def on_treeview_right_row_activated(self, treeview, path, view_column):
        """ Occurs when somebody double-clicks or enters an item in the
        file list. """
        import os.path
        
        treeselection = treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        newdir = model.get_value(iter, 1)
        
        if newdir == '..':
            self.comm.set_path(os.path.split(self.comm.get_path())[0])
        else:
            self.comm.set_path(self.comm.get_path() + '/' + newdir)
        
        self.comm.refresh_right()
    
    def not_implemented(self, widget):
        """ Display a Not implemented error message. """
        self.dialog.error_dialog('This feature is not yet implemented.')

