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

import bzrlib.errors as errors

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
                print _('UI description file cannot be found.')
                sys.exit(1)
        
        self.gladefile = gladefile
        self.comm = comm
        self.dialog = dialog
        
        # Create the file list context menu
        self.ui = gtk.UIManager()
        
        self.actiongroup = gtk.ActionGroup('context')
        self.actiongroup.add_actions([('add', gtk.STOCK_ADD,
                                       _('Add'), None,
                                       _('Add the selected file'),
                                       self.add_file),
                                      ('remove', gtk.STOCK_REMOVE,
                                       _('Remove'), None,
                                       _('Remove the selected file'),
                                       self.remove_file),
                                      ('commit', None,
                                       _('Commit'), None,
                                       _('Commit the changes'),
                                       self.commit),
                                      ('diff', None,
                                       _('Diff'), None,
                                       _('Show the diff of the file'),
                                       self.diff),
                                      ('bookmark', None,
                                       _('Bookmark'), None,
                                       _('Bookmark current location'),
                                       self.bookmark),
                                      ('edit_bookmark', gtk.STOCK_EDIT,
                                       _('Edit'), None,
                                       _('Edit the selected bookmark'),
                                       self.edit_bookmark),
                                      ('remove_bookmark', gtk.STOCK_REMOVE,
                                       _('Remove'), None,
                                       _('Remove the selected bookmark'),
                                       self.remove_bookmark),
                                      ('diff_selected', None,
                                       _('Selected...'), None,
                                       _('Show the differences of the selected file'),
                                       self.diff_selected),
                                      ('diff_all', None,
                                       _('All...'), None,
                                       _('Show the differences of all files'),
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
            self.dialog.error_dialog(_('No file was selected'),
                                     _('Please select a file from the list,\nor choose the other option.'))
            return
        
        try:
            bzrlib.add.smart_add([directory + '/' + filename])
        except errors.NotBranchError:
            self.dialog.error_dialog(_('Directory is not a branch'),
                                     _('You can perform this action only in a branch.'))
            return
        
        self.comm.refresh_right()
    
    def remove_file(self, action):
        """ Right context menu -> Remove """
        # Remove only the selected file
        directory = self.comm.get_path()
        filename = self.comm.get_selected_right()
        
        if filename is None:
            self.dialog.error_dialog(_('No file was selected'),
                                     _('Please select a file from the list,\nor choose the other option.'))
            return
        
        try:
            fileops.remove([directory + '/' + filename])
        except errors.NotBranchError:
            self.dialog.error_dialog(_('Directory is not a branch'),
                                     _('You can perform this action only in a branch.'))
            return
        except errors.NotVersionedError:
            self.dialog.error_dialog(_('File not versioned'),
                                     _('The selected file is not versioned.'))
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
            self.dialog.info_dialog(_('Bookmark successfully added'),
                                    _('The current directory was bookmarked. You can reach\nit by selecting it from the left panel.'))
        else:
            self.dialog.warning_dialog(_('Location already bookmarked'),
                                       _('The current directory is already bookmarked.\nSee the left panel for reference.'))
        
        self.comm.refresh_left()

    def edit_bookmark(self, action):
        """ Left context menu -> Edit """
        from bookmark import OliveBookmark
        bookmark = OliveBookmark(self.gladefile, self.comm, self.dialog)
        bookmark.display()

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
