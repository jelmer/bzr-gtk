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
import time

# gettext support
import gettext
gettext.install('olive-gtk')

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gobject
import gtk
import gtk.gdk
import gtk.glade

from bzrlib.branch import Branch
import bzrlib.errors as bzrerrors
from bzrlib.lazy_import import lazy_import
from bzrlib.ui import ui_factory
from bzrlib.workingtree import WorkingTree

from bzrlib.plugins.gtk.dialog import error_dialog, info_dialog, warning_dialog
from bzrlib.plugins.gtk.errors import show_bzr_error
from guifiles import GLADEFILENAME

from bzrlib.plugins.gtk.diff import DiffWindow
lazy_import(globals(), """
from bzrlib.plugins.gtk.viz import branchwin
""")
from bzrlib.plugins.gtk.annotate.gannotate import GAnnotateWindow
from bzrlib.plugins.gtk.annotate.config import GAnnotateConfig
from bzrlib.plugins.gtk.commit import CommitDialog
from bzrlib.plugins.gtk.conflicts import ConflictsDialog
from bzrlib.plugins.gtk.initialize import InitDialog
from bzrlib.plugins.gtk.push import PushDialog

class OliveGtk:
    """ The main Olive GTK frontend class. This is called when launching the
    program. """
    
    def __init__(self):
        self.toplevel = gtk.glade.XML(GLADEFILENAME, 'window_main', 'olive-gtk')
        self.window = self.toplevel.get_widget('window_main')
        self.pref = Preferences()
        self.path = None

        # Initialize the statusbar
        self.statusbar = self.toplevel.get_widget('statusbar')
        self.context_id = self.statusbar.get_context_id('olive')
        
        # Get the main window
        self.window_main = self.toplevel.get_widget('window_main')
        # Get the HPaned
        self.hpaned_main = self.toplevel.get_widget('hpaned_main')
        # Get the TreeViews
        self.treeview_left = self.toplevel.get_widget('treeview_left')
        self.treeview_right = self.toplevel.get_widget('treeview_right')
        # Get some important menu items
        self.menuitem_add_files = self.toplevel.get_widget('menuitem_add_files')
        self.menuitem_remove_files = self.toplevel.get_widget('menuitem_remove_file')
        self.menuitem_file_make_directory = self.toplevel.get_widget('menuitem_file_make_directory')
        self.menuitem_file_rename = self.toplevel.get_widget('menuitem_file_rename')
        self.menuitem_file_move = self.toplevel.get_widget('menuitem_file_move')
        self.menuitem_file_annotate = self.toplevel.get_widget('menuitem_file_annotate')
        self.menuitem_view_show_hidden_files = self.toplevel.get_widget('menuitem_view_show_hidden_files')
        self.menuitem_branch = self.toplevel.get_widget('menuitem_branch')
        self.menuitem_branch_init = self.toplevel.get_widget('menuitem_branch_initialize')
        self.menuitem_branch_get = self.toplevel.get_widget('menuitem_branch_get')
        self.menuitem_branch_checkout = self.toplevel.get_widget('menuitem_branch_checkout')
        self.menuitem_branch_pull = self.toplevel.get_widget('menuitem_branch_pull')
        self.menuitem_branch_push = self.toplevel.get_widget('menuitem_branch_push')
        self.menuitem_branch_revert = self.toplevel.get_widget('menuitem_branch_revert')
        self.menuitem_branch_merge = self.toplevel.get_widget('menuitem_branch_merge')
        self.menuitem_branch_commit = self.toplevel.get_widget('menuitem_branch_commit')
        self.menuitem_branch_tags = self.toplevel.get_widget('menuitem_branch_tags')
        self.menuitem_branch_status = self.toplevel.get_widget('menuitem_branch_status')
        self.menuitem_branch_missing = self.toplevel.get_widget('menuitem_branch_missing_revisions')
        self.menuitem_branch_conflicts = self.toplevel.get_widget('menuitem_branch_conflicts')
        self.menuitem_stats = self.toplevel.get_widget('menuitem_stats')
        self.menuitem_stats_diff = self.toplevel.get_widget('menuitem_stats_diff')
        self.menuitem_stats_log = self.toplevel.get_widget('menuitem_stats_log')
        # Get some toolbuttons
        #self.menutoolbutton_diff = self.toplevel.get_widget('menutoolbutton_diff')
        self.toolbutton_diff = self.toplevel.get_widget('toolbutton_diff')
        self.toolbutton_log = self.toplevel.get_widget('toolbutton_log')
        self.toolbutton_commit = self.toplevel.get_widget('toolbutton_commit')
        self.toolbutton_pull = self.toplevel.get_widget('toolbutton_pull')
        self.toolbutton_push = self.toplevel.get_widget('toolbutton_push')
        # Get the drive selector
        self.combobox_drive = gtk.combo_box_new_text()
        self.combobox_drive.connect("changed", self._refresh_drives)
        
        # Get the navigation widgets
        self.hbox_location = self.toplevel.get_widget('hbox_location')
        self.button_location_up = self.toplevel.get_widget('button_location_up')
        self.button_location_jump = self.toplevel.get_widget('button_location_jump')
        self.entry_location = self.toplevel.get_widget('entry_location')
        self.image_location_error = self.toplevel.get_widget('image_location_error')
        
        self.vbox_main_right = self.toplevel.get_widget('vbox_main_right')
        
        # Dictionary for signal_autoconnect
        dic = { "on_window_main_destroy": gtk.main_quit,
                "on_window_main_delete_event": self.on_window_main_delete_event,
                "on_quit_activate": self.on_window_main_delete_event,
                "on_about_activate": self.on_about_activate,
                "on_menuitem_add_files_activate": self.on_menuitem_add_files_activate,
                "on_menuitem_remove_file_activate": self.on_menuitem_remove_file_activate,
                "on_menuitem_file_make_directory_activate": self.on_menuitem_file_make_directory_activate,
                "on_menuitem_file_move_activate": self.on_menuitem_file_move_activate,
                "on_menuitem_file_rename_activate": self.on_menuitem_file_rename_activate,
                "on_menuitem_file_annotate_activate": self.on_menuitem_file_annotate_activate,
                "on_menuitem_view_show_hidden_files_activate": self.on_menuitem_view_show_hidden_files_activate,
                "on_menuitem_view_refresh_activate": self.on_menuitem_view_refresh_activate,
                "on_menuitem_branch_initialize_activate": self.on_menuitem_branch_initialize_activate,
                "on_menuitem_branch_get_activate": self.on_menuitem_branch_get_activate,
                "on_menuitem_branch_checkout_activate": self.on_menuitem_branch_checkout_activate,
                "on_menuitem_branch_revert_activate": self.on_menuitem_branch_revert_activate,
                "on_menuitem_branch_merge_activate": self.on_menuitem_branch_merge_activate,
                "on_menuitem_branch_commit_activate": self.on_menuitem_branch_commit_activate,
                "on_menuitem_branch_push_activate": self.on_menuitem_branch_push_activate,
                "on_menuitem_branch_pull_activate": self.on_menuitem_branch_pull_activate,
                "on_menuitem_branch_tags_activate": self.on_menuitem_branch_tags_activate,
                "on_menuitem_branch_status_activate": self.on_menuitem_branch_status_activate,
                "on_menuitem_branch_missing_revisions_activate": self.on_menuitem_branch_missing_revisions_activate,
                "on_menuitem_branch_conflicts_activate": self.on_menuitem_branch_conflicts_activate,
                "on_menuitem_stats_diff_activate": self.on_menuitem_stats_diff_activate,
                "on_menuitem_stats_log_activate": self.on_menuitem_stats_log_activate,
                "on_menuitem_stats_infos_activate": self.on_menuitem_stats_infos_activate,
                "on_toolbutton_refresh_clicked": self.on_menuitem_view_refresh_activate,
                "on_toolbutton_log_clicked": self.on_menuitem_stats_log_activate,
                #"on_menutoolbutton_diff_clicked": self.on_menuitem_stats_diff_activate,
                "on_toolbutton_diff_clicked": self.on_menuitem_stats_diff_activate,
                "on_toolbutton_commit_clicked": self.on_menuitem_branch_commit_activate,
                "on_toolbutton_pull_clicked": self.on_menuitem_branch_pull_activate,
                "on_toolbutton_push_clicked": self.on_menuitem_branch_push_activate,
                "on_treeview_right_button_press_event": self.on_treeview_right_button_press_event,
                "on_treeview_right_row_activated": self.on_treeview_right_row_activated,
                "on_treeview_left_button_press_event": self.on_treeview_left_button_press_event,
                "on_treeview_left_row_activated": self.on_treeview_left_row_activated,
                "on_button_location_up_clicked": self.on_button_location_up_clicked,
                "on_button_location_jump_clicked": self.on_button_location_jump_clicked,
                "on_entry_location_key_press_event": self.on_entry_location_key_press_event
            }
        
        # Connect the signals to the handlers
        self.toplevel.signal_autoconnect(dic)
        
        self._just_started = True
        
        # Apply window size and position
        width = self.pref.get_preference('window_width', 'int')
        height = self.pref.get_preference('window_height', 'int')
        self.window.resize(width, height)
        x = self.pref.get_preference('window_x', 'int')
        y = self.pref.get_preference('window_y', 'int')
        self.window.move(x, y)
        # Apply paned position
        pos = self.pref.get_preference('paned_position', 'int')
        self.hpaned_main.set_position(pos)
        
        # Apply menu to the toolbutton
        #menubutton = self.toplevel.get_widget('menutoolbutton_diff')
        #menubutton.set_menu(handler.menu.toolbar_diff)
        
        # Now we can show the window
        self.window.show()
        
        # Show drive selector if under Win32
        if sys.platform == 'win32':
            self.hbox_location.pack_start(self.combobox_drive, False, False, 0)
            self.hbox_location.reorder_child(self.combobox_drive, 1)
            self.combobox_drive.show()
            self.gen_hard_selector()
        
        self._load_left()

        # Apply menu state
        self.menuitem_view_show_hidden_files.set_active(self.pref.get_preference('dotted_files', 'bool'))

        # We're starting local
        self.remote = False
        self.remote_branch = None
        self.remote_path = None
        
        self.set_path(os.getcwd())
        self._load_right()
        
        self._just_started = False

    def set_path(self, path):
        self.notbranch = False
        
        if os.path.isdir(path):
            self.image_location_error.destroy()
            self.remote = False
            
            # We're local
            try:
                self.wt, self.wtpath = WorkingTree.open_containing(path)
            except (bzrerrors.NotBranchError, bzrerrors.NoWorkingTree):
                self.notbranch = True
            
            # If we're in the root, we cannot go up anymore
            if sys.platform == 'win32':
                drive, tail = os.path.splitdrive(self.path)
                if tail in ('', '/', '\\'):
                    self.button_location_up.set_sensitive(False)
                else:
                    self.button_location_up.set_sensitive(True)
            else:
                if self.path == '/':
                    self.button_location_up.set_sensitive(False)
                else:
                    self.button_location_up.set_sensitive(True)
        elif not os.path.isfile(path):
            # Doesn't seem to be a file nor a directory, trying to open a
            # remote location
            self._show_stock_image(gtk.STOCK_DISCONNECT)
            try:
                br = Branch.open_containing(path)[0]
            except bzrerrors.NotBranchError:
                self._show_stock_image(gtk.STOCK_DIALOG_ERROR)
                return False
            except bzrerrors.UnsupportedProtocol:
                self._show_stock_image(gtk.STOCK_DIALOG_ERROR)
                return False
            
            self._show_stock_image(gtk.STOCK_CONNECT)
            
            self.remote = True
           
            # We're remote
            tstart = time.time()
            self.remote_branch, self.remote_path = Branch.open_containing(path)
            tend = time.time()
            print "DEBUG: opening branch =", tend - tstart
            
            tstart = time.time()
            self.remote_entries = self.remote_branch.repository.get_inventory(self.remote_branch.last_revision()).entries()
            tend = time.time()
            print "DEBUG: retrieving entries =", tend - tstart
            
            tstart = time.time()
            if len(self.remote_path) == 0:
                self.remote_parent = self.remote_branch.repository.get_inventory(self.remote_branch.last_revision()).iter_entries_by_dir().next()[1].file_id
            else:
                for (name, type) in self.remote_entries:
                    if name == self.remote_path:
                        self.remote_parent = type.file_id
                        break
            tend = time.time()
            print "DEBUG: find parent id =", tend - tstart
            
            if not path.endswith('/'):
                path += '/'
            
            if self.remote_branch.base == path:
                self.button_location_up.set_sensitive(False)
            else:
                self.button_location_up.set_sensitive(True)
        
        self.statusbar.push(self.context_id, path)
        self.entry_location.set_text(path)
        self.path = path
        return True

    def get_path(self):
        if not self.remote:
            return self.path
        else:
            # Remote mode
            if len(self.remote_path) > 0:
                return self.remote_branch.base + self.remote_path + '/'
            else:
                return self.remote_branch.base
   
    def on_about_activate(self, widget):
        from bzrlib.plugins.gtk.dialog import about
        about()
        
    def on_button_location_up_clicked(self, widget):
        """ Location Up button handler. """
        if not self.remote:
            # Local mode
            self.set_path(os.path.split(self.get_path())[0])
        else:
            # Remote mode
            delim = '/'
            newpath = delim.join(self.get_path().split(delim)[:-2])
            newpath += '/'
            self.set_path(newpath)

        self.refresh_right()
    
    def on_button_location_jump_clicked(self, widget):
        """ Location Jump button handler. """
        location = self.entry_location.get_text()
        
        if self.set_path(location):
            self.refresh_right()
    
    def on_entry_location_key_press_event(self, widget, event):
        """ Key pressed handler for the location entry. """
        if event.keyval == 65293:
            # Return was hit, so we have to jump
            self.on_button_location_jump_clicked(widget)
    
    def on_menuitem_add_files_activate(self, widget):
        """ Add file(s)... menu handler. """
        from add import OliveAdd
        add = OliveAdd(self.wt, self.wtpath, self.get_selected_right())
        add.display()
    
    def on_menuitem_branch_get_activate(self, widget):
        """ Branch/Get... menu handler. """
        from bzrlib.plugins.gtk.branch import BranchDialog
        branch = BranchDialog(self.get_path(), self.window)
        response = branch.run()
        if response != gtk.RESPONSE_NONE:
            branch.hide()
        
            if response == gtk.RESPONSE_OK:
                self.refresh_right()
            
            branch.destroy()
    
    def on_menuitem_branch_checkout_activate(self, widget):
        """ Branch/Checkout... menu handler. """
        from bzrlib.plugins.gtk.checkout import CheckoutDialog
        checkout = CheckoutDialog(self.get_path(), self.window)
        response = checkout.run()
        if response != gtk.RESPONSE_NONE:
            checkout.hide()
        
            if response == gtk.RESPONSE_OK:
                self.refresh_right()
            
            checkout.destroy()
    
    @show_bzr_error
    def on_menuitem_branch_commit_activate(self, widget):
        """ Branch/Commit... menu handler. """
        commit = CommitDialog(self.wt, self.wtpath, self.notbranch, self.get_selected_right(), self.window)
        response = commit.run()
        if response != gtk.RESPONSE_NONE:
            commit.hide()
        
            if response == gtk.RESPONSE_OK:
                self.refresh_right()
            
            commit.destroy()
    
    def on_menuitem_branch_conflicts_activate(self, widget):
        """ Branch/Conflicts... menu handler. """
        conflicts = ConflictsDialog(self.wt, self.window)
        response = conflicts.run()
        if response != gtk.RESPONSE_NONE:
            conflicts.destroy()
    
    def on_menuitem_branch_merge_activate(self, widget):
        """ Branch/Merge... menu handler. """
        from bzrlib.plugins.gtk.merge import MergeDialog
        
        if self.check_for_changes():
            error_dialog(_('There are local changes in the branch'),
                         _('Please commit or revert the changes before merging.'))
        else:
            merge = MergeDialog(self.wt, self.wtpath)
            merge.display()

    @show_bzr_error
    def on_menuitem_branch_missing_revisions_activate(self, widget):
        """ Branch/Missing revisions menu handler. """
        local_branch = self.wt.branch
        
        other_branch = local_branch.get_parent()
        if other_branch is None:
            error_dialog(_('Parent location is unknown'),
                         _('Cannot determine missing revisions if no parent location is known.'))
            return
        
        remote_branch = Branch.open(other_branch)
        
        if remote_branch.base == local_branch.base:
            remote_branch = local_branch

        ret = len(local_branch.missing_revisions(remote_branch))

        if ret > 0:
            info_dialog(_('There are missing revisions'),
                        _('%d revision(s) missing.') % ret)
        else:
            info_dialog(_('Local branch up to date'),
                        _('There are no missing revisions.'))

    @show_bzr_error
    def on_menuitem_branch_pull_activate(self, widget):
        """ Branch/Pull menu handler. """
        branch_to = self.wt.branch

        location = branch_to.get_parent()
        if location is None:
            error_dialog(_('Parent location is unknown'),
                                     _('Pulling is not possible until there is a parent location.'))
            return

        branch_from = Branch.open(location)

        if branch_to.get_parent() is None:
            branch_to.set_parent(branch_from.base)

        #old_rh = branch_to.revision_history()
        #if tree_to is not None:
        #    tree_to.pull(branch_from)
        #else:
        #    branch_to.pull(branch_from)
        ret = branch_to.pull(branch_from)
        
        info_dialog(_('Pull successful'), _('%d revision(s) pulled.') % ret)
    
    def on_menuitem_branch_push_activate(self, widget):
        """ Branch/Push... menu handler. """
        push = PushDialog(self.wt.branch, self.window)
        response = push.run()
        if response != gtk.RESPONSE_NONE:
            push.destroy()
    
    @show_bzr_error
    def on_menuitem_branch_revert_activate(self, widget):
        """ Branch/Revert all changes menu handler. """
        ret = self.wt.revert([])
        if ret:
            warning_dialog(_('Conflicts detected'),
                           _('Please have a look at the working tree before continuing.'))
        else:
            info_dialog(_('Revert successful'),
                        _('All files reverted to last revision.'))
        self.refresh_right()
    
    def on_menuitem_branch_status_activate(self, widget):
        """ Branch/Status... menu handler. """
        from bzrlib.plugins.gtk.status import StatusDialog
        status = StatusDialog(self.wt, self.wtpath)
        response = status.run()
        if response != gtk.RESPONSE_NONE:
            status.destroy()
    
    def on_menuitem_branch_initialize_activate(self, widget):
        """ Initialize current directory. """
        init = InitDialog(self.path, self.window)
        response = init.run()
        if response != gtk.RESPONSE_NONE:
            init.hide()
        
            if response == gtk.RESPONSE_OK:
                self.refresh_right()
            
            init.destroy()
        
    def on_menuitem_branch_tags_activate(self, widget):
        """ Branch/Tags... menu handler. """
        from bzrlib.plugins.gtk.tags import TagsWindow
        window = TagsWindow(self.wt.branch, self.window)
        window.show()
    
    def on_menuitem_file_annotate_activate(self, widget):
        """ File/Annotate... menu handler. """
        if self.get_selected_right() is None:
            error_dialog(_('No file was selected'),
                         _('Please select a file from the list.'))
            return
        
        branch = self.wt.branch
        file_id = self.wt.path2id(self.wt.relpath(os.path.join(self.path, self.get_selected_right())))
        
        window = GAnnotateWindow(all=False, plain=False)
        window.set_title(os.path.join(self.path, self.get_selected_right()) + " - Annotate")
        config = GAnnotateConfig(window)
        window.show()
        branch.lock_read()
        try:
            window.annotate(self.wt, branch, file_id)
        finally:
            branch.unlock()
    
    def on_menuitem_file_make_directory_activate(self, widget):
        """ File/Make directory... menu handler. """
        from mkdir import OliveMkdir
        mkdir = OliveMkdir(self.wt, self.wtpath)
        mkdir.display()
    
    def on_menuitem_file_move_activate(self, widget):
        """ File/Move... menu handler. """
        from move import OliveMove
        move = OliveMove(self.wt, self.wtpath, self.get_selected_right())
        move.display()
    
    def on_menuitem_file_rename_activate(self, widget):
        """ File/Rename... menu handler. """
        from rename import OliveRename
        rename = OliveRename(self.wt, self.wtpath, self.get_selected_right())
        rename.display()

    def on_menuitem_remove_file_activate(self, widget):
        """ Remove (unversion) selected file. """
        from remove import OliveRemoveDialog
        remove = OliveRemoveDialog(self.wt, self.wtpath,
                                   selected=self.get_selected_right(),
                                   parent=self.window)
        response = remove.run()
        
        if response != gtk.RESPONSE_NONE:
            remove.hide()
        
            if response == gtk.RESPONSE_OK:
                self.set_path(self.path)
                self.refresh_right()
            
            remove.destroy()
    
    def on_menuitem_stats_diff_activate(self, widget):
        """ Statistics/Differences... menu handler. """
        window = DiffWindow()
        parent_tree = self.wt.branch.repository.revision_tree(self.wt.branch.last_revision())
        window.set_diff(self.wt.branch.nick, self.wt, parent_tree)
        window.show()
    
    def on_menuitem_stats_infos_activate(self, widget):
        """ Statistics/Informations... menu handler. """
        from info import OliveInfo
        info = OliveInfo(self.wt)
        info.display()
    
    def on_menuitem_stats_log_activate(self, widget):
        """ Statistics/Log... menu handler. """
        window = branchwin.BranchWindow()
        window.set_branch(self.wt.branch, self.wt.branch.last_revision(), None)
        window.show()
    
    def on_menuitem_view_refresh_activate(self, widget):
        """ View/Refresh menu handler. """
        # Refresh the left pane
        self.refresh_left()
        # Refresh the right pane
        self.refresh_right()
   
    def on_menuitem_view_show_hidden_files_activate(self, widget):
        """ View/Show hidden files menu handler. """
        self.pref.set_preference('dotted_files', widget.get_active())
        if self.path is not None:
            self.refresh_right()

    def on_treeview_left_button_press_event(self, widget, event):
        """ Occurs when somebody right-clicks in the bookmark list. """
        if event.button == 3:
            # Don't show context with nothing selected
            if self.get_selected_left() == None:
                return

            # Create a menu
            from menu import OliveMenu
            menu = OliveMenu(path=self.get_path(),
                             selected=self.get_selected_left(),
                             app=self)
            
            menu.left_context_menu().popup(None, None, None, 0,
                                           event.time)

    def on_treeview_left_row_activated(self, treeview, path, view_column):
        """ Occurs when somebody double-clicks or enters an item in the
        bookmark list. """

        newdir = self.get_selected_left()
        print "DEBUG: newdir =", newdir
        if newdir == None:
            return

        if self.set_path(newdir):
            self.refresh_right()

    def on_treeview_right_button_press_event(self, widget, event):
        """ Occurs when somebody right-clicks in the file list. """
        if event.button == 3:
            # Create a menu
            from menu import OliveMenu
            menu = OliveMenu(path=self.get_path(),
                             selected=self.get_selected_right(),
                             app=self)
            # get the menu items
            m_add = menu.ui.get_widget('/context_right/add')
            m_remove = menu.ui.get_widget('/context_right/remove')
            m_rename = menu.ui.get_widget('/context_right/rename')
            m_revert = menu.ui.get_widget('/context_right/revert')
            m_commit = menu.ui.get_widget('/context_right/commit')
            m_diff = menu.ui.get_widget('/context_right/diff')
            # check if we're in a branch
            try:
                from bzrlib.branch import Branch
                Branch.open_containing(self.get_path())
                m_add.set_sensitive(True)
                m_remove.set_sensitive(True)
                m_rename.set_sensitive(True)
                m_revert.set_sensitive(True)
                m_commit.set_sensitive(True)
                m_diff.set_sensitive(True)
            except bzrerrors.NotBranchError:
                m_add.set_sensitive(False)
                m_remove.set_sensitive(False)
                m_rename.set_sensitive(False)
                m_revert.set_sensitive(False)
                m_commit.set_sensitive(False)
                m_diff.set_sensitive(False)

            menu.right_context_menu().popup(None, None, None, 0,
                                            event.time)
        
    def on_treeview_right_row_activated(self, treeview, path, view_column):
        """ Occurs when somebody double-clicks or enters an item in the
        file list. """
        from launch import launch
        
        newdir = self.get_selected_right()
        
        if not self.remote:
            # We're local
            if newdir == '..':
                self.set_path(os.path.split(self.get_path())[0])
            else:
                fullpath = os.path.join(self.get_path(), newdir)
                if os.path.isdir(fullpath):
                    # selected item is an existant directory
                    self.set_path(fullpath)
                else:
                    launch(fullpath)
        else:
            # We're remote
            if self._is_remote_dir(self.get_path() + newdir):
                self.set_path(self.get_path() + newdir)
        
        self.refresh_right()
    
    def on_window_main_delete_event(self, widget, event=None):
        """ Do some stuff before exiting. """
        width, height = self.window_main.get_size()
        self.pref.set_preference('window_width', width)
        self.pref.set_preference('window_height', height)
        x, y = self.window_main.get_position()
        self.pref.set_preference('window_x', x)
        self.pref.set_preference('window_y', y)
        self.pref.set_preference('paned_position',
                                 self.hpaned_main.get_position())
        
        self.pref.write()
        self.window_main.destroy()
        
    def _load_left(self):
        """ Load data into the left panel. (Bookmarks) """
        # Create TreeStore
        treestore = gtk.TreeStore(str, str)
        
        # Get bookmarks
        bookmarks = self.pref.get_bookmarks()
        
        # Add them to the TreeStore
        titer = treestore.append(None, [_('Bookmarks'), None])
        for item in bookmarks:
            title = self.pref.get_bookmark_title(item)
            treestore.append(titer, [title, item])
        
        # Create the column and add it to the TreeView
        self.treeview_left.set_model(treestore)
        tvcolumn_bookmark = gtk.TreeViewColumn(_('Bookmark'))
        self.treeview_left.append_column(tvcolumn_bookmark)
        
        # Set up the cells
        cell = gtk.CellRendererText()
        tvcolumn_bookmark.pack_start(cell, True)
        tvcolumn_bookmark.add_attribute(cell, 'text', 0)
        
        # Expand the tree
        self.treeview_left.expand_all()

    def _load_right(self):
        """ Load data into the right panel. (Filelist) """
        # Create ListStore
        # Model: [icon, dir, name, status text, status, size (int), size (human), mtime (int), mtime (local)]
        liststore = gtk.ListStore(str, gobject.TYPE_BOOLEAN, str, str, str, gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_STRING)
        
        dirs = []
        files = []
        
        # Fill the appropriate lists
        dotted_files = self.pref.get_preference('dotted_files', 'bool')
        for item in os.listdir(self.path):
            if not dotted_files and item[0] == '.':
                continue
            if os.path.isdir(self.path + os.sep + item):
                dirs.append(item)
            else:
                files.append(item)
        
        if not self.notbranch:
            branch = self.wt.branch
            tree2 = self.wt.branch.repository.revision_tree(branch.last_revision())
        
            delta = self.wt.changes_from(tree2, want_unchanged=True)
        
        # Add'em to the ListStore
        for item in dirs:
            statinfo = os.stat(self.path + os.sep + item)
            liststore.append([gtk.STOCK_DIRECTORY, True, item, '', '', statinfo.st_size, self._format_size(statinfo.st_size), statinfo.st_mtime, self._format_date(statinfo.st_mtime)])
        for item in files:
            status = 'unknown'
            if not self.notbranch:
                filename = self.wt.relpath(self.path + os.sep + item)
                
                try:
                    self.wt.lock_read()
                    
                    for rpath, rpathnew, id, kind, text_modified, meta_modified in delta.renamed:
                        if rpathnew == filename:
                            status = 'renamed'
                    for rpath, id, kind in delta.added:
                        if rpath == filename:
                            status = 'added'
                    for rpath, id, kind in delta.removed:
                        if rpath == filename:
                            status = 'removed'
                    for rpath, id, kind, text_modified, meta_modified in delta.modified:
                        if rpath == filename:
                            status = 'modified'
                    for rpath, id, kind in delta.unchanged:
                        if rpath == filename:
                            status = 'unchanged'
                    for rpath, file_class, kind, id, entry in self.wt.list_files():
                        if rpath == filename and file_class == 'I':
                            status = 'ignored'
                finally:
                    self.wt.unlock()
            
            #try:
            #    status = fileops.status(path + os.sep + item)
            #except errors.PermissionDenied:
            #    continue
            
            if status == 'renamed':
                st = _('renamed')
            elif status == 'removed':
                st = _('removed')
            elif status == 'added':
                st = _('added')
            elif status == 'modified':
                st = _('modified')
            elif status == 'unchanged':
                st = _('unchanged')
            elif status == 'ignored':
                st = _('ignored')
            else:
                st = _('unknown')
            
            statinfo = os.stat(self.path + os.sep + item)
            liststore.append([gtk.STOCK_FILE, False, item, st, status, statinfo.st_size, self._format_size(statinfo.st_size), statinfo.st_mtime, self._format_date(statinfo.st_mtime)])
        
        # Create the columns and add them to the TreeView
        self.treeview_right.set_model(liststore)
        self._tvcolumn_filename = gtk.TreeViewColumn(_('Filename'))
        self._tvcolumn_status = gtk.TreeViewColumn(_('Status'))
        self._tvcolumn_size = gtk.TreeViewColumn(_('Size'))
        self._tvcolumn_mtime = gtk.TreeViewColumn(_('Last modified'))
        self.treeview_right.append_column(self._tvcolumn_filename)
        self.treeview_right.append_column(self._tvcolumn_status)
        self.treeview_right.append_column(self._tvcolumn_size)
        self.treeview_right.append_column(self._tvcolumn_mtime)
        
        # Set up the cells
        cellpb = gtk.CellRendererPixbuf()
        cell = gtk.CellRendererText()
        self._tvcolumn_filename.pack_start(cellpb, False)
        self._tvcolumn_filename.pack_start(cell, True)
        self._tvcolumn_filename.set_attributes(cellpb, stock_id=0)
        self._tvcolumn_filename.add_attribute(cell, 'text', 2)
        self._tvcolumn_status.pack_start(cell, True)
        self._tvcolumn_status.add_attribute(cell, 'text', 3)
        self._tvcolumn_size.pack_start(cell, True)
        self._tvcolumn_size.add_attribute(cell, 'text', 6)
        self._tvcolumn_mtime.pack_start(cell, True)
        self._tvcolumn_mtime.add_attribute(cell, 'text', 8)
        
        # Set up the properties of the TreeView
        self.treeview_right.set_headers_visible(True)
        self.treeview_right.set_headers_clickable(True)
        self.treeview_right.set_search_column(1)
        self._tvcolumn_filename.set_resizable(True)
        self._tvcolumn_status.set_resizable(True)
        self._tvcolumn_size.set_resizable(True)
        self._tvcolumn_mtime.set_resizable(True)
        # Set up sorting
        liststore.set_sort_func(13, self._sort_filelist_callback, None)
        liststore.set_sort_column_id(13, gtk.SORT_ASCENDING)
        self._tvcolumn_filename.set_sort_column_id(13)
        self._tvcolumn_status.set_sort_column_id(3)
        self._tvcolumn_size.set_sort_column_id(5)
        self._tvcolumn_mtime.set_sort_column_id(7)
        
        # Set sensitivity
        self.set_sensitivity()
        
    def get_selected_right(self):
        """ Get the selected filename. """
        treeselection = self.treeview_right.get_selection()
        (model, iter) = treeselection.get_selected()
        
        if iter is None:
            return None
        else:
            return model.get_value(iter, 2)
    
    def get_selected_left(self):
        """ Get the selected bookmark. """
        treeselection = self.treeview_left.get_selection()
        (model, iter) = treeselection.get_selected()
        
        if iter is None:
            return None
        else:
            return model.get_value(iter, 1)

    def set_statusbar(self, message):
        """ Set the statusbar message. """
        self.statusbar.push(self.context_id, message)
    
    def clear_statusbar(self):
        """ Clean the last message from the statusbar. """
        self.statusbar.pop(self.context_id)
    
    def set_sensitivity(self):
        """ Set menu and toolbar sensitivity. """
        self.menuitem_branch_init.set_sensitive(self.notbranch)
        self.menuitem_branch_get.set_sensitive(self.notbranch)
        self.menuitem_branch_checkout.set_sensitive(self.notbranch)
        self.menuitem_branch_pull.set_sensitive(not self.notbranch)
        self.menuitem_branch_push.set_sensitive(not self.notbranch)
        self.menuitem_branch_revert.set_sensitive(not self.notbranch)
        self.menuitem_branch_merge.set_sensitive(not self.notbranch)
        self.menuitem_branch_commit.set_sensitive(not self.notbranch)
        self.menuitem_branch_tags.set_sensitive(not self.notbranch)
        self.menuitem_branch_status.set_sensitive(not self.notbranch)
        self.menuitem_branch_missing.set_sensitive(not self.notbranch)
        self.menuitem_branch_conflicts.set_sensitive(not self.notbranch)
        self.menuitem_stats.set_sensitive(not self.notbranch)
        self.menuitem_add_files.set_sensitive(not self.notbranch)
        self.menuitem_remove_files.set_sensitive(not self.notbranch)
        self.menuitem_file_make_directory.set_sensitive(not self.notbranch)
        self.menuitem_file_rename.set_sensitive(not self.notbranch)
        self.menuitem_file_move.set_sensitive(not self.notbranch)
        self.menuitem_file_annotate.set_sensitive(not self.notbranch)
        #self.menutoolbutton_diff.set_sensitive(True)
        self.toolbutton_diff.set_sensitive(not self.notbranch)
        self.toolbutton_log.set_sensitive(not self.notbranch)
        self.toolbutton_commit.set_sensitive(not self.notbranch)
        self.toolbutton_pull.set_sensitive(not self.notbranch)
        self.toolbutton_push.set_sensitive(not self.notbranch)
    
    def refresh_left(self):
        """ Refresh the bookmark list. """
        
        # Get TreeStore and clear it
        treestore = self.treeview_left.get_model()
        treestore.clear()

        # Re-read preferences
        self.pref.read()
        
        # Get bookmarks
        bookmarks = self.pref.get_bookmarks()

        # Add them to the TreeStore
        titer = treestore.append(None, [_('Bookmarks'), None])
        for item in bookmarks:
            title = self.pref.get_bookmark_title(item)
            treestore.append(titer, [title, item])

        # Add the TreeStore to the TreeView
        self.treeview_left.set_model(treestore)

        # Expand the tree
        self.treeview_left.expand_all()

    def refresh_right(self, path=None):
        """ Refresh the file list. """
        if not self.remote:
            # We're local
            from bzrlib.workingtree import WorkingTree
    
            if path is None:
                path = self.get_path()
    
            # A workaround for double-clicking Bookmarks
            if not os.path.exists(path):
                return
    
            # Get ListStore and clear it
            liststore = self.treeview_right.get_model()
            liststore.clear()
            
            # Show Status column
            self._tvcolumn_status.set_visible(True)
    
            dirs = []
            files = []
    
            # Fill the appropriate lists
            dotted_files = self.pref.get_preference('dotted_files', 'bool')
            for item in os.listdir(path):
                if not dotted_files and item[0] == '.':
                    continue
                if os.path.isdir(path + os.sep + item):
                    dirs.append(item)
                else:
                    files.append(item)
            
            # Try to open the working tree
            notbranch = False
            try:
                tree1 = WorkingTree.open_containing(path)[0]
            except (bzrerrors.NotBranchError, bzrerrors.NoWorkingTree):
                notbranch = True
            
            if not notbranch:
                branch = tree1.branch
                tree2 = tree1.branch.repository.revision_tree(branch.last_revision())
            
                delta = tree1.changes_from(tree2, want_unchanged=True)
                
            # Add'em to the ListStore
            for item in dirs:
                statinfo = os.stat(self.path + os.sep + item)
                liststore.append([gtk.STOCK_DIRECTORY, True, item, '', '', statinfo.st_size, self._format_size(statinfo.st_size), statinfo.st_mtime, self._format_date(statinfo.st_mtime)])
            for item in files:
                status = 'unknown'
                if not notbranch:
                    filename = tree1.relpath(path + os.sep + item)
                    
                    try:
                        self.wt.lock_read()
                        
                        for rpath, rpathnew, id, kind, text_modified, meta_modified in delta.renamed:
                            if rpathnew == filename:
                                status = 'renamed'
                        for rpath, id, kind in delta.added:
                            if rpath == filename:
                                status = 'added'                
                        for rpath, id, kind in delta.removed:
                            if rpath == filename:
                                status = 'removed'
                        for rpath, id, kind, text_modified, meta_modified in delta.modified:
                            if rpath == filename:
                                status = 'modified'
                        for rpath, id, kind in delta.unchanged:
                            if rpath == filename:
                                status = 'unchanged'
                        for rpath, file_class, kind, id, entry in self.wt.list_files():
                            if rpath == filename and file_class == 'I':
                                status = 'ignored'
                    finally:
                        self.wt.unlock()
                
                #try:
                #    status = fileops.status(path + os.sep + item)
                #except errors.PermissionDenied:
                #    continue
    
                if status == 'renamed':
                    st = _('renamed')
                elif status == 'removed':
                    st = _('removed')
                elif status == 'added':
                    st = _('added')
                elif status == 'modified':
                    st = _('modified')
                elif status == 'unchanged':
                    st = _('unchanged')
                elif status == 'ignored':
                    st = _('ignored')
                else:
                    st = _('unknown')
                
                statinfo = os.stat(self.path + os.sep + item)
                liststore.append([gtk.STOCK_FILE, False, item, st, status, statinfo.st_size, self._format_size(statinfo.st_size), statinfo.st_mtime, self._format_date(statinfo.st_mtime)])
        else:
            # We're remote
            # NOTE: First approach, without any caching or optimization
            
            # Get ListStore and clear it
            liststore = self.treeview_right.get_model()
            liststore.clear()
            
            # Hide Status column
            self._tvcolumn_status.set_visible(False)
            
            dirs = []
            files = []
            
            self._show_stock_image(gtk.STOCK_REFRESH)
            
            tstart = time.time()
            for (name, type) in self.remote_entries:
                if type.kind == 'directory':
                    dirs.append(type)
                elif type.kind == 'file':
                    files.append(type)
            tend = time.time()
            print "DEBUG: separating files and dirs =", tend - tstart
            
            class HistoryCache:
                """ Cache based on revision history. """
                def __init__(self, history):
                    self._history = history
                
                def _lookup_revision(self, revid):
                    print "DEBUG: looking up revision =", revid
                    for r in self._history:
                        if r.revision_id == revid:
                            print "DEBUG: revision found =", r
                            return r
                    print "DEBUG: revision not found, adding it to the cache."
                    rev = repo.get_revision(revid)
                    self._history.append(rev)
                    return rev
            
            repo = self.remote_branch.repository
            
            tstart = time.time()
            revhistory = self.remote_branch.revision_history()
            try:
                revs = repo.get_revisions(revhistory)
                cache = HistoryCache(revs)
            except bzrerrors.InvalidHttpResponse:
                # Fallback to dummy algorithm, because of LP: #115209
                cache = HistoryCache([])
            
            tend = time.time()
            print "DEBUG: fetching all revisions =", tend - tstart
            
            tstart = time.time()
            for item in dirs:
                ts = time.time()
                if item.parent_id == self.remote_parent:
                    rev = cache._lookup_revision(item.revision)
                    print "DEBUG: revision result =", rev
                    liststore.append([ gtk.STOCK_DIRECTORY,
                                       True,
                                       item.name,
                                       '',
                                       '',
                                       0,
                                       self._format_size(0),
                                       rev.timestamp,
                                       self._format_date(rev.timestamp)
                                   ])
                while gtk.events_pending():
                    gtk.main_iteration()
                te = time.time()
                print "DEBUG: processed", item.name, "in", te - ts
            tend = time.time()
            print "DEBUG: filling up dirs =", tend - tstart
            
            tstart = time.time()
            for item in files:
                ts = time.time()
                if item.parent_id == self.remote_parent:
                    rev = cache._lookup_revision(item.revision)
                    liststore.append([ gtk.STOCK_FILE,
                                       False,
                                       item.name,
                                       '',
                                       '',
                                       item.text_size,
                                       self._format_size(item.text_size),
                                       rev.timestamp,
                                       self._format_date(rev.timestamp)
                                   ])
                while gtk.events_pending():
                    gtk.main_iteration()
                te = time.time()
                print "DEBUG: processed", item.name, "in", te - ts
            tend = time.time()
            print "DEBUG: filling up files =", tend - tstart
            
            self.image_location_error.destroy()

        # Columns should auto-size
        self.treeview_right.columns_autosize()
        
        # Set sensitivity
        self.set_sensitivity()

    def _harddisks(self):
        """ Returns hard drive letters under Win32. """
        try:
            import win32file
            import string
        except ImportError:
            if sys.platform == 'win32':
                print "pyWin32 modules needed to run Olive on Win32."
                sys.exit(1)
            else:
                pass
        
        driveletters = []
        for drive in string.ascii_uppercase:
            if win32file.GetDriveType(drive+':') == win32file.DRIVE_FIXED:
                driveletters.append(drive+':')
        return driveletters
    
    def gen_hard_selector(self):
        """ Generate the hard drive selector under Win32. """
        drives = self._harddisks()
        for drive in drives:
            self.combobox_drive.append_text(drive)
        self.combobox_drive.set_active(drives.index(os.getcwd()[0:2]))
    
    def _refresh_drives(self, combobox):
        if self._just_started:
            return
        model = combobox.get_model()
        active = combobox.get_active()
        if active >= 0:
            drive = model[active][0]
            self.set_path(drive + '\\')
            self.refresh_right(drive + '\\')
    
    def check_for_changes(self):
        """ Check whether there were changes in the current working tree. """
        old_tree = self.wt.branch.repository.revision_tree(self.wt.branch.last_revision())
        delta = self.wt.changes_from(old_tree)

        changes = False
        
        if len(delta.added) or len(delta.removed) or len(delta.renamed) or len(delta.modified):
            changes = True
        
        return changes
    
    def _sort_filelist_callback(self, model, iter1, iter2, data):
        """ The sort callback for the file list, return values:
        -1: iter1 < iter2
        0: iter1 = iter2
        1: iter1 > iter2
        """
        name1 = model.get_value(iter1, 2)
        name2 = model.get_value(iter2, 2)
        
        if model.get_value(iter1, 1):
            # item1 is a directory
            if not model.get_value(iter2, 1):
                # item2 isn't
                return -1
            else:
                # both of them are directories, we compare their names
                if name1 < name2:
                    return -1
                elif name1 == name2:
                    return 0
                else:
                    return 1
        else:
            # item1 is not a directory
            if model.get_value(iter2, 1):
                # item2 is
                return 1
            else:
                # both of them are files, compare them
                if name1 < name2:
                    return -1
                elif name1 == name2:
                    return 0
                else:
                    return 1
    
    def _format_size(self, size):
        """ Format size to a human readable format. """
        return size
    
    def _format_date(self, timestamp):
        """ Format the time (given in secs) to a human readable format. """
        return time.ctime(timestamp)
    
    def _is_remote_dir(self, location):
        """ Determine whether the given location is a directory or not. """
        if not self.remote:
            # We're in local mode
            return False
        else:
            branch, path = Branch.open_containing(location)
            for (name, type) in self.remote_entries:
                if name == path and type.kind == 'directory':
                    # We got it
                    return True
            # Either it's not a directory or not in the inventory
            return False
    
    def _show_stock_image(self, stock_id):
        """ Show a stock image next to the location entry. """
        self.image_location_error.destroy()
        self.image_location_error = gtk.image_new_from_stock(stock_id, gtk.ICON_SIZE_BUTTON)
        self.hbox_location.pack_start(self.image_location_error, False, False, 0)
        if sys.platform == 'win32':
            self.hbox_location.reorder_child(self.image_location_error, 2)
        else:
            self.hbox_location.reorder_child(self.image_location_error, 1)
        self.image_location_error.show()
        while gtk.events_pending():
            gtk.main_iteration()

