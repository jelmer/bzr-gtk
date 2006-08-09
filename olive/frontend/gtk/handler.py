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

import olive.backend.errors as errors

from dialog import OliveDialog
from menu import OliveMenu

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
        add = OliveAdd(self.gladefile, self.comm)
        add.display()
    
    def on_menuitem_branch_get_activate(self, widget):
        """ Branch/Get... menu handler. """
        from branch import OliveBranch
        branch = OliveBranch(self.gladefile, self.comm)
        branch.display()
    
    def on_menuitem_branch_checkout_activate(self, widget):
        """ Branch/Checkout... menu handler. """
        from checkout import OliveCheckout
        checkout = OliveCheckout(self.gladefile, self.comm)
        checkout.display()
    
    def on_menuitem_branch_commit_activate(self, widget):
        """ Branch/Commit... menu handler. """
        from commit import OliveCommit
        commit = OliveCommit(self.gladefile, self.comm)
        commit.display()
    
    def on_menuitem_branch_pull_activate(self, widget):
        """ Branch/Pull menu handler. """
        import olive.backend.update as update
        
        self.comm.set_busy(self.comm.window_main)
        
        try:
            ret = update.pull(self.comm.get_path())
        except errors.NotBranchError:
            self.dialog.error_dialog('Directory is not a branch.')
        except errors.NoLocationKnown:
            self.dialog.error_dialog('Parent location is unknown.')
        else:
            self.dialog.info_dialog('%d revision(s) pulled.' % ret)
        
        self.comm.set_busy(self.comm.window_main, False)
    
    def on_menuitem_branch_push_activate(self, widget):
        """ Branch/Push... menu handler. """
        from push import OlivePush
        push = OlivePush(self.gladefile, self.comm)
        push.display()
    
    def on_menuitem_branch_status_activate(self, widget):
        """ Branch/Status... menu handler. """
        from status import OliveStatus
        status = OliveStatus(self.gladefile, self.comm)
        status.display()
    
    def on_menuitem_branch_initialize_activate(self, widget):
        """ Initialize current directory. """
        import olive.backend.init as init
        
        try:
            init.init(self.comm.get_path())
        except errors.AlreadyBranchError, errmsg:
            self.dialog.error_dialog('Directory is already a branch: %s' % errmsg)
        except errors.BranchExistsWithoutWorkingTree, errmsg:
            self.dialog.error_dialog('Branch exists without a working tree: %s' % errmsg)
        else:
            self.dialog.info_dialog('Directory successfully initialized.')
            self.comm.refresh_right()
        
    def on_menuitem_file_make_directory_activate(self, widget):
        """ File/Make directory... menu handler. """
        from mkdir import OliveMkdir
        mkdir = OliveMkdir(self.gladefile, self.comm)
        mkdir.display()
    
    def on_menuitem_file_move_activate(self, widget):
        """ File/Move... menu handler. """
        from move import OliveMove
        move = OliveMove(self.gladefile, self.comm)
        move.display()
    
    def on_menuitem_file_rename_activate(self, widget):
        """ File/Rename... menu handler. """
        from rename import OliveRename
        rename = OliveRename(self.gladefile, self.comm)
        rename.display()

    def on_menuitem_remove_file_activate(self, widget):
        """ Remove (unversion) selected file. """
        from remove import OliveRemove
        remove = OliveRemove(self.gladefile, self.comm)
        remove.display()
    
    def on_menuitem_stats_diff_activate(self, widget):
        """ Statistics/Differences... menu handler. """
        from diff import OliveDiff
        diff = OliveDiff(self.gladefile, self.comm)
        diff.display()
    
    def on_treeview_left_button_press_event(self, widget, event):
        """ Occurs when somebody right-clicks in the bookmark list. """
        if event.button == 3:
            self.menu.left_context_menu().popup(None, None, None, 0,
                                                 event.time)
        
    def on_treeview_left_row_activated(self, treeview, path, view_column):
        """ Occurs when somebody double-clicks or enters an item in the
        bookmark list. """
        self.comm.set_busy(treeview)
        
        newdir = self.comm.get_selected_left()
        self.comm.set_path(newdir)
        
        self.comm.refresh_right()
        
        self.comm.set_busy(treeview, False)
    
    def on_treeview_right_button_press_event(self, widget, event):
        """ Occurs when somebody right-clicks in the file list. """
        if event.button == 3:
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
            self.comm.set_path(self.comm.get_path() + '/' + newdir)
        
        self.comm.refresh_right()
    
    def on_window_main_delete_event(self, widget, event=None):
        """ Do some stuff before exiting. """
        self.comm.pref.write()
        self.comm.window_main.destroy()

    def not_implemented(self, widget):
        """ Display a Not implemented error message. """
        self.dialog.error_dialog('This feature is not yet implemented.')

