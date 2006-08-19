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

class OliveMenu:
    """ This class is responsible for building the context menus. """
    def __init__(self, gladefile, comm, dialog):
        # Load the UI file
        if sys.platform == 'win32':
            self.uifile = os.path.dirname(sys.executable) + "/share/olive/cmenu.ui"
        else:
            self.uifile = "/usr/share/olive/cmenu.ui"
        
        if not os.path.exists(self.uifile):
            # Load from current directory if not installed
            self.uifile = "cmenu.ui"
            # Check again
            if not os.path.exists(self.uifile):
                # Fail
                print "UI description file cannot be found."
                sys.exit(1)
        
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
                                      ('commit', None,
                                       'Commit', None,
                                       'Commit the changes',
                                       self.commit),
                                      ('diff', None,
                                       'Diff', None,
                                       'Show the diff of the file',
                                       self.diff),
                                      ('bookmark', None,
                                       'Bookmark', None,
                                       'Bookmark current location',
                                       self.bookmark),
                                      ('remove_bookmark', gtk.STOCK_REMOVE,
                                       'Remove', None,
                                       'Remove the selected bookmark',
                                       self.remove_bookmark),
                                      ('diff_selected', None,
                                       'Selected...', None,
                                       'Show the differences of the selected file',
                                       self.diff_selected),
                                      ('diff_all', None,
                                       'All...', None,
                                       'Show the differences of all files',
                                       self.diff_all)
                                     ])
        
        self.ui.insert_action_group(self.actiongroup, 0)
        self.ui.add_ui_from_file(self.uifile)
        
        self.cmenu_right = self.ui.get_widget('/context_right')
        self.cmenu_left = self.ui.get_widget('/context_left')
        self.toolbar_diff = self.ui.get_widget('/toolbar_diff')
        
        # Set icons
        commit_menu = self.ui.get_widget('/context_right/commit')
        commit_image = self.comm.menuitem_branch_commit.get_image()
        commit_pixbuf = commit_image.get_pixbuf()
        commit_icon = gtk.Image()
        commit_icon.set_from_pixbuf(commit_pixbuf)
        commit_menu.set_image(commit_icon)
        diff_menu = self.ui.get_widget('/context_right/diff')
        diff_image = self.comm.menuitem_stats_diff.get_image()
        diff_pixbuf = diff_image.get_pixbuf()
        diff_icon = gtk.Image()
        diff_icon.set_from_pixbuf(diff_pixbuf)
        diff_menu.set_image(diff_icon)

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
            self.dialog.error_dialog('No file was selected',
                                     'Please select a file from the list,\nor choose the other option.')
            return
        
        try:
            fileops.add([directory + '/' + filename])
        except errors.NotBranchError:
            self.dialog.error_dialog('Directory is not a branch',
                                     'You can perform this action only in a branch.')
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
            self.dialog.error_dialog('No file was selected',
                                     'Please select a file from the list,\nor choose the other option.')
            return
        
        try:
            fileops.remove([directory + '/' + filename])
        except errors.NotBranchError:
            self.dialog.error_dialog('Directory is not a branch',
                                     'You can perform this action only in a branch.')
            return
        except errors.NotVersionedError:
            self.dialog.error_dialog('File not versioned',
                                     'The selected file is not versioned.')
            return
        except:
            raise
        
        self.comm.refresh_right()

    def commit(self, action):
        """ Right context menu -> Commit """
        from commit import OliveCommit
        commit = OliveCommit(self.gladefile, self.comm, self.dialog)
        commit.display()
    
    def diff(self, action):
        """ Right context menu -> Diff """
        from diff import OliveDiff
        diff = OliveDiff(self.gladefile, self.comm, self.dialog)
        diff.display()
    
    def bookmark(self, action):
        """ Right context menu -> Bookmark """
        if self.comm.pref.add_bookmark(self.comm.get_path()):
            self.dialog.info_dialog('Bookmark successfully added',
                                    'The current directory was bookmarked. You can reach\nit by selecting it from the left panel.')
        else:
            self.dialog.warning_dialog('Location already bookmarked'
                                       'The current directory is already bookmarked.\nSee the left panel for reference.')
        
        self.comm.refresh_left()

    def remove_bookmark(self, action):
        """ Left context menu -> Remove """
        self.comm.pref.remove_bookmark(self.comm.get_selected_left())
        
        self.comm.refresh_left()
    
    def diff_selected(self, action):
        """ Diff toolbutton -> Selected... """
        print "DEBUG: not implemented."
    
    def diff_all(self, action):
        """ Diff toolbutton -> All... """
        from diff import OliveDiff
        diff = OliveDiff(self.gladefile, self.comm, self.dialog)
        diff.display()