import ConfigParser

class Preferences:
    """ A class which handles Olive's preferences. """
    def __init__(self, path=None):
        """ Initialize the Preferences class. """
        # Some default options
        self.defaults = { 'strict_commit' : False,
                          'dotted_files'  : False,
                          'window_width'  : 700,
                          'window_height' : 400,
                          'window_x'      : 40,
                          'window_y'      : 40,
                          'paned_position': 200 }

        # Create a config parser object
        self.config = ConfigParser.RawConfigParser()

        # Set filename
        if path is None:
            if sys.platform == 'win32':
                # Windows - no dotted files
                self._filename = os.path.expanduser('~/olive.conf')
            else:
                self._filename = os.path.expanduser('~/.olive.conf')
        else:
            self._filename = path
        
        # Load the configuration
        self.read()
        
    def _get_default(self, option):
        """ Get the default option for a preference. """
        try:
            ret = self.defaults[option]
        except KeyError:
            return None
        else:
            return ret

    def refresh(self):
        """ Refresh the configuration. """
        # First write out the changes
        self.write()
        # Then load the configuration again
        self.read()

    def read(self):
        """ Just read the configuration. """
        # Re-initialize the config parser object to avoid some bugs
        self.config = ConfigParser.RawConfigParser()
        self.config.read([self._filename])
    
    def write(self):
        """ Write the configuration to the appropriate files. """
        fp = open(self._filename, 'w')
        self.config.write(fp)
        fp.close()

    def get_bookmarks(self):
        """ Return the list of bookmarks. """
        bookmarks = self.config.sections()
        if self.config.has_section('preferences'):
            bookmarks.remove('preferences')
        return bookmarks

    def add_bookmark(self, path):
        """ Add bookmark. """
        try:
            self.config.add_section(path)
        except ConfigParser.DuplicateSectionError:
            return False
        else:
            return True

    def get_bookmark_title(self, path):
        """ Get bookmark title. """
        try:
            ret = self.config.get(path, 'title')
        except ConfigParser.NoOptionError:
            ret = path
        
        return ret
    
    def set_bookmark_title(self, path, title):
        """ Set bookmark title. """
        # FIXME: What if path isn't listed yet?
        # FIXME: Canonicalize paths first?
        self.config.set(path, 'title', title)
    
    def remove_bookmark(self, path):
        """ Remove bookmark. """
        return self.config.remove_section(path)

    def set_preference(self, option, value):
        """ Set the value of the given option. """
        if value is True:
            value = 'yes'
        elif value is False:
            value = 'no'
        
        if self.config.has_section('preferences'):
            self.config.set('preferences', option, value)
        else:
            self.config.add_section('preferences')
            self.config.set('preferences', option, value)

    def get_preference(self, option, kind='str'):
        """ Get the value of the given option.
        
        :param kind: str/bool/int/float. default: str
        """
        if self.config.has_option('preferences', option):
            if kind == 'bool':
                return self.config.getboolean('preferences', option)
            elif kind == 'int':
                return self.config.getint('preferences', option)
            elif kind == 'float':
                return self.config.getfloat('preferences', option)
            else:
                return self.config.get('preferences', option)
        else:
            try:
                return self._get_default(option)
            except KeyError:
                return None
 
