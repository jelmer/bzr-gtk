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
import os.path
import shutil
import sys

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gtk
from dialog import question_dialog

import bzrlib.errors as errors
from bzrlib.workingtree import WorkingTree

from bzrlib.plugins.gtk.dialog import error_dialog, info_dialog, warning_dialog
from bzrlib.plugins.gtk.errors import show_bzr_error
from bzrlib.plugins.gtk.annotate.gannotate import GAnnotateWindow
from bzrlib.plugins.gtk.annotate.config import GAnnotateConfig
from bzrlib.plugins.gtk.diff import DiffWindow
from launch import launch
from olive import Preferences

class OliveMenu:
    """ This class is responsible for building the context menus. """
    def __init__(self, path, selected, app=None):
        # Load the UI file
        from guifiles import UIFILENAME

        self.uifile = UIFILENAME

        # Preferences handler
        self.pref = Preferences()
        
        # Set default values
        self.path = path
        self.selected = selected
        self.app = app
        
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
                                      ('remove_and_delete', gtk.STOCK_REMOVE,
                                       _('Remove and delete'), None,
                                       _('Remove the selected file/dir and delete from disk'),
                                       self.remove_and_delete_file),
                                      ('rename', None,
                                       _('Rename'), None,
                                       _('Rename the selected file'),
                                       self.rename_file),
                                      ('open', gtk.STOCK_OPEN,
                                       _('Open'), None,
                                       _('Open the selected file'),
                                       self.open_file),
                                      ('revert', None,
                                       _('Revert'), None,
                                       _('Revert the changes'),
                                       self.revert),
                                      ('commit', None,
                                       _('Commit'), None,
                                       _('Commit the changes'),
                                       self.commit),
                                      ('annotate', None,
                                       _('Annotate'), None,
                                       _('Annotate the selected file'),
                                       self.annotate),
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
                                      ('open_folder', gtk.STOCK_OPEN,
                                       _('Open Folder'), None,
                                       _('Open bookmark folder in Nautilus'),
                                       self.open_folder),
                                      ('diff_selected', None,
                                       _('Selected...'), None,
                                       _('Show the differences of the selected file'),
                                       self.diff_selected),
                                      ('diff_all', None,
                                       _('All...'), None,
                                       _('Show the differences of all files'),
                                       self.diff_all),
                                      ('view_remote', None,
                                       _('View contents'), None,
                                       _('View the contents of the file in a builtin viewer'),
                                       self.view_remote),
                                      ('diff_remote', None,
                                       _('Show differences'), None,
                                       _('Show the differences between two revisions of the file'),
                                       self.diff_remote),
                                      ('revert_remote', None,
                                       _('Revert to this revision'), None,
                                       _('Revert the selected file to the selected revision'),
                                       self.revert_remote)
                                     ])
        
        self.ui.insert_action_group(self.actiongroup, 0)
        self.ui.add_ui_from_file(self.uifile)
        
        self.cmenu_right = self.ui.get_widget('/context_right')
        self.cmenu_left = self.ui.get_widget('/context_left')
        self.toolbar_diff = self.ui.get_widget('/toolbar_diff')
        self.cmenu_remote = self.ui.get_widget('/context_remote')
        
        # Set icons
        # TODO: do it without using deprecated comm
        #commit_menu = self.ui.get_widget('/context_right/commit')
        #commit_image = self.comm.menuitem_branch_commit.get_image()
        #commit_pixbuf = commit_image.get_pixbuf()
        #commit_icon = gtk.Image()
        #commit_icon.set_from_pixbuf(commit_pixbuf)
        #commit_menu.set_image(commit_icon)
        #diff_menu = self.ui.get_widget('/context_right/diff')
        #diff_image = self.comm.menuitem_stats_diff.get_image()
        #diff_pixbuf = diff_image.get_pixbuf()
        #diff_icon = gtk.Image()
        #diff_icon.set_from_pixbuf(diff_pixbuf)
        #diff_menu.set_image(diff_icon)

    def right_context_menu(self):
        return self.cmenu_right
    
    def left_context_menu(self):
        return self.cmenu_left
    
    def remote_context_menu(self):
        return self.cmenu_remote
    
    @show_bzr_error
    def add_file(self, action):
        """ Right context menu -> Add """
        import bzrlib.add
        
        # Add only the selected file
        directory = self.path
        filename = self.selected
            
        if filename is None:
            error_dialog(_('No file was selected'),
                         _('Please select a file from the list,\nor choose the other option.'))
            return
        
        bzrlib.add.smart_add([os.path.join(directory, filename)])
    
    @show_bzr_error
    def annotate(self, action):
        """ Right context menu -> Annotate """
        directory = self.path
        filename = self.selected
        
        if filename is None:
            error_dialog(_('No file was selected'),
                         _('Please select a file from the list.'))
            return
        
        wt, path = WorkingTree.open_containing(os.path.join(directory, filename))
        
        branch = wt.branch
        file_id = wt.path2id(wt.relpath(os.path.join(directory, filename)))
        
        window = GAnnotateWindow(all=False, plain=False)
        window.set_title(os.path.join(directory, filename) + " - Annotate")
        config = GAnnotateConfig(window)
        window.show()
        branch.lock_read()
        try:
            window.annotate(wt, branch, file_id)
        finally:
            branch.unlock()
    
    @show_bzr_error
    def remove_file(self, action,delete_on_disk=0):
        """ Right context menu -> Remove """
        # Remove only the selected file
        directory = self.path
        filename = self.selected
        
        if filename is None:
            error_dialog(_('No file was selected'),
                         _('Please select a file from the list,\nor choose the other option.'))
            return
        
        wt, path = WorkingTree.open_containing(os.path.join(directory, filename))
        wt.remove(path)
        
        if delete_on_disk:
            abs_filename = os.path.join(directory,filename)
            if os.path.isdir(abs_filename):
                response = question_dialog(_('Delete directory with all directories below ?'), abs_filename )
                if response == gtk.RESPONSE_YES:
                    shutil.rmtree(abs_filename)
            else:
                os.remove(abs_filename)
                
        self.app.set_path(self.path)
        self.app.refresh_right()
        
    def remove_and_delete_file(self, action):
        """ Right context menu -> Remove and delete"""
        self.remove_file(action,delete_on_disk=1)

    def rename_file(self, action):
        """ Right context menu -> Rename """
        from rename import OliveRename
        wt = WorkingTree.open_containing(self.path + os.sep + self.selected)[0]
        rename = OliveRename(wt, wt.relpath(self.path), self.selected)
        rename.display()
    
    def open_file(self, action):
        """ Right context menu -> Open """
        # Open only the selected file
        filename = self.selected
        
        if filename is None:
            error_dialog(_('No file was selected'),
                         _('Please select a file from the list,\nor choose the other option.'))
            return

        if filename == '..':
            # TODO: how to enter a directory?
            return
        else:
            fullpath = self.path + os.sep + filename
            if os.path.isdir(fullpath):
                # selected item is an existant directory
                # TODO: how to enter a directory?
                return
            else:
                launch(fullpath) 

    def revert(self, action):
        """ Right context menu -> Revert """
        wt, path = WorkingTree.open_containing(self.path)
        ret = wt.revert([os.path.join(path, self.selected)])
        if ret:
            warning_dialog(_('Conflicts detected'),
                           _('Please have a look at the working tree before continuing.'))
        else:
            info_dialog(_('Revert successful'),
                        _('All files reverted to last revision.'))
        self.app.refresh_right()       
    
    def commit(self, action):
        """ Right context menu -> Commit """
        from commit import CommitDialog
        branch = None
        try:
            wt, path = WorkingTree.open_containing(self.path)
            branch = wt.branch
        except NotBranchError, e:
            path = e.path
        
        commit = CommitDialog(wt, path, not branch, self.selected)
        response = commit.run()
        if response != gtk.RESPONSE_NONE:
            commit.hide()
        
            if response == gtk.RESPONSE_OK:
                self.app.refresh_right()
            
            commit.destroy()
    
    @show_bzr_error
    def diff(self, action):
        """ Right context menu -> Diff """
        wt = WorkingTree.open_containing(self.path)[0]
        window = DiffWindow()
        parent_tree = wt.branch.repository.revision_tree(wt.branch.last_revision())
        window.set_diff(wt.branch.nick, wt, parent_tree)
        window.set_file(wt.relpath(self.path + os.sep + self.selected))
        window.show()
    
    def bookmark(self, action):
        """ Right context menu -> Bookmark """
        if self.pref.add_bookmark(self.path):
            info_dialog(_('Bookmark successfully added'),
                        _('The current directory was bookmarked. You can reach\nit by selecting it from the left panel.'))
            self.pref.write()
        else:
            warning_dialog(_('Location already bookmarked'),
                           _('The current directory is already bookmarked.\nSee the left panel for reference.'))
        
        self.app.refresh_left()

    def edit_bookmark(self, action):
        """ Left context menu -> Edit """
        from bookmark import BookmarkDialog
        
        if self.selected != None:
            bookmark = BookmarkDialog(self.selected, self.app.window)
            response = bookmark.run()
            
            if response != gtk.RESPONSE_NONE:
                bookmark.hide()
        
                if response == gtk.RESPONSE_OK:
                    self.app.refresh_left()
            
                bookmark.destroy()

    def remove_bookmark(self, action):
        """ Left context menu -> Remove """
        
        if self.selected != None:
            self.pref.remove_bookmark(self.selected)
            self.pref.write()
        
        self.app.refresh_left()
    
    def open_folder(self, action):
        """ Left context menu -> Open Folder """
        path = self.selected

        if path != None:
            launch(path)
    
    def diff_selected(self, action):
        """ Diff toolbutton -> Selected... """
        print "DEBUG: not implemented."
    
    def diff_all(self, action):
        """ Diff toolbutton -> All... """
        from diff import OliveDiff
        diff = OliveDiff(self.comm)
        diff.display()
    
    def view_remote(self, action):
        """ Remote context menu -> View contents """
        print "DEBUG: view contents."
    
    def diff_remote(self, action):
        """ Remote context menu -> Show differences """
        print "DEBUG: show differences."
    
    def revert_remote(self, action):
        """ Remote context menu -> Revert to this revision """
        print "DEBUG: revert to this revision."
