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
from bzrlib.branch import Branch

from dialog import OliveDialog
from menu import OliveMenu
from launch import launch

class OliveHandler:
    """ Signal handler class for Olive. """
    def __init__(self, gladefile, comm):
        self.gladefile = gladefile
        self.comm = comm
        
        self.dialog = OliveDialog(self.gladefile)
        
        self.menu = OliveMenu(self.gladefile, self.comm, self.dialog)
    
    def on_about_activate(self, widget):
        self.dialog.about()
        
    def on_menuitem_add_files_activate(self, widget):
        """ Add file(s)... menu handler. """
        from add import OliveAdd
        add = OliveAdd(self.gladefile, self.comm, self.dialog)
        add.display()
    
    def on_menuitem_branch_get_activate(self, widget):
        """ Branch/Get... menu handler. """
        from branch import OliveBranch
        branch = OliveBranch(self.gladefile, self.comm, self.dialog)
        branch.display()
    
    def on_menuitem_branch_checkout_activate(self, widget):
        """ Branch/Checkout... menu handler. """
        from checkout import OliveCheckout
        checkout = OliveCheckout(self.gladefile, self.comm, self.dialog)
        checkout.display()
    
    def on_menuitem_branch_commit_activate(self, widget):
        """ Branch/Commit... menu handler. """
        from commit import OliveCommit
        commit = OliveCommit(self.gladefile, self.comm, self.dialog)
        commit.display()
    
    def on_menuitem_branch_missing_revisions_activate(self, widget):
        """ Branch/Missing revisions menu handler. """
        
        self.comm.set_busy(self.comm.window_main)
        
        try:
            import bzrlib
            
            try:
                local_branch = Branch.open_containing(self.comm.get_path())[0]
            except NotBranchError:
                self.dialog.error_dialog(_('Directory is not a branch'),
                                         _('You can perform this action only in a branch.'))
                return
            
            other_branch = local_branch.get_parent()
            if other_branch is None:
                self.dialog.error_dialog(_('Parent location is unknown'),
                                         _('Cannot determine missing revisions if no parent location is known.'))
                return
            
            remote_branch = Branch.open(other_branch)
            
            if remote_branch.base == local_branch.base:
                remote_branch = local_branch

            ret = len(local_branch.missing_revisions(remote_branch))

            if ret > 0:
                self.dialog.info_dialog(_('There are missing revisions'),
                                        _('%d revision(s) missing.') % ret)
            else:
                self.dialog.info_dialog(_('Local branch up to date'),
                                        _('There are no missing revisions.'))
        finally:
            self.comm.set_busy(self.comm.window_main, False)
    
    def on_menuitem_branch_pull_activate(self, widget):
        """ Branch/Pull menu handler. """
        
        self.comm.set_busy(self.comm.window_main)

        try:
            try:
                from bzrlib.workingtree import WorkingTree
                tree_to = WorkingTree.open_containing(self.comm.get_path())[0]
                branch_to = tree_to.branch
            except errors.NoWorkingTree:
                tree_to = None
                branch_to = Branch.open_containing(self.comm.get_path())[0]
            except errors.NotBranchError:
                 self.dialog.error_dialog(_('Directory is not a branch'),
                                         _('You can perform this action only in a branch.'))

            location = branch_to.get_parent()
            if location is None:
                self.dialog.error_dialog(_('Parent location is unknown'),
                                         _('Pulling is not possible until there is a parent location.'))
                return

            try:
                branch_from = Branch.open(location)
            except errors.NotBranchError:
                self.dialog.error_dialog(_('Directory is not a branch'),
                                         _('You can perform this action only in a branch.'))

            if branch_to.get_parent() is None:
                branch_to.set_parent(branch_from.base)

            old_rh = branch_to.revision_history()
            if tree_to is not None:
                tree_to.pull(branch_from)
            else:
                branch_to.pull(branch_from)
            
            self.dialog.info_dialog(_('Pull successful'),
                                    _('%d revision(s) pulled.') % ret)
            
        finally:
            self.comm.set_busy(self.comm.window_main, False)
    
    def on_menuitem_branch_push_activate(self, widget):
        """ Branch/Push... menu handler. """
        from push import OlivePush
        push = OlivePush(self.gladefile, self.comm, self.dialog)
        push.display()
    
    def on_menuitem_branch_status_activate(self, widget):
        """ Branch/Status... menu handler. """
        from status import OliveStatus
        status = OliveStatus(self.gladefile, self.comm, self.dialog)
        status.display()
    
    def on_menuitem_branch_initialize_activate(self, widget):
        """ Initialize current directory. """
        try:
            location = self.comm.get_path()
            from bzrlib.builtins import get_format_type

            format = get_format_type('default')
 
            if not os.path.exists(location):
                os.mkdir(location)
     
            try:
                existing_bzrdir = bzrdir.BzrDir.open(location)
            except NotBranchError:
                bzrdir.BzrDir.create_branch_convenience(location, format=format)
            else:
                if existing_bzrdir.has_branch():
                    if existing_bzrdir.has_workingtree():
                        raise AlreadyBranchError(location)
                    else:
                        raise BranchExistsWithoutWorkingTree(location)
                else:
                    existing_bzrdir.create_branch()
                    existing_bzrdir.create_workingtree()
        except errors.AlreadyBranchError, errmsg:
            self.dialog.error_dialog(_('Directory is already a branch'),
                                     _('The current directory (%s) is already a branch.\nYou can start using it, or initialize another directory.') % errmsg)
        except errors.BranchExistsWithoutWorkingTree, errmsg:
            self.dialog.error_dialog(_('Branch without a working tree'),
                                     _('The current directory (%s)\nis a branch without a working tree.') % errmsg)
        else:
            self.dialog.info_dialog(_('Initialize successful'),
                                    _('Directory successfully initialized.'))
            self.comm.refresh_right()
        
    def on_menuitem_file_make_directory_activate(self, widget):
        """ File/Make directory... menu handler. """
        from mkdir import OliveMkdir
        mkdir = OliveMkdir(self.gladefile, self.comm, self.dialog)
        mkdir.display()
    
    def on_menuitem_file_move_activate(self, widget):
        """ File/Move... menu handler. """
        from move import OliveMove
        move = OliveMove(self.gladefile, self.comm, self.dialog)
        move.display()
    
    def on_menuitem_file_rename_activate(self, widget):
        """ File/Rename... menu handler. """
        from rename import OliveRename
        rename = OliveRename(self.gladefile, self.comm, self.dialog)
        rename.display()

    def on_menuitem_remove_file_activate(self, widget):
        """ Remove (unversion) selected file. """
        from remove import OliveRemove
        remove = OliveRemove(self.gladefile, self.comm, self.dialog)
        remove.display()
    
    def on_menuitem_stats_diff_activate(self, widget):
        """ Statistics/Differences... menu handler. """
        from diff import OliveDiff
        diff = OliveDiff(self.gladefile, self.comm, self.dialog)
        diff.display()
    
    def on_menuitem_stats_infos_activate(self, widget):
        """ Statistics/Informations... menu handler. """
        from info import OliveInfo
        info = OliveInfo(self.gladefile, self.comm, self.dialog)
        info.display()
    
    def on_menuitem_stats_log_activate(self, widget):
        """ Statistics/Log... menu handler. """
        from log import OliveLog
        log = OliveLog(self.gladefile, self.comm, self.dialog)
        log.display()
    
    def on_menuitem_view_refresh_activate(self, widget):
        """ View/Refresh menu handler. """
        # Refresh the left pane
        self.comm.refresh_left()
        # Refresh the right pane
        self.comm.refresh_right()
    
    def on_menuitem_view_show_hidden_files_activate(self, widget):
        """ View/Show hidden files menu handler. """
        if widget.get_active():
            # Show hidden files
            self.comm.pref.set_preference('dotted_files', True)
            self.comm.pref.refresh()
            self.comm.refresh_right()
        else:
            # Do not show hidden files
            self.comm.pref.set_preference('dotted_files', False)
            self.comm.pref.refresh()
            self.comm.refresh_right()

    def on_treeview_left_button_press_event(self, widget, event):
        """ Occurs when somebody right-clicks in the bookmark list. """
        if event.button == 3:
            # Don't show context with nothing selected
            if self.comm.get_selected_left() == None:
                return

            self.menu.left_context_menu().popup(None, None, None, 0,
                                                event.time)
        
    def on_treeview_left_row_activated(self, treeview, path, view_column):
        """ Occurs when somebody double-clicks or enters an item in the
        bookmark list. """

        newdir = self.comm.get_selected_left()
        if newdir == None:
            return

        self.comm.set_busy(treeview)
        self.comm.set_path(newdir)
        self.comm.refresh_right()
        self.comm.set_busy(treeview, False)
    
    def on_treeview_right_button_press_event(self, widget, event):
        """ Occurs when somebody right-clicks in the file list. """
        if event.button == 3:
            # get the menu items
            m_add = self.menu.ui.get_widget('/context_right/add')
            m_remove = self.menu.ui.get_widget('/context_right/remove')
            m_commit = self.menu.ui.get_widget('/context_right/commit')
            m_diff = self.menu.ui.get_widget('/context_right/diff')
            # check if we're in a branch
            try:
                from bzrlib.branch import Branch
                Branch.open_containing(self.comm.get_path())
                m_add.set_sensitive(False)
                m_remove.set_sensitive(False)
                m_commit.set_sensitive(False)
                m_diff.set_sensitive(False)
            except errors.NotBranchError:
                m_add.set_sensitive(True)
                m_remove.set_sensitive(True)
                m_commit.set_sensitive(True)
                m_diff.set_sensitive(True)
            self.menu.right_context_menu().popup(None, None, None, 0,
                                                 event.time)
        
    def on_treeview_right_row_activated(self, treeview, path, view_column):
        """ Occurs when somebody double-clicks or enters an item in the
        file list. """
        import os.path
        
        newdir = self.comm.get_selected_right()
        
        if newdir == '..':
            self.comm.set_path(os.path.split(self.comm.get_path())[0])
        else:
            fullpath = self.comm.get_path() + os.sep + newdir
            if os.path.isdir(fullpath):
                # selected item is an existant directory
                self.comm.set_path(fullpath)
            else:
                launch(fullpath) 
        
        self.comm.refresh_right()
    
    def on_window_main_delete_event(self, widget, event=None):
        """ Do some stuff before exiting. """
        width, height = self.comm.window_main.get_size()
        self.comm.pref.set_preference('window_width', width)
        self.comm.pref.set_preference('window_height', height)
        x, y = self.comm.window_main.get_position()
        self.comm.pref.set_preference('window_x', x)
        self.comm.pref.set_preference('window_y', y)
        self.comm.pref.set_preference('paned_position',
                                      self.comm.hpaned_main.get_position())
        
        self.comm.pref.write()
        self.comm.window_main.destroy()

    def not_implemented(self, widget):
        """ Display a Not implemented error message. """
        self.dialog.error_dialog(_('We feel sorry'),
                                 _('This feature is not yet implemented.'))

