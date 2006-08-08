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

import os.path
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

import olive.backend.fileops as fileops
import olive.backend.errors as errors

from commit import OliveCommit
from diff import OliveDiff

class OliveMenu:
    """ This class is responsible for building the context menus. """
    def __init__(self, gladefile, comm, dialog):
        # Load the UI file
        self.uifile = "/usr/share/olive/cmenu.ui"
        if not os.path.exists(self.uifile):
            # Load from current directory if not installed
            self.uifile = "cmenu.ui"
        
        self.gladefile = gladefile
        self.comm = comm
        self.dialog = dialog
        
        # Create the file list context menu
        self.ui = gtk.UIManager()
        
        self.actiongroup = gtk.ActionGroup('context')
        self.actiongroup.add_actions([('add', gtk.STOCK_ADD,
                                       'Add', None,
                                       'Add the selected file',
                                       self.add_file),
                                      ('remove', gtk.STOCK_REMOVE,
                                       'Remove', None,
                                       'Remove the selected file',
                                       self.remove_file),
                                      ('commit', gtk.STOCK_REDO,
                                       'Commit', None,
                                       'Commit the changes',
                                       self.commit),
                                      ('diff', None,
                                       'Diff', None,
                                       'Show the diff of the file',
                                       self.diff),
                                      ('log', None,
                                       'Log', None,
                                       'Show the log of the file',
                                       self.log),
                                      ('bookmark', None,
                                       'Bookmark', None,
                                       'Bookmark current location',
                                       self.bookmark),
                                      ('remove_bookmark', gtk.STOCK_REMOVE,
                                       'Remove', None,
                                       'Remove the selected bookmark',
                                       self.remove_bookmark)
                                     ])
        
        self.ui.insert_action_group(self.actiongroup, 0)
        self.ui.add_ui_from_file(self.uifile)
        
        self.cmenu_right = self.ui.get_widget('/context_right')
        
        self.cmenu_left = self.ui.get_widget('/context_left')

    def right_context_menu(self):
        return self.cmenu_right
    
    def left_context_menu(self):
        return self.cmenu_left
    
    def add_file(self, action):
        """ Right context menu -> Add """
        # Add only the selected file
        directory = self.comm.get_path()
        filename = self.comm.get_selected_right()
            
        if filename is None:
            self.dialog.error_dialog('No file was selected.')
            return
        
        try:
            fileops.add([directory + '/' + filename])
        except errors.NotBranchError:
            self.dialog.error_dialog('The directory is not a branch.')
            return
        except:
            raise
        
        self.comm.refresh_right()
    
    def remove_file(self, action):
        """ Right context menu -> Remove """
        # Remove only the selected file
        directory = self.comm.get_path()
        filename = self.comm.get_selected_right()
        
        if filename is None:
            self.dialog.error_dialog('No file was selected.')
            return
        
        try:
            fileops.remove([directory + '/' + filename])
        except errors.NotBranchError:
            self.dialog.error_dialog('The directory is not a branch.')
            return
        except errors.NotVersionedError:
            self.dialog.error_dialog('Selected file is not versioned.')
            return
        except:
            raise
        
        self.comm.refresh_right()

    def commit(self, action):
        """ Right context menu -> Commit """
        commit = OliveCommit(self.gladefile, self.comm)
        commit.display()
    
    def diff(self, action):
        """ Right context menu -> Diff """
        diff = OliveDiff(self.gladefile, self.comm)
        diff.display()
    
    def log(self, action):
        """ Right context menu -> Log """
        self.dialog.error_dialog('This feature is not yet implemented.')
    
    def bookmark(self, action):
        """ Right context menu -> Bookmark """
        if self.comm.pref.add_bookmark(self.comm.get_path()):
            self.dialog.info_dialog('Bookmark successfully added.')
        else:
            self.dialog.warning_dialog('Location already bookmarked.')
        
        self.comm.refresh_left()

    def remove_bookmark(self, action):
        """ Left context menu -> Remove """
        self.comm.pref.remove_bookmark(self.comm.get_selected_left())
        
        self.comm.refresh_left()
